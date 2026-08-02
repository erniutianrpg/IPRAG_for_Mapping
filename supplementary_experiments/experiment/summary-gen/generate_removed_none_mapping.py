import argparse
import csv
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_RESULT_ROOT = Path(
    REPO_ROOT / "experiment" / "result" / "java" / "javaexperiment_results" / "IP-RAG"
)


def removed_module_name(case_dir):
    name = case_dir.name
    if name.startswith("removed_"):
        return name[len("removed_") :]
    return name


def iter_none_files(clustering_path):
    with clustering_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    for group in data.get("structure", []):
        if group.get("@type") != "group":
            continue
        if str(group.get("name", "")).strip().lower() != "none":
            continue

        for item in group.get("nested", []):
            if item.get("@type") != "item":
                continue
            file_name = item.get("name")
            if file_name:
                yield file_name.replace("\\", "/").strip()


def build_mapping(result_root):
    mapping = {}
    rows = []
    warnings = []

    for project_dir in sorted(path for path in result_root.iterdir() if path.is_dir()):
        project_mapping = {}

        for case_dir in sorted(path for path in project_dir.iterdir() if path.is_dir()):
            if not case_dir.name.startswith("removed_"):
                continue

            clustering_path = case_dir / "clustering_before_feedback.json"
            if not clustering_path.exists():
                warnings.append(f"Missing clustering file: {clustering_path}")
                continue

            module_name = removed_module_name(case_dir)
            files = sorted(set(iter_none_files(clustering_path)))
            file_mapping = {file_path: module_name for file_path in files}
            project_mapping[module_name] = file_mapping

            for file_path in files:
                rows.append(
                    {
                        "project": project_dir.name,
                        "removed_case": case_dir.name,
                        "removed_module": module_name,
                        "file": file_path,
                    }
                )

        if project_mapping:
            mapping[project_dir.name] = project_mapping

    return mapping, rows, warnings


def write_json(path, mapping):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(mapping, handle, ensure_ascii=False, indent=2)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["project", "removed_case", "removed_module", "file"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate file -> removed module mappings from files assigned to "
            "None in clustering_before_feedback.json."
        )
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        default=DEFAULT_RESULT_ROOT,
        help="Root directory containing project/removed_* result folders.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(__file__).with_name("removed_none_file_mapping.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path(__file__).with_name("removed_none_file_mapping.csv"),
        help="Output CSV path.",
    )
    args = parser.parse_args()

    result_root = args.result_root
    if not result_root.exists():
        raise FileNotFoundError(f"Result root does not exist: {result_root}")

    mapping, rows, warnings = build_mapping(result_root)
    write_json(args.output_json, mapping)
    write_csv(args.output_csv, rows)

    print(f"Projects: {len(mapping)}")
    print(f"Mappings: {len(rows)}")
    print(f"JSON: {args.output_json}")
    print(f"CSV: {args.output_csv}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
