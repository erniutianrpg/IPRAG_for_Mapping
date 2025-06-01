import json
from openai import OpenAI
from utils import convert_to_json
from metric.evaluator import get_evaluator

#设置你的 OpenAI API 密钥
client = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-mrjpmzgmaghweqpdjamedwbmnkkshdmdeokcrrbhsawpvtzz"
)

def refine_description(description):
    """调用 GPT 对描述进行语义整合与功能提取"""
    prompt = (
        "Please consolidate semantically redundant content in the following description, "
        "and retain only the functional aspects. Do not add any new information.Limit the output to 100 words.:\n\n"
        f"{description}\n\n"
        "Return the revised version only:"
    )
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": "You are a technical writing assistant specialized in concise module documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error during OpenAI API call:", e)
        return description  # 出错时使用原始描述

# 加载 JSON 输入
with open('input.json', 'r', encoding='utf-8') as f:
    module_data = json.load(f)

# 构造输入列表
src_list = []
ref_list = []
output_list = []
module_names = []

for module in module_data:
    module_names.append(module['module_name'])
    src_list.append(module['reference_description'])  # 作为 source
    ref_list.append(module['reference_description'])  # 作为 reference

    # 修改 generated_description：语义整合 + 功能提取
    original_desc = module['generated_description']
    # refined_desc = refine_description(original_desc)
    # output_list.append(refined_desc)
    output_list.append(module['generated_description'])

# 构造数据用于评估器
data = convert_to_json(output_list=output_list, src_list=src_list, ref_list=ref_list)

# 初始化评估器
task = 'summarization'
evaluator = get_evaluator(task)

# 评估（默认所有四个维度，含 overall）
eval_scores = evaluator.evaluate(data, print_result=False)

# 写入结果
with open('evaluation_results.txt', 'w', encoding='utf-8') as f:
    for module_name, score_dict in zip(module_names, eval_scores):
        f.write(f'Module: {module_name}\n')
        for dim in ['coherence', 'consistency', 'fluency', 'relevance', 'overall']:
            if dim in score_dict:
                f.write(f'{dim.capitalize()}: {round(score_dict[dim], 6)}\n')
        f.write('\n')
