import argparse
import json
import os
import subprocess
import sys

from eval_file_filter import write_eval_file_list
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
        "python",
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
    datapath = resolve_source_root(datapath, suffix=".py")
    if os.path.abspath(datapath) != datapath:
        print(f"[Path] Resolved source root: {datapath}")

    module_info = parse_module_info(module_info_file)
    all_module_names = list(module_info.keys())
    project = os.path.basename(os.path.normpath(datapath))

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
    parser = argparse.ArgumentParser(description="Run Python project module-removal experiments.")
    parser.add_argument("datapath", type=str, help="Path to the Python project folder")
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
