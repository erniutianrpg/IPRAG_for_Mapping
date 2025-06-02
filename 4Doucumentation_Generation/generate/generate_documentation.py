import json
import random
from pathlib import Path
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import time


# 初始化 OpenAI 客户端（DeepSeek API）
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="sk-742fae6ebace4e29abe324cd5d3cb752"
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
                print(f"⚠️ 第 {attempt+1} 次请求触发限流，等待重试中...")
                #time.sleep(1)  # 延长等待时间
            else:
                print(f"⚠️ summarize_code 异常：{e}")
                break
    raise RuntimeError("summarize_code 重试失败")


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

        # 只保留从 "src" 开始的路径部分（不包括前面的模块路径）
        src_index = header.lower().find("src")
        if src_index != -1:
            trimmed_path = header[src_index:]
        else:
            trimmed_path = Path(header).name  # fallback: 只保留文件名

        # 替换路径分隔符，生成可用文件名
        sanitized_name = trimmed_path.replace("/", "_").replace("\\", "_")
        file_path = output_dir / f"{sanitized_name}.txt"

        # 写入文件内容
        file_path.write_text(content, encoding="utf-8")

    # 写入模块描述
    module_file = output_dir / "module_description.txt"
    module_file.write_text(module_description, encoding="utf-8")

def analyze_project(project_name, project_root, json_file_path, json_folder_name, max_code_length=100000):
    try:
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 无法读取 JSON 文件 {json_file_path}: {e}")
            return
        MAX_SUMMARIES = 350
        random.seed(42)
        paths = random.sample(extract_file_paths(data), min(MAX_SUMMARIES, len(extract_file_paths(data))))
        total = len(paths)
        summaries = []

        print(f"\n🟩 正在分析项目：{project_name} / {json_folder_name}（共 {total} 个 None 文件）")

        for idx, path in enumerate(paths, 1):
            code = read_file_content(path, project_root)
            if code:
                # 截断过长代码
                if len(code) > max_code_length:
                    code = code[:max_code_length]
                    code += "\n// ⚠️ 代码已截断，仅保留前 {max_code_length} 个字符。"
                summary = summarize_code(code)
                if summary:
                    summaries.append(f"{path}:\n{summary}")
            print(f"{project_name}/{json_folder_name}：{idx}/{total}")

        if not summaries:
            print(f"⚠️ 没有可用的代码进行摘要：{project_name} / {json_folder_name}")
            return

        # MAX_SUMMARIES = 450
        # random.seed(42)
        # sampled_summaries = random.sample(summaries, min(MAX_SUMMARIES, len(summaries)))
        module_description = generate_module_description(summaries)

        save_summary_output(project_name, json_folder_name, summaries, module_description)
        print(f"✅ 分析完成：{project_name} / {json_folder_name}\n")
    except Exception as e:\
        print(f"❌ 分析中断：{project_name} / {json_folder_name}，原因：{e}")
# ==== 要分析的项目名列表 ====
projects_to_process = [
    "hadoop"
]

# ==== 基础路径设置 ====
parent_dir = Path(__file__).parent.parent.parent
BASE_JSON_PATH = parent_dir / 'dataset' 
BASE_PROJECT_PATH = parent_dir / 'datase' 

# ==== 主逻辑 ====
for project in projects_to_process:
    project_json_dir = BASE_JSON_PATH / project
    project_code_root = BASE_PROJECT_PATH / project

    if not project_json_dir.exists():
        print(f"❌ 项目 JSON 路径不存在：{project_json_dir}")
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

    # 用线程池并发处理当前项目的多个 JSON 文件夹
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
