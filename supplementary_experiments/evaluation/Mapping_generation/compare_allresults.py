#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: <your-name>
Date  : 2025-05-30
Desc  : Uniformly output three reports:
        1. disagreement_report.csv(keep the old logic, threshold =50)
        2. tfidf_threshold_sweep_report.csv (TF-IDF threshold 10-90)
        3. llmprob_threshold_sweep_report.csv(LLM-Prob threshold 10-90)
"""
import json
import csv
import os
import re
import argparse
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]


def normalize_file_key(path):
    normalized = path.strip().replace("\\", "/")
    duplicate_project_prefixes = {
        "bgslibrary/bgslibrary/": "bgslibrary/",
        "proxygen/proxygen/": "proxygen/",
    }
    for prefix, replacement in duplicate_project_prefixes.items():
        if normalized.startswith(prefix):
            return replacement + normalized[len(prefix):]

    lerobot_legacy_prefixes = {
        "common/datasets/": "datasets/",
        "common/envs/": "envs/",
        "common/policies/": "policies/",
        "common/robot_devices/": "robot_devices/",
        "common/utils/": "utils/",
        "common/optim/": "optim/",
    }
    for prefix, replacement in lerobot_legacy_prefixes.items():
        if normalized.startswith(prefix):
            return replacement + normalized[len(prefix):]

    source_prefixes = (
        "fastmcp/fastmcp_slim/fastmcp/",
        "fastmcp_slim/fastmcp/",
        "lerobot/src/lerobot/",
        "distributed_camera/",
        "audioFlux/",
        "audioflux/",
        "celery/celery/",
        "qlib/qlib/",
        "src/lerobot/",
        "fastmcp/",
        "lerobot/",
        "celery/",
        "qlib/",
    )
    for prefix in source_prefixes:
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized


def load_samcodetlr_map(project_name, module):
    """
    Read arcotl under samCodeTlr_<project>.csv, Return {file_path -> sentenceID}
    """
    base_arcotl = REPO_ROOT / "experiment" / "project" / "java" / "hadoop" / "arcotl"
    sam_file = os.path.join(base_arcotl, project_name, f"removed_{module}", f"samCodeTlr_{project_name}.csv")
    mapping = {}
    if not os.path.exists(sam_file):
        return mapping

    with open(sam_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')  # file is  tab separated
        for row in reader:
            sentence_id = row["sentenceID"].strip()
            code_id = row["codeID"].strip()
            mapping[normalize_file_key(code_id)] = sentence_id
    return mapping


def load_mapping(file_path, gt_mapping=None, exclude_test=False, excluded_groups=None):
    """
    LoadJSONfile and build the file-item  -> group mapping dictionary.

    :param file_path: JSONfile path
    :param gt_mapping: If provided, it is used to determine whether loaded group names are in the allowlist
    :param exclude_test: If  True,exclude items whose names contain  'test' items
    :param excluded_groups: that must be forced to  None group set (the modules to exclude)
    :return: dictionary whose keys are file-item names(such as a  .java file),values are processed group names
    """
    excluded_groups = set(excluded_groups or [])
    allowed_groups = set()

    # If provided gt_mapping,then count all existing group names
    if gt_mapping:
        for value in gt_mapping.values():
            if isinstance(value, (list, tuple, set)):
                allowed_groups.update(value)
            else:
                allowed_groups.add(str(value))

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[Warning] File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"[Warning] JSONparse error: {file_path}")
        return {}

    item_to_group = {}
    for group in data.get('structure', []):
        raw_group = group.get('name', '')
        # Clean special symbols (keep only letters, digits, and underscores)
        # cleaned_group = re.sub(r'\W+', '', raw_group.strip())
        if raw_group is not None:
            # cleaned_group = re.sub(r'\W+', '', raw_group.strip())
            cleaned_group = raw_group
        else:
            cleaned_group = 'None'


        # Based on exclude /allow/exclude lists to determine the final group name
        if cleaned_group in excluded_groups:
            final_group = 'None'
        elif gt_mapping and cleaned_group not in allowed_groups and len(allowed_groups) > 0:
            # If provided gt_mapping,but the current group name is not in the allowlist, set it to  None
            final_group = 'None'
        else:
            final_group = cleaned_group

        for item in group.get('nested', []):
            item_name = item.get('name', '')
            # if exclude_test and '/test/' in item_name.lower():
            #     continue  # Skip test classes/file
            if item_name == "src/main/java/org/jabref/gui/mergeentries/newmergedialog/fieldsmerger/GroupMerger.java":
                flag=1
            item_to_group[normalize_file_key(item_name)] = final_group

    return item_to_group
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
                dp[i-1][j] + 1,      # delete
                dp[i][j-1] + 1,      # insert
                dp[i-1][j-1] + cost  # replace
            )
    return dp[m][n]

def find_close_group_names(module_name, all_gt_groups, distance_threshold=2):
    """
    Find group names in all_gt_groups whose edit distance from module_name is <= distance_threshold.
    Return a set().
    """
    results = set()
    # First  module itself first for simple cleaning(lowercase, remove special symbols, etc.),for easier comparison
    module_clean = re.sub(r'\W+', '', module_name.lower())

    for gt_grp in all_gt_groups:
        gt_grp_clean = re.sub(r'\W+', '', gt_grp.lower())
        dist = compute_edit_distance(module_clean, gt_grp_clean)
        if dist <= distance_threshold:
            results.add(gt_grp)

    # At the same time, add  module itself as well, in case  module is exactly  GT is exactly the name written in the GT
    # results.add(module_name)
    return results

def collect_all_groups_from_gt(gt_file_path):
    """
    Open the gt_file JSON and collect all group.name values.
    Return a  set(),Contains all deduplicated group-name strings.
    """
    if not os.path.exists(gt_file_path):
        print(f"[Warning] GT File does not exist: {gt_file_path}")
        return set()

    try:
        with open(gt_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[Warning] GT file JSON parse failed: {gt_file_path}")
        return set()

    group_names = set()
    for group_info in data.get('structure', []):
        raw_group_name = group_info.get('name')
        if raw_group_name and raw_group_name.strip():
            group_names.add(raw_group_name.strip())
    return group_names
def extract_modules_from_file(modules_file):
    """
    From a  INMAP configuration file (ModuleNames section).

    File example:
    // *** INMAP CONFIG FILE ***
    // ------------------------------
    // Program Specific Settings
    // ------------------------------
    ModuleNames : {
        "HTML5 Client"
        "HTML5 Server"
        "BBB web"
        "Redis DB"
        "Apps"
        "FSESL"
        "FreeSWITCH"
        "WebRTC-SFU"
        "Internal network connections"
    }
    """

    # Check whether the file exists
    if not os.path.exists(modules_file):
        print(f"[Warning] Module file does not exist: {modules_file}")
        return []

    # Read file content
    with open(modules_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use a regular expression to extract  "ModuleNames" section content
    # Extract ModuleNames all module names in the section
    match = re.search(r'ModuleNames\s*:\s*\{([\s\S]+?)\}', content)
    if not match:
        print(f"[Warning] Not found in the file:  ModuleNames section: {modules_file}")
        return []

    # Get the matched module section and clean up spaces and line breaks in it
    module_names_section = match.group(1).strip()

    # Use regex to extract module names
    modules = re.findall(r'"([^"]+)"', module_names_section)

    return modules  # Return the module-name list
def find_best_match(group_name, modules_list):
    """
    Return (best_module, min_dist),that is, with  group_name module with the smallest edit distance and that distance.
    """
    best_module = None
    min_dist = float('inf')

    # Clean the current group name for comparison (remove special symbols, convert to lowercase, etc.)
    clean_g = re.sub(r'\W+', '', group_name.lower())

    for module in modules_list:
        clean_m = re.sub(r'\W+', '', module.lower())
        dist = compute_edit_distance(clean_g, clean_m)
        if dist < min_dist:
            min_dist = dist
            best_module = module

    return best_module, min_dist
def unify_all_gt_groups_in_memory(gt_path, modules_list, distance_threshold=2,excluded_candidates= None):
    """
    Read the gt_path JSON,
    For each  group["name"],if it has  module edit distance <= distance_threshold,
    then  group["name"] to that  module,and merge similar groups'  nested list.
    """
    if not os.path.exists(gt_path):
        print(f"[Warning] GT File does not exist: {gt_path}")
        return gt_path  # Return the original path if the file cannot be found, or return empty as needed

    # 1) read JSON
    try:
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[Warning] GT File parse error: {gt_path}")
        return gt_path
    excluded_candidates = set(excluded_candidates or [])
    # 2) Use a dictionary to merge similar groups
    groups_map = {}  # Used to store the final group mapping, key: module_name, value: group_info

    for group_info in data.get("structure", []):
        raw_name = group_info.get("name")
        if not raw_name:
            continue

        # Find the best-matching  module and distance
        best_module, best_dist = find_best_match(raw_name, modules_list)
        # Whether either of the two rules is matched
        is_match = best_dist <= distance_threshold
        is_excluded = raw_name in excluded_candidates
        if not (is_match or is_excluded):
            continue
        # Choose the merge key: prefer the matched module name
        key = best_module if is_match else raw_name

        if key in groups_map:
            groups_map[key]["nested"].extend(group_info.get("nested", []))
        else:
            groups_map[key] = group_info.copy()
            groups_map[key]["name"] = key

    # 3) Update the modified results back into the original data structure
    data["structure"] = list(groups_map.values())  # Get the merged values

    # 4) Write back to a new temporary file
    base_dir = os.path.dirname(gt_path)
    base_name = os.path.basename(gt_path)
    tmp_file_name = base_name + ".unified.tmp.json"
    tmp_full_path = os.path.join(base_dir, tmp_file_name)

    with open(tmp_full_path, 'w', encoding='utf-8') as out_f:
        json.dump(data, out_f, indent=2, ensure_ascii=False)

    return tmp_full_path
def load_csv_mapping_with_threshold(file_path, threshold=50.0):
    item_to_group = {}
    item_to_score = {}

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                file_item = normalize_file_key(row["file_path"])
                best_module = row.get("best_module", "").strip()
                # best_module = re.sub(r'\W+', '', best_module.strip())
                best_likelihood = float(row.get("best_likelihood", 0))

                if best_likelihood <= threshold:
                    final_group = "None"
                else:
                    final_group = best_module

                item_to_group[file_item] = final_group
                item_to_score[file_item] = best_likelihood
    except FileNotFoundError:
        print(f"[Warning] CSV File not found: {file_path}")
    except Exception as e:
        print(f"[Error] Load CSV file failed: {file_path}, reason: {e}")

    return item_to_group, item_to_score

def load_cluster_mapping(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for group in data.get("structure", []):
        group_name = group.get("name")
        # group_name = re.sub(r'\W+', '', group_name.strip())
        for item in group.get("nested", []):
            file_name = item.get("name")
            if file_name:
                mapping[normalize_file_key(file_name)] = group_name
    return mapping

def compare_clusterings(before_path, after_path):
    before = load_cluster_mapping(before_path)
    after = load_cluster_mapping(after_path)

    before_files = set(before.keys())
    after_files = set(after.keys())

    added_files = after_files - before_files
    removed_files = before_files - after_files
    common_files = before_files & after_files

    moved_files = {
        f: (before[f], after[f])
        for f in common_files
        if before[f] != after[f]
    }

    return {
        "added_files": added_files,
        "removed_files": removed_files,
        "moved_files": moved_files
    }

import csv
import json
import os
import re
from load_output import write_pr_curve_stacked
# ──────────────────────────────────────────────
#  1. Existing helper functions (unchanged parts omitted)
# ──────────────────────────────────────────────
# ... ...  load_mapping / compute_edit_distance / and other functions remain unchanged ... ...

# ──────────────────────────────────────────────
#  2. New: base loading--parse once CSV get "original best_module and likelihood"
# ──────────────────────────────────────────────
def load_csv_base(file_path):
    """
    Read <file_path>,Return:
        base_map   : {file_item -> (best_module, best_likelihood)}
        score_dict : {file_item -> best_likelihood}
    Do not apply threshold checks, so the data can be reused across multiple thresholds.
    """
    base_map, score_dict = {}, {}
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                file_item      = normalize_file_key(row["file_path"])
                best_module    = row.get("best_module", "").strip()
                best_likelihood = float(row.get("best_likelihood", 0))
                base_map[file_item]  = (best_module, best_likelihood)
                score_dict[file_item] = best_likelihood
    except FileNotFoundError:
        print(f"[Warning] CSV File not found: {file_path}")
    except Exception as e:
        print(f"[Error] Load CSV file failed: {file_path}, reason: {e}")
    return base_map, score_dict


def build_mapping_from_base(base_map, threshold):
    """
    Based on <base_map>(file -> (best_module, score))and the given  threshold,
    Return {file -> final_group},consistent with the old implementation:
        if score <= threshold → None
        otherwise                → best_module
    """
    mapping = {}
    for file_item, (module, score) in base_map.items():
        mapping[file_item] = "None" if score <= threshold else module
    return mapping


# ──────────────────────────────────────────────
#  3. original  compare_three_clusterings is retained for table  1(threshold=50)
# ──────────────────────────────────────────────
def compare_three_clusterings(map1, map2, map3, map4, score1, score2, gt_mapping,
                              project_name, module_name,
                              name1="TFIDF", name2="LLMProb", name3="LLMAssign"):
    all_files = set(map1.keys()) & set(map2.keys()) & set(map3.keys()) \
                & set(map4.keys()) & set(gt_mapping.keys())
    output_rows = []
    for file in all_files:
        if file == "src/main/java/org/jabref/gui/mergeentries/newmergedialog/fieldsmerger/GroupMerger.java":
            flag=1
        g1 = map1[file]
        g2 = map2[file]
        g3 = map3[file]
        g4 = map4[file]
        gt = gt_mapping.get(file, "N/A")
        output_rows.append([
            project_name, module_name, file, gt,
            g1, f"{score1[file]:.2f}",
            g2, f"{score2[file]:.2f}",
            g3,
            g4
        ])
    return output_rows

def compare_three_clusterings(map1, map2, map3, map4, score1, score2, gt_mapping,
                              project_name, module_name,
                              name1="TFIDF", name2="LLMProb", name3="LLMAssign",
                              sam_map=None):
    all_files = set(map1.keys()) & set(map2.keys()) & set(map3.keys()) \
                & set(map4.keys()) & set(gt_mapping.keys())
    output_rows = []
    for file in all_files:
        g1 = map1[file]
        g2 = map2[file]
        g3 = map3[file]
        g4 = map4[file]
        gt = gt_mapping.get(file, "N/A")
        sam_val = sam_map.get(file, "non") if sam_map else "non"
        output_rows.append([
            project_name, module_name, file, gt,
            g1, f"{score1[file]:.2f}",
            g2, f"{score2[file]:.2f}",
            g3,
            g4,
            sam_val           # ← New SAMCodeTLR column
        ])
    return output_rows


THRESHOLDS = list(range(10, 100, 10))                            # ← adjustable
# NEW: Column-header construction helper (with  Precision/Recall)
def make_curve_header():
    hdr = ["Project"]
    for thr in THRESHOLDS:
        hdr.extend([f"Prec@{thr}", f"Reca@{thr}", f"F1@{thr}"])
    return hdr


def strip_project_prefix_for_multi(path, project_names):
    normalized = normalize_file_key(path)
    for project_name in sorted(set(project_names or []), key=len, reverse=True):
        prefix = project_name.strip().replace("\\", "/").strip("/") + "/"
        if prefix and normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized


def renormalize_keys_for_multi(mapping, project_names):
    renormalized = {}
    for key, value in mapping.items():
        renormalized[strip_project_prefix_for_multi(key, project_names)] = value
    return renormalized


def filter_mapping_keys(mapping, allowed_keys):
    if not allowed_keys:
        return mapping
    return {key: value for key, value in mapping.items() if key in allowed_keys}


def load_eval_file_keys(eval_files_path, project_names):
    if not eval_files_path or not os.path.exists(eval_files_path):
        return None
    keys = set()
    with open(eval_files_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                keys.add(strip_project_prefix_for_multi(line, project_names))
    return keys or None


def first_existing_path(*paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return paths[0] if paths else None


def find_project_config_file(project_dir, project_name):
    candidates = [
        f"updated_config_{project_name}.txt",
        f"{project_name}_accurateModules1.txt",
        f"{project_name}_early1.txt",
        "hadoop_early1.txt",
    ]
    for candidate in candidates:
        path = os.path.join(project_dir, candidate)
        if os.path.exists(path):
            return path
    for pattern in (r".*accurateModules.*\.txt$", r"updated_config.*\.txt$", r".*early.*\.txt$"):
        for filename in sorted(os.listdir(project_dir)) if os.path.isdir(project_dir) else []:
            if re.match(pattern, filename):
                return os.path.join(project_dir, filename)
    return None


def find_project_gt_file(project_dir, project_name):
    candidates = [
        f"updated_{project_name}_gt.json",
        f"{project_name}_gt.json",
    ]
    for candidate in candidates:
        path = os.path.join(project_dir, candidate)
        if os.path.exists(path):
            return path
    for filename in sorted(os.listdir(project_dir)) if os.path.isdir(project_dir) else []:
        if filename.lower().endswith(".json") and "gt" in filename.lower():
            return os.path.join(project_dir, filename)
    return None


def discover_multi_missing_cases(multi_missing_root, projects=None):
    llms_root = os.path.join(multi_missing_root, "LLM-S")
    if projects:
        project_names = projects
    elif os.path.isdir(llms_root):
        project_names = [
            name for name in sorted(os.listdir(llms_root))
            if os.path.isdir(os.path.join(llms_root, name))
        ]
    else:
        project_names = []

    for project_name in project_names:
        project_dir = os.path.join(llms_root, project_name)
        if not os.path.isdir(project_dir):
            print(f"[skip] LLM-S project directory not found: {project_dir}")
            continue
        for case_name in sorted(os.listdir(project_dir)):
            case_dir = os.path.join(project_dir, case_name)
            if case_name.startswith("removed_") and os.path.isdir(case_dir):
                yield project_name, case_name


def load_multi_gt_map(gt_file, original_modules, removed_modules, project_names):
    all_gt_groups = collect_all_groups_from_gt(gt_file)
    excluded_candidates = set(removed_modules)
    for removed_module in removed_modules:
        excluded_candidates.update(find_close_group_names(removed_module, all_gt_groups, 1))

    unified_gt_file = unify_all_gt_groups_in_memory(
        gt_file,
        original_modules,
        2,
        excluded_candidates,
    )
    gt_map = load_mapping(unified_gt_file, excluded_groups=excluded_candidates)
    return renormalize_keys_for_multi(gt_map, project_names)


def append_threshold_rows_for_case(project_name, case_label, gt_map,
                                   base_tfidf, tfidf_scores,
                                   base_llmp, llmp_scores,
                                   tbl2_rows, tbl3_rows,
                                   tfidf_stats, llmp_stats,
                                   agg_tfidf_match, agg_llmp_match):
    tfidf_match_stats_mod = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}
    llmp_match_stats_mod = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}

    all_files = set(base_tfidf.keys()) & set(base_llmp.keys()) & set(gt_map.keys())
    for file in all_files:
        row2 = [project_name, case_label, file, gt_map.get(file, "N/A")]
        row3 = [project_name, case_label, file, gt_map.get(file, "N/A")]
        gt_none = (gt_map.get(file, "N/A") == "None")

        for thr in THRESHOLDS:
            tf_pred_none = base_tfidf[file][1] <= thr
            tf_group = "None" if tf_pred_none else base_tfidf[file][0]
            row2.extend([tf_group, f"{tfidf_scores[file]:.2f}"])

            if tf_pred_none and gt_none:
                tfidf_stats[thr]['tp'] += 1
            elif tf_pred_none and (not gt_none):
                tfidf_stats[thr]['fp'] += 1
            elif (not tf_pred_none) and gt_none:
                tfidf_stats[thr]['fn'] += 1

            lp_pred_none = base_llmp[file][1] <= thr
            lp_group = "None" if lp_pred_none else base_llmp[file][0]
            row3.extend([lp_group, f"{llmp_scores[file]:.2f}"])

            if lp_pred_none and gt_none:
                llmp_stats[thr]['tp'] += 1
            elif lp_pred_none and (not gt_none):
                llmp_stats[thr]['fp'] += 1
            elif (not lp_pred_none) and gt_none:
                llmp_stats[thr]['fn'] += 1

            gt_label = gt_map.get(file, "N/A")
            gt_pos = (gt_label != "None")

            tf_pred_label = "None" if tf_pred_none else base_tfidf[file][0]
            if (tf_pred_label != "None") and (tf_pred_label == gt_label):
                tfidf_match_stats_mod[thr]['tp'] += 1
            elif (tf_pred_label != "None") and (tf_pred_label != gt_label):
                tfidf_match_stats_mod[thr]['fp'] += 1
            if gt_pos and (tf_pred_label != gt_label):
                tfidf_match_stats_mod[thr]['fn'] += 1

            lp_pred_label = "None" if lp_pred_none else base_llmp[file][0]
            if (lp_pred_label != "None") and (lp_pred_label == gt_label):
                llmp_match_stats_mod[thr]['tp'] += 1
            elif (lp_pred_label != "None") and (lp_pred_label != gt_label):
                llmp_match_stats_mod[thr]['fp'] += 1
            if gt_pos and (lp_pred_label != gt_label):
                llmp_match_stats_mod[thr]['fn'] += 1

        tbl2_rows.append(row2)
        tbl3_rows.append(row3)

    for thr in THRESHOLDS:
        tp, fp, fn = (
            tfidf_match_stats_mod[thr]['tp'],
            tfidf_match_stats_mod[thr]['fp'],
            tfidf_match_stats_mod[thr]['fn'],
        )
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        agg_tfidf_match[thr]['p'].append(p)
        agg_tfidf_match[thr]['r'].append(r)
        agg_tfidf_match[thr]['f1'].append(f1)

        tp, fp, fn = (
            llmp_match_stats_mod[thr]['tp'],
            llmp_match_stats_mod[thr]['fp'],
            llmp_match_stats_mod[thr]['fn'],
        )
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        agg_llmp_match[thr]['p'].append(p)
        agg_llmp_match[thr]['r'].append(r)
        agg_llmp_match[thr]['f1'].append(f1)


def write_evaluation_outputs(output_dir, tbl1_rows, tbl2_rows, tbl3_rows,
                             curve_rows_tfidf, curve_rows_llmp,
                             curve_rows_tfidf_match, curve_rows_llmp_match):
    def output_path(filename):
        return os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path("disagreement_report_new1111test1.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Project", "Module", "File", "GT",
                         "TFIDF", "TFIDF Score",
                         "LLMProb", "LLMProb Score",
                         "LLMAssign", "LLMAssign-IPRAG",
                         "SAMCodeTLR"])
        for row in tbl1_rows:
            normalized_row = ['non' if str(cell).strip() == "None" else cell for cell in row]
            writer.writerow(normalized_row)

    def make_header(prefix):
        hd = ["Project", "Module", "File", "GT"]
        for thr in THRESHOLDS:
            hd.extend([f"{prefix}@{thr}", f"Score@{thr}"])
        return hd

    with open(output_path("tfidf_threshold_sweep_report-new.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(make_header("TFIDF"))
        writer.writerows(tbl2_rows)

    with open(output_path("llmprob_threshold_sweep_report.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(make_header("LLMProb"))
        writer.writerows(tbl3_rows)

    with open(output_path("tfidf_none_pr_curve-new.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_tfidf])

    with open(output_path("llmprob_none_pr_curve.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_llmp])

    with open(output_path("tfidf_match_pr_curve-new.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_tfidf_match])

    with open(output_path("llmprob_match_pr_curve.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_llmp_match])

    write_pr_curve_stacked(output_path("llmprob_none_pr_curve1.csv"), curve_rows_llmp, THRESHOLDS)
    write_pr_curve_stacked(output_path("llmprob_match_pr_curve1.csv"), curve_rows_llmp_match, THRESHOLDS)


def main_multi_missing(output_dir, multi_missing_root, project_root, projects=None, multi_tfidf_root=None):
    os.makedirs(output_dir, exist_ok=True)
    project_names_for_prefix = projects or [
        name for name in os.listdir(project_root)
        if os.path.isdir(os.path.join(project_root, name))
    ]

    tbl1_rows, tbl2_rows, tbl3_rows = [], [], []
    curve_rows_tfidf, curve_rows_llmp = [], []
    curve_rows_tfidf_match, curve_rows_llmp_match = [], []

    def avg(x):
        return sum(x) / len(x) if x else 0.0

    current_project = None
    project_state = None

    def flush_project_state():
        if not project_state:
            return
        project_name = project_state["project_name"]
        curve_row_tf = [project_name]
        curve_row_lp = [project_name]
        for thr in THRESHOLDS:
            tp, fp, fn = (
                project_state["tfidf_stats"][thr]['tp'],
                project_state["tfidf_stats"][thr]['fp'],
                project_state["tfidf_stats"][thr]['fn'],
            )
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            reca = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * reca / (prec + reca) if (prec + reca) else 0.0
            curve_row_tf.extend([f"{prec:.4f}", f"{reca:.4f}", f"{f1:.4f}"])

            tp, fp, fn = (
                project_state["llmp_stats"][thr]['tp'],
                project_state["llmp_stats"][thr]['fp'],
                project_state["llmp_stats"][thr]['fn'],
            )
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            reca = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * reca / (prec + reca) if (prec + reca) else 0.0
            curve_row_lp.extend([f"{prec:.4f}", f"{reca:.4f}", f"{f1:.4f}"])

        curve_rows_tfidf.append(curve_row_tf)
        curve_rows_llmp.append(curve_row_lp)

        curve_row_tf_match = [project_name]
        curve_row_lp_match = [project_name]
        for thr in THRESHOLDS:
            p = avg(project_state["agg_tfidf_match"][thr]['p'])
            r = avg(project_state["agg_tfidf_match"][thr]['r'])
            f1 = 2 * p * r / (p + r) if (p + r) else 0.0
            curve_row_tf_match.extend([f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])

            p = avg(project_state["agg_llmp_match"][thr]['p'])
            r = avg(project_state["agg_llmp_match"][thr]['r'])
            f1 = 2 * p * r / (p + r) if (p + r) else 0.0
            curve_row_lp_match.extend([f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])

        curve_rows_tfidf_match.append(curve_row_tf_match)
        curve_rows_llmp_match.append(curve_row_lp_match)

    for project_name, case_name in discover_multi_missing_cases(multi_missing_root, projects):
        if project_name != current_project:
            flush_project_state()
            current_project = project_name
            project_state = {
                "project_name": project_name,
                "tfidf_stats": {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS},
                "llmp_stats": {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS},
                "agg_tfidf_match": {thr: {'p': [], 'r': [], 'f1': []} for thr in THRESHOLDS},
                "agg_llmp_match": {thr: {'p': [], 'r': [], 'f1': []} for thr in THRESHOLDS},
            }
            print(f"\n=== {project_name} ===")

        case_label = case_name[len("removed_"):] if case_name.startswith("removed_") else case_name
        print(f"-- processing multi-missing case {case_label}")

        project_dir = os.path.join(project_root, project_name)
        modules_file = find_project_config_file(project_dir, project_name)
        gt_file = find_project_gt_file(project_dir, project_name)
        if not modules_file or not gt_file:
            print(f"[skip] missing project config or GT for {project_name}")
            continue

        original_modules = extract_modules_from_file(modules_file)
        updated_modules_file = first_existing_path(
            os.path.join(multi_missing_root, "LLM-S", project_name, case_name, "updated_module_info.txt"),
            os.path.join(multi_missing_root, "LLM-A", project_name, case_name, "updated_module_info.txt"),
            os.path.join(multi_missing_root, "IP-RAG", project_name, case_name, "updated_module_info.txt"),
        )
        updated_modules = extract_modules_from_file(updated_modules_file) if updated_modules_file else []
        removed_modules = [module for module in original_modules if module not in set(updated_modules)]
        if not removed_modules:
            print(f"[skip] cannot infer removed modules for {project_name}/{case_name}")
            continue

        llms_case = os.path.join(multi_missing_root, "LLM-S", project_name, case_name)
        llma_case = os.path.join(multi_missing_root, "LLM-A", project_name, case_name)
        iprag_case = os.path.join(multi_missing_root, "IP-RAG", project_name, case_name)
        tfidf_candidates = []
        if multi_tfidf_root:
            tfidf_candidates.append(
                os.path.join(multi_tfidf_root, project_name, case_name, "tfidf-file-module_scores.csv")
            )
        tfidf_candidates.extend([
            os.path.join(iprag_case, "tfidf-file-module_scores.csv"),
            os.path.join(llms_case, "tfidf-file-module_scores.csv"),
            os.path.join(llma_case, "tfidf-file-module_scores.csv"),
        ])
        tfidf_path = first_existing_path(*tfidf_candidates)
        llmp_path = os.path.join(llms_case, "module_mapping_scores.csv")
        llas_path = os.path.join(llma_case, "clustering_before_feedback.json")
        llasp_path = os.path.join(iprag_case, "clustering_before_feedback.json")
        eval_files_path = first_existing_path(
            os.path.join(llms_case, "eval_files.txt"),
            os.path.join(llma_case, "eval_files.txt"),
            os.path.join(iprag_case, "eval_files.txt"),
        )

        required_paths = {
            "TFIDF": tfidf_path,
            "LLM-S": llmp_path,
            "LLM-A": llas_path,
            "IP-RAG": llasp_path,
        }
        missing = [(name, path) for name, path in required_paths.items() if not os.path.exists(path)]
        if missing:
            print("[skip] missing multi-missing inputs:")
            for name, path in missing:
                print(f"  - {name}: {path}")
            continue

        gt_map = load_multi_gt_map(gt_file, original_modules, removed_modules, project_names_for_prefix)
        eval_keys = load_eval_file_keys(eval_files_path, project_names_for_prefix)
        gt_map = filter_mapping_keys(gt_map, eval_keys)

        map_tfidf_50, score_tfidf = load_csv_mapping_with_threshold(tfidf_path, 80)
        map_llmp_50, score_llmp = load_csv_mapping_with_threshold(llmp_path, 80)
        map_llas = load_cluster_mapping(llas_path)
        map_llasp = load_cluster_mapping(llasp_path)
        map_tfidf_50 = filter_mapping_keys(renormalize_keys_for_multi(map_tfidf_50, project_names_for_prefix), eval_keys)
        score_tfidf = filter_mapping_keys(renormalize_keys_for_multi(score_tfidf, project_names_for_prefix), eval_keys)
        map_llmp_50 = filter_mapping_keys(renormalize_keys_for_multi(map_llmp_50, project_names_for_prefix), eval_keys)
        score_llmp = filter_mapping_keys(renormalize_keys_for_multi(score_llmp, project_names_for_prefix), eval_keys)
        map_llas = filter_mapping_keys(renormalize_keys_for_multi(map_llas, project_names_for_prefix), eval_keys)
        map_llasp = filter_mapping_keys(renormalize_keys_for_multi(map_llasp, project_names_for_prefix), eval_keys)

        tbl1_rows.extend(
            compare_three_clusterings(
                map_tfidf_50, map_llmp_50, map_llas, map_llasp,
                score_tfidf, score_llmp, gt_map,
                project_name, case_label
            )
        )

        base_tfidf, tfidf_scores = load_csv_base(tfidf_path)
        base_llmp, llmp_scores = load_csv_base(llmp_path)
        base_tfidf = filter_mapping_keys(renormalize_keys_for_multi(base_tfidf, project_names_for_prefix), eval_keys)
        tfidf_scores = filter_mapping_keys(renormalize_keys_for_multi(tfidf_scores, project_names_for_prefix), eval_keys)
        base_llmp = filter_mapping_keys(renormalize_keys_for_multi(base_llmp, project_names_for_prefix), eval_keys)
        llmp_scores = filter_mapping_keys(renormalize_keys_for_multi(llmp_scores, project_names_for_prefix), eval_keys)

        append_threshold_rows_for_case(
            project_name, case_label, gt_map,
            base_tfidf, tfidf_scores, base_llmp, llmp_scores,
            tbl2_rows, tbl3_rows,
            project_state["tfidf_stats"], project_state["llmp_stats"],
            project_state["agg_tfidf_match"], project_state["agg_llmp_match"],
        )

    flush_project_state()
    write_evaluation_outputs(
        output_dir,
        tbl1_rows, tbl2_rows, tbl3_rows,
        curve_rows_tfidf, curve_rows_llmp,
        curve_rows_tfidf_match, curve_rows_llmp_match,
    )
    print(f"[OK] multi-missing evaluation outputs saved to {output_dir}")

# ──────────────────────────────────────────────
#  4. Main workflow main()
# ──────────────────────────────────────────────
def main(output_dir=".", multi_missing_root=None, multi_project_root=None,
         multi_projects=None, multi_tfidf_root=None):
    if multi_missing_root:
        project_root = multi_project_root or str(REPO_ROOT / "experiment" / "project" / "java")
        main_multi_missing(output_dir, multi_missing_root, project_root, multi_projects, multi_tfidf_root)
        return

    os.makedirs(output_dir, exist_ok=True)

    def output_path(filename):
        return os.path.join(output_dir, filename)
    # === Basic configuration ===
    base_project_path = str(REPO_ROOT / "experiment" / "project" / "java")
    base_result_path = str(REPO_ROOT / "experiment" / "result" / "java" / "java_experiment_results")
    base_tfidf_path = str(REPO_ROOT / "baseline-tfidf" / "result" / "java")
    model = "glm-4-air-250414"
    # projects = ["audioflux", "bgslibrary", "distributed_camera","proxygen"]
    # projects = ["celery", "fastmcp", "lerobot", "qlib"]
    projects = ["bigbluebutton","jabref","mediastore","teammates","teastore","hadoop"]
    # projects = ["audioflux"]
    # Threshold sequence 10-90(step  10)
    THRESHOLDS = list(range(10, 100, 10))

    # Row caches for the three tables
    tbl1_rows, tbl2_rows, tbl3_rows = [], [], []
    # NEW: two curve tables
    curve_rows_tfidf, curve_rows_llmp = [], []
    curve_rows_tfidf_match, curve_rows_llmp_match = [], []

    def avg(x):
        return sum(x) / len(x) if x else 0.0

    def first_existing_path(*paths):
        for path in paths:
            if os.path.exists(path):
                return path
        return paths[0]

    def print_missing_inputs(paths_by_name):
        missing = [(name, path) for name, path in paths_by_name.items()
                   if not os.path.exists(path)]
        if not missing:
            return False
        print("[skip] Some input files are missing:")
        for name, path in missing:
            print(f"  - {name}: {path}")
        return True

    # ---- Project iteration ----
    addition = "" #_precisionDown,_recallDown
    for project_name in projects:
        print(f"\n=== {project_name} ===")
        # Aggregation container: collect each module's  Prec/Rec/F1,do simple averaging at the end of the project
        agg_tfidf_match = {thr: {'p': [], 'r': [], 'f1': []} for thr in THRESHOLDS}     # positive class="predicted as non- None and hits  GT"
        agg_llmp_match  = {thr: {'p': [], 'r': [], 'f1': []} for thr in THRESHOLDS}

        # NEW: Initialize the statistics dictionary for the current project
        tfidf_stats = {thr: {'tp':0,'fp':0,'fn':0} for thr in THRESHOLDS}
        llmp_stats  = {thr: {'tp':0,'fp':0,'fn':0} for thr in THRESHOLDS}
        # New: correct matches are treated as the positive class (>THR and best_module == GT)
        tfidf_match_stats = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}
        llmp_match_stats = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}
        # --- Path preparation (same as the old logic, omitted) ---
        # ... ...(Keep your original path derivation)...
        gt_file = os.path.join(base_project_path, project_name,
                               f"updated_{project_name}_gt.json")
        modules_file = os.path.join(base_project_path, project_name,
                                    f"updated_config_{project_name}.txt")
        if project_name == "bigbluebutton":
            modules_file = os.path.join(base_project_path, project_name,
                                        "updated_config_bigbluebutton.txt")
        elif project_name == "hadoop":
            modules_file = os.path.join(base_project_path +
                                        r"\hadoop",
                                        "hadoop_early1.txt")
            gt_file = os.path.join(base_project_path +
                                   r"\hadoop",
                                   f"updated_{project_name}_gt.json")
        else:
            modules_file = os.path.join(base_project_path, project_name,
                                        f"{project_name}_accurateModules1.txt")

        modules_list = extract_modules_from_file(modules_file)
        if not modules_list:
            print(f"[Warning] not in  {modules_file} any modules from ")
            continue
        if project_name == "hadoop":
            modules_list = ["MapReduce", "Common", "HDFS", "YARN"]

        all_gt_groups = collect_all_groups_from_gt(gt_file)

        # --- Filter valid modules ---
        valid_modules = []
        for mod in modules_list:
            if find_close_group_names(mod, all_gt_groups, 2):
                valid_modules.append(mod)
            else:
                print(f"[Warning] module {mod} in GT has no approximate match in the GT and has been ignored.")

        if not valid_modules:
            print("[Warning] No valid modules; skipping project.")
            continue

        # --- unify GT group names to the most similar modules ---
        # unified_gt_file = unify_all_gt_groups_in_memory(gt_file, modules_list, 2)

        # ---- Module iteration ----
        if project_name == "hadoop":
            valid_modules = ["YARN"]        # Hadoop special handling

        for module in valid_modules:
            print(f"-- Processing module {module} --")
            excluded_candidates = find_close_group_names(module, all_gt_groups, 1)
            # Read and immediately convert to a set
            if project_name == "bigbluebutton":
                initial_modules_file = modules_file
            elif project_name == "hadoop":
                initial_modules_file = modules_file
            else:
                initial_modules_file = os.path.join(
                    # base_project_path, project_name, f"updated_config_{project_name}.txt"
                    base_project_path, project_name, f"{project_name}_accurateModules1.txt"
                )

            initial_modules = set(extract_modules_from_file(initial_modules_file))
            current_modules = set(extract_modules_from_file(modules_file))

            # Union first, then difference -- same as the original expression
            excluded_candidates = excluded_candidates | (initial_modules - current_modules)
            unified_gt_file = unify_all_gt_groups_in_memory(gt_file, modules_list, 2, excluded_candidates)

            # Similar group names (to exclude)
            # excluded = find_close_group_names(module, all_gt_groups, 2)

            gt_map = load_mapping(
                unified_gt_file if project_name != "hadoop" else gt_file,
                excluded_groups=excluded_candidates
            )
            test=gt_map.get("src/main/java/org/jabref/gui/mergeentries/newmergedialog/fieldsmerger/GroupMerger.java", "N/A")

            # path
            tfidf_path = os.path.join(base_tfidf_path, project_name, f"removed_{module}",
                                      "tfidf-file-module_scores.csv")
            llmp_path = first_existing_path(
                os.path.join(base_result_path, "LLM-S", model, project_name, f"removed_{module}",
                                     "module_mapping_scores.csv"),
                os.path.join(base_result_path, "LLM-S", project_name, f"removed_{module}",
                         "module_mapping_scores.csv"),
            )
            llas_path = first_existing_path(
                os.path.join(base_result_path, "LLM-A", model, project_name, f"removed_{module}",
                             "clustering_before_feedback.json"),
                os.path.join(base_result_path, "LLM-A", project_name, f"removed_{module}",
                             "clustering_before_feedback.json"),
            )
            llasp_path = first_existing_path(
                os.path.join(base_result_path, "IP-RAG", model, project_name, f"removed_{module}",
                             "clustering_before_feedback.json"),
                os.path.join(base_result_path, "IP-RAG", project_name, f"removed_{module}",
                             "clustering_before_feedback.json"),
            )

            if print_missing_inputs({
                "TFIDF": tfidf_path,
                "LLM-S": llmp_path,
                "LLM-A": llas_path,
                "IP-RAG": llasp_path,
            }):
                continue

            # === 1) Old logic (threshold =50) ===
            map_tfidf_50, score_tfidf = load_csv_mapping_with_threshold(tfidf_path, 100)
            map_llmp_50,  score_llmp  = load_csv_mapping_with_threshold(llmp_path, 80)
            map_llas   = load_cluster_mapping(llas_path)
            map_llasp  = load_cluster_mapping(llasp_path)

            # tbl1_rows.extend(
            #     compare_three_clusterings(
            #         map_tfidf_50, map_llmp_50, map_llas, map_llasp,
            #         score_tfidf, score_llmp, gt_map,
            #         project_name, module
            #     )
            # )
            sam_map = load_samcodetlr_map(project_name, module)

            tbl1_rows.extend(
                compare_three_clusterings(
                    map_tfidf_50, map_llmp_50, map_llas, map_llasp,
                    score_tfidf, score_llmp, gt_map,
                    project_name, module
                )
            )

            # === 2) Threshold-sweep preparation (parse the base  CSV) ===
            base_tfidf, tfidf_scores = load_csv_base(tfidf_path)
            base_llmp,  llmp_scores  = load_csv_base(llmp_path)

            # -- In-module statistics containers (same structure as the original project-level containers, but scoped only to the current module)--
            tfidf_stats_mod = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}       # None as the positive class
            llmp_stats_mod  = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}
            tfidf_match_stats_mod = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS} # positive class="predicted as non- None and hits  GT"
            llmp_match_stats_mod  = {thr: {'tp': 0, 'fp': 0, 'fn': 0} for thr in THRESHOLDS}


            # All files (ensure keys exist)
            all_files = set(base_tfidf.keys()) & set(base_llmp.keys()) & set(gt_map.keys())
            for file in all_files:
                row2 = [project_name, module, file, gt_map.get(file, "N/A")]
                row3 = [project_name, module, file, gt_map.get(file, "N/A")]

                gt_none = (gt_map.get(file, "N/A") == "None")

                for thr in THRESHOLDS:
                    # -- TF-IDF -- (generate sweep table + update statistics)
                    tf_pred_none = base_tfidf[file][1] <= thr
                    tf_group = "None" if tf_pred_none else base_tfidf[file][0]
                    row2.extend([tf_group, f"{tfidf_scores[file]:.2f}"])

                    if tf_pred_none and gt_none:
                        tfidf_stats[thr]['tp'] += 1
                    elif tf_pred_none and (not gt_none):
                        tfidf_stats[thr]['fp'] += 1
                    elif (not tf_pred_none) and gt_none:
                        tfidf_stats[thr]['fn'] += 1

                    # -- LLM-Prob -- (generate sweep table + update statistics)
                    lp_pred_none = base_llmp[file][1] <= thr
                    lp_group = "None" if lp_pred_none else base_llmp[file][0]
                    row3.extend([lp_group, f"{llmp_scores[file]:.2f}"])

                    if lp_pred_none and gt_none:
                        llmp_stats[thr]['tp'] += 1
                    elif lp_pred_none and (not gt_none):
                        llmp_stats[thr]['fp'] += 1
                    elif (not lp_pred_none) and gt_none:
                        llmp_stats[thr]['fn'] += 1

                    # -- positive class="predicted as non- None and hits  GT"statistics --(match evaluation)
                    gt_label = gt_map.get(file, "N/A")
                    gt_pos = (gt_label != "None")

                    tf_pred_label = "None" if tf_pred_none else base_tfidf[file][0]
                    if (tf_pred_label != "None") and (tf_pred_label == gt_label):
                        tfidf_match_stats_mod[thr]['tp'] += 1
                    elif (tf_pred_label != "None") and (tf_pred_label != gt_label):
                        tfidf_match_stats_mod[thr]['fp'] += 1
                    if gt_pos and (tf_pred_label != gt_label):
                        tfidf_match_stats_mod[thr]['fn'] += 1

                    lp_pred_label = "None" if lp_pred_none else base_llmp[file][0]
                    if (lp_pred_label != "None") and (lp_pred_label == gt_label):
                        llmp_match_stats_mod[thr]['tp'] += 1
                    elif (lp_pred_label != "None") and (lp_pred_label != gt_label):
                        llmp_match_stats_mod[thr]['fp'] += 1
                    if gt_pos and (lp_pred_label != gt_label):
                        llmp_match_stats_mod[thr]['fn'] += 1

                tbl2_rows.append(row2)
                tbl3_rows.append(row3)
                # -- End of module: compute this module's  P/R/F1 and add them to the project aggregation container (for simple averaging)--
            for thr in THRESHOLDS:
                # Matches are positive-class -- TFIDF
                tp, fp, fn = tfidf_match_stats_mod[thr]['tp'], tfidf_match_stats_mod[thr]['fp'], \
                tfidf_match_stats_mod[thr]['fn']
                p = tp / (tp + fp) if (tp + fp) else 0.0
                r = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * p * r / (p + r) if (p + r) else 0.0
                agg_tfidf_match[thr]['p'].append(p);
                agg_tfidf_match[thr]['r'].append(r);
                agg_tfidf_match[thr]['f1'].append(f1)

                # Matches are positive-class -- LLMProb
                tp, fp, fn = llmp_match_stats_mod[thr]['tp'], llmp_match_stats_mod[thr]['fp'], \
                llmp_match_stats_mod[thr]['fn']
                p = tp / (tp + fp) if (tp + fp) else 0.0
                r = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * p * r / (p + r) if (p + r) else 0.0
                agg_llmp_match[thr]['p'].append(p);
                agg_llmp_match[thr]['r'].append(r);
                agg_llmp_match[thr]['f1'].append(f1)

        # ---- After iterating through all modules (the end of the project), compute  PR ----
        curve_row_tf = [project_name]
        curve_row_lp = [project_name]
        for thr in THRESHOLDS:
            # TF-IDF
            tp, fp, fn = tfidf_stats[thr]['tp'], tfidf_stats[thr]['fp'], tfidf_stats[thr]['fn']
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            reca = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * reca / (prec + reca) if (prec + reca) else 0.0
            curve_row_tf.extend([f"{prec:.4f}", f"{reca:.4f}", f"{f1:.4f}"])

            # LLMProb
            tp, fp, fn = llmp_stats[thr]['tp'], llmp_stats[thr]['fp'], llmp_stats[thr]['fn']
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            reca = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * reca / (prec + reca) if (prec + reca) else 0.0
            curve_row_lp.extend([f"{prec:.4f}", f"{reca:.4f}", f"{f1:.4f}"])

        curve_rows_tfidf.append(curve_row_tf)
        curve_rows_llmp.append(curve_row_lp)


        # ---- End of project: average the module metrics for each threshold and write them to the project curve row ----
        curve_row_tf_match = [project_name]
        curve_row_lp_match = [project_name]
        for thr in THRESHOLDS:
            # Matches are positive-class -- TFIDF
            p = avg(agg_tfidf_match[thr]['p']); r = avg(agg_tfidf_match[thr]['r'])
            f1 = 2 * p * r / (p + r) if (p + r) else 0.0
            curve_row_tf_match.extend([f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])
            # Matches are positive-class -- LLMProb
            p = avg(agg_llmp_match[thr]['p']); r = avg(agg_llmp_match[thr]['r'])
            f1 = 2 * p * r / (p + r) if (p + r) else 0.0
            curve_row_lp_match.extend([f"{p:.4f}", f"{r:.4f}", f"{f1:.4f}"])
        curve_rows_tfidf_match.append(curve_row_tf_match)
        curve_rows_llmp_match.append(curve_row_lp_match)
        # # =========== 2a) TF-IDF threshold sweep table ===========
            # for file in all_files:
            #     row = [project_name, module, file, gt_map.get(file, "N/A")]
            #     for thr in THRESHOLDS:
            #         group = "None" if base_tfidf[file][1] <= thr else base_tfidf[file][0]
            #         row.append(group)
            #         row.append(f"{tfidf_scores[file]:.2f}")
            #     tbl2_rows.append(row)
            #
            # # =========== 2b) LLM-Prob threshold sweep table ==========
            # for file in all_files:
            #     row = [project_name, module, file, gt_map.get(file, "N/A")]
            #     for thr in THRESHOLDS:
            #         group = "None" if base_llmp[file][1] <= thr else base_llmp[file][0]
            #         row.append(group)
            #         row.append(f"{llmp_scores[file]:.2f}")
            #     tbl3_rows.append(row)

    # ──────────────────────────────────────────────
    #  5. Write the three tables
    # ──────────────────────────────────────────────
    # table 1
    # with open("disagreement_report_new1111.csv", "w", newline='', encoding='utf-8') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["Project", "Module", "File", "GT",
    #                      "TFIDF", "TFIDF Score",
    #                      "LLMProb", "LLMProb Score",
    #                      "LLMAssign", "LLMAssign-IPRAG"])
    #     # writer.writerows(tbl1_rows)
    #     # # for each row's Nonereplace item by item
    #     for row in tbl1_rows:
    #         normalized_row = ['non' if str(cell).strip() == "None" else cell for cell in row]
    #         writer.writerow(normalized_row)
    with open(output_path("disagreement_report_new1111test1.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Project", "Module", "File", "GT",
                         "TFIDF", "TFIDF Score",
                         "LLMProb", "LLMProb Score",
                         "LLMAssign", "LLMAssign-IPRAG",
                         "SAMCodeTLR"])  # ← New column header
        for row in tbl1_rows:
            normalized_row = ['non' if str(cell).strip() == "None" else cell for cell in row]
            writer.writerow(normalized_row)

    print("[OK] disagreement_report.csv has been generated")

    # # Header construction helper
    def make_header(prefix):
        hd = ["Project", "Module", "File", "GT"]
        for thr in THRESHOLDS:
            hd.extend([f"{prefix}@{thr}", f"Score@{thr}"])
        return hd

    # table 2:TFIDF
    with open(output_path("tfidf_threshold_sweep_report-new.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(make_header("TFIDF"))
        writer.writerows(tbl2_rows)
    print("[OK] tfidf_threshold_sweep_report.csv has been generated")

    # table 3:LLMProb
    with open(output_path("llmprob_threshold_sweep_report.csv"), "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(make_header("LLMProb"))
        writer.writerows(tbl3_rows)
    print("[OK] llmprob_threshold_sweep_report.csv has been generated")
    # NEW: write Precision / Recall curve table
    with open(output_path("tfidf_none_pr_curve-new.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_tfidf])
    print("[OK] tfidf_none_pr_curve.csv has been generated")

    with open(output_path("llmprob_none_pr_curve.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_llmp])
    print("[OK] llmprob_none_pr_curve.csv has been generated")

    # NEW: write "correct matches are positive-class  Precision / Recall / F1 curve table
    with open(output_path("tfidf_match_pr_curve-new.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_tfidf_match])
    print("[OK] tfidf_match_pr_curve.csv has been generated")

    with open(output_path("llmprob_match_pr_curve.csv"), "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([make_curve_header(), *curve_rows_llmp_match])
    print("[OK] llmprob_match_pr_curve.csv has been generated")

    # Use Precision one row / Recall one row / F1 one row LLMProb two curve tables
    write_pr_curve_stacked(output_path("llmprob_none_pr_curve1.csv"),  curve_rows_llmp,        THRESHOLDS)
    print("[OK] llmprob_none_pr_curve.csv has been generated ( Precision/Recall/F1 shown horizontally by row)")

    write_pr_curve_stacked(output_path("llmprob_match_pr_curve1.csv"), curve_rows_llmp_match,  THRESHOLDS)
    print("[OK] llmprob_match_pr_curve.csv has been generated ( Precision/Recall/F1 shown horizontally by row)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory where generated evaluation CSV files are saved.",
    )
    parser.add_argument(
        "--multi-missing-root",
        default=None,
        help="Enable multi-module-missing evaluation with this result root.",
    )
    parser.add_argument(
        "--multi-project-root",
        default=str(REPO_ROOT / "experiment" / "project" / "java"),
        help="Project root containing module config and GT files for multi-module-missing evaluation.",
    )
    parser.add_argument(
        "--multi-projects",
        nargs="*",
        default=None,
        help="Optional project names to include in multi-module-missing evaluation.",
    )
    parser.add_argument(
        "--multi-tfidf-root",
        default=None,
        help="Optional TF-IDF-only multi-module-missing result root.",
    )
    args = parser.parse_args()
    main(
        args.output_dir,
        multi_missing_root=args.multi_missing_root,
        multi_project_root=args.multi_project_root,
        multi_projects=args.multi_projects,
        multi_tfidf_root=args.multi_tfidf_root,
    )
