from deepseek_api import read_modules_from_config, remove_license_header, call_deepseek_api, extract_probability, \
    call_deepseek_for_package_files_decision, call_deepseek_for_subpackages_decision, \
    handle_module_discrepancy
import re
import os
import sys
import random
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from parallel_llm import get_llm_workers
from python_code_info import extract_source_info as summarize_source_info
###############################################################################
# Global dictionary for mapping file paths to their best matching module names.
###############################################################################
GLOBAL_FILE_TO_MODULE_before_FEEDBACK = {}
GLOBAL_FILE_TO_BEST_MODULE ={}

def read_additional_mapping(json_file):
    """
    Reads the additional file-module mappings from the provided JSON file.
    Returns a dictionary where keys are file paths and values are their mapped modules.
    The structure is nested, so the function needs to recurse through the groups and items.
    """
    try:
        if json_file and json_file.lower().endswith(".csv"):
            additional_mappings = {}
            with open(json_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    file_path = row.get("file_path")
                    best_module = row.get("best_module")
                    if file_path and best_module:
                        additional_mappings[file_path] = best_module
            return additional_mappings

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Dictionary to store the mapping: file_path -> module_name
        additional_mappings = {}

        # Iterate through the structure to extract file paths and their corresponding module names
        for group in data.get('structure', []):
            group_name = group.get('name', 'Unknown')  # Assuming the group name is the module name

            # Process all nested items under the group
            for item in group.get('nested', []):
                file_path = item.get('name')
                if file_path:
                    additional_mappings[file_path] = group_name  # Map file_path to module name

        return additional_mappings

    except Exception as e:
        print(f"Error reading {json_file}: {e}")
        return {}

def extract_assigned_module(response_content): 
    try:
        # Split the response content into lines
        lines = response_content.strip().split('\n')
        
        # Start from the last line and work backwards
        for line in reversed(lines):
            match = re.search(
                r'(?i)\bAssigned Module\b.*?:\s*([^\n]+)', 
                line
            )
            
            if match:
                raw_module = match.group(1).strip()
                cleaned_module = re.sub(r'[^a-zA-Z0-9_\- ]', '', raw_module)
                
                if cleaned_module and cleaned_module.lower() != 'none':
                    return cleaned_module
                else:
                    return None
        
        print("No 'Assigned Module' keyword detected, returning None")
        return None
            
    except Exception as e:
        print(f"Error parsing module name: {e}")
        return None



def extract_source_info(content, file_path=None):
    return summarize_source_info(content, file_path)


def process_file_assignment(file_node, modules, project_path, output_path, few_shot_prompt):
    file_path = file_node.full_path
    print(f"[Step1] Processing file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    try:
        file_content = extract_source_info(raw_content, file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}, using raw content instead.")
        file_content = raw_content

    response_text = call_deepseek_api(
        file_content=file_content,
        modules=modules,
        file_path=file_path,
        output_path=output_path,
        project_path=project_path,
        few_shot_prompt=few_shot_prompt
    )

    if response_text:
        assigned_module = str(extract_assigned_module(response_text))
    else:
        assigned_module = "None"

    print(f"File: {file_path} => Assigned Module: {assigned_module}")
    relative_file_path = os.path.relpath(file_path, project_path)
    return relative_file_path, assigned_module


def process_leaf_files(current_node, processed_nodes, config_file, node_to_module, json_file, project_path,output_path,few_shot_prompt):
    """
    Processes all files in the current package node to determine module assignments using DeepSeek.
    This function has been updated to compare the best module with an additional mapping from a JSON file.
    """

    # Read additional mappings from the provided JSON file
    additional_mappings = read_additional_mapping(json_file)

    # If there are any unprocessed children, we skip this node
    if any(child not in processed_nodes for child in current_node.children.values()):
        return None

    modules = read_modules_from_config(config_file)
    all_module_names = list(modules.keys())

    package_full_name = current_node.get_full_package_name()

    workers = min(get_llm_workers(), len(current_node.files)) if current_node.files else 1
    print(f"[Parallel] Processing {len(current_node.files)} files with {workers} workers.")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                process_file_assignment,
                file_node,
                modules,
                project_path,
                output_path,
                few_shot_prompt
            )
            for file_node in current_node.files
        ]
        for future in as_completed(futures):
            try:
                relative_file_path, assigned_module = future.result()
                GLOBAL_FILE_TO_MODULE_before_FEEDBACK[relative_file_path] = assigned_module
            except Exception as e:
                print(f"Error processing file in parallel: {e}")
                raise

    export_clustering_json(GLOBAL_FILE_TO_MODULE_before_FEEDBACK, os.path.join(output_path, "clustering_before_feedback.json"))

    processed_nodes.add(current_node)
    return True

def process_parent_and_children_from_leaf(leaf_files, node, processed_nodes, module_path, node_to_module, json_file, project_path,output_path, few_shot_prompt):
    """
    Starts from the leaf file nodes and processes parent package nodes and their files.
    """
    current_node = node
    while current_node is not None:
        if current_node not in processed_nodes:
            flag = process_leaf_files(current_node, processed_nodes, module_path, node_to_module, json_file, project_path,output_path,few_shot_prompt)
            if not flag:
                return
        current_node = current_node.parent


def find_leaf_files(node):
    """
    Finds all leaf file nodes under the current package node.
    """
    leaf_files = []

    def recurse(current_node):
        if not current_node.children and current_node.files:
            leaf_files.extend(current_node.files)
        for child in current_node.children.values():
            recurse(child)

    recurse(node)
    return leaf_files


###############################################################################
# Function to export the clustering JSON
###############################################################################
def export_clustering_json(file_to_module_map, output_json_path="clustering.json"):
    """
    Exports the mapping of files to their best matching modules into a clustering JSON format.
    """
    module_to_files = {}
    for file_path, mod in file_to_module_map.items():
        module_to_files.setdefault(mod, []).append(file_path)

    structure_list = []
    for mod, files in module_to_files.items():
        group_obj = {
            "@type": "group",
            "name": mod,
            "nested": []
        }
        for fpath in files:
            group_obj["nested"].append({
                "@type": "item",
                "name": fpath
            })
        structure_list.append(group_obj)

    clustering_obj = {
        "@schemaVersion": "1/0",
        "name": "clustering",
        "structure": structure_list
    }

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(clustering_obj, f, ensure_ascii=False, indent=4)
        print(f"[export_clustering_json] Generated file: {output_json_path}")
    except Exception as e:
        print(f"Error writing {output_json_path}: {e}")


from fewshot_generation import build_few_shot_prompt

def traverse_and_process(node, module_path, json_file, project_path, output_path):
    """
    Traverses the package tree and processes each package node to determine module mappings.
    """
    modules = read_modules_from_config(module_path)
    few_shot_prompt = build_few_shot_prompt(output_path, modules, project_path)
    processed_nodes = set()
    node_to_module = {}

    leaf_files = find_leaf_files(node)

    for leaf_file in leaf_files:
        parent_node = leaf_file.parent
        process_parent_and_children_from_leaf(
            leaf_files,
            parent_node,
            processed_nodes,
            module_path,
            node_to_module,
            json_file, project_path,output_path,few_shot_prompt
        )

    output_json_path = os.path.join(output_path, "file_to_best_module.json")
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(GLOBAL_FILE_TO_BEST_MODULE, f, ensure_ascii=False, indent=4)
        print(f"[traverse_and_process] file_to_best_module.json saved to {output_json_path}")
    except Exception as e:
        print(f"Error writing file_to_best_module.json: {e}")

    export_clustering_json(GLOBAL_FILE_TO_MODULE_before_FEEDBACK, os.path.join(output_path, "clustering_before_feedback.json"))
    export_clustering_json(GLOBAL_FILE_TO_BEST_MODULE, os.path.join(output_path, "clustering_after_feedback.json"))
    
    return node_to_module
