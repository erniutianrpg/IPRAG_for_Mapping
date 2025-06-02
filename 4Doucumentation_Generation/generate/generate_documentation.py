import json
import random
from pathlib import Path
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import time

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="your-private-key"
)

def extract_file_paths(data):
    paths = []
    def recurse(node, group=None):
        if isinstance(node, dict):
            if node.get('@type') == 'group':
                for child in node.get('nested', []):
                    recurse(child, group=node.get('name'))
            elif node.get('@type') == 'item' and group == "None":
                paths.append(node['name'])
        elif isinstance(node, list):
            for item in node:
                recurse(item, group=group)
    recurse(data.get('structure', []))
    return list(set(paths))

def read_file_content(file_path, root_dir):
    full_path = Path(root_dir) / file_path
    if full_path.exists():
        return full_path.read_text(encoding='utf-8', errors='ignore')
    return None

def summarize_code(code, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a code understanding assistant skilled at summarizing code functionality."},
                    {"role": "user", "content": f"Please summarize the functionality of the following code in less than 100 words:\n{code}"}
                ],
                timeout=30
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e):
                print("Request has triggered rate limiting, waiting to retry.")
            else:
                print(f"summarize_code Error：{e}")
                break
    raise RuntimeError("summarize_code Retry failed")


def generate_module_description(summaries):
    combined = "\n\n".join(summaries)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an advanced software module analysis assistant. "
                    "Your task is to provide a concise and high-level summary paragraph "
                    "that captures the core functionality and purpose of the entire module. "
                    "Do not list individual features or detailed points."
                )
            },
            {
                "role": "user",
                "content": (
                    "The following is a summary of the functions of each file in this module. "
                    "Please summarize the overall function of the module. "
                    "Use a paragraph to briefly describe its core function and purpose, do not list every sub-function.\n\n"
                    f"{combined}"
                )
            }
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def save_summary_output(project_name, json_folder_name, summaries, module_description):
    output_dir = Path("summary_output") / project_name / json_folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    for summary in summaries:
        header, content = summary.split(":\n", 1)

        src_index = header.lower().find("src")
        if src_index != -1:
            trimmed_path = header[src_index:]
        else:
            trimmed_path = Path(header).name  

        sanitized_name = trimmed_path.replace("/", "_").replace("\\", "_")
        file_path = output_dir / f"{sanitized_name}.txt"

        file_path.write_text(content, encoding="utf-8")

    module_file = output_dir / "module_description.txt"
    module_file.write_text(module_description, encoding="utf-8")

def analyze_project(project_name, project_root, json_file_path, json_folder_name, max_code_length=100000):
    try:
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"can't read JSON file {json_file_path}: {e}")
            return
        MAX_SUMMARIES = 350
        random.seed(42)
        paths = random.sample(extract_file_paths(data), min(MAX_SUMMARIES, len(extract_file_paths(data))))
        total = len(paths)
        summaries = []

        print(f"\n Analyzing the project：{project_name} / {json_folder_name}（{total} None files）")

        for idx, path in enumerate(paths, 1):
            code = read_file_content(path, project_root)
            if code:
                if len(code) > max_code_length:
                    code = code[:max_code_length]
                summary = summarize_code(code)
                if summary:
                    summaries.append(f"{path}:\n{summary}")
            print(f"{project_name}/{json_folder_name}：{idx}/{total}")

        if not summaries:
            print(f"No available code for summarization：{project_name} / {json_folder_name}")
            return
        module_description = generate_module_description(summaries)

        save_summary_output(project_name, json_folder_name, summaries, module_description)
        print(f"Analysis completed：{project_name} / {json_folder_name}\n")
    except Exception as e:\
        print(f"Analysis interrupted：{project_name} / {json_folder_name}，原因：{e}")

projects_to_process = [
    "bigbluebutton",
    "teammates",
    "teastore",
    "mediastore",
    "jabref",
    "hadoop"
]

parent_dir = Path(__file__).parent.parent.parent
BASE_JSON_PATH = parent_dir / 'dataset' 
BASE_PROJECT_PATH = parent_dir / 'datase' 

for project in projects_to_process:
    project_json_dir = BASE_JSON_PATH / project
    project_code_root = BASE_PROJECT_PATH / project

    if not project_json_dir.exists():
        print(f"project's JSON path doesn't exit：{project_json_dir}")
        continue

    json_jobs = []
    for json_subdir in project_json_dir.iterdir():
        if json_subdir.is_dir():
            json_file_path = json_subdir / "groundtruth.json"
            if json_file_path.exists():
                json_jobs.append({
                    "project_name": project,
                    "project_root": project_code_root,
                    "json_file_path": json_file_path,
                    "json_folder_name": json_subdir.name
                })

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                analyze_project,
                job["project_name"],
                job["project_root"],
                job["json_file_path"],
                job["json_folder_name"]
            ) for job in json_jobs
        ]
