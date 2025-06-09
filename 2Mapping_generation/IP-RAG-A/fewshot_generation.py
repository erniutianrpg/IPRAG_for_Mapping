import textwrap
import ollama
import os
import json
import javalang     
import csv
import re
import json
import javalang
from typing import Dict, Any

import re
from typing import Dict, Any

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


def extract_java_info(content: str) -> str:
    try:
        tree = javalang.parse.parse(content)
        
        def get_inheritance(cls):
            if isinstance(cls, javalang.tree.InterfaceDeclaration):
                return {
                    "parent_interface": None,
                    "extended_interfaces": [ext.name for ext in cls.extends] if cls.extends else []
                }
            else:
                return {
                    "parent_class": cls.extends.name if cls.extends else None,
                    "implemented_interfaces": [impl.name for impl in cls.implements] if cls.implements else []
                }

        ast = {
            "package": tree.package.name if tree.package else None,
            "classes": [{
                "class_name": cls.name,
                "class_type": "interface" if isinstance(cls, javalang.tree.InterfaceDeclaration) else "class",
                "annotations": [ann.name for ann in getattr(cls, 'annotations', [])],
                "inheritance": get_inheritance(cls),
                "fields": [
                    f"{field.type.name} {declarator.name}"
                    for field in getattr(cls, 'fields', [])
                    for declarator in field.declarators
                    if 'final' not in field.modifiers
                ],
                "methods": [
                    f"{method.name}({', '.join(p.type.name for p in method.parameters)})"
                    for method in getattr(cls, 'methods', [])
                ]
            } for cls in tree.types]
        }
        return json.dumps(ast, ensure_ascii=False)

    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
        return json.dumps(regex_fallback(content), ensure_ascii=False)

def extract_gt_filepaths(gt_json_path):
    filepaths = set()
    with open(gt_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for group in data.get('structure', []):
        for item in group.get('nested', []):
            name = item.get('name', '')
            if name:
                filepaths.add(name.strip())
    return filepaths


def find_min_likelihood_mapping(csv_file_path, gt_json_path):
    gt_files = extract_gt_filepaths(gt_json_path)
    min_row = None
    min_likelihood = float('inf')

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_item = row["file_path"].strip()
            likelihood = float(row.get("best_likelihood", 0))
            if file_item in gt_files and "test/" not in file_item.lower() and likelihood < min_likelihood:
                min_likelihood = likelihood
                min_row = row
    return min_row
    
def load_group_examples(output_path):
    """
    Parse few-shot_mapping.json and return {group_name: file_path}.
    Assumption: all 'group' nodes are at the first level of 'structure'.
    """
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
        resp = ollama.chat(
            model="deepseek-r1:70b",
            messages=[{"role": "user", "content": prompt.strip()}]
        )
        return resp["message"]["content"].strip().replace("\n", " ")
    except Exception as e:
        print(f"[Warn] LLM Thought generation failed: {e}")
        return "Reasoning omitted (fallback)."


# ------------------------------------------------------------------
# Revised Few-Shot prompt builder
# ------------------------------------------------------------------
def build_few_shot_prompt(output_path, modules, base_dir=None,weakest_mapping_csv=None, gt_json_path=None):
    """
    Build Few-Shot COT blocks with auto?generated short thoughts.
    """
    group_examples=load_group_examples(output_path)
    # Sample modules that have example files
    pairs = [(m, group_examples[m]) for m in modules if m in group_examples]

    blocks = []
    for mod_name, path in pairs:
        try:
            flie_path=os.path.join(base_dir,path)
            with open(flie_path, encoding="utf-8") as f:
                raw_content = f.read()
            
            try:
                file_content = extract_java_info(raw_content)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}, using raw content instead.")
                file_content = raw_content    
                
            #print (file_content)
            #short_thought = _gen_short_thought(file_content, mod_name)

            block = textwrap.dedent(f"""
            ### Example.
            File path: {path}
            File content:
            {file_content}

            - **Assigned Module**: {mod_name}
            """).strip()
            blocks.append(block)

        except Exception as e:
            print(f"[Warn] Skip example '{path}': {e}")
            
    weakest_mapping_csv=os.path.join(output_path, "tfidf-file-module_scores.csv")
    project = os.path.basename(os.path.normpath(base_dir))
    gt_json_path = os.path.join(base_dir, f"updated_{project}_gt.json")
    if weakest_mapping_csv and gt_json_path:
        weakest_row = find_min_likelihood_mapping(weakest_mapping_csv, gt_json_path)
        if weakest_row:
            file_path = weakest_row['file_path']
            abs_path = os.path.join(base_dir, file_path)
            try:
                with open(abs_path, encoding="utf-8") as f:
                    raw_content = f.read()
                try:
                    file_content = extract_java_info(raw_content)
                except:
                    file_content = raw_content
                none_block = textwrap.dedent(f"""
                ### Example.
                File path: {file_path}
                File content:
                {file_content}

                - **Assigned Module**: None
                """).strip()
                blocks.append(none_block)
            except Exception as e:
                print(f"[Warn] Cannot load weakest-matching file {file_path}: {e}")    
    print(f"[DEBUG] Few shot prompt blocks generated: {blocks}")
    return "\n\n".join(blocks)
