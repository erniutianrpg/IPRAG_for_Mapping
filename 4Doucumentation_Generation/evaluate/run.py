import json
from openai import OpenAI
from utils import convert_to_json
from metric.evaluator import get_evaluator

client = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key="your-private-key"
)

def refine_description(description):
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
        return description  

with open('input_data.json', 'r', encoding='utf-8') as f:
    module_data = json.load(f)

src_list = []
ref_list = []
output_list = []
module_names = []

for module in module_data:
    module_names.append(module['module_name'])
    src_list.append(module['reference_description'])  
    ref_list.append(module['reference_description'])  

    original_desc = module['generated_description']
    refined_desc = refine_description(original_desc)
    output_list.append(refined_desc)

data = convert_to_json(output_list=output_list, src_list=src_list, ref_list=ref_list)

task = 'summarization'
evaluator = get_evaluator(task)

eval_scores = evaluator.evaluate(data, print_result=False)
