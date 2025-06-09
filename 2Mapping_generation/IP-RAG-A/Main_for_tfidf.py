import argparse
import os
import random
import subprocess
import sys

MAPPING_PATH = 'Mapping-jar-with-dependencies.jar'
MAPPING_FEWSHOT_PATH = 'few-shot_mapping.jar'
MAPPING_None_PATH = 'tfidf_score.jar'
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
        project_name, project_folder, module_info_file, method, str(threshold), output_directory
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
        project_name, project_folder, module_info_file, method, str(threshold), output_directory
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
        project_name, project_folder, module_info_file, method, str(threshold), output_directory
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to execute JAR file:", e)
        return None

def execute_package_tree(project_path, module_info_file,output_directory):
    """Execute package_tree.py using nohup, redirect output to a log file."""
    project = os.path.basename(project_path)
    command = 'nohup python -u package_tree.py ' \
              f'{project_path} --exclude test build out ' \
              f'--module_path "{module_info_file}" ' \
              f'--tfidf_result_path "{output_directory}/file-module_mapping-tfidf.json" ' \
              f'--output_path "{output_directory}" ' \
              f'> "{output_directory}/call_deepseek.log" 2>&1'
    
    # Start the command asynchronously using Popen
    process = subprocess.Popen(command, shell=True)

    # Wait for the process to finish before continuing (if you want to wait for it)
    process.wait()


def delete_and_update_module(module_info, module_info_file, datapath, gt_path):
    """Delete modules one by one and update the module info file."""
    module_names = list(module_info.keys())  # Convert module names to a list and delete in order
    gt_groups = extract_group_names(gt_path)  # may be None
    project=os.path.basename(datapath)
    for module_to_remove in module_names:
        if gt_groups is not None and module_to_remove not in gt_groups:
            print(f"[Skip] '{module_to_remove}' not exsit in Ground Truth group, continue")
            continue    
        output_directory = os.path.join(project, f"removed_{module_to_remove}")
        if os.path.exists(output_directory):
            print(f"[Skip] '{output_directory}' exsit")
            continue
            
        # Delete a module
        updated_module_info = module_info.copy()
        print(f"Deleting module: {module_to_remove}")

        del updated_module_info[module_to_remove]

        
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

        # Run JAR file to process the new module info
        generate_and_load_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 50, output_directory)
        generate_and_load_fewshot_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 0, output_directory)
        generate_and_load_none_mappings(os.path.basename(datapath), datapath, new_module_info_file, 'tfidf', 50, output_directory)

        # Execute package_tree.py
        execute_package_tree(datapath, new_module_info_file,output_directory)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gradually delete architecture modules and generate mappings.')
    parser.add_argument('datapath', type=str, help='Path to the project folder')
    parser.add_argument('-m', '--module_info', type=str, required=True, help='Path to the module info file')
    parser.add_argument('-a', '--mapping', type=str, default='tfidf', help='Mapping method')
    parser.add_argument('-t', '--threshold', type=float, default=50, help='Mapping threshold')
    parser.add_argument('-g', '--gt', type=str, help='Ground Truth Path')

    args = parser.parse_args()

    # Parse the original module info
    module_info = parse_module_info(args.module_info)

    # Perform the gradual module deletion
    delete_and_update_module(module_info, args.module_info, args.datapath, args.gt)
