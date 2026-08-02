#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate the detailed IP-RAG evaluation report for the three teastore prompt
ablation variants.

This keeps the IP-RAG side of compare_allresults.py:
- normalize GT group names with edit-distance matching;
- mark the removed module as None/non in GT;
- evaluate IP-RAG from clustering_before_feedback.json;
- write a disagreement-style CSV for downstream DM/UM evaluation.
"""

import argparse
import csv
import os
from pathlib import Path

from compare_allresults import (
    collect_all_groups_from_gt,
    extract_modules_from_file,
    find_close_group_names,
    load_cluster_mapping,
    load_mapping,
    unify_all_gt_groups_in_memory,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "mediastore"
VARIANTS = (
    "mediastore-no-role-description",
    "mediastore-nocot",
    "mediastore-noumaware"
)

PROJECT_DIR = REPO_ROOT / "experiment" / "project" / "java" / PROJECT_NAME
VARIANT_ROOT = REPO_ROOT / "experiment" / "experiment-java" / "IP-RAG"


def first_existing_file(base_dir, candidates):
    for candidate in candidates:
        path = base_dir / candidate
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find module info file. Tried: "
        + ", ".join(str(base_dir / candidate) for candidate in candidates)
    )


def normalize_none(value):
    return "non" if str(value).strip() == "None" else value


def build_rows():
    gt_file = PROJECT_DIR / f"updated_{PROJECT_NAME}_gt.json"
    modules_file = first_existing_file(
        PROJECT_DIR,
        (
            f"updated_config_{PROJECT_NAME}.txt",
            f"{PROJECT_NAME}_accurateModules1.txt",
            f"{PROJECT_NAME}_early1.txt",
        ),
    )

    modules_list = extract_modules_from_file(str(modules_file))
    if not modules_list:
        raise RuntimeError(f"No modules parsed from {modules_file}")

    all_gt_groups = collect_all_groups_from_gt(str(gt_file))
    valid_modules = [
        module
        for module in modules_list
        if find_close_group_names(module, all_gt_groups, 2)
    ]

    rows = []
    for variant in VARIANTS:
        variant_dir = VARIANT_ROOT / variant
        if not variant_dir.exists():
            print(f"[Skip] Variant directory not found: {variant_dir}")
            continue

        print(f"\n=== {variant} ===")
        for module in valid_modules:
            removed_dir = variant_dir / f"removed_{module}"
            iprag_path = removed_dir / "clustering_before_feedback.json"
            if not iprag_path.exists():
                print(f"[Skip] Missing IP-RAG result: {iprag_path}")
                continue

            print(f"-- Module: {module}")
            excluded_candidates = find_close_group_names(module, all_gt_groups, 1)
            unified_gt_file = unify_all_gt_groups_in_memory(
                str(gt_file),
                modules_list,
                2,
                excluded_candidates,
            )
            gt_map = load_mapping(
                unified_gt_file,
                excluded_groups=excluded_candidates,
            )
            iprag_map = load_cluster_mapping(str(iprag_path))

            for file_path in sorted(set(iprag_map.keys()) & set(gt_map.keys())):
                rows.append(
                    [
                        variant,
                        module,
                        file_path,
                        normalize_none(gt_map.get(file_path, "N/A")),
                        normalize_none(iprag_map[file_path]),
                    ]
                )

    return rows


def main(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "iprag_variants_disagreement_report.csv"

    rows = build_rows()
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Project", "Module", "File", "GT", "LLMAssign-IPRAG"])
        writer.writerows(rows)

    print(f"[OK] Wrote {len(rows)} rows to {output_file}")
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(REPO_ROOT / "evaluation" / "result" / "java" / "iprag_variants"),
        help="Directory where generated evaluation CSV files are saved.",
    )
    args = parser.parse_args()
    main(args.output_dir)
