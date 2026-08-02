import argparse
import json
import os
import re
import subprocess
import sys

from eval_file_filter import normalize_relpath, write_eval_file_list
from path_config import resolve_source_root


DEFAULT_EXCLUDES = [
    "test",
    "tests",
    "build",
    "dist",
    "out",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
]
CPP_SOURCE_EXTENSIONS = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx")


def jar_arg_path(path):
    return os.path.abspath(path).replace(os.sep, "/")


def parse_module_info(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    module_names_start = file_content.find("ModuleNames : {") + len("ModuleNames : {")
    module_names_end = file_content.find("}", module_names_start)
    module_descriptions_start = file_content.find("ModuleDescriptions : {") + len("ModuleDescriptions : {")
    module_descriptions_end = file_content.find("}", module_descriptions_start)

    module_names_raw = file_content[module_names_start:module_names_end].strip()
    module_descriptions_raw = file_content[module_descriptions_start:module_descriptions_end].strip()

    module_names = [name.strip('"\n\t ') for name in module_names_raw.splitlines() if name.strip()]
    module_descriptions = [desc.strip('"\n\t ') for desc in module_descriptions_raw.splitlines() if desc.strip()]

    if len(module_names) != len(module_descriptions):
        raise ValueError("Module names and descriptions count mismatch.")

    return dict(zip(module_names, module_descriptions))


def extract_group_names(json_path):
    if not json_path or not os.path.exists(json_path):
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        entry.get("name")
        for entry in data.get("structure", [])
        if entry.get("@type") == "group" and entry.get("name")
    ]


def extract_gt_file_paths(json_path):
    if not json_path or not os.path.exists(json_path):
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_paths = []

    def visit(node):
        if isinstance(node, dict):
            if node.get("@type") == "item" and node.get("name"):
                file_paths.append(normalize_relpath(node["name"]))
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(data.get("structure", []))
    return file_paths


def has_cpp_sources(path):
    if not path or not os.path.isdir(path):
        return False
    for current_dir, _, files in os.walk(path):
        if any(file.lower().endswith(CPP_SOURCE_EXTENSIONS) for file in files):
            return True
    return False


def candidate_source_roots(input_path):
    candidates = []

    def add(path):
        if path and os.path.isdir(path):
            resolved = os.path.abspath(path)
            if resolved not in candidates:
                candidates.append(resolved)

    input_path = os.path.abspath(input_path)
    add(input_path)
    add(resolve_source_root(input_path, suffix=CPP_SOURCE_EXTENSIONS))

    basename = os.path.basename(os.path.normpath(input_path))
    add(os.path.join(input_path, basename))

    for child in sorted(os.listdir(input_path)) if os.path.isdir(input_path) else []:
        child_path = os.path.join(input_path, child)
        if os.path.isdir(child_path) and has_cpp_sources(child_path):
            add(child_path)
            add(resolve_source_root(child_path, suffix=CPP_SOURCE_EXTENSIONS))

    return candidates


def gt_path_matches(relative_file_path, gt_file_path):
    if relative_file_path == gt_file_path:
        return True
    if relative_file_path.endswith("/" + gt_file_path):
        return True
    if gt_file_path.endswith("/" + relative_file_path):
        return True
    return False


def score_source_root(source_root, gt_file_paths):
    if not gt_file_paths or not has_cpp_sources(source_root):
        return (0, 0)

    gt_file_set = set(gt_file_paths)
    exact_matches = 0
    suffix_matches = 0
    source_files = []
    for current_dir, _, files in os.walk(source_root):
        for file in files:
            if file.lower().endswith(CPP_SOURCE_EXTENSIONS):
                abs_file_path = os.path.join(current_dir, file)
                source_files.append(normalize_relpath(os.path.relpath(abs_file_path, source_root)))

    for relative_file_path in source_files:
        if relative_file_path in gt_file_set:
            exact_matches += 1
            continue
        if any(gt_path_matches(relative_file_path, gt_file_path) for gt_file_path in gt_file_paths):
            suffix_matches += 1

    return (exact_matches, suffix_matches)


def resolve_source_root_for_gt(input_path, gt_path):
    fallback = resolve_source_root(input_path, suffix=CPP_SOURCE_EXTENSIONS)
    gt_file_paths = extract_gt_file_paths(gt_path)
    if not gt_file_paths:
        return fallback

    candidates = candidate_source_roots(input_path)
    if os.path.isdir(fallback):
        candidates.extend(candidate_source_roots(fallback))

    best_path = fallback
    best_score = (-1, -1)
    for candidate in candidates:
        score = score_source_root(candidate, gt_file_paths)
        if score > best_score:
            best_path = candidate
            best_score = score

    if best_score > (0, 0):
        return best_path
    return fallback


def infer_project_name(datapath, module_info_file):
    module_filename = os.path.basename(module_info_file)
    match = re.match(r"updated_config_(.+)\.txt$", module_filename)
    if match:
        return match.group(1)
    return os.path.basename(os.path.normpath(datapath))


def write_module_info(module_info, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("ModuleNames : {\n")
        for module in module_info.keys():
            file.write(f'    "{module}"\n')
        file.write("}\n\nModuleDescriptions : {\n")
        for desc in module_info.values():
            file.write(f'    "{desc}"\n')
        file.write("}\n")


def generate_tfidf_scores(script_dir, project_name, project_folder, module_info_file, threshold, output_directory):
    project_parent, _ = os.path.split(os.path.abspath(project_folder))
    jar_path = os.path.join(script_dir, "tfidf_score.jar")
    command = [
        "java",
        "-jar",
        jar_arg_path(jar_path),
        project_name,
        jar_arg_path(project_parent),
        jar_arg_path(module_info_file),
        "tfidf",
        str(threshold),
        jar_arg_path(output_directory),
        "cpp",
    ]
    subprocess.run(command, check=True)


def execute_package_tree(script_dir, project_path, module_info_file, output_directory, eval_files_path=None):
    command = [
        sys.executable,
        "-u",
        os.path.join(script_dir, "package_tree.py"),
        project_path,
        "--exclude",
        *DEFAULT_EXCLUDES,
        "--module_path",
        module_info_file,
        "--tfidf_result_path",
        os.path.join(output_directory, "tfidf-file-module_scores.csv"),
        "--output_path",
        output_directory,
    ]
    if eval_files_path:
        command.extend(["--eval_files", eval_files_path])

    with open(os.path.join(output_directory, "call_deepseek.log"), "w", encoding="utf-8") as log_file:
        subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT, check=True)


def iter_removed_modules(module_info, gt_path, max_modules):
    module_names = list(module_info.keys())
    gt_groups = extract_group_names(gt_path)
    selected = module_names if max_modules is None else module_names[:max_modules]

    for module_name in selected:
        if gt_groups is not None and module_name not in gt_groups:
            print(f"[Skip] '{module_name}' not exist in Ground Truth group, continue")
            continue
        yield module_name


def run_python_experiment(script_dir, datapath, module_info_file, gt_path, threshold, max_modules):
    input_datapath = os.path.abspath(datapath)
    datapath = resolve_source_root_for_gt(input_datapath, gt_path)
    if os.path.abspath(datapath) != input_datapath:
        print(f"[Path] Resolved source root: {datapath}")

    module_info = parse_module_info(module_info_file)
    all_module_names = list(module_info.keys())
    project = infer_project_name(datapath, module_info_file)

    for module_to_remove in iter_removed_modules(module_info, gt_path, max_modules):
        output_directory = os.path.join(script_dir, project, f"removed_{module_to_remove}")
        if os.path.exists(output_directory):
            print(f"[Skip] '{output_directory}' exists")
            continue

        updated_module_info = module_info.copy()
        del updated_module_info[module_to_remove]

        os.makedirs(output_directory, exist_ok=True)
        new_module_info_file = os.path.join(output_directory, "updated_module_info.txt")
        write_module_info(updated_module_info, new_module_info_file)
        print(f"New module info file generated: {new_module_info_file}")

        eval_files_path = write_eval_file_list(gt_path, all_module_names, module_to_remove, output_directory)
        generate_tfidf_scores(script_dir, project, datapath, new_module_info_file, threshold, output_directory)
        execute_package_tree(script_dir, datapath, new_module_info_file, output_directory, eval_files_path)


def main(script_dir, default_max_modules=5):
    parser = argparse.ArgumentParser(description="Run C/C++ project module-removal experiments.")
    parser.add_argument("datapath", type=str, help="Path to the C/C++ project folder")
    parser.add_argument("-m", "--module_info", type=str, required=True, help="Path to the module info file")
    parser.add_argument("-a", "--mapping", type=str, default="tfidf", help="Kept for command compatibility")
    parser.add_argument("-t", "--threshold", type=float, default=50, help="TF-IDF score threshold")
    parser.add_argument("-g", "--gt", type=str, help="Ground Truth Path")
    parser.add_argument(
        "--max-modules",
        type=int,
        default=default_max_modules,
        help="Maximum number of modules to remove; use 0 to process all modules",
    )
    args = parser.parse_args()

    max_modules = None if args.max_modules == 0 else args.max_modules
    run_python_experiment(
        script_dir=os.path.abspath(script_dir),
        datapath=args.datapath,
        module_info_file=args.module_info,
        gt_path=args.gt,
        threshold=args.threshold,
        max_modules=max_modules,
    )
