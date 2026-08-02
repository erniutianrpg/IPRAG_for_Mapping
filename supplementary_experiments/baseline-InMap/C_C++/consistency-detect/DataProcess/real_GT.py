import pandas as pd
import json
import re
import os

def generate_json_from_uml_and_csv(uml_file_path, csv_file_path, output_json_path):
    # Load the CSV file
    df = pd.read_csv(csv_file_path)

    # Filter to include only .java files
    df = df[df['CodeElementId'].str.endswith('.java')]

    # Read UML XML file as plain text
    with open(uml_file_path, 'r', encoding='utf-8') as file:
        uml_data = file.read()

    # Extract component and interface names with their IDs from the UML plain text
    elements = {}

    # Function to extract elements
    def extract_elements(tag):
        pattern = re.compile(rf'<packagedElement.*?xmi:type="uml:{tag}".*?xmi:id="(.*?)".*?name="(.*?)".*?>', re.DOTALL)
        matches = pattern.findall(uml_data)
        for match in matches:
            element_id, element_name = match
            if element_name not in elements:
                elements[element_name] = []
            elements[element_name].append(element_id)

    extract_elements("Component")
    extract_elements("Interface")

    # Prepare the JSON structure
    json_structure = {
        "@schemaVersion": "1/0",
        "name": "clustering",
        "structure": []
    }

    # Group files by the component and interface names
    grouped_files = {}
    for index, row in df.iterrows():
        element_id = row['ArchitectureElementId']
        file_name = row['CodeElementId']
        for name, ids in elements.items():
            if element_id in ids:
                if name not in grouped_files:
                    grouped_files[name] = []
                grouped_files[name].append(file_name)

    # Populate the JSON structure with groups and items
    for group_name, files in grouped_files.items():
        group = {
            "@type": "group",
            "name": group_name,
            "nested": []
        }
        for file in files:
            item = {
                "@type": "item",
                "name": file
            }
            group["nested"].append(item)
        json_structure["structure"].append(group)

    # Output the JSON structure to a file
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_structure, json_file, indent=4, ensure_ascii=False)


# Base paths
base_uml_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/models/uml'
base_csv_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/SAM-Code-goldstandards'
base_output_directory = '/Users/liujingwen/Desktop/consistency/consistency-detect'

# Projects to process
projects = ['teammates', 'bigbluebutton', 'jabref', 'mediastore', 'teastore']

for project in projects:
    uml_file_path = os.path.join(base_uml_path, f'{project}.uml')
    csv_file_path = os.path.join(base_csv_path, f'goldstandard-{project}.csv')
    output_json_path = os.path.join(base_output_directory,  f'updated_{project}_gt.json')

    # Process each project and generate JSON output
    generate_json_from_uml_and_csv(uml_file_path, csv_file_path, output_json_path)
