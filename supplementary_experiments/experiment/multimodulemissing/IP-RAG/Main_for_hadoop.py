import argparse
import os
import random
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from path_config import resolve_source_root
from eval_file_filter import write_eval_file_list

MAPPING_PATH = os.path.join(SCRIPT_DIR, 'Mapping-jar-with-dependencies.jar')
MAPPING_FEWSHOT_PATH = os.path.join(SCRIPT_DIR, 'few-shot_mapping.jar')
MAPPING_None_PATH = os.path.join(SCRIPT_DIR, 'tfidf_score.jar')
PACKAGE_TREE_PATH = os.path.join(SCRIPT_DIR, 'package_tree.py')


def jar_arg_path(path):
    return os.path.abspath(path).replace(os.sep, '/')
def parse_module_info(file_path):
    """Parse module info and return a dictionary of module names and descriptions."""
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    module_names_start = file_content.find("ModuleNames : {") + len("ModuleNames : {")
    module_names_end = file_content.find("}", module_names_start)
    module_descriptions_start = file_content.find("ModuleDescriptions : {") + len("ModuleDescriptions : {")
    module_descriptions_end = file_content.find("}", module_descriptions_start)

    module_names_raw = file_content[module_names_start:module_names_end].strip()
    module_descriptions_raw = file_content[module_descriptions_start:module_descriptions_end].strip()

    module_names = [name.strip('"\n\t') for name in module_names_raw.splitlines() if name.strip()]
    module_descriptions = [desc.strip('"\n\t') for desc in module_descriptions_raw.splitlines() if desc.strip()]

    if len(module_names) != len(module_descriptions):
        raise ValueError("Module names and descriptions count mismatch.")

    return dict(zip(module_names, module_descriptions))

import json

def extract_group_names(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    structure = data.get("structure", [])
    group_names = [entry.get("name") for entry in structure if entry.get("@type") == "group"]
    return group_names


def generate_and_load_mappings(project_name, project_folder, module_info_file, method, threshold, output_directory):
    """Run JAR file to generate module mappings and load the JSON result."""
    project_folder, prj_name1 = os.path.split(project_folder)
    command = [
        'java', '-jar', MAPPING_PATH,
        project_name, jar_arg_path(project_folder), jar_arg_path(module_info_file),
        method, str(threshold), jar_arg_path(output_directory)
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to execute JAR file:", e)
        return None

def generate_and_load_fewshot_mappings(project_name, project_folder, module_info_file, method, threshold, output_directory):
    """Run JAR file to generate module mappings and load the JSON result."""
    project_folder, prj_name1 = os.path.split(project_folder)
    command = [
        'java', '-jar', MAPPING_FEWSHOT_PATH,
        project_name, jar_arg_path(project_folder), jar_arg_path(module_info_file),
        method, str(threshold), jar_arg_path(output_directory)
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to execute JAR file:", e)
        return None

def generate_and_load_none_mappings(project_name, project_folder, module_info_file, method, threshold, output_directory):
    """Run JAR file to generate module mappings and load the JSON result."""
    project_folder, prj_name1 = os.path.split(project_folder)
    command = [
        'java', '-jar', MAPPING_None_PATH,
        project_name, jar_arg_path(project_folder), jar_arg_path(module_info_file),
        method, str(threshold), jar_arg_path(output_directory)
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to execute JAR file:", e)
        return None

def execute_package_tree(project_path, module_info_file, output_directory, eval_files_path=None):
    """Execute package_tree.py and redirect output to a log file."""
    command = [
        sys.executable, '-u', PACKAGE_TREE_PATH,
        project_path,
        '--exclude', 'test', 'build', 'out',
        '--module_path', module_info_file,
        '--tfidf_result_path', os.path.join(output_directory, 'file-module_mapping-tfidf.json'),
        '--output_path', output_directory,
    ]
    if eval_files_path:
        command.extend(['--eval_files', eval_files_path])
    with open(os.path.join(output_directory, 'call_deepseek.log'), 'w', encoding='utf-8') as log_file:
        subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT, check=True)


def delete_and_update_module(module_info, module_info_file, datapath, gt_path):
    """Delete modules one by one and update the module info file."""
    project=os.path.basename(datapath)
    module_to_remove = "YARN"
    output_directory = os.path.join(project, f"removed_{module_to_remove}")
    # Delete a module
    updated_module_info = module_info.copy()
    os.makedirs(output_directory, exist_ok=True)  
    
    # Generate a new module info file
    new_module_info_file = os.path.join(output_directory, 'updated_module_info.txt')
    with open(new_module_info_file, 'w', encoding='utf-8') as file:
        file.write("ModuleNames : {\n")
        for module in updated_module_info.keys():
            file.write(f'    "{module}"\n')
        file.write("}\n\nModuleDescriptions : {\n")
        for desc in updated_module_info.values():
            file.write(f'    "{desc}"\n')
        file.write("}\n")

    print(f"New module info file generated: {new_module_info_file}")
    eval_files_path = write_eval_file_list(gt_path, list(module_info.keys()), module_to_remove, output_directory)

    # Run JAR file to process the new module info
    generate_and_load_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 50, output_directory)
    generate_and_load_fewshot_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 50, output_directory)
    generate_and_load_none_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 50, output_directory)

    # Execute package_tree.py
    execute_package_tree(datapath, new_module_info_file, output_directory, eval_files_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gradually delete architecture modules and generate mappings.')
    parser.add_argument('datapath', type=str, help='Path to the project folder')
    parser.add_argument('-m', '--module_info', type=str, required=True, help='Path to the module info file')
    parser.add_argument('-a', '--mapping', type=str, default='tfidf', help='Mapping method')
    parser.add_argument('-t', '--threshold', type=float, default=50, help='Mapping threshold')
    parser.add_argument('-g', '--gt', type=str, help='Ground Truth Path')

    args = parser.parse_args()

    # Parse the original module info
    datapath = resolve_source_root(args.datapath)
    if os.path.abspath(args.datapath) != datapath:
        print(f"[Path] Resolved source root: {datapath}")

    module_info = parse_module_info(args.module_info)

    # Perform the gradual module deletion
    delete_and_update_module(module_info, args.module_info, datapath, args.gt)
