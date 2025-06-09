from deepseek_api import read_modules_from_config, remove_license_header, call_deepseek_api, extract_probability, \
    call_deepseek_for_package_files_decision, call_deepseek_for_subpackages_decision, \
    handle_module_discrepancy
import re
import ollama
import os
import random
import json
import javalang
from typing import Dict, Any
###############################################################################
# Global dictionary for mapping file paths to their best matching module names.
###############################################################################
GLOBAL_FILE_TO_MODULE_before_FEEDBACK = {}
GLOBAL_FILE_TO_BEST_MODULE ={}
all_results = []


def read_additional_mapping(json_file):
    """
    Reads the additional file-module mappings from the provided JSON file.
    Returns a dictionary where keys are file paths and values are their mapped modules.
    The structure is nested, so the function needs to recurse through the groups and items.
    """
    try:
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



def extract_module_from_explanation(explanation):
    # Use regular expression to extract the module name from the explanation
    if explanation:
        match = re.search(r'\*\*Assigned Module\*\*: (\S+)', explanation)
        if match:
            return match.group(1)  # Return the matched module name
        else:
            return 'None'  # If no module name is found, return 'None'
    else:
        return 'None'  # If no module name is found, return 'None'


def regex_fallback(content: str) -> Dict[str, Any]:
    result = {
        "package": None,
        "classes": [{
            "class_name": "UnknownClass",
            "class_type": "class",
            "annotations": [],
            "inheritance": {"parent_class": None, "implemented_interfaces": []},
            "fields": [],
            "methods": []
        }]
    }

    # Package matching
    package_match = re.search(r'package\s+([\w.]+)\s*;', content)
    if package_match:
        result["package"] = package_match.group(1)

    # Class matching
    class_match = re.search(r'(class|interface)\s+(\w+)', content)
    if class_match:
        class_name = class_match.group(2)
        result["classes"][0]["class_name"] = class_name
        result["classes"][0]["class_type"] = class_match.group(1)

    # Inheritance matching
    extends_match = re.search(r'extends\s+([\w.<>, ]+)', content)
    if extends_match:
        result["classes"][0]["inheritance"]["parent_class"] = extends_match.group(1).strip()

    impl_match = re.search(r'implements\s+([\w.<>, ]+)', content)
    if impl_match:
        result["classes"][0]["inheritance"]["implemented_interfaces"] = [i.strip() for i in impl_match.group(1).split(',')]

    # Method matching
    method_pattern = r'^\s*(?:@\w+\s+)*(?:public|private|protected|static|final|abstract|synchronized|native|transient|volatile)\s+([\w<>[\]]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w.<>, ]+)?\s*{'
    methods = re.findall(method_pattern, content, re.MULTILINE)
    
    class_name = result["classes"][0]["class_name"]
    processed_methods = []
    for return_type, name, params in methods:
        param_types = []
        for param in params.split(','):
            param = param.strip()
            if param:
                type_part = param.split()[0] if param.split() else ''
                param_types.append(type_part)
        processed_methods.append(f"{name}({', '.join(param_types)})")

    result["classes"][0]["methods"] = processed_methods

    # Field matching
    field_pattern = r'(?:public|private|protected|static|final)\s+([\w<>]+)\s+(\w+)\s*[;=]'
    fields = re.findall(field_pattern, content)
    result["classes"][0]["fields"] = [f"{t} {n}" for t, n in fields]

    return result


def extract_java_info(content: str) -> str:
    try:
        tree = javalang.parse.parse(content)
        
        def get_inheritance(cls):
            if isinstance(cls, javalang.tree.InterfaceDeclaration):
                return {
                    "parent_interface": None,
                    "extended_interfaces": [ext.name for ext in cls.extends] if cls.extends else []
                }
            else:
                return {
                    "parent_class": cls.extends.name if cls.extends else None,
                    "implemented_interfaces": [impl.name for impl in cls.implements] if cls.implements else []
                }

        ast = {
            "package": tree.package.name if tree.package else None,
            "classes": [{
                "class_name": cls.name,
                "class_type": "interface" if isinstance(cls, javalang.tree.InterfaceDeclaration) else "class",
                "annotations": [ann.name for ann in getattr(cls, 'annotations', [])],
                "inheritance": get_inheritance(cls),
                "fields": [
                    f"{field.type.name} {declarator.name}"
                    for field in getattr(cls, 'fields', [])
                    for declarator in field.declarators
                    if 'final' not in field.modifiers
                ],
                "methods": [
                    f"{method.name}({', '.join(p.type.name for p in method.parameters)})"
                    for method in getattr(cls, 'methods', [])
                ]
            } for cls in tree.types]
        }
        return json.dumps(ast, ensure_ascii=False)

    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
        return json.dumps(regex_fallback(content), ensure_ascii=False)
        
def process_leaf_files(current_node, processed_nodes, config_file, node_to_module, json_file, project_path,output_path):
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

    file_to_best_module = {}
    for file_node in current_node.files:
        file_path = file_node.full_path
        print(f"[Step1] Processing file: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            raw_content = f.read()
        
        try:
            file_content = extract_java_info(raw_content)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}, using raw content instead.")
            file_content = raw_content

        relative_file_path = os.path.relpath(file_path, project_path)
        row_data = {"file_path": relative_file_path}
        # Find the best matching module for the file
        best_likelihood = -1.0
        best_module = None
        all_probabilities_below_50 = True  # To check if all probabilities are below 50%

        # Placeholder for TF-IDF based module (assuming you already have this part)
        tfidf_module = None
        tfidf_module_description = "No description available"
        response_text = call_deepseek_api(file_content, modules, file_path,project_path,output_path)
        if response_text:
            for module_name, module_description in modules.items():
                prob = extract_probability(module_name, response_text)
                if prob is not None:
                    prob_value = float(prob)
                else:
                    prob_value = 0.0  # 无匹配默认设为0
            
                row_data[module_name] = f"{prob_value:.2f}"  # 始终记录
            
                print(f"File: {file_path} => Module: {module_name}, Probability: {prob_value:.2f}%")
            
                if prob_value >= 50:
                    all_probabilities_below_50 = False
                if prob_value > best_likelihood:
                    best_likelihood = prob_value
                    best_module = module_name

            row_data["best_module"] = best_module if best_module else "None"
            row_data["best_likelihood"] = f"{best_likelihood:.2f}" if best_module else "0.00"
        # If all probabilities are below 50%, set the best module to "None"
        if all_probabilities_below_50:
            best_module = "None"

        
        GLOBAL_FILE_TO_MODULE_before_FEEDBACK[relative_file_path] = best_module
        all_results.append(row_data)
    # After processing, update the JSON files
    export_clustering_json(GLOBAL_FILE_TO_MODULE_before_FEEDBACK, os.path.join(output_path, "clustering_before_feedback.json"))
    
    processed_nodes.add(current_node)
    return True

def process_parent_and_children_from_leaf(leaf_files, node, processed_nodes, module_path, node_to_module, json_file, project_path,output_path):
    """
    Starts from the leaf file nodes and processes parent package nodes and their files.
    """
    current_node = node
    while current_node is not None:
        if current_node not in processed_nodes:
            flag = process_leaf_files(current_node, processed_nodes, module_path, node_to_module, json_file, project_path,output_path)
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
    except Exception as e:
        print(f"Error writing {output_json_path}: {e}")

import csv
def write_results_to_csv(results, output_path):
    if not results:
        print("No results to write.")
        return

    output_csv_path = os.path.join(output_path, "module_mapping_scores.csv")
    fieldnames = list(results[0].keys())

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"[?] All mapping results written to {output_csv_path}")


def traverse_and_process(node, module_path, json_file, project_path, output_path):
    """
    Traverses the package tree and processes each package node to determine module mappings.
    """
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
            json_file, project_path,output_path
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
    write_results_to_csv(all_results, output_path)
    
    return node_to_module
