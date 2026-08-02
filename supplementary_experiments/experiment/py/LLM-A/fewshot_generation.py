import textwrap
import os
import json
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_env import env_first, openai_client, chat_completion_content_with_retry

import re
import json
from typing import Dict, Any

import re
from typing import Dict, Any
from python_code_info import extract_python_info

def regex_fallback(content: str) -> Dict[str, Any]:
    result = {
        "package": None,
        "classes": [{
            "class_name": "UnknownClass",
            "class_type": "class",
            "annotations": [],
            "inheritance": {"parent_class": None, "implemented_interfaces": []},
            "fields": [],
            "methods": []
        }]
    }

    # Package matching
    package_match = re.search(r'package\s+([\w.]+)\s*;', content)
    if package_match:
        result["package"] = package_match.group(1)

    # Class matching
    class_match = re.search(r'(class|interface)\s+(\w+)', content)
    if class_match:
        class_name = class_match.group(2)
        result["classes"][0]["class_name"] = class_name
        result["classes"][0]["class_type"] = class_match.group(1)

    # Inheritance matching
    extends_match = re.search(r'extends\s+([\w.<>, ]+)', content)
    if extends_match:
        result["classes"][0]["inheritance"]["parent_class"] = extends_match.group(1).strip()

    impl_match = re.search(r'implements\s+([\w.<>, ]+)', content)
    if impl_match:
        result["classes"][0]["inheritance"]["implemented_interfaces"] = [i.strip() for i in impl_match.group(1).split(',')]

    # Method matching
    method_pattern = r'^\s*(?:@\w+\s+)*(?:public|private|protected|static|final|abstract|synchronized|native|transient|volatile)\s+([\w<>[\]]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w.<>, ]+)?\s*{'
    methods = re.findall(method_pattern, content, re.MULTILINE)
    
    class_name = result["classes"][0]["class_name"]
    processed_methods = []
    for return_type, name, params in methods:
        param_types = []
        for param in params.split(','):
            param = param.strip()
            if param:
                type_part = param.split()[0] if param.split() else ''
                param_types.append(type_part)
        processed_methods.append(f"{name}({', '.join(param_types)})")

    result["classes"][0]["methods"] = processed_methods

    # Field matching
    field_pattern = r'(?:public|private|protected|static|final)\s+([\w<>]+)\s+(\w+)\s*[;=]'
    fields = re.findall(field_pattern, content)
    result["classes"][0]["fields"] = [f"{t} {n}" for t, n in fields]

    return result


def extract_source_info(content: str) -> str:
    return extract_python_info(content)

    
def load_group_examples(output_path):
    """
    Parse few-shot_mapping.json and return {group_name: file_path}.
    Assumption: all 'group' nodes are at the first level of 'structure'.
    """
    csv_path = os.path.join(output_path, "tfidf-file-module_scores.csv")
    if os.path.exists(csv_path):
        return load_group_examples_from_scores(csv_path)

    json_path = os.path.join(output_path, "few-shot_mapping.json")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    group_to_file = {}
    for node in data.get("structure", []):
        if node.get("@type") != "group":
            continue
        group_name = node["name"]
        # take the first item as the example
        for child in node.get("nested", []):
            if child.get("@type") == "item":
                file_path = child["name"]
                group_to_file[group_name] = file_path
                break  # only one example per group needed
    return group_to_file


def load_group_examples_from_scores(csv_path):
    group_to_best = {}
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_path = row.get("file_path", "").strip()
            best_module = row.get("best_module", "").strip()
            if not file_path or not best_module or best_module == "None":
                continue
            try:
                likelihood = float(row.get("best_likelihood", 0) or 0)
            except ValueError:
                likelihood = 0.0
            current = group_to_best.get(best_module)
            if current is None or likelihood > current[0]:
                group_to_best[best_module] = (likelihood, file_path)
    return {module: file_path for module, (_, file_path) in group_to_best.items()}


def _normalize_rel_path(path: str) -> str:
    return os.path.normpath(path.strip().replace("\\", os.sep).replace("/", os.sep))


def resolve_source_file(base_dir, file_path):
    if not file_path:
        raise FileNotFoundError("empty file path")

    normalized = _normalize_rel_path(file_path)
    candidates = []

    if os.path.isabs(normalized):
        candidates.append(normalized)

    if base_dir:
        base_abs = os.path.abspath(base_dir)
        candidates.append(os.path.join(base_abs, normalized))

        parts = [part for part in normalized.split(os.sep) if part]
        for start in range(1, len(parts)):
            candidates.append(os.path.join(base_abs, *parts[start:]))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(candidates[0] if candidates else normalized)


def display_path_for_prompt(abs_path, base_dir, fallback):
    if base_dir:
        try:
            rel_path = os.path.relpath(abs_path, base_dir)
            if not rel_path.startswith(".."):
                return rel_path.replace(os.sep, "/")
        except ValueError:
            pass
    return fallback.strip().replace("\\", "/")

# ------------------------------------------------------------------
# Helper: generate a concise CoT explanation for one example file
# ------------------------------------------------------------------
def _gen_short_thought(code_excerpt: str, module_name: str, max_tokens: int = 120) -> str:
    """
    Query the LLM and obtain a 2-3 sentenceexplaining
    why the file belongs to `module_name`.
    """
    prompt = f"""
    You are an architecture mapping expert.
    Read the code AST below and Explain in 1 line why this file belongs to the '{module_name}' module by chain-of-thought, based on its functionality, operations, and directory location.

    Code AST:
    {code_excerpt[:1800]}   # safety cutoff to limit prompt length
    """
    try:
        client = openai_client(
            ["LLM_A_API_KEY", "LLM_API_KEY", "SILICONFLOW_API_KEY"],
            ["LLM_A_BASE_URL", "LLM_BASE_URL", "SILICONFLOW_BASE_URL"],
            None
        )
        response_content = chat_completion_content_with_retry(
            client,
            context=f"LLM-A few-shot thought: {module_name}",
            model=env_first(["LLM_A_CHAT_MODEL", "LLM_CHAT_MODEL", "SILICONFLOW_CHAT_MODEL"], required=True),
            messages=[{"role": "user", "content": prompt.strip()}],
            stream=True
        )
        return response_content.strip().replace("\n", " ")
    except Exception as e:
        print(f"[Warn] LLM Thought generation failed: {e}")
        return "Reasoning omitted (fallback)."


# ------------------------------------------------------------------
# Revised Few-Shot prompt builder
# ------------------------------------------------------------------
def build_few_shot_prompt(output_path, modules, base_dir=None):
    """
    Build Few-Shot COT blocks with auto?generated short thoughts.
    """
    group_examples=load_group_examples(output_path)
    # Sample modules that have example files
    pairs = [(m, group_examples[m]) for m in modules if m in group_examples]

    blocks = []
    for mod_name, path in pairs:
        try:
            file_path = resolve_source_file(base_dir, path)
            prompt_path = display_path_for_prompt(file_path, base_dir, path)
            with open(file_path, encoding="utf-8") as f:
                raw_content = f.read()
            
            try:
                file_content = extract_source_info(raw_content)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}, using raw content instead.")
                file_content = raw_content    
                
            #print (file_content)
            short_thought = _gen_short_thought(file_content, mod_name)

            block = textwrap.dedent(f"""
            ### Example.
            File path: {prompt_path}
            File content:
            {file_content}

            Thought: {short_thought}

            - **Assigned Module**: {mod_name}
            """).strip()
            blocks.append(block)

        except Exception as e:
            print(f"[Warn] Skip example '{path}': {e}")
    print(f"[DEBUG] Few shot prompt blocks generated: {blocks}")
    return "\n\n".join(blocks)
