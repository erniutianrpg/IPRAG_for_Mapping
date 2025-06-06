import re
import json
import pandas as pd

from hadoop.load_input import load_mapping, load_csv_mapping_with_threshold
from hadoop.precision_of_mapping_for5project import extract_modules_from_file

def compute_edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    if m == 0:
        return n
    if n == 0:
        return m
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1):
        dp[i][0] = i
    for j in range(n+1):
        dp[0][j] = j

    for i in range(1, m+1):
        for j in range(1, n+1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      
                dp[i][j-1] + 1,      
                dp[i-1][j-1] + cost  
            )
    return dp[m][n]

def collect_all_groups_from_gt(gt_file_path):
    if not os.path.exists(gt_file_path):
        print(f"warning: GT file doesn't exist: {gt_file_path}")
        return set()

    try:
        with open(gt_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"warning: Failed to parse the GT file JSON: {gt_file_path}")
        return set()

    group_names = set()
    for group_info in data.get('structure', []):
        raw_group_name = group_info.get('name')
        if raw_group_name and raw_group_name.strip():
            group_names.add(raw_group_name.strip())
    return group_names

def find_close_group_names(module_name, all_gt_groups, distance_threshold=2):
    results = set()
    module_clean = re.sub(r'\W+', '', module_name.lower())

    for gt_grp in all_gt_groups:
        gt_grp_clean = re.sub(r'\W+', '', gt_grp.lower())
        dist = compute_edit_distance(module_clean, gt_grp_clean)
        if dist <= distance_threshold:
            results.add(gt_grp)
    return results


def find_best_match(group_name, modules_list):
    best_module = None
    min_dist = float('inf')

    clean_g = re.sub(r'\W+', '', group_name.lower())

    for module in modules_list:
        clean_m = re.sub(r'\W+', '', module.lower())
        dist = compute_edit_distance(clean_g, clean_m)
        if dist < min_dist:
            min_dist = dist
            best_module = module

    return best_module, min_dist


def unify_all_gt_groups_in_memory(gt_path, modules_list, distance_threshold=2):
    if not os.path.exists(gt_path):
        print(f"warning: GT file doesn't exist：{gt_path}")
        return gt_path  

    try:
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"warning: Failed to parse the GT file JSON：{gt_path}")
        return gt_path

    groups_map = {}  

    for group_info in data.get("structure", []):
        raw_name = group_info.get("name")
        if not raw_name:
            continue

        best_module, best_dist = find_best_match(raw_name, modules_list)

        if best_dist <= distance_threshold:
            if best_module in groups_map:
                groups_map[best_module]["nested"].extend(group_info.get("nested", []))
            else:
                groups_map[best_module] = group_info
                groups_map[best_module]["name"] = best_module

    data["structure"] = list(groups_map.values())  
    base_dir = os.path.dirname(gt_path)
    base_name = os.path.basename(gt_path)
    tmp_file_name = base_name + ".unified.tmp.json"
    tmp_full_path = os.path.join(base_dir, tmp_file_name)

    with open(tmp_full_path, 'w', encoding='utf-8') as out_f:
        json.dump(data, out_f, indent=2, ensure_ascii=False)

    return tmp_full_path


import os

def get_all_files_in_directory(project_path):
    all_files = set()
    for root, dirs, files in os.walk(project_path):
        for file in files:
            all_files.add(os.path.relpath(os.path.join(root, file), project_path))
    return all_files

def calculate_precision_recall(evaluated_mapping, gt_mapping, project_path=None):
    common_items = set(evaluated_mapping.keys()) & set(gt_mapping.keys())
    evaluated_mapping = {k: v for k, v in evaluated_mapping.items() if k in common_items}
    gt_mapping = {k: v for k, v in gt_mapping.items() if k in common_items}

    group_to_items_pred = {}
    for item, group in evaluated_mapping.items():
        if group != 'None':
            group_to_items_pred.setdefault(group, set()).add(item)

    group_to_items_gt = {}
    for item, group in gt_mapping.items():
        if group != 'None':
            group_to_items_gt.setdefault(group, set()).add(item)

    results = {}
    all_correct = 0
    all_pred = 0
    all_gt = 0

    for group, gt_items in group_to_items_gt.items():
        pred_items = group_to_items_pred.get(group, set())

        correct_items = pred_items & gt_items
        incorrect_items = pred_items - gt_items
        missed_items = gt_items - pred_items

        correct = len(correct_items)
        pred_total = len(pred_items)
        gt_total = len(gt_items)

        precision = correct / pred_total if pred_total > 0 else 0.0
        recall = correct / gt_total if gt_total > 0 else 0.0

        results[group] = {
            "precision": precision,
            "recall": recall,
            "correct_items": sorted(correct_items),
            "incorrect_items": sorted(incorrect_items),
            "missed_items": sorted(missed_items)
        }

        all_correct += correct
        all_pred += pred_total
        all_gt += gt_total

    results["overall_precision"] = all_correct / all_pred if all_pred > 0 else 0.0
    results["overall_recall"] = all_correct / all_gt if all_gt > 0 else 0.0

    return results

def analyze_group(
        evaluated_map,
        gt_map,
        target_group="None",
        *,
        verbose=True):
    gt_items = {f for f, g in gt_map.items() if g == target_group}
    predicted_none_items = {f for f, g in evaluated_map.items() if g == target_group and f in gt_map.keys()}
    gt_items &= evaluated_map.keys()

    correct_items       = predicted_none_items & gt_items
    misclassified_items = predicted_none_items - gt_items

    correct       = len(correct_items)
    misclassified = len(misclassified_items)
    total_pred    = len(predicted_none_items)
    total_gt      = len(gt_items)
    check = gt_items-predicted_none_items

    precision_ratio      = correct / total_pred if total_pred else 0.0      
    misclassified_ratio  = misclassified / total_pred if total_pred else 0.0
    recall_ratio         = correct / total_gt if total_gt else 0.0

    if verbose:
        print(f"       Precision : {precision_ratio:.2%}（Total number of files predicted as None: {total_pred} ）")
        print(f"       Recall    : {recall_ratio:.2%}（Total number of files which group is 'None' in the GT: {total_gt} ）")


    return (correct, misclassified,
            precision_ratio, misclassified_ratio,
            sorted(misclassified_items),
            recall_ratio,predicted_none_items)

def evaluate_and_print_results(gt_map, file_path, module_name, exclude_test=True, result_data=None, project_path=None):

    if "tfidf" in file_path and file_path.endswith(".csv"):
        evaluated_map = load_csv_mapping_with_threshold(
            file_path,
            threshold=50.0,
            gt_mapping=gt_map,
            exclude_test=exclude_test,
            excluded_groups={module_name}
        )
    else:
        evaluated_map = load_mapping(
            file_path,
            gt_mapping=gt_map,
            exclude_test=exclude_test,
            excluded_groups={module_name}
        )


    if not evaluated_map:
        print(f"skip file {file_path}: Does not exist or parsed as empty。")
        return

    pr_details = calculate_precision_recall(evaluated_map, gt_map, project_path=project_path)
    print(f"\n  >>> Evaluation results for File A:{file_path} ")
    print("    Precision and Recall for Each Group：")
    overall_precision = pr_details.pop("overall_precision")
    overall_recall = pr_details.pop("overall_recall")

    for grp, details in pr_details.items():
        size_grp_pred = len(details['correct_items']) + len(details['incorrect_items'])
        print(f"      - Group: {grp}")
        print(f"        Precision: {details['precision']:.2f} (Total Number of Files Predicted for This Group: {size_grp_pred})")
        print(f"        Recall   : {details['recall']:.2f} (Total Number of Files in This Group According to the GT: {len(details['correct_items']) + len(details['missed_items'])})")
        print(f"        Correct reflection: {len(details['correct_items'])} ，"
              f"Wrong reflection: {len(details['incorrect_items'])} ，"
              f"Missed Assignment: {len(details['missed_items'])} ")
        print(f"Missed Assignment: {details['missed_items']}")
    print(f"    >> Overall Precision : {overall_precision:.2f}")
    print(f"    >> Overall Recall   : {overall_recall:.2f}")
    
    target_group = "None"
    treat_missing = "tfidf-file-module_scores" in file_path
    correct, misclassified, correct_ratio, misclassified_ratio, \
    misclassified_items, recall_none_ratio,predicted_none_items = analyze_group(evaluated_map, gt_map, target_group=target_group)
    print(f"    >> Analysis of Target Group '{target_group}':")
    print(f"       Correct reflection: {correct}（Accounting for {correct_ratio:.2%}），Wrong reflection: {misclassified}（Accounting for {misclassified_ratio:.2%}）")

    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    file_root, _ = os.path.splitext(base_name)

    new_file_name = file_root + "_undocumented.txt"

    output_path = os.path.join(dir_name, new_file_name)

    with open(output_path, "w", encoding="utf-8") as f:
        for item in sorted(predicted_none_items):
            f.write(item + "\n")

    if result_data is not None:
        if "tfidf-file-module_scores" in file_path:
            result_data['tfidf_file_1_precision'].append(overall_precision)
            result_data['tfidf_file_1_recall'].append(overall_recall)
            result_data['tfidf_file_1_Correct Mapping Ratio for Target Group None'].append(correct_ratio)
            result_data['tfidf_file_1_Wrong Mapping Ratio for Target Group None'].append(misclassified_ratio)
            result_data['tfidf_file_1_目标组None_正确召回比例'].append(recall_none_ratio)
        elif "before_feedback" in file_path:
            result_data['before_feedback_precision'].append(overall_precision)
            result_data['before_feedback_recall'].append(overall_recall)
            result_data['before_feedback_目标组None_正确映射比例'].append(correct_ratio)
            result_data['before_feedback_目标组None_错误映射比例'].append(misclassified_ratio)
            result_data['before_feedback_目标组None_正确召回比例'].append(recall_none_ratio)
        elif "after_feedback" in file_path:
            result_data['after_feedback_precision'].append(overall_precision)
            result_data['after_feedback_recall'].append(overall_recall)
            result_data['after_feedback_目标组None_正确映射比例'].append(correct_ratio)
            result_data['after_feedback_目标组None_错误映射比例'].append(misclassified_ratio)
            result_data['after_feedback_目标组None_正确召回比例'].append(recall_none_ratio)

def process_single_project(project_name, gt_file, modules_file, deepseek_folder, tfidf_folder, exclude_test=True, project_path=None):

    print(f"\n=== Starting to Process Project: {project_name} ===")
    all_gt_groups = collect_all_groups_from_gt(gt_file)
    modules_list = extract_modules_from_file(modules_file)
    if not modules_list:
        print(f"Warning No modules were parsed from {modules_file}")
        return
    valid_modules_list = []
    for module in modules_list:
        excluded_candidates = find_close_group_names(module, all_gt_groups, distance_threshold=2)
        if excluded_candidates:  
            valid_modules_list.append(module)
        else:
            print(f"Warning No GT group name with a sufficiently close edit distance was found for module {module}; it has been removed from the processing list。")
    if not valid_modules_list:
        print("Warning None of the modules have matching GT group names; skipping the processing of this project")
        return
        
    unified_gt_file = unify_all_gt_groups_in_memory(
        gt_file,
        modules_list,
        distance_threshold=2  
    )

    result_data = {
        '模块名称': [],
        'tfidf_file_1_precision': [],
        'tfidf_file_1_recall': [],
        'tfidf_file_1_目标组None_正确映射比例': [],
        'tfidf_file_1_目标组None_正确召回比例': [],
        'tfidf_file_1_目标组None_错误映射比例': [],
        'before_feedback_precision': [],
        'before_feedback_recall': [],
        'before_feedback_目标组None_正确映射比例': [],
        'before_feedback_目标组None_正确召回比例': [],
        'before_feedback_目标组None_错误映射比例': [],
        'after_feedback_precision': [],
        'after_feedback_recall': [],
        'after_feedback_目标组None_正确映射比例': [],
        'after_feedback_目标组None_正确召回比例': [],
        'after_feedback_目标组None_错误映射比例': []
    }
    if project_name=="hadoop":
        valid_modules_list=["YARN"]
    for module in valid_modules_list:
        print(f"\n[项目 {project_name}] >>> 正在排除模块: {module}")

        excluded_candidates = find_close_group_names(module, all_gt_groups, distance_threshold=2)

        gt_map = load_mapping(
            unified_gt_file,
            exclude_test=exclude_test,
            excluded_groups=excluded_candidates
        )
        if project_name=="hadoop":
            gt_map = load_mapping(
                gt_file,
                exclude_test=exclude_test,
                excluded_groups=excluded_candidates
            )
        if not gt_map:
            print(f"[警告] Ground Truth 加载结果为空，跳过后续计算。({unified_gt_file})")
            continue


        tfidf_file_1 = os.path.join(tfidf_folder, f"removed_{module}", "tfidf-file-module_scores.csv")
        before_feedback_path = os.path.join(deepseek_folder, f"removed_{module}", "clustering_before_feedback.json")
        after_feedback_path = os.path.join(deepseek_folder, f"removed_{module}", "clustering_after_feedback.json")

        if not (os.path.exists(tfidf_file_1) and
                os.path.exists(before_feedback_path)):
            print(f"[跳过] 模块 {module} 的文件缺失，跳过该模块的评估。")
            continue
        if "Test" in module:
            continue
        result_data['模块名称'].append(module)
        # ========== 使用相同的 excluded_candidates 来评估各种 mapping 文件 ==========
        # 评估第一个文件：file-module_mapping-tfidf-removed_{module}.json
        # evaluate_and_print_results(gt_map, tfidf_file_1, module, exclude_test=exclude_test, result_data=result_data, project_path=project_path)

        # 评估第二个文件：removed_{module}/clustering_before_feedback.json
        evaluate_and_print_results(gt_map, before_feedback_path, module, exclude_test=exclude_test,
                                   result_data=result_data, project_path=project_path)

        # 评估第三个文件：removed_{module}/clustering_after_feedback.json
        # evaluate_and_print_results(gt_map, after_feedback_path, module, exclude_test=exclude_test,result_data=result_data, project_path=project_path)

    df_result = pd.DataFrame(result_data)
    df_result = df_result[[
        '模块名称',
        'tfidf_file_1_precision', 'before_feedback_precision','after_feedback_precision',
        'tfidf_file_1_recall','before_feedback_recall','after_feedback_recall',
        'tfidf_file_1_目标组None_正确映射比例', 'before_feedback_目标组None_正确映射比例','after_feedback_目标组None_正确映射比例',
        'tfidf_file_1_目标组None_正确召回比例',  
        'before_feedback_目标组None_正确召回比例',  
        'after_feedback_目标组None_正确召回比例', 
        'tfidf_file_1_目标组None_错误映射比例', 'before_feedback_目标组None_错误映射比例','after_feedback_目标组None_错误映射比例']]
    print(df_result.to_string(index=False)) 
    csv_file_path = 'AST_fewCOT_deepseek.csv'

    with open(csv_file_path, 'a', encoding='utf-8-sig') as f:
        f.write(project_name+"\n")
    if not os.path.exists(csv_file_path):
        df_result.to_csv(csv_file_path, index=False, mode='w', header=True, encoding='utf-8-sig')
    else:
        df_result.to_csv(csv_file_path, index=False, mode='a', header=False, encoding='utf-8-sig')

    with open(csv_file_path, 'a', encoding='utf-8-sig') as f:
        f.write("\n")

    print(f"\n=== Finish Processing Project: {project_name} ===\n")

def main():
    base_project_path = r"E:\Zurich\code\consistency-detect\consistency-detect" 
    base_deepseek_path   = r"E:\Zurich\code\lda_demo\lda_demo\hadoop\AST_Prob_gpt" 
    base_tfidf_path = r"E:\Zurich\code\lda_demo\lda_demo\hadoop\TFIDF"

    projects = ["teammates", "teastore", "mediastore", "bigbluebutton", "jabref", "hadoop"]

    for project_name in projects:
        gt_file = os.path.join(base_project_path, project_name, f"updated_{project_name}_gt.json")
        if project_name == "bigbluebutton":
            modules_file = os.path.join(base_project_path, project_name, f"updated_config_bigbluebutton.txt")
        elif project_name == "hadoop":
            modules_file = os.path.join(base_project_path+"\\hadoop0.23.0\\hadoop", "hadoop_early1.txt")
            gt_file = os.path.join(base_project_path+"\\hadoop0.23.0\\hadoop", f"updated_{project_name}_gt.json")
        else:
            modules_file = os.path.join(base_project_path, project_name, f"{project_name}_accurateModules1.txt")

        deepseek_folder = os.path.join(base_deepseek_path, project_name)
        tfidf_folder = os.path.join(base_tfidf_path, project_name)
        project_path = os.path.join(base_project_path, project_name)
        process_single_project(
            project_name=project_name,
            gt_file=gt_file,
            modules_file=modules_file,
            deepseek_folder=deepseek_folder,
            tfidf_folder=tfidf_folder,
            exclude_test=True,
            project_path=project_path
        )

if __name__ == "__main__":
    main()
