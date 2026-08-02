import argparse
import json
import os
import re
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASELINE_ROOT = SCRIPT_DIR.parents[1]
REPO_ROOT = SCRIPT_DIR.parents[2]
TFIDF_JAR = SCRIPT_DIR / "tfidf_score.jar"
DEFAULT_PROJECT_ROOT = REPO_ROOT / "experiment" / "project" / "java"
DEFAULT_OUTPUT_ROOT = BASELINE_ROOT / "result" / "java-multi_missing-2"


def jar_arg_path(path):
    return str(Path(path).resolve()).replace(os.sep, "/")


def has_source_files(path, suffix=".java"):
    path = Path(path)
    return path.exists() and path.is_dir() and any(path.rglob(f"*{suffix}"))


def resolve_source_root(project_dir, project_name=None, suffix=".java"):
    project_dir = Path(project_dir).resolve()
    project_name = project_name or project_dir.name

    nested_same_name = project_dir / project_name
    if has_source_files(nested_same_name, suffix):
        return nested_same_name
    if has_source_files(project_dir, suffix):
        return project_dir

    for child in sorted(project_dir.iterdir() if project_dir.exists() else []):
        if child.is_dir() and has_source_files(child, suffix):
            return child
    return project_dir


def first_existing_file(base_dir, candidates):
    base_dir = Path(base_dir)
    for candidate in candidates:
        path = base_dir / candidate
        if path.exists():
            return path
    return None


def infer_module_info(project_dir, project_name):
    found = first_existing_file(
        project_dir,
        [
            f"updated_config_{project_name}.txt",
            f"{project_name}_accurateModules1.txt",
            f"{project_name}_early1.txt",
            "hadoop_early1.txt",
        ],
    )
    if found:
        return found

    project_dir = Path(project_dir)
    for pattern in ("*accurateModules*.txt", "updated_config*.txt", "*early*.txt"):
        matches = sorted(project_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def infer_gt_file(project_dir, project_name):
    found = first_existing_file(
        project_dir,
        [
            f"updated_{project_name}_gt.json",
            f"{project_name}_gt.json",
        ],
    )
    if found:
        return found

    matches = sorted(Path(project_dir).glob("*gt*.json"))
    return matches[0] if matches else None


def parse_module_info(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    names_match = re.search(r"ModuleNames\s*:\s*\{([\s\S]+?)\}", content)
    desc_match = re.search(r"ModuleDescriptions\s*:\s*\{([\s\S]+?)\}", content)
    if not names_match or not desc_match:
        raise ValueError(f"Cannot parse module info file: {file_path}")

    module_names = re.findall(r'"([^"]+)"', names_match.group(1))
    module_descriptions = re.findall(r'"([^"]+)"', desc_match.group(1))
    if len(module_names) != len(module_descriptions):
        raise ValueError("Module names and descriptions count mismatch.")
    return dict(zip(module_names, module_descriptions))


def write_module_info(module_info, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("ModuleNames : {\n")
        for module in module_info.keys():
            file.write(f'    "{module}"\n')
        file.write("}\n\nModuleDescriptions : {\n")
        for desc in module_info.values():
            file.write(f'    "{desc}"\n')
        file.write("}\n")


def clean_name(value):
    return re.sub(r"\W+", "", value.lower())


def edit_distance(left, right):
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, 1):
        current = [i]
        for j, right_char in enumerate(right, 1):
            cost = 0 if left_char == right_char else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def best_module(group_name, modules):
    cleaned_group = clean_name(group_name)
    best_name = None
    best_distance = 10**9
    for module in modules:
        distance = edit_distance(cleaned_group, clean_name(module))
        if distance < best_distance:
            best_name = module
            best_distance = distance
    return best_name, best_distance


def close_gt_groups(module, gt_groups, threshold):
    cleaned_module = clean_name(module)
    return {
        group
        for group in gt_groups
        if edit_distance(cleaned_module, clean_name(group)) <= threshold
    }


def build_eval_file_list(gt_path, modules, removed_modules, distance_threshold=2):
    if not gt_path or not Path(gt_path).exists():
        return []

    with open(gt_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    gt_groups = {
        group.get("name", "").strip()
        for group in data.get("structure", [])
        if group.get("name", "").strip()
    }
    excluded_groups = set()
    for removed_module in removed_modules:
        excluded_groups.update(close_gt_groups(removed_module, gt_groups, threshold=1))

    files = []
    seen = set()
    for group in data.get("structure", []):
        raw_group = group.get("name")
        if not raw_group:
            continue

        matched_module, distance = best_module(raw_group, modules)
        is_match = matched_module is not None and distance <= distance_threshold
        is_excluded = raw_group in excluded_groups
        if not (is_match or is_excluded):
            continue

        for item in group.get("nested", []):
            item_name = item.get("name")
            if not item_name:
                continue
            normalized = item_name.replace("\\", "/").strip()
            if normalized not in seen:
                files.append(normalized)
                seen.add(normalized)
    return files


def write_eval_file_list(gt_path, modules, removed_modules, output_directory):
    files = build_eval_file_list(gt_path, modules, removed_modules)
    if not files:
        return None

    output_path = Path(output_directory) / "eval_files.txt"
    with open(output_path, "w", encoding="utf-8") as handle:
        for file_path in files:
            handle.write(file_path + "\n")
    return output_path


def module_windows(module_names, missing_count):
    if missing_count < 1:
        raise ValueError("--missing-count must be at least 1.")
    if missing_count > len(module_names):
        return []
    return [
        module_names[index:index + missing_count]
        for index in range(len(module_names) - missing_count + 1)
    ]


def removed_modules_label(removed_modules):
    invalid_chars = '<>:"/\\|?*'
    labels = []
    for module in removed_modules:
        label = "".join("_" if char in invalid_chars else char for char in module)
        labels.append(label.strip() or "module")
    return "__".join(labels)


def run_tfidf(project_name, source_root, module_info_file, method, threshold, output_directory):
    project_parent = Path(source_root).resolve().parent
    command = [
        "java",
        "-jar",
        str(TFIDF_JAR),
        project_name,
        jar_arg_path(project_parent),
        jar_arg_path(module_info_file),
        method,
        str(threshold),
        jar_arg_path(output_directory),
    ]
    subprocess.run(command, cwd=SCRIPT_DIR, check=True)


def generate_project(project_dir, project_name, output_root, missing_count, method, threshold, overwrite):
    module_info_file = infer_module_info(project_dir, project_name)
    gt_file = infer_gt_file(project_dir, project_name)
    if not module_info_file:
        print(f"[Skip] Module info file not found: {project_dir}")
        return
    if not gt_file:
        print(f"[Skip] GT file not found: {project_dir}")
        return

    source_root = resolve_source_root(project_dir, project_name)
    module_info = parse_module_info(module_info_file)
    original_modules = list(module_info.keys())
    windows = module_windows(original_modules, missing_count)
    if not windows:
        print(f"[Skip] missing_count={missing_count} is larger than module count={len(original_modules)}")
        return

    for removed_modules in windows:
        case_name = f"removed_{removed_modules_label(removed_modules)}"
        output_directory = Path(output_root) / project_name / case_name
        csv_path = output_directory / "tfidf-file-module_scores.csv"
        if csv_path.exists() and csv_path.stat().st_size > 0 and not overwrite:
            print(f"[Skip] Existing TF-IDF result: {csv_path}")
            continue

        updated_module_info = module_info.copy()
        for module_to_remove in removed_modules:
            del updated_module_info[module_to_remove]

        output_directory.mkdir(parents=True, exist_ok=True)
        updated_module_info_file = output_directory / "updated_module_info.txt"
        write_module_info(updated_module_info, updated_module_info_file)
        write_eval_file_list(gt_file, original_modules, removed_modules, output_directory)

        print(f"[Run] {project_name}/{case_name}: removed {', '.join(removed_modules)}")
        run_tfidf(project_name, source_root, updated_module_info_file, method, threshold, output_directory)


def main():
    parser = argparse.ArgumentParser(description="Generate TF-IDF-only results for multi-module-missing Java cases.")
    parser.add_argument("--project-root", default=str(DEFAULT_PROJECT_ROOT), help="Root containing Java project datasets.")
    parser.add_argument("-o", "--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Root for generated TF-IDF results.")
    parser.add_argument("--projects", nargs="*", default=None, help="Optional project names to process.")
    parser.add_argument("-k", "--missing-count", type=int, default=2, help="Number of consecutive modules to remove.")
    parser.add_argument("-a", "--mapping", default="tfidf", help="Mapping method passed to the TF-IDF jar.")
    parser.add_argument("-t", "--threshold", type=float, default=50, help="Threshold passed to the TF-IDF jar.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate cases even when a non-empty CSV exists.")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    if args.projects:
        projects = args.projects
    else:
        projects = [path.name for path in sorted(project_root.iterdir()) if path.is_dir()]

    for project_name in projects:
        project_dir = project_root / project_name
        if not project_dir.exists():
            print(f"[Skip] Project directory not found: {project_dir}")
            continue
        generate_project(
            project_dir,
            project_name,
            args.output_root,
            args.missing_count,
            args.mapping,
            args.threshold,
            args.overwrite,
        )


if __name__ == "__main__":
    main()
