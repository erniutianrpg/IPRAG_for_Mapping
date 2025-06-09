import re
import ollama
import os
import random
import json
from openai import OpenAI
import httpx

def read_modules_from_config(config_file):
    """
    Reads the example configuration of modules.
    Returns a dictionary where keys are module names and
    values are their corresponding descriptions.
    """
    modules = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            content = file.read()

            module_names_match = re.search(r'ModuleNames\s*:\s*\{(.*?)\}', content, re.DOTALL)
            module_descriptions_match = re.search(r'ModuleDescriptions\s*:\s*\{(.*?)\}', content, re.DOTALL)

            if module_names_match and module_descriptions_match:
                module_names = [
                    name.strip().strip('"')
                    for name in module_names_match.group(1).splitlines() if name.strip()
                ]
                module_descriptions = [
                    desc.strip().strip('"')
                    for desc in module_descriptions_match.group(1).splitlines() if desc.strip()
                ]

                for i in range(len(module_names)):
                    modules[module_names[i]] = (
                        module_descriptions[i] if i < len(module_descriptions) else "No description available"
                    )
    except Exception as e:
        print(f"Error reading module data: {e}")
    return modules


def remove_license_header(file_content):
    """
    Removes the license comment at the beginning of the file content.
    """
    license_pattern = re.compile(r'(?s)^\s*/\*.*?\*/')
    cleaned_content = re.sub(license_pattern, '', file_content)
    return cleaned_content

import os
import re
def call_deepseek_api(file_content, modules, file_path, output_path, project_path,few_shot_prompt):
    """
    Example function to call the DeepSeek model (via Ollama) with a given prompt.
    Returns the module assigned or 'None' if no module is assigned.
    """
    # 3.2 Build Few?Shot prompt
    relative_file_path = os.path.relpath(file_path, project_path)
    # Build the prompt with all module names and descriptions
    modules_description = "\n".join([
        f"{module_name}: {module_description}" 
        for module_name, module_description in modules.items()
    ])

    # Use the exact original prompt
    prompt = f"""
    You are an expert at mapping code files to architecture modules. Analyze the given file's content and package, and compare it with the listed candidate modules. Use the listed reference examples below to guide your reasoning and help determine the most appropriate module.
    Reason step by step based on these comparisons. If the file does not clearly belong to any module, respond with '**Assigned Module**: ['None']'.
    
    File path:
    {relative_file_path}
    File content:
    {file_content}    
    
    Candidate Modules:
    {modules_description}
    
    Reference Examples:
    {few_shot_prompt}

    Expected response format:
    - **Assigned Module**: [Module Name or 'None']
    Ensure that your analysis is precise, logically reasoned, and clearly justified.
    """

    print(prompt)
    try:
        # Initialize the OpenAI client with the SiliconFlow base URL
        client = OpenAI(
            base_url='https://api.siliconflow.cn/v1',
            api_key='your_api_key'
        )

        # Send the request with streaming enabled
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        # Collect streamed response content
        response_content = ""
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                response_content += delta.content
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                response_content += delta.reasoning_content

        # Prepare directory for saving model responses
        fixed_response_dir = os.path.join(output_path, 'deepseek_response_forFile')
        os.makedirs(fixed_response_dir, exist_ok=True)
        file_name = os.path.basename(file_path)
        response_file_path = os.path.join(fixed_response_dir, f"{file_name}_response.txt")

        # Write the complete response to a file
        with open(response_file_path, 'w', encoding='utf-8') as f:
            f.write(response_content)

        return response_content

    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return None


def extract_probability(response_text):
    """
    Extracts the probability number from the model's response text.
    The function looks for a pattern like "85%" or "85.5%".
    """
    match = re.search(r'(\d{1,3}(?:\.\d+)?)\s*%', response_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def summarize_files_best_modules(file_to_best_module):
    """
    Summarizes the mapping of files to their most likely modules in a textual format.
    """
    lines = []
    for file_path, mod in file_to_best_module.items():
        lines.append(f"- File: {file_path}, Most likely module: {mod}")
    return "\n".join(lines)


def generate_example_choices(all_modules):
    """
    Based on the all_modules list, generates example choices.
    """
    examples = []
    # 1) Always have ["None"]
    examples.append('["None"]')

    # 2) If there's at least one module, show the first module
    if len(all_modules) >= 1:
        examples.append(f'["{all_modules[0]}"]')

    # 3) If there are at least two modules, show the first two
    if len(all_modules) >= 2:
        examples.append(f'["{all_modules[0]}", "{all_modules[1]}"]')

    if len(examples) == 1:
        return examples[0]
    else:
        return ', '.join(examples[:-1]) + f', or {examples[-1]}'


def extract_module_array(response_text):
    """
    Extracts a module array like ["Foo", "Bar"], ["Foo"], or ["None"] from the response text.
    """
    pattern = r'(\[[^\]]*\])$'

    lines = response_text.strip().split('\n')
    for line in reversed(lines):
        line = line.strip()
        match = re.search(pattern, line)
        if match:
            array_str = match.group(1)
            try:
                modules = json.loads(array_str)
                if isinstance(modules, list):
                    return modules
            except json.JSONDecodeError:
                pass

    return None


def call_deepseek_for_package_files_decision(package_name, file_to_best_module, all_modules):
    """
    Uses the DeepSeek model to determine which module(s) the entire package might belong to.
    """
    summary_text = summarize_files_best_modules(file_to_best_module)
    possible_choices = all_modules + ["None"]

    example_str = generate_example_choices(all_modules)

    prompt = f"""
    We have a package named "{package_name}" containing the following files and their most likely module assignments:
    {summary_text}

    Below is the list of possible modules (plus "None"):
    {possible_choices}

    Please choose **one or more** modules for the entire package from the above list. 
    If you think no existing module fits, return ["None"].

    **Important**: 
    - Return your final decision in a short JSON array. 
    - No additional text or explanation. 
    - Only use the items from the possible choices.

    For example: {example_str}.
    """

    try:
        response = ollama.chat(
            model="deepseek-r1:70b",
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw_text = response['message']['content'].strip()

        modules_list = extract_module_array(raw_text)
        if modules_list is None:
            print("[Warning] Could not parse valid module array from response. Full response:")
            print(raw_text)
            return raw_text
        else:
            return modules_list
    except Exception as e:
        print(f"Error calling DeepSeek for package_files_decision: {e}")
        return None

def call_deepseek_for_subpackages_decision(package_name, subpackage_to_modules, all_modules):
    """
    Uses the DeepSeek model to decide which module(s) a package belongs to, based on
    the possible modules of its subpackages. Also restricted to the same possible choices.
    """
    lines = []
    for subpkg, mods in subpackage_to_modules.items():
        lines.append(f"- Subpackage: {subpkg}, possible modules: {mods}")
    summary_text = "\n".join(lines)
    # Possible choices are the modules plus ["None"]
    possible_choices = all_modules + ["None"]

    # Generate example choices
    example_str = generate_example_choices(all_modules)

    prompt = f"""
    We have a package named "{package_name}" that contains the following subpackages and their possible modules:
    {summary_text}

    Below is the list of possible modules (plus "None"):
    {possible_choices}

    Please decide which module(s) this package as a whole might belong to, from the above list.
    If you think this package does not belong to any existing modules, just return ["None"].

    **Important**: 
    - Return your final decision in a short JSON array. 
    - No additional text or explanation. 
    - Only use the items from the possible choices.

    For example: {example_str}.
    """

    try:
        response = ollama.chat(
            model="deepseek-r1:70b",
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw_text = response['message']['content'].strip()

        # Try to parse the response as a valid JSON array
        modules_list = extract_module_array(raw_text)
        if modules_list is None:
            print("[Warning] Could not parse valid module array from response. Full response:")
            print(raw_text)
            return raw_text
        else:
            return modules_list  # e.g., ["MapReduce"]
    except Exception as e:
        print(f"Error calling DeepSeek for package_files_decision: {e}")
        return None

def call_deepseek_for_module_comparison(
    file_content,
    tfidf_module,
    deepseek_module,
    tfidf_module_description,
    deepseek_module_description,
    file_path,
    project_path,
    output_path
):
    """
    Calls the DeepSeek model to compare two different module matches for the same file.
    Asks the model to provide a detailed explanation on which module is more accurate.
    One module is derived from TF-IDF similarity, the other from DeepSeek code analysis.
    """

    prompt = f"""
    File name: {file_path}
    Content in file: {file_content}

    We have two different methods of tracing which architecture module this file belongs to:

    1. **TF-IDF Method**: Assigned to **{tfidf_module}** based on the highest semantic similarity to the module description: {tfidf_module_description}

    2. **DeepSeek Method**: Assigned to **{deepseek_module}** based on direct analysis of the code: {deepseek_module_description}

    **Task**:
    Analyze the file content and decide which module it belongs to. Explain why one method is more accurate than the other, or if neither method applies, return 'None'.

    Expected response format:
    - **Assigned Module**: [Module Name or 'None']
    """

    try:
        # Initialize the OpenAI client via SiliconFlow
        client = OpenAI(
            base_url='https://api.siliconflow.cn/v1',
            api_key='your_api_key'
        )

        # Call the model with streaming response
        response = client.chat.completions.create(
            model="Pro/deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        # Collect streamed response content
        response_content = ""
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                response_content += delta.content
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                response_content += delta.reasoning_content

        # Prepare output directory
        fixed_response_dir = os.path.join(output_path, 'deepseek_response_forComparison')
        os.makedirs(fixed_response_dir, exist_ok=True)

        # Sanitize module names for safe filenames
        sanitized_module_name_1 = re.sub(r'[<>:"/\\|?*]', '_', tfidf_module)
        sanitized_module_name_2 = re.sub(r'[<>:"/\\|?*]', '_', deepseek_module)
        file_name = os.path.basename(file_path)
        response_file_name = f"{sanitized_module_name_1}_{sanitized_module_name_2}_{file_name}_response.txt"
        response_file_path = os.path.join(fixed_response_dir, response_file_name)

        # Save response to file
        with open(response_file_path, 'w', encoding='utf-8') as response_file:
            response_file.write(response_content)

        return response_content

    except Exception as e:
        print(f"Error calling DeepSeek API for module comparison: {e}")
        return None

def handle_module_discrepancy(file_content, file_path, tfidf_module, deepseek_module, modules,project_path,output_path):
    """
    Handles the case where the best matching module and mapped module are different,
    by calling DeepSeek for a detailed comparison and explanation.
    """
    # Get descriptions for the two methods
    tfidf_module_description = modules.get(tfidf_module, 'No description available')
    deepseek_module_description = modules.get(deepseek_module, 'No description available')

    # Call DeepSeek for a detailed comparison between the two modules
    explanation = call_deepseek_for_module_comparison(
        file_content, tfidf_module,deepseek_module,
        tfidf_module_description, deepseek_module_description, file_path,project_path,output_path
    )
    return explanation
