"""Select qualitative-analysis samples from a disagreement report.

The script is intentionally independent from the metric evaluation scripts. It
reads a per-file disagreement CSV and emits a compact CSV for manual review.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = (
    REPO_ROOT
    / "evaluation"
    / "result"
    / "java"
    / "deepseek"
    / "disagreement_report_new1111test1.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "evaluation"
    / "result"
    / "java"
    / "deepseek"
    / "qualitative_sample_selection.csv"
)

BASELINE_METHODS = ("TFIDF", "LLMProb", "LLMAssign")
IPRAG_METHOD = "LLMAssign-IPRAG"
METHODS = (*BASELINE_METHODS, IPRAG_METHOD)
UNMAPPED_VALUES = {"", "non", "none", "null", "nan"}


def normalize(value: object) -> str:
    return str(value or "").strip().casefold()


def is_unmapped(value: object) -> bool:
    return normalize(value) in UNMAPPED_VALUES


def is_correct(row: dict[str, str], method: str) -> bool:
    return normalize(row.get(method)) == normalize(row.get("GT"))


def correctness_pattern(row: dict[str, str]) -> str:
    return ";".join(f"{method}={'Y' if is_correct(row, method) else 'N'}" for method in METHODS)


def add_correctness_columns(row: dict[str, str]) -> dict[str, str]:
    enriched = dict(row)
    for method in METHODS:
        enriched[f"{method}_correct"] = "1" if is_correct(row, method) else "0"
    enriched["correctness_pattern"] = correctness_pattern(row)
    enriched["manual_gt_rationale"] = ""
    enriched["manual_error_analysis"] = ""
    enriched["notes"] = ""
    return enriched


def category_rules() -> list[tuple[str, Callable[[dict[str, str]], bool]]]:
    return [
        (
            "iprag_correct_all_baselines_wrong",
            lambda row: is_correct(row, IPRAG_METHOD)
            and all(not is_correct(row, method) for method in BASELINE_METHODS),
        ),
        (
            "iprag_correct_some_baseline_wrong",
            lambda row: is_correct(row, IPRAG_METHOD)
            and any(not is_correct(row, method) for method in BASELINE_METHODS)
            and any(is_correct(row, method) for method in BASELINE_METHODS),
        ),
        (
            "baseline_correct_iprag_wrong",
            lambda row: not is_correct(row, IPRAG_METHOD)
            and any(is_correct(row, method) for method in BASELINE_METHODS),
        ),
        (
            "all_methods_wrong",
            lambda row: all(not is_correct(row, method) for method in METHODS),
        ),
        (
            "all_methods_correct",
            lambda row: all(is_correct(row, method) for method in METHODS),
        ),
    ]


def balanced_sample(
    rows: Iterable[dict[str, str]],
    per_category: int,
    seed: int,
) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    rng = random.Random(seed)

    for row in rows:
        grouped[row.get("Project", "")].append(row)

    for project_rows in grouped.values():
        project_rows.sort(
            key=lambda row: (
                row.get("Module", ""),
                row.get("File", ""),
                row.get("GT", ""),
                correctness_pattern(row),
            )
        )
        rng.shuffle(project_rows)

    selected: list[dict[str, str]] = []
    project_names = sorted(grouped)
    index_by_project = {project: 0 for project in project_names}

    while len(selected) < per_category and project_names:
        progressed = False
        for project in project_names:
            index = index_by_project[project]
            project_rows = grouped[project]
            if index < len(project_rows):
                selected.append(project_rows[index])
                index_by_project[project] = index + 1
                progressed = True
                if len(selected) >= per_category:
                    break
        if not progressed:
            break

    return selected


def read_rows(path: Path, include_unmapped: bool) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"Project", "Module", "File", "GT", *METHODS}
        missing = sorted(required_columns.difference(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {', '.join(missing)}")

        rows = []
        for row in reader:
            if include_unmapped or not is_unmapped(row.get("GT")):
                rows.append(row)
        return rows


def output_columns(input_columns: list[str]) -> list[str]:
    preferred = [
        "case_type",
        "Project",
        "Module",
        "File",
        "GT",
        "TFIDF",
        "TFIDF_correct",
        "TFIDF Score",
        "LLMProb",
        "LLMProb_correct",
        "LLMProb Score",
        "LLMAssign",
        "LLMAssign_correct",
        "LLMAssign-IPRAG",
        "LLMAssign-IPRAG_correct",
        "correctness_pattern",
        "manual_gt_rationale",
        "manual_error_analysis",
        "notes",
    ]
    extras = [column for column in input_columns if column not in preferred]
    return preferred + extras


def write_rows(path: Path, rows: list[dict[str, str]], input_columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = output_columns(input_columns)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select balanced qualitative samples from a disagreement report."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input disagreement CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output sample CSV.")
    parser.add_argument(
        "--per-category",
        type=int,
        default=5,
        help="Number of samples selected for each case type.",
    )
    parser.add_argument(
        "--include-unmapped",
        action="store_true",
        help="Include rows whose GT is non/none/null. By default they are excluded.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed used for deterministic within-project ordering.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = read_rows(input_path, include_unmapped=args.include_unmapped)
    selected_rows: list[dict[str, str]] = []
    category_counts: dict[str, int] = {}

    for offset, (case_type, predicate) in enumerate(category_rules()):
        candidates = [row for row in rows if predicate(row)]
        sampled = balanced_sample(candidates, args.per_category, args.seed + offset)
        category_counts[case_type] = len(sampled)
        for row in sampled:
            enriched = add_correctness_columns(row)
            enriched["case_type"] = case_type
            selected_rows.append(enriched)

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        input_columns = list(csv.DictReader(handle).fieldnames or [])
    write_rows(output_path, selected_rows, input_columns)

    print(f"Input rows after GT filtering: {len(rows)}")
    print(f"Output rows: {len(selected_rows)}")
    print(f"Output CSV: {output_path}")
    for case_type, count in category_counts.items():
        suffix = "" if count >= args.per_category else f" (only {count} available)"
        print(f"{case_type}: {count}{suffix}")


if __name__ == "__main__":
    main()
