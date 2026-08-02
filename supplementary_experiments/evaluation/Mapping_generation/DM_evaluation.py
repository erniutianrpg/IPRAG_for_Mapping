
# import csv
# from collections import defaultdict
#
# def compute_overall_precision_recall(y_true, y_pred):
#     all_tp = 0
#     all_fp = 0
#     all_fn = 0
#     per_label_metrics = {}
#
#     labels = (set(y_true) | set(y_pred)) - {"non"}
#
#     for label in labels:
#         tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp == label)
#         fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != label and yp == label)
#         fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp != label)
#
#         all_tp += tp
#         all_fp += fp
#         all_fn += fn
#
#         precision = tp / (tp + fp) if (tp + fp) else 0.0
#         recall = tp / (tp + fn) if (tp + fn) else 0.0
#
#         per_label_metrics[label] = {
#             "precision": round(precision, 4),
#             "recall": round(recall, 4)
#         }
#
#     overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) else 0.0
#     overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) else 0.0
#
#     return {
#         "overall_precision": round(overall_precision, 4),
#         "overall_recall": round(overall_recall, 4),
#         "per_label_metrics": per_label_metrics
#     }
#
# def evaluate_by_project_and_module_to_csv(file_path, output_csv_path):
#     with open(file_path, newline='', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
#
#         data = defaultdict(lambda: defaultdict(lambda: {
#             "tfidf_preds": [], "tfidf_gts": [],
#             "llmassign_preds": [], "llmassign_gts": [],
#             "sam_preds": [], "sam_gts": []
#         }))
#
#         for row in reader:
#             project = row["Project"].strip()
#             module = row["Module"].strip()
#             gt = row["GT"].strip()
#
#             data[project][module]["tfidf_preds"].append(row["TFIDF"].strip())
#             data[project][module]["tfidf_gts"].append(gt)
#
#             data[project][module]["llmassign_preds"].append(row["LLMAssign-IPRAG"].strip())
#             data[project][module]["llmassign_gts"].append(gt)
#
#             # Read SAMCodeTLR column
#             if "SAMCodeTLR" in row:
#                 data[project][module]["sam_preds"].append(row["SAMCodeTLR"].strip())
#                 data[project][module]["sam_gts"].append(gt)
#
#     def average(lst):
#         return round(sum(lst) / len(lst), 4) if lst else 0.0
#
#     output_rows = []
#     for project, modules in data.items():
#         tfidf_precisions, tfidf_recalls = [], []
#         llmassign_precisions, llmassign_recalls = [], []
#         sam_precisions, sam_recalls = [], []
#
#         print(f"\n========== Project: {project} ==========")
#         for module, values in modules.items():
#             if module == "cli":
#                 flag=1
#             tfidf_result = compute_overall_precision_recall(values["tfidf_gts"], values["tfidf_preds"])
#             llmassign_result = compute_overall_precision_recall(values["llmassign_gts"], values["llmassign_preds"])
#             sam_result = compute_overall_precision_recall(values["sam_gts"], values["sam_preds"]) if values["sam_preds"] else {"overall_precision":0.0,"overall_recall":0.0}
#
#             tfidf_p = tfidf_result['overall_precision']
#             tfidf_r = tfidf_result['overall_recall']
#             tfidf_f1 = round(2 * tfidf_p * tfidf_r / (tfidf_p + tfidf_r), 4) if (tfidf_p + tfidf_r) else 0.0
#
#             llmassign_p = llmassign_result['overall_precision']
#             llmassign_r = llmassign_result['overall_recall']
#             llmassign_f1 = round(2 * llmassign_p * llmassign_r / (llmassign_p + llmassign_r), 4) if (llmassign_p + llmassign_r) else 0.0
#
#             sam_p = sam_result['overall_precision']
#             sam_r = sam_result['overall_recall']
#             sam_f1 = round(2 * sam_p * sam_r / (sam_p + sam_r), 4) if (sam_p + sam_r) else 0.0
#
#             tfidf_precisions.append(tfidf_p)
#             tfidf_recalls.append(tfidf_r)
#             llmassign_precisions.append(llmassign_p)
#             llmassign_recalls.append(llmassign_r)
#             if values["sam_preds"]:
#                 sam_precisions.append(sam_p)
#                 sam_recalls.append(sam_r)
#
#             print(f"\n-- Module: {module} --")
#             print(f"TFIDF - Precision: {tfidf_p}, Recall: {tfidf_r}, F1: {tfidf_f1}")
#             print(f"LLMAssign-IPRAG - Precision: {llmassign_p}, Recall: {llmassign_r}, F1: {llmassign_f1}")
#             if values["sam_preds"]:
#                 print(f"SAMCodeTLR - Precision: {sam_p}, Recall: {sam_r}, F1: {sam_f1}")
#
#         avg_tfidf_p = average(tfidf_precisions)
#         avg_tfidf_r = average(tfidf_recalls)
#         avg_tfidf_f1 = round(2 * avg_tfidf_p * avg_tfidf_r / (avg_tfidf_p + avg_tfidf_r), 4) if (avg_tfidf_p + avg_tfidf_r) else 0.0
#
#         avg_llmassign_p = average(llmassign_precisions)
#         avg_llmassign_r = average(llmassign_recalls)
#         avg_llmassign_f1 = round(2 * avg_llmassign_p * avg_llmassign_r / (avg_llmassign_p + avg_llmassign_r), 4) if (avg_llmassign_p + avg_llmassign_r) else 0.0
#
#         avg_sam_p = average(sam_precisions)
#         avg_sam_r = average(sam_recalls)
#         avg_sam_f1 = round(2 * avg_sam_p * avg_sam_r / (avg_sam_p + avg_sam_r), 4) if (avg_sam_p + avg_sam_r) else 0.0
#
#         print(f"\n>>> Summary for Project {project} <<<")
#         print(f"TFIDF - Avg Precision: {avg_tfidf_p}, Avg Recall: {avg_tfidf_r}, F1: {avg_tfidf_f1}")
#         print(f"LLMAssign-IPRAG - Avg Precision: {avg_llmassign_p}, Avg Recall: {avg_llmassign_r}, F1: {avg_llmassign_f1}")
#         print(f"SAMCodeTLR - Avg Precision: {avg_sam_p}, Avg Recall: {avg_sam_r}, F1: {avg_sam_f1}")
#
#         output_rows.append({
#             "Project": project,
#             "TFIDF_Avg_Precision": avg_tfidf_p,
#             "TFIDF_Avg_Recall": avg_tfidf_r,
#             "TFIDF_F1": avg_tfidf_f1,
#             "LLMAssign_Avg_Precision": avg_llmassign_p,
#             "LLMAssign_Avg_Recall": avg_llmassign_r,
#             "LLMAssign_F1": avg_llmassign_f1,
#             "SAMCodeTLR_Avg_Precision": avg_sam_p,
#             "SAMCodeTLR_Avg_Recall": avg_sam_r,
#             "SAMCodeTLR_F1": avg_sam_f1
#         })
#
#     with open(output_csv_path, "w", newline='', encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=output_rows[0].keys())
#         writer.writeheader()
#         writer.writerows(output_rows)
#
#     return output_csv_path
#
# output_csv = "project_summary_output.csv"
# evaluate_by_project_and_module_to_csv("disagreement_report_new1111test.csv", output_csv)

import csv
from collections import defaultdict

def compute_overall_precision_recall(y_true, y_pred):
    all_tp = 0
    all_fp = 0
    all_fn = 0
    per_label_metrics = {}

    # Ignore non"label
    labels = (set(y_true) | set(y_pred)) - {"non"}

    for label in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp == label)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != label and yp == label)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp != label)

        all_tp += tp
        all_fp += fp
        all_fn += fn

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        per_label_metrics[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4)
        }

    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) else 0.0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) else 0.0

    return {
        "overall_precision": round(overall_precision, 4),
        "overall_recall": round(overall_recall, 4),
        "per_label_metrics": per_label_metrics
    }

def evaluate_by_project_and_module_to_csv(file_path, output_csv_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Whether each column exists (improves robustness)
        has_tfidf = "TFIDF" in fieldnames
        has_llmprob = "LLMProb" in fieldnames
        has_llmassign_plain = "LLMAssign" in fieldnames
        has_llmassign_iprag = "LLMAssign-IPRAG" in fieldnames
        has_sam = "SAMCodeTLR" in fieldnames

        # Aggregate data by project and module
        data = defaultdict(lambda: defaultdict(lambda: {
            "tfidf_preds": [], "tfidf_gts": [],
            "llmprob_preds": [], "llmprob_gts": [],
            "llmassign_plain_preds": [], "llmassign_plain_gts": [],
            "llmassign_iprag_preds": [], "llmassign_iprag_gts": [],
            "sam_preds": [], "sam_gts": []
        }))

        for row in reader:
            project = row["Project"].strip()
            module = row["Module"].strip()
            gt = row["GT"].strip()

            if has_tfidf:
                data[project][module]["tfidf_preds"].append(row["TFIDF"].strip())
                data[project][module]["tfidf_gts"].append(gt)

            if has_llmprob:
                data[project][module]["llmprob_preds"].append(row["LLMProb"].strip())
                data[project][module]["llmprob_gts"].append(gt)

            if has_llmassign_plain:
                data[project][module]["llmassign_plain_preds"].append(row["LLMAssign"].strip())
                data[project][module]["llmassign_plain_gts"].append(gt)

            if has_llmassign_iprag:
                data[project][module]["llmassign_iprag_preds"].append(row["LLMAssign-IPRAG"].strip())
                data[project][module]["llmassign_iprag_gts"].append(gt)

            if has_sam:
                data[project][module]["sam_preds"].append(row["SAMCodeTLR"].strip())
                data[project][module]["sam_gts"].append(gt)

    def average(lst):
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    output_rows = []
    for project, modules in data.items():
        # Used for project-level averaging
        tfidf_precisions, tfidf_recalls = [], []
        llmprob_precisions, llmprob_recalls = [], []
        llmassign_plain_precisions, llmassign_plain_recalls = [], []
        llmassign_iprag_precisions, llmassign_iprag_recalls = [], []
        sam_precisions, sam_recalls = [], []

        print(f"\n========== Project: {project} ==========")
        for module, values in modules.items():
            # Compute by model
            def prf(res):
                p = res['overall_precision']; r = res['overall_recall']
                f1 = round(2 * p * r / (p + r), 4) if (p + r) else 0.0
                return p, r, f1

            # TFIDF
            if values["tfidf_preds"]:
                tfidf_result = compute_overall_precision_recall(values["tfidf_gts"], values["tfidf_preds"])
                tfidf_p, tfidf_r, tfidf_f1 = prf(tfidf_result)
                tfidf_precisions.append(tfidf_p); tfidf_recalls.append(tfidf_r)
            else:
                tfidf_p = tfidf_r = tfidf_f1 = 0.0

            # LLMProb
            if values["llmprob_preds"]:
                llmprob_result = compute_overall_precision_recall(values["llmprob_gts"], values["llmprob_preds"])
                llmprob_p, llmprob_r, llmprob_f1 = prf(llmprob_result)
                llmprob_precisions.append(llmprob_p); llmprob_recalls.append(llmprob_r)
            else:
                llmprob_p = llmprob_r = llmprob_f1 = 0.0

            # LLMAssign(new)
            if values["llmassign_plain_preds"]:
                llmassign_plain_result = compute_overall_precision_recall(
                    values["llmassign_plain_gts"], values["llmassign_plain_preds"]
                )
                llmassign_plain_p, llmassign_plain_r, llmassign_plain_f1 = prf(llmassign_plain_result)
                llmassign_plain_precisions.append(llmassign_plain_p)
                llmassign_plain_recalls.append(llmassign_plain_r)
            else:
                llmassign_plain_p = llmassign_plain_r = llmassign_plain_f1 = 0.0

            # LLMAssign-IPRAG(existing)
            if values["llmassign_iprag_preds"]:
                llmassign_iprag_result = compute_overall_precision_recall(
                    values["llmassign_iprag_gts"], values["llmassign_iprag_preds"]
                )
                llmassign_iprag_p, llmassign_iprag_r, llmassign_iprag_f1 = prf(llmassign_iprag_result)
                llmassign_iprag_precisions.append(llmassign_iprag_p)
                llmassign_iprag_recalls.append(llmassign_iprag_r)
            else:
                llmassign_iprag_p = llmassign_iprag_r = llmassign_iprag_f1 = 0.0

            # SAMCodeTLR
            if values["sam_preds"]:
                sam_result = compute_overall_precision_recall(values["sam_gts"], values["sam_preds"])
                sam_p, sam_r, sam_f1 = prf(sam_result)
                sam_precisions.append(sam_p); sam_recalls.append(sam_r)
            else:
                sam_p = sam_r = sam_f1 = 0.0

            # Per-module console output (print only when present)
            print(f"\n-- Module: {module} --")
            if has_tfidf: print(f"TFIDF - Precision: {tfidf_p}, Recall: {tfidf_r}, F1: {tfidf_f1}")
            if has_llmprob: print(f"LLMProb - Precision: {llmprob_p}, Recall: {llmprob_r}, F1: {llmprob_f1}")
            if has_llmassign_plain: print(f"LLMAssign - Precision: {llmassign_plain_p}, Recall: {llmassign_plain_r}, F1: {llmassign_plain_f1}")
            if has_llmassign_iprag: print(f"LLMAssign-IPRAG - Precision: {llmassign_iprag_p}, Recall: {llmassign_iprag_r}, F1: {llmassign_iprag_f1}")
            if has_sam: print(f"SAMCodeTLR - Precision: {sam_p}, Recall: {sam_r}, F1: {sam_f1}")

        # Project-level average (first compute the arithmetic mean of each module's  overall overall metrics)
        avg_tfidf_p = average(tfidf_precisions);          avg_tfidf_r = average(tfidf_recalls)
        avg_llmprob_p = average(llmprob_precisions);      avg_llmprob_r = average(llmprob_recalls)
        avg_llmassign_plain_p = average(llmassign_plain_precisions);  avg_llmassign_plain_r = average(llmassign_plain_recalls)
        avg_llmassign_iprag_p = average(llmassign_iprag_precisions);  avg_llmassign_iprag_r = average(llmassign_iprag_recalls)
        avg_sam_p = average(sam_precisions);              avg_sam_r = average(sam_recalls)

        def f1(p, r): return round(2 * p * r / (p + r), 4) if (p + r) else 0.0

        avg_tfidf_f1 = f1(avg_tfidf_p, avg_tfidf_r)
        avg_llmprob_f1 = f1(avg_llmprob_p, avg_llmprob_r)
        avg_llmassign_plain_f1 = f1(avg_llmassign_plain_p, avg_llmassign_plain_r)
        avg_llmassign_iprag_f1 = f1(avg_llmassign_iprag_p, avg_llmassign_iprag_r)
        avg_sam_f1 = f1(avg_sam_p, avg_sam_r)

        print(f"\n>>> Summary for Project {project} <<<")
        if has_tfidf:
            print(f"TFIDF - Avg Precision: {avg_tfidf_p}, Avg Recall: {avg_tfidf_r}, F1: {avg_tfidf_f1}")
        if has_llmprob:
            print(f"LLMProb - Avg Precision: {avg_llmprob_p}, Avg Recall: {avg_llmprob_r}, F1: {avg_llmprob_f1}")
        if has_llmassign_plain:
            print(f"LLMAssign - Avg Precision: {avg_llmassign_plain_p}, Avg Recall: {avg_llmassign_plain_r}, F1: {avg_llmassign_plain_f1}")
        if has_llmassign_iprag:
            print(f"LLMAssign-IPRAG - Avg Precision: {avg_llmassign_iprag_p}, Avg Recall: {avg_llmassign_iprag_r}, F1: {avg_llmassign_iprag_f1}")
        if has_sam:
            print(f"SAMCodeTLR - Avg Precision: {avg_sam_p}, Avg Recall: {avg_sam_r}, F1: {avg_sam_f1}")

        # Write one row (column order strictly follows the requirements)
        output_rows.append({
            "Project": project,
            "TFIDF_Avg_Precision": avg_tfidf_p,
            "TFIDF_Avg_Recall": avg_tfidf_r,
            "TFIDF_F1": avg_tfidf_f1,

            "LLMProb_Avg_Precision": avg_llmprob_p,
            "LLMProb_Avg_Recall": avg_llmprob_r,
            "LLMProb_F1": avg_llmprob_f1,

            "LLMAssign_Avg_Precision": avg_llmassign_plain_p,
            "LLMAssign_Avg_Recall": avg_llmassign_plain_r,
            "LLMAssign_F1": avg_llmassign_plain_f1,

            "LLMAssign-IPRAG_Avg_Precision": avg_llmassign_iprag_p,
            "LLMAssign-IPRAG_Avg_Recall": avg_llmassign_iprag_r,
            "LLMAssign-IPRAG_F1": avg_llmassign_iprag_f1,

            "SAMCodeTLR_Avg_Precision": avg_sam_p,
            "SAMCodeTLR_Avg_Recall": avg_sam_r,
            "SAMCodeTLR_F1": avg_sam_f1
        })

    # Write the header in the specified order
    header = [
        "Project",
        "TFIDF_Avg_Precision", "TFIDF_Avg_Recall", "TFIDF_F1",
        "LLMProb_Avg_Precision", "LLMProb_Avg_Recall", "LLMProb_F1",
        "LLMAssign_Avg_Precision", "LLMAssign_Avg_Recall", "LLMAssign_F1",
        "LLMAssign-IPRAG_Avg_Precision", "LLMAssign-IPRAG_Avg_Recall", "LLMAssign-IPRAG_F1",
        "SAMCodeTLR_Avg_Precision", "SAMCodeTLR_Avg_Recall", "SAMCodeTLR_F1"
    ]

    with open(output_csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    return output_csv_path


# Usage example
output_csv = "project_summary_output1.csv"
evaluate_by_project_and_module_to_csv("disagreement_report_new1111test1.csv", output_csv)
