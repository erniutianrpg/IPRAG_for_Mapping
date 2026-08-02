#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute DM metrics for teastore IP-RAG prompt ablation variants."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULT_DIR = REPO_ROOT / "evaluation" / "result" / "java" / "iprag_variants"


def compute_overall_precision_recall(y_true, y_pred):
    all_tp = 0
    all_fp = 0
    all_fn = 0
    labels = (set(y_true) | set(y_pred)) - {"non"}

    for label in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp == label)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != label and yp == label)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp != label)
        all_tp += tp
        all_fp += fp
        all_fn += fn

    precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) else 0.0
    recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) else 0.0
    return round(precision, 4), round(recall, 4)


def f1(precision, recall):
    return round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0


def average(values):
    return round(sum(values) / len(values), 4) if values else 0.0


def evaluate(input_csv, output_csv):
    data = defaultdict(lambda: defaultdict(lambda: {"preds": [], "gts": []}))
    with open(input_csv, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            project = row["Project"].strip()
            module = row["Module"].strip()
            data[project][module]["gts"].append(row["GT"].strip())
            data[project][module]["preds"].append(row["LLMAssign-IPRAG"].strip())

    rows = []
    for project, modules in data.items():
        precisions = []
        recalls = []
        print(f"\n========== Project: {project} ==========")
        for module, values in modules.items():
            precision, recall = compute_overall_precision_recall(values["gts"], values["preds"])
            precisions.append(precision)
            recalls.append(recall)
            print(f"{module} - LLMAssign-IPRAG Precision: {precision}, Recall: {recall}, F1: {f1(precision, recall)}")

        avg_precision = average(precisions)
        avg_recall = average(recalls)
        rows.append(
            {
                "Project": project,
                "LLMAssign-IPRAG_Avg_Precision": avg_precision,
                "LLMAssign-IPRAG_Avg_Recall": avg_recall,
                "LLMAssign-IPRAG_F1": f1(avg_precision, avg_recall),
            }
        )

    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "Project",
            "LLMAssign-IPRAG_Avg_Precision",
            "LLMAssign-IPRAG_Avg_Recall",
            "LLMAssign-IPRAG_F1",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

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
        default=str(DEFAULT_RESULT_DIR / "iprag_variants_DM_summary.csv"),
    )
    args = parser.parse_args()
    evaluate(args.input_csv, args.output_csv)
