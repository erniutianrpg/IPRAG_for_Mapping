#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute UM metrics for teastore IP-RAG prompt ablation variants."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULT_DIR = REPO_ROOT / "evaluation" / "result" / "java" / "iprag_variants"


def compute_um(ground_truth, predictions):
    tp = sum(1 for gt, pred in zip(ground_truth, predictions) if pred == "non" and gt == "non")
    fp = sum(1 for gt, pred in zip(ground_truth, predictions) if pred == "non" and gt != "non")
    fn = sum(1 for gt, pred in zip(ground_truth, predictions) if pred != "non" and gt == "non")

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def evaluate(input_csv, output_csv, processed_csv):
    data = defaultdict(lambda: {"gts": [], "preds": []})
    processed_rows = []

    with open(input_csv, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            processed = dict(row)
            processed["GT"] = "non" if row["GT"].strip() == "non" else "non-None"
            processed["LLMAssign-IPRAG"] = (
                "non" if row["LLMAssign-IPRAG"].strip() == "non" else "non-None"
            )
            processed_rows.append(processed)

            project = row["Project"].strip()
            data[project]["gts"].append(row["GT"].strip())
            data[project]["preds"].append(row["LLMAssign-IPRAG"].strip())

    with open(processed_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    rows = []
    for project, values in data.items():
        precision, recall, score = compute_um(values["gts"], values["preds"])
        rows.append(
            {
                "Project": project,
                "precision_LLMAssign-IPRAG": precision,
                "recall_LLMAssign-IPRAG": recall,
                "f1_LLMAssign-IPRAG": score,
            }
        )

    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "Project",
            "precision_LLMAssign-IPRAG",
            "recall_LLMAssign-IPRAG",
            "f1_LLMAssign-IPRAG",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {processed_csv}")
    print(f"[OK] Wrote {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-csv",
        default=str(DEFAULT_RESULT_DIR / "iprag_variants_disagreement_report.csv"),
    )
    parser.add_argument(
        "-o",
        "--output-csv",
        default=str(DEFAULT_RESULT_DIR / "iprag_variants_UM_summary.csv"),
    )
    parser.add_argument(
        "-p",
        "--processed-csv",
        default=str(DEFAULT_RESULT_DIR / "iprag_variants_UM_processed.csv"),
    )
    args = parser.parse_args()
    evaluate(args.input_csv, args.output_csv, args.processed_csv)
