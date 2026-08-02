import json

# Assuming 'hadoop.rfx.json' is the file containing the original structure
file_path = '/Users/liujingwen/Desktop/3Erefactor/3Erefactor/architectureModel/hadoop/hadoop.rfx.json'


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def transform_structure(original):
    def transform_nested(nested):
        transformed = []
        for item in nested:
            if 'nested' in item:  # It's a group
                transformed.append({
                    "@type": "group",
                    "name": item['name'],
                    "nested": transform_nested(item['nested'])
                })
            else:  # It's an item
                transformed.append({
                    "@type": "item",
                    "name": item['rawName']
                })
        return transformed

    # Main transformation
    transformed_structure = {
        "@schemaVersion": "1/0",
        "name": original['structure'][0]['name'],  # Using the name from the original structure
        "structure": transform_nested(original['structure'][0]['nested'])
        # Assuming the top-level structure is the first item
    }

    return transformed_structure


# Read the original structure from file
original_structure = read_json_file(file_path)

# Transform the structure
transformed_structure = transform_structure(original_structure)

# To save the transformed structure back to a file
with open('transformed_hadoop.json', 'w') as outfile:
    json.dump(transformed_structure, outfile, indent=4)

print("Transformation completed and saved to 'transformed_hadoop.json'.")
