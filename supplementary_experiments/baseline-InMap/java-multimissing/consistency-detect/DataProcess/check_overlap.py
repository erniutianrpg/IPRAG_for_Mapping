import pandas as pd
import re
import json


def load_uml_data(uml_file_path):
    """Load UML XML data and extract names and IDs."""
    with open(uml_file_path, 'r', encoding='utf-8') as file:
        uml_data = file.read()

    elements = {}
    pattern = re.compile(
        r'<packagedElement[^>]*?xmi:type="uml:(Component|Interface)"[^>]*?xmi:id="(.*?)".*?name="(.*?)"[^>]*>',
        re.DOTALL)
    for match in pattern.findall(uml_data):
        uml_type, element_id, element_name = match
        elements[element_id] = element_name
    return elements


def filter_java_files_and_replace_ids(data, id_name_map):
    """Filter out Java files and replace IDs with real names."""
    data['is_java'] = data['CodeElementId'].str.endswith('.java')
    java_data = data[data['is_java']]
    java_data['ArchitectureElementId'] = java_data['ArchitectureElementId'].apply(lambda x: id_name_map.get(x, x))
    return java_data


def check_coverage_and_similarity(data):
    """Check each pair for complete coverage or at least 80% similarity, excluding comparisons of the same name."""
    results = []
    grouped_data = data.groupby('ArchitectureElementId')['CodeElementId'].apply(set)
    keys = list(grouped_data.keys())
    for i, name1 in enumerate(keys):
        for j in range(i + 1, len(keys)):
            name2 = keys[j]
            files1 = grouped_data[name1]
            files2 = grouped_data[name2]
            if files1.issubset(files2):
                results.append((name1, name2, f'{name1} is completely covered by {name2}'))
            elif files2.issubset(files1):
                results.append((name1, name2, f'{name2} is completely covered by {name1}'))
            else:
                intersection = files1.intersection(files2)
                smaller_set_size = min(len(files1), len(files2))
                similarity_ratio = len(intersection) / smaller_set_size if smaller_set_size > 0 else 0
                if similarity_ratio >= 0.8:
                    results.append((name1, name2, 'At Least 80% Similar'))
    return results


# Define paths
uml_file_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/models/uml/mediastore.uml'
csv_file_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/SAM-Code-goldstandards/goldstandard-mediastore.csv'

# Load and process data
uml_data = load_uml_data(uml_file_path)
data = pd.read_csv(csv_file_path)
id_name_map = load_uml_data(uml_file_path)
java_data = filter_java_files_and_replace_ids(data, id_name_map)

# Perform the checks
results = check_coverage_and_similarity(java_data)

# Print the results
for result in results:
    id1, id2, status = result
    print(f"{id1} and {id2}: {status}")
