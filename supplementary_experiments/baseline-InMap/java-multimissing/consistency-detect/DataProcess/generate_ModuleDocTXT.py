import pandas as pd
import re
import os

def load_uml_data(uml_file_path):
    """Load UML XML data and extract names and IDs."""
    with open(uml_file_path, 'r', encoding='utf-8') as file:
        uml_data = file.read()

    elements = {}
    pattern = re.compile(
        r'<packagedElement[^>]*?xmi:type="uml:(Component|Interface)"[^>]*?xmi:id="(.*?)".*?name="(.*?)"[^>]*>',
        re.DOTALL)
    for match in pattern.findall(uml_data):
        _, element_id, element_name = match
        elements[element_id] = element_name
    return elements

# def load_valid_ids(reference_csv_path):
#     """Load valid IDs from the reference CSV file."""
#     return pd.read_csv(reference_csv_path)['ArchitectureElementId'].unique()
def load_valid_ids(reference_csv_path):
    """Load valid IDs from the reference CSV file where codeelement ends with .java."""
    df = pd.read_csv(reference_csv_path)
    # Filter rows where 'codeelement' ends with '.java'
    df = df[df['CodeElementId'].str.endswith('.java', na=False)]
    return df['ArchitectureElementId'].unique()
def map_ids_to_module_names(csv_file_path, id_to_name_map, valid_ids):
    """Map IDs in the CSV file to module names using the UML data and keep SentenceId."""
    df = pd.read_csv(csv_file_path)
    df = df[df['ArchitectureElementId'].isin(valid_ids)]  # Filter to only include valid IDs
    df['ModuleName'] = df['ArchitectureElementId'].apply(lambda x: id_to_name_map.get(x, 'Unknown Module'))
    return df[['ModuleName', 'SentenceId']]

def read_module_descriptions(description_folder):
    """Read module descriptions from text files where the filename corresponds to SentenceId."""
    descriptions = {}
    for file_name in os.listdir(description_folder):
        if file_name.endswith(".txt"):
            sentence_id = int(file_name.split('.')[0])
            with open(os.path.join(description_folder, file_name), 'r', encoding='utf-8') as file:
                descriptions[sentence_id] = ' '.join(file.read().strip().split())
    return descriptions

def aggregate_descriptions(data, descriptions):
    """Aggregate descriptions by module name, cleaning and concatenating them."""
    data['Description'] = data['SentenceId'].apply(lambda x: descriptions.get(x, ""))
    aggregated_data = data.groupby('ModuleName')['Description'].apply(lambda x: " ".join(x)).reset_index()
    return aggregated_data

def create_output_file(aggregated_data, output_path):
    """Generate an output file with module names and aggregated descriptions."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write("\tModuleNames : {\n")
        for name in aggregated_data['ModuleName']:
            file.write(f'\t\t"{name}"\n')
        file.write("\t}\n\n")
        file.write("\tModuleDescriptions : {\n")
        for _, row in aggregated_data.iterrows():
            file.write(f'\t\t"{row['Description']}"\n')
        file.write("\t}\n")

# Base paths
base_uml_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/models/uml'
base_csv_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/SAD-SAM-goldstandards'
base_description_folder = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/ftlr-texts'
base_output_directory = '/Users/liujingwen/Desktop/consistency/consistency-detect'
base_reference_csv_path = '/Users/liujingwen/Downloads/ReplicationPackageICSE24-main/data/SAM-Code-goldstandards'

# Projects to process
projects = ['teammates', 'bigbluebutton', 'jabref', 'mediastore', 'teastore']

for project in projects:
    uml_file_path = os.path.join(base_uml_path, f'{project}.uml')
    csv_file_path = os.path.join(base_csv_path, f'goldstandard-{project}.csv')
    reference_csv_path = os.path.join(base_reference_csv_path, f'goldstandard-{project}.csv')
    valid_ids = load_valid_ids(reference_csv_path)  # Load valid IDs for each project
    description_folder = os.path.join(base_description_folder, project)
    output_file_path = os.path.join(base_output_directory, project, f'updated_config_{project}.txt')

    id_to_name_map = load_uml_data(uml_file_path)  # Load the UML data to get the mapping from IDs to module names
    mapped_data = map_ids_to_module_names(csv_file_path, id_to_name_map, valid_ids)  # Convert IDs to module names
    module_descriptions = read_module_descriptions(description_folder)  # Load module descriptions
    aggregated_data = aggregate_descriptions(mapped_data, module_descriptions)  # Aggregate descriptions by module name
    create_output_file(aggregated_data, output_file_path)  # Generate the output file

    print(f"Output file for {project} has been generated successfully at {output_file_path}")
