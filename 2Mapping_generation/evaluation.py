import re
import json
import pandas as pd

from hadoop.load_input import load_mapping, load_csv_mapping_with_threshold
from hadoop.precision_of_mapping_for5project import extract_modules_from_file


# ========== 1. 计算 Levenshtein 编辑距离的函数，可用第三方库替代 ==========
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
                dp[i-1][j] + 1,      # 删除
                dp[i][j-1] + 1,      # 插入
                dp[i-1][j-1] + cost  # 替换
            )
    return dp[m][n]


# ========== 2. 从 GT 文件中收集所有实际出现过的组名 ==========
def collect_all_groups_from_gt(gt_file_path):
    """
    打开 gt_file 的 JSON 并收集其中所有 group.name。
    返回一个 set()，包含所有（去重后的）组名字符串。
    """
    if not os.path.exists(gt_file_path):
        print(f"[警告] GT 文件不存在: {gt_file_path}")
        return set()

    try:
        with open(gt_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[警告] GT 文件 JSON 解析失败: {gt_file_path}")
        return set()

    group_names = set()
    for group_info in data.get('structure', []):
        raw_group_name = group_info.get('name')
        if raw_group_name and raw_group_name.strip():
            group_names.add(raw_group_name.strip())
    return group_names


# ========== 3. 针对当前模块名，找出与之相近的所有 GT 组名 ==========
def find_close_group_names(module_name, all_gt_groups, distance_threshold=2):
    """
    从 all_gt_groups 中找出与 module_name 编辑距离 <= distance_threshold 的组名。
    返回一个 set()。
    """
    results = set()
    # 先对 module 本身做简单清理(小写去特殊符号等)，方便比较
    module_clean = re.sub(r'\W+', '', module_name.lower())

    for gt_grp in all_gt_groups:
        gt_grp_clean = re.sub(r'\W+', '', gt_grp.lower())
        dist = compute_edit_distance(module_clean, gt_grp_clean)
        if dist <= distance_threshold:
            results.add(gt_grp)

    # 同时把 module 自身也加入，防止刚好 module 就是 GT 里写的那个名字
    # results.add(module_name)
    return results


def find_best_match(group_name, modules_list):
    """
    返回 (best_module, min_dist)，即与 group_name 编辑距离最小的模块 及 该距离。
    """
    best_module = None
    min_dist = float('inf')

    # 清洗当前组名以便比较（去除特殊符号，小写等）
    clean_g = re.sub(r'\W+', '', group_name.lower())

    for module in modules_list:
        clean_m = re.sub(r'\W+', '', module.lower())
        dist = compute_edit_distance(clean_g, clean_m)
        if dist < min_dist:
            min_dist = dist
            best_module = module

    return best_module, min_dist


def unify_all_gt_groups_in_memory(gt_path, modules_list, distance_threshold=2):
    """
    读取 gt_path 的 JSON，
    对其中的每个 group["name"]，若与某 module 的编辑距离 <= distance_threshold，
    则将 group["name"] 改为该 module，并合并相似组的 nested 列表。
    """
    if not os.path.exists(gt_path):
        print(f"[警告] GT 文件不存在：{gt_path}")
        return gt_path  # 找不到文件时就返回原路径，或按需返回空

    # 1) 读 JSON
    try:
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[警告] GT 文件解析错误：{gt_path}")
        return gt_path

    # 2) 使用字典合并相似的组
    groups_map = {}  # 用来保存最终的组映射，key: module_name, value: group_info

    for group_info in data.get("structure", []):
        raw_name = group_info.get("name")
        if not raw_name:
            continue

        # 找到最匹配的 module 及距离
        best_module, best_dist = find_best_match(raw_name, modules_list)

        if best_dist <= distance_threshold:
            # 如果已经有这个 module_name，则合并 nested
            if best_module in groups_map:
                # 合并 nested 文件列表
                groups_map[best_module]["nested"].extend(group_info.get("nested", []))
            else:
                # 第一次遇到这个 module，直接加入
                groups_map[best_module] = group_info
                # 替换 name
                groups_map[best_module]["name"] = best_module

    # 3) 重新将修改后的结果更新回原数据结构
    data["structure"] = list(groups_map.values())  # 获取合并后的值

    # 4) 写回新的临时文件
    base_dir = os.path.dirname(gt_path)
    base_name = os.path.basename(gt_path)
    tmp_file_name = base_name + ".unified.tmp.json"
    tmp_full_path = os.path.join(base_dir, tmp_file_name)

    with open(tmp_full_path, 'w', encoding='utf-8') as out_f:
        json.dump(data, out_f, indent=2, ensure_ascii=False)

    return tmp_full_path


import os

def get_all_files_in_directory(project_path):
    """
    获取 project_path 下所有文件（包括子文件夹中的文件）。

    :param project_path: 项目路径
    :return: 所有文件的相对路径列表
    """
    all_files = set()
    for root, dirs, files in os.walk(project_path):
        for file in files:
            # 获取文件的相对路径（相对于 project_path）
            all_files.add(os.path.relpath(os.path.join(root, file), project_path))
    return all_files

# def calculate_precision_recall(evaluated_mapping, gt_mapping, project_path=None):
#     """
#     计算每个组的精确度（precision）与召回率（recall），并记录正确映射项、错误映射项以及漏分配项等信息。
#
#     :param evaluated_mapping: 由 “文件 -> 组” 组成的映射字典（评估结果）
#     :param gt_mapping: Ground Truth（真实映射关系）
#     :param project_path: 当前项目的根路径，用于过滤不在此项目下的文件（可为空，若为空则不做过滤）
#     :return: 结果字典，形如：
#        {
#          "组名A": {
#             "precision": 0.5,
#             "recall": 0.4,
#             "correct_items": [...],     # 该组里预测正确的文件
#             "incorrect_items": [...],  # 该组里预测为该组但GT不属于该组的文件
#             "missed_items": [...]      # GT属于该组，但未预测到该组的文件（即漏分配）
#          },
#          ...
#          "overall_precision": 0.XX,   # 所有组综合的精确度
#          "overall_recall": 0.XX       # 所有组综合的召回率
#        }
#     """
#
#
#     # ------------------
#     # （2）按组收集预测的文件
#     # ------------------
#     group_to_items_pred = {}
#     for item, group in evaluated_mapping.items():
#         if group != 'None':
#             group_to_items_pred.setdefault(group, set()).add(item)
#
#     # ------------------
#     # （3）按组收集实际的文件
#     # ------------------
#     group_to_items_gt = {}
#     for item, group in gt_mapping.items():
#         if group != 'None':
#             group_to_items_gt.setdefault(group, set()).add(item)
#
#     # ------------------
#     # （4）计算每个组的 Precision 和 Recall
#     # ------------------
#     results = {}
#     all_correct = 0      # 所有组正确映射的文件数
#     all_pred = 0         # 所有组预测到的文件总数
#     all_gt = 0           # 所有组在 GT 中标注的文件总数
#
#     for group, gt_items in group_to_items_gt.items():
#         pred_items = group_to_items_pred.get(group, set())
#
#         correct_items = pred_items & gt_items  # 交集：正确预测的文件
#         incorrect_items = pred_items - gt_items  # 预测该组，但不在 GT 中
#         missed_items = gt_items - pred_items      # 在 GT 中但未预测到该组的文件
#         # （可选）把“不在GT中的文件”单独罗列
#         not_in_gt_items = [f for f in pred_items if f not in gt_mapping]
#         correct = len(correct_items)
#         pred_total = len(pred_items)
#         gt_total = len(gt_items)
#
#         # 计算 Precision 和 Recall
#         precision = correct / pred_total if pred_total > 0 else 0.0
#         recall = correct / gt_total if gt_total > 0 else 0.0
#
#         results[group] = {
#             "precision": precision,
#             "recall": recall,
#             "correct_items": sorted(list(correct_items)),
#             "incorrect_items": sorted(list(incorrect_items)),
#             "missed_items": sorted(list(missed_items))
#         }
#
#         # 汇总到整体统计
#         all_correct += correct
#         all_pred += pred_total
#         all_gt += gt_total
#
#     # ------------------
#     # （5）计算所有组的整体 Precision 和 Recall
#     # ------------------
#     overall_precision = all_correct / all_pred if all_pred > 0 else 0.0
#     overall_recall = all_correct / all_gt if all_gt > 0 else 0.0
#
#     results["overall_precision"] = overall_precision
#     results["overall_recall"] = overall_recall
#
#     return results


# def calculate_precision_recall(evaluated_mapping, gt_mapping, project_path=None):
#     """
#     计算每个组的精确度（precision）与召回率（recall），并记录正确映射项、错误映射项以及漏分配项等信息。
#     此处将只对 “同时存在于 evaluated_mapping 和 gt_mapping 的文件” 进行处理。
#     即若某文件只在其中一个映射里出现，则此处直接忽略该文件。
#
#     :param evaluated_mapping: 由 “文件 -> 组” 组成的映射字典（评估结果）
#     :param gt_mapping: Ground Truth（真实映射关系）
#     :param project_path: 当前项目的根路径，用于过滤不在此项目下的文件（可为空，若为空则不做过滤）
#     :return: 结果字典，形如：
#        {
#          "组名A": {
#             "precision": 0.5,
#             "recall": 0.4,
#             "correct_items": [...],     # 该组里预测正确的文件
#             "incorrect_items": [...],  # 该组里预测为该组但GT不属于该组的文件 (此时为空，因为只统计共同文件)
#             "missed_items": [...]      # GT属于该组，但未预测到该组的文件（即漏分配）
#          },
#          ...
#          "overall_precision": 0.XX,   # 所有组综合的精确度
#          "overall_recall": 0.XX       # 所有组综合的召回率
#        }
#     """
#
#     # 0) 如果需要根据 project_path 做额外过滤，这里可插入逻辑
#     #    （省略具体实现，或使用您已有的过滤方法）
#     # ------------------
#     # （1）仅保留同时在 evaluated_mapping 和 gt_mapping 中的文件
#     # ------------------
#     common_items = set(evaluated_mapping.keys()) & set(gt_mapping.keys())
#
#     # ------------------
#     # （2）按组收集“预测（evaluated_mapping）”的文件，但只保留 common_items
#     # ------------------
#     group_to_items_pred = {}
#     for item, group in evaluated_mapping.items():
#         if item in gt_mapping.keys() and group != 'None':
#             group_to_items_pred.setdefault(group, set()).add(item)
#
#     # ------------------
#     # （3）按组收集“实际（gt_mapping）”的文件，但只保留 common_items
#     # ------------------
#     group_to_items_gt = {}
#     for item, group in gt_mapping.items():
#         if group != 'None':
#             group_to_items_gt.setdefault(group, set()).add(item)
#     # 计算两个映射中所有 group 的文件集合之和（即合并所有 values）
#     # 找出 GT 和 Pred 共同出现的文件（即被两个 mapping 都定义了的项）
#     common_items = set(gt_mapping.keys()) & set(evaluated_mapping.keys())
#
#     # 仅保留 common_items 中的文件构造映射
#     group_to_items_pred = {}
#     for item in common_items:
#         group = evaluated_mapping[item]
#         if group != 'None':
#             group_to_items_pred.setdefault(group, set()).add(item)
#
#     group_to_items_gt = {}
#     for item in common_items:
#         group = gt_mapping[item]
#         if group != 'None':
#             group_to_items_gt.setdefault(group, set()).add(item)
#
#     # 再统一比较所有值的并集
#     all_gt_items = set().union(*group_to_items_gt.values())
#     all_pred_items = set().union(*group_to_items_pred.values())
#
#     missing_in_pred = all_gt_items - all_pred_items
#     extra_in_pred = all_pred_items - all_gt_items
#     common_items_final = all_gt_items & all_pred_items
#
#     # ------------------
#     # （4）计算每个组的 Precision 和 Recall
#     # ------------------
#     results = {}
#     all_correct = 0      # 所有组正确映射的文件数
#     all_pred = 0         # 所有组预测到的文件总数
#     all_gt = 0           # 所有组在 GT 中标注的文件总数
#
#     # 注意：只遍历 GT 中实际存在的组（group_to_items_gt.keys()）
#     for group, gt_items in group_to_items_gt.items():
#         pred_items = group_to_items_pred.get(group, set())
#
#         correct_items = pred_items & gt_items       # 同时预测到、且 GT 也属此组
#         incorrect_items = pred_items - gt_items     # 预测到该组，但 GT 不在此组
#         missed_items = gt_items - pred_items        # GT 属于此组，但未预测到
#
#         correct = len(correct_items)
#         pred_total = len(pred_items)
#         gt_total = len(gt_items)
#
#         # 计算 Precision 和 Recall
#         precision = correct / pred_total if pred_total > 0 else 0.0
#         recall = correct / gt_total if gt_total > 0 else 0.0
#
#         results[group] = {
#             "precision": precision,
#             "recall": recall,
#             "correct_items": sorted(list(correct_items)),
#             "incorrect_items": sorted(list(incorrect_items)),
#             "missed_items": sorted(list(missed_items))
#         }
#
#         # 汇总到整体统计
#         all_correct += correct
#         all_pred += pred_total
#         all_gt += gt_total
#
#     # ------------------
#     # （5）计算所有组的整体 Precision 和 Recall
#     # ------------------
#     overall_precision = all_correct / all_pred if all_pred > 0 else 0.0
#     overall_recall = all_correct / all_gt if all_gt > 0 else 0.0
#
#     results["overall_precision"] = overall_precision
#     results["overall_recall"] = overall_recall
#
#     return results

def calculate_precision_recall(evaluated_mapping, gt_mapping, project_path=None):
    """
    同步 evaluated_mapping 与 gt_mapping 的文件键后，计算每个组的精确度（precision）与召回率（recall），
    并记录正确映射项、错误映射项以及漏分配项等信息。

    :param evaluated_mapping: 由 “文件 -> 组” 组成的映射字典（评估结果）
    :param gt_mapping: Ground Truth（真实映射关系）
    :param project_path: 可选，项目根路径过滤（当前未使用）
    :return: 每组的 Precision / Recall / 正确项 / 错误项 / 漏分配项，以及 overall 指标
    """

    # ------------------
    # （1）双向同步映射，只保留共同文件
    # ------------------
    common_items = set(evaluated_mapping.keys()) & set(gt_mapping.keys())
    evaluated_mapping = {k: v for k, v in evaluated_mapping.items() if k in common_items}
    gt_mapping = {k: v for k, v in gt_mapping.items() if k in common_items}

    # ------------------
    # （2）按组收集映射项
    # ------------------
    group_to_items_pred = {}
    for item, group in evaluated_mapping.items():
        if group != 'None':
            group_to_items_pred.setdefault(group, set()).add(item)

    group_to_items_gt = {}
    for item, group in gt_mapping.items():
        if group != 'None':
            group_to_items_gt.setdefault(group, set()).add(item)

    # ------------------
    # （3）计算每个组的 Precision 和 Recall
    # ------------------
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

    # ------------------
    # （4）整体统计
    # ------------------
    results["overall_precision"] = all_correct / all_pred if all_pred > 0 else 0.0
    results["overall_recall"] = all_correct / all_gt if all_gt > 0 else 0.0

    return results

def analyze_group(
        evaluated_map,
        gt_map,
        target_group="None",
        *,
          # ★ 新增
        verbose=True):
    ...

    """
    针对 target_group（默认 "None"）统计：
        · Precision  (返回的第 3 个值，变量仍叫 correct_ratio，但含义已改为 precision)
        · Recall     (返回的第 6 个值 recall_ratio)
    判定规则：只要文件不在 evaluated_map 中，就认为“预测为 None”。
    返回：
        correct, misclassified, precision_ratio, misclassified_ratio,
        misclassified_items, recall_ratio
    """
    # ① Ground-Truth 中属于 target_group 的所有文件
    # --- ①   GT 中属于 target_group 的所有文件 -----------------
    gt_items = {f for f, g in gt_map.items() if g == target_group}

    # predicted_none_items=set()
    # # ★ 若开启特殊规则 → 把 “缺失于 evaluated_map 的条目” 也视作预测 None
    # if treat_missing_as_none:
    #     predicted_none_items |= (set(gt_map.keys()) - set(evaluated_map.keys()))
    # else:
        # --- ②   预测为 target_group 的文件 -------------------------
    predicted_none_items = {f for f, g in evaluated_map.items() if g == target_group and f in gt_map.keys()}
    gt_items &= evaluated_map.keys()



    # ③ 正确 / 错误计数
    correct_items       = predicted_none_items & gt_items
    misclassified_items = predicted_none_items - gt_items

    correct       = len(correct_items)
    misclassified = len(misclassified_items)
    total_pred    = len(predicted_none_items)
    total_gt      = len(gt_items)
    check = gt_items-predicted_none_items

    # --- Precision & Recall -----------------------------
    precision_ratio      = correct / total_pred if total_pred else 0.0      # ★ 核心改动
    misclassified_ratio  = misclassified / total_pred if total_pred else 0.0
    recall_ratio         = correct / total_gt if total_gt else 0.0

    # ④ 可选打印
    if verbose:
        print(f"       Precision : {precision_ratio:.2%}（预测为 None 的文件共 {total_pred} 个）")
        print(f"       召回率    : {recall_ratio:.2%}（GT 为 None 的文件共 {total_gt} 个）")


    return (correct, misclassified,
            precision_ratio, misclassified_ratio,
            sorted(misclassified_items),
            recall_ratio,predicted_none_items)




def evaluate_and_print_results(gt_map, file_path, module_name, exclude_test=True, result_data=None, project_path=None):
    """
    加载给定 file_path 的映射文件，排除指定 module_name，
    然后计算精度并打印结果。
    """

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
        print(f"[跳过] 文件 {file_path} 不存在或解析为空。")
        return

    # 计算各组的精确度
    # precision_details = calculate_precision(evaluated_map, gt_map)
    pr_details = calculate_precision_recall(evaluated_map, gt_map, project_path=project_path)
    # 输出结果
    print(f"\n  >>> 对文件：{file_path} 的评估结果：")

    # 每个组的精确度/召回率
    print("    各组的精确度（Precision）与召回率（Recall）：")
    # 移除最后两个键（overall_precision, overall_recall）以便只迭代具体组
    overall_precision = pr_details.pop("overall_precision")
    overall_recall = pr_details.pop("overall_recall")

    for grp, details in pr_details.items():
        size_grp_pred = len(details['correct_items']) + len(details['incorrect_items'])
        print(f"      - 组: {grp}")
        print(f"        Precision: {details['precision']:.2f} (预测到该组的文件总数: {size_grp_pred})")
        print(f"        Recall   : {details['recall']:.2f} (该组在 GT 中的文件总数: {len(details['correct_items']) + len(details['missed_items'])})")
        print(f"        正确映射: {len(details['correct_items'])} 个，"
              f"错误映射: {len(details['incorrect_items'])} 个，"
              f"漏分配: {len(details['missed_items'])} 个")
        print(f"漏分配: {details['missed_items']}")
    # 打印总体精确度和召回率
    print(f"    >> 整体精确度(Precision) : {overall_precision:.2f}")
    print(f"    >> 整体召回率(Recall)   : {overall_recall:.2f}")

    # 可选：分析某一特定组(如 'None')
    target_group = "None"
    # correct, misclassified, correct_ratio, misclassified_ratio, misclassified_items = analyze_group(
    #     evaluated_map, gt_map, target_group=target_group
    # )
    treat_missing = "tfidf-file-module_scores" in file_path
    correct, misclassified, correct_ratio, misclassified_ratio, \
    misclassified_items, recall_none_ratio,predicted_none_items = analyze_group(evaluated_map, gt_map, target_group=target_group)
    print(f"    >> 目标组 '{target_group}' 的分析：")
    print(f"       正确映射数: {correct}（占比 {correct_ratio:.2%}），错误映射数: {misclassified}（占比 {misclassified_ratio:.2%}）")
    # print("被错误映射的文件列表：")
    # for item in misclassified_items:
    #     print(f"  - {item}")
    # 拆分目录、文件名、扩展名
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    file_root, _ = os.path.splitext(base_name)

    # 构造新的文件名
    new_file_name = file_root + "_undocumented.txt"

    # 拼接成完整路径
    output_path = os.path.join(dir_name, new_file_name)

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        for item in sorted(predicted_none_items):
            f.write(item + "\n")

    # 将评估结果添加到结果数据字典中
    if result_data is not None:
        if "tfidf-file-module_scores" in file_path:
            result_data['tfidf_file_1_precision'].append(overall_precision)
            result_data['tfidf_file_1_recall'].append(overall_recall)
            result_data['tfidf_file_1_目标组None_正确映射比例'].append(correct_ratio)
            result_data['tfidf_file_1_目标组None_错误映射比例'].append(misclassified_ratio)
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

# ========== 4. 在 process_single_project 中做“扩展排除”处理 ==========
def process_single_project(project_name, gt_file, modules_file, deepseek_folder, tfidf_folder, exclude_test=True, project_path=None):
    """
    在这里，针对每个 module，先收集所有 GT 组名，再找出与 module 名近似的组名集合，
    然后再传给 load_mapping，实现真正“排除”。
    """
    print(f"\n=== 开始处理项目：{project_name} ===")

    # 先一次性获取 GT 中出现的全部组名
    all_gt_groups = collect_all_groups_from_gt(gt_file)
    # (a) 先读出 modules_list
    modules_list = extract_modules_from_file(modules_file)
    if not modules_list:
        print(f"[警告] 未在 {modules_file} 中解析到任何模块。")
        return
    valid_modules_list = []
    for module in modules_list:
        # 找到与该 module 编辑距离接近的 GT 组名
        excluded_candidates = find_close_group_names(module, all_gt_groups, distance_threshold=2)
        if excluded_candidates:  # 如果找到了至少一个接近的组名
            valid_modules_list.append(module)
        else:
            print(f"[警告] 模块 {module} 没有找到与其编辑距离接近的 GT 组名，已从处理列表中删除。")

    if not valid_modules_list:
        print("[警告] 所有模块都没有匹配的 GT 组名，跳过该项目的处理。")
        return
    # (b) 在遍历 for module in modules_list 之前，先统一改写 GT 文件
    #     使得里面所有组名都对齐到最相似的 module。
    unified_gt_file = unify_all_gt_groups_in_memory(
        gt_file,
        modules_list,
        distance_threshold=2  # 可自行调整
    )

    # (c) 再进入 for module in modules_list, 做排除并计算精度
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

        # ========== 关键改动：先在 GT 里找所有与 module 相近的组名 ==========
        excluded_candidates = find_close_group_names(module, all_gt_groups, distance_threshold=2)

        # 然后把这些相近组名一起传给 load_mapping，相当于“排除所有相近名称”
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

        # 判断文件是否都存在
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

    # 将评估结果转换为 DataFrame 并显示
    df_result = pd.DataFrame(result_data)
    # 重新排列列顺序，将精确度、正确映射比例、错误映射比例放在一起
    df_result = df_result[[
        '模块名称',
        'tfidf_file_1_precision', 'before_feedback_precision','after_feedback_precision',
        'tfidf_file_1_recall','before_feedback_recall','after_feedback_recall',
        'tfidf_file_1_目标组None_正确映射比例', 'before_feedback_目标组None_正确映射比例','after_feedback_目标组None_正确映射比例',
        'tfidf_file_1_目标组None_正确召回比例',  # ** 新增
        'before_feedback_目标组None_正确召回比例',  # ** 新增
        'after_feedback_目标组None_正确召回比例',  # ** 新增
        'tfidf_file_1_目标组None_错误映射比例', 'before_feedback_目标组None_错误映射比例','after_feedback_目标组None_错误映射比例']]
    print(df_result.to_string(index=False))  # index=False 不显示行索引
    csv_file_path = 'AST_fewCOT_deepseek.csv'
    # 在每个项目的结果后插入一行空行
    with open(csv_file_path, 'a', encoding='utf-8-sig') as f:
        f.write(project_name+"\n")
    # 检查文件是否存在，如果存在则追加，如果不存在则创建文件并写入表头
    if not os.path.exists(csv_file_path):
        # 如果文件不存在，写入表头
        df_result.to_csv(csv_file_path, index=False, mode='w', header=True, encoding='utf-8-sig')
    else:
        # 如果文件已存在，追加数据，并在每个项目之间插入空行
        df_result.to_csv(csv_file_path, index=False, mode='a', header=False, encoding='utf-8-sig')

    # 在每个项目的结果后插入一行空行
    with open(csv_file_path, 'a', encoding='utf-8-sig') as f:
        f.write("\n")

    print(f"\n=== 结束处理项目：{project_name} ===\n")


# ========== main 函数示意，不展开 ==========
def main():
    """
    主函数示例：通过同一个“公共路径”并结合项目列表，自动遍历多个项目进行分析。
    """

    # 公共部分
    base_project_path = r"E:\Zurich\code\consistency-detect\consistency-detect"  # 存放 GT 和模块定义文件
    base_deepseek_path   = r"E:\Zurich\code\lda_demo\lda_demo\hadoop\AST_Prob_gpt"              # 存放各项目 TF-IDF 结果的路径
    base_tfidf_path = r"E:\Zurich\code\lda_demo\lda_demo\hadoop\TFIDF"
    # 如果您有多个项目，这里可以放在一个列表中
    projects = ["teammates", "teastore", "mediastore", "bigbluebutton", "jabref", "hadoop"]
    #, "teastore", "mediastore", "bigbluebutton", "jabref"
    projects = ["bigbluebutton"]

    # 循环处理每个项目
    for project_name in projects:
        # 根据项目名构建其专属路径
        # 例如 ground truth 文件： updated_{project_name}_gt.json
        #      模块定义文件： {project_name}_accurateModules1.txt
        #      TF-IDF 文件夹： {base_tfidf_path}\{project_name}
        gt_file = os.path.join(base_project_path, project_name, f"updated_{project_name}_gt.json")
        # 根据项目名称使用不同的模块定义文件命名
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
        # 执行对单个项目的分析流程
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