import argparse
import json
import os
import subprocess

MAPPING_PATH = 'tfidf_score.jar'


def normalize_language(language):
    normalized = (language or 'cpp').strip().lower()
    if normalized in ('py', 'python'):
        return 'python'
    if normalized in ('c', 'cc', 'cpp', 'cxx', 'c++'):
        return 'cpp'
    return 'java'


def parse_module_info(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    module_names_start = file_content.find("ModuleNames : {") + len("ModuleNames : {")
    module_names_end = file_content.find("}", module_names_start)
    module_descriptions_start = file_content.find("ModuleDescriptions : {") + len("ModuleDescriptions : {")
    module_descriptions_end = file_content.find("}", module_descriptions_start)

    module_names_raw = file_content[module_names_start:module_names_end].strip()
    module_descriptions_raw = file_content[module_descriptions_start:module_descriptions_end].strip()

    module_names = [name.strip('"\n\t ') for name in module_names_raw.splitlines() if name.strip()]
    module_descriptions = [desc.strip('"\n\t ') for desc in module_descriptions_raw.splitlines() if desc.strip()]

    if len(module_names) != len(module_descriptions):
        raise ValueError("Module names and descriptions count mismatch.")

    return dict(zip(module_names, module_descriptions))


def extract_group_names(json_path):
    if not json_path:
        return None
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    structure = data.get("structure", [])
    return [entry.get("name") for entry in structure if entry.get("@type") == "group"]


def generate_tfidf_scores(project_name, project_folder, module_info_file, threshold, output_directory, language):
    project_parent, _ = os.path.split(project_folder)
    command = [
        'java', '-jar', MAPPING_PATH,
        project_name, project_parent, module_info_file, 'tfidf', str(threshold), output_directory, language
    ]
    subprocess.run(command, check=True)


def write_module_info(module_info, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("ModuleNames : {\n")
        for module in module_info.keys():
            file.write(f'    "{module}"\n')
        file.write("}\n\nModuleDescriptions : {\n")
        for desc in module_info.values():
            file.write(f'    "{desc}"\n')
        file.write("}\n")


def run_hadoop_tfidf(module_info, datapath, threshold, language):
    project = os.path.basename(datapath)
    module_to_remove = "YARN"
    output_directory = os.path.join(project, f"removed_{module_to_remove}")
    os.makedirs(output_directory, exist_ok=True)

    new_module_info_file = os.path.join(output_directory, 'updated_module_info.txt')
    write_module_info(module_info, new_module_info_file)
    print(f"New module info file generated: {new_module_info_file}")

    generate_tfidf_scores(project, datapath, new_module_info_file, threshold, output_directory, language)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Hadoop TF-IDF scores.')
    parser.add_argument('datapath', type=str, help='Path to the project folder')
    parser.add_argument('-m', '--module_info', type=str, required=True, help='Path to the module info file')
    parser.add_argument('-t', '--threshold', type=float, default=50, help='TF-IDF score threshold')
    parser.add_argument('-g', '--gt', type=str, help='Unused; kept for command compatibility')
    parser.add_argument('-l', '--lang', type=str, default='cpp',
                        choices=['java', 'python', 'py', 'c', 'cc', 'cpp', 'cxx', 'c++'],
                        help='Source language for TF-IDF preprocessing')

    args = parser.parse_args()
    language = normalize_language(args.lang)
    module_info = parse_module_info(args.module_info)
    run_hadoop_tfidf(module_info, args.datapath, args.threshold, language)
