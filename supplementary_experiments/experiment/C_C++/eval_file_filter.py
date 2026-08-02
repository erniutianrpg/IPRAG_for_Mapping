import json
import os
import re


def normalize_relpath(path):
    return path.replace("\\", "/").strip()


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
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
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


def build_eval_file_list(gt_path, modules, removed_module, distance_threshold=2):
    if not gt_path or not os.path.exists(gt_path):
        return []

    with open(gt_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    gt_groups = {
        group.get("name", "").strip()
        for group in data.get("structure", [])
        if group.get("name", "").strip()
    }
    excluded_groups = close_gt_groups(removed_module, gt_groups, threshold=1)

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
            normalized = normalize_relpath(item_name)
            if normalized not in seen:
                files.append(normalized)
                seen.add(normalized)

    return files


def write_eval_file_list(gt_path, modules, removed_module, output_directory):
    files = build_eval_file_list(gt_path, modules, removed_module)
    if not files:
        return None

    output_path = os.path.join(output_directory, "eval_files.txt")
    with open(output_path, "w", encoding="utf-8") as handle:
        for file_path in files:
            handle.write(file_path + "\n")
    print(f"[EvalFilter] Wrote {len(files)} files to {output_path}")
    return output_path


def load_eval_file_set(eval_files_path):
    if not eval_files_path or not os.path.exists(eval_files_path):
        return None

    with open(eval_files_path, "r", encoding="utf-8") as handle:
        files = {
            normalize_relpath(line)
            for line in handle
            if line.strip()
        }
    return files or None
