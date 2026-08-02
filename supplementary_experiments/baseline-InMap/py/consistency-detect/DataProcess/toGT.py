import json
import re


def clean_string(s):
    """
    Cleans the string by removing unwanted quotation marks and leading/trailing spaces.
    """
    return s.strip().strip('"')


def parse_inmap_config_file(file_path):
    module_file_mapping = {}

    with open(file_path, 'r') as file:
        lines = file.readlines()

    inside_entity_mapping = False
    module_name = ""

    for line in lines:
        if 'EntityMapping :' in line:
            inside_entity_mapping = True
            continue

        if inside_entity_mapping:
            if 'MODULE :' in line:
                module_name = clean_string(line.split(':')[1])
                module_file_mapping[module_name] = []
            elif line.strip() and 'MODULE :' not in line:
                cleaned_line = clean_string(line)
                if cleaned_line:  # Avoid adding empty lines
                    module_file_mapping[module_name].append(cleaned_line)

    return module_file_mapping


def convert_to_json_format(module_file_mapping):
    structure = []

    for module_name, file_paths in module_file_mapping.items():
        group = {
            "@type": "group",
            "name": module_name,
            "nested": [{"@type": "item", "name": file_path} for file_path in file_paths]
        }
        structure.append(group)

    json_data = {
        "@schemaVersion": "1/0",
        "name": "clustering",
        "structure": structure
    }

    return json.dumps(json_data, indent=4)


def main():
    # Specify the path to the INMAP CONFIG FILE here
    project="teastore"
    file_path = '../'+project+'/config_'+project+'.txt'

    module_file_mapping = parse_inmap_config_file(file_path)
    json_output = convert_to_json_format(module_file_mapping)
    # Write the JSON output to a file
    output_path='../'+project+'/'+project+'_gt1.json'
    with open(output_path, 'w') as json_file:
        json_file.write(json_output)
    # Optionally, write the JSON output to a file
    # with open('output.json', 'w') as json_file:
    #     json_file.write(json_output)


# Call the main function
if __name__ == "__main__":
    main()
