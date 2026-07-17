# from similarModule import is_similar, share_common_word
import numpy as np
import re
import csv
import os
import difflib

def extract_modules(content):
    # Regular expression pattern to match module names and descriptions
    pattern = r'(?:module|Module) Name:\s*(.*?)(?:,\s*module|,\s*Module|module|Module) Description:(.*?)(?=(?:module|Module) Name:|$)'

    # Find all matches using case-insensitive and multiline matching
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    # Create a list containing module names and descriptions
    modules = [{'module name': name.strip(), 'module description': description.strip()} for name, description in matches]

    return modules


# Extract module names and descriptions from narrative text
def extract_modules_from_narrative(text):
    module_pattern = re.compile(
        r'(?P<module_name>^[A-Z][a-zA-Z\s]*(?:\s\(.*?\))?):\s*(?P<module_description>.*?)(?=\n[A-Z]|$)',
        re.MULTILINE | re.DOTALL
    )

    matches = module_pattern.finditer(text)
    modules = []

    for match in matches:
        module_name = match.group('module_name').strip()
        module_description = match.group('module_description').strip()
        modules.append({'module name': module_name, 'module description': module_description})

    return modules


# Select the appropriate extraction function according to the text format
def process_text(text):
    # Ignore capitalization when detecting the text format
    if "module name:" in text.lower() or "module description:" in text.lower():
        return extract_modules(text)
    else:
        return extract_modules_from_narrative(text)

def is_similar(name1, name2, threshold=0.7):
    # 将字符串转换为小写以进行不区分大小写的比较
    name1 = name1.lower()
    name2 = name2.lower()

    similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
    return similarity >= threshold


def share_common_word(name1, name2):
    name1 = name1.lower()
    name2 = name2.lower()
    # common_words = set(name1.split()) & set(name2.split())
    # Filter out trivial/common words if needed (e.g., 'the', 'of', 'and')
    # 使用正则表达式拆分字符串
    words1 = re.findall(r'\b\w+\b', name1)
    words2 = re.findall(r'\b\w+\b', name2)
    common_words = set(words1) & set(words2)
    trivial_words = {'the', 'of', 'and', 'in', 'on', 'at', 'for', 'with', 'to'}
    non_trivial_common_words = common_words - trivial_words
    return len(non_trivial_common_words) > 0

# Ground-truth module names for each project
module_names_by_project = {
    'teammates': ['E2E', 'Common', 'Test Driver', 'Storage', 'UI', 'Logic', 'Client', 'GAE Datastore'],
    'bigbluebutton': ['HTML5 Client', 'HTML5 Server', 'Apps', 'BBB web', 'Redis PubSub', 'Redis DB', 'FreeSWITCH', 'FSESL', 'WebRTC-SFU', 'kurento', 'Presentation Conversion'],
    'jabref': ['gui', 'model', 'logic', 'preferences', 'cli'],
    'mediastore': ['Facade', 'MediaManagement', 'UserManagement', 'UserDBAdapter', 'TagWatermarking', 'Packaging', 'Reencoding', 'DataBase', 'MediaAccess', 'FileStorage'],
    'teastore': ['Registry', 'ImageProvider', 'WebUI', 'Auth', 'Persistence', 'Recommender']
}

# projects = ['teammates', 'bigbluebutton', 'jabref', 'mediastore', 'teastore']
projects = [ 'bigbluebutton', 'jabref', 'mediastore', 'teammates','teastore']
# projects = ['jabref']

model = 'deepseek-v3'  # deepseek-v3/gpt_4o


for project in projects:

    # Retrieve the ground-truth module names for the current project
    module_names = module_names_by_project[project]

    # Number of output files to compare
    num_output_files = 20

    # Initialize lists for collecting precision, recall, and F1 scores
    precisions = []
    recalls = []
    f1_scores = []

    # Process each output file
    for i in range(1, num_output_files + 1):

        output_file_path = f'LLM_responses/{model}/{project}/output_{i}.txt'

        # Read the output file
        with open(output_file_path, 'r') as file:
            output_text = file.read()

        # Extract modules from the output file
        extracted_modules = process_text(output_text)

        # Initialize sets for module categorization
        similar_names = set()
        only_in_uml = set(module_names)
        only_in_extracted = set(module['module name'] for module in extracted_modules)

        # Match each ground-truth module name against the extracted module names
        for uml_name in module_names:
            matched = False

            # Perform exact matching first
            for extracted_module in extracted_modules:
                if matched:
                    break

                extracted_name = extracted_module['module name']

                if uml_name.strip().lower() == extracted_name.strip().lower():
                    similar_names.add((uml_name, extracted_name))
                    only_in_uml.discard(uml_name)
                    only_in_extracted.discard(extracted_name)
                    matched = True
                    break

            # Perform similarity-based matching if no exact match was found
            if not matched:
                for extracted_module in extracted_modules:
                    if matched:
                        break

                    extracted_name = extracted_module['module name']

                    if is_similar(uml_name, extracted_name) or share_common_word(uml_name, extracted_name):
                        similar_names.add((uml_name, extracted_name))
                        only_in_uml.discard(uml_name)
                        only_in_extracted.discard(extracted_name)
                        matched = True

        # Skip the current file if no module names were matched
        if len(similar_names) == 0:
            continue

        # Print the results for the current output file
        print(f"\nResults for {output_file_path}:")

        print("Similar Names:")
        for name_pair in similar_names:
            print(name_pair)

        print("\nOnly in Ground-Truth Model:")
        for name in only_in_uml:
            print(name)

        print("\nOnly in LLM Output:")
        for name in only_in_extracted:
            print(name)

        # Calculate precision, recall, and F1 score for the current file
        precision = len(similar_names) / (len(similar_names) + len(only_in_extracted)) if similar_names or only_in_extracted else 0
        recall = len(similar_names) / (len(similar_names) + len(only_in_uml)) if similar_names or only_in_uml else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print("Precision:", precision, "Recall:", recall, "F1:", f1_score)

        # Collect precision, recall, and F1 score data
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1_score)

    # Calculate the average evaluation metrics
    average_precision = np.mean(precisions) * 100
    average_recall = np.mean(recalls) * 100
    average_f1_score = np.mean(f1_scores) * 100

    # Calculate the sample standard deviations
    std_dev_precision = np.std(precisions, ddof=1) * 100
    std_dev_recall = np.std(recalls, ddof=1) * 100
    std_dev_f1_score = np.std(f1_scores, ddof=1) * 100

    print(f"Average Precision: {average_precision:.2f}%")
    print(f"Average Recall: {average_recall:.2f}%")
    print(f"Average F1 Score: {average_f1_score:.2f}%")
    print(f"Precision Standard Deviation: {std_dev_precision:.2f}%")
    print(f"Recall Standard Deviation: {std_dev_recall:.2f}%")
    print(f"F1 Score Standard Deviation: {std_dev_f1_score:.2f}%")

    # Append the project statistics to the CSV file
    csvfile_path = 'project_statistics-' + model + '.csv'
    file_exists = os.path.isfile(csvfile_path)

    with open(csvfile_path, mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                'Project',
                'Precision Mean (%)',
                'Precision Standard Deviation (%)',
                'Recall Mean (%)',
                'Recall Standard Deviation (%)',
                'F1 Score Mean (%)',
                'F1 Score Standard Deviation (%)'
            ])

        writer.writerow([
            project,
            average_precision,
            std_dev_precision,
            average_recall,
            std_dev_recall,
            average_f1_score,
            std_dev_f1_score
        ])