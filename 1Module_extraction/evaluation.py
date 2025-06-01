import os
import glob
import shutil
import numpy as np
import re
import csv
import difflib
import xml.etree.ElementTree as ET


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

def parse_uml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # 定义 XML 文件中使用的命名空间
    namespaces = {
        'xmi': 'http://www.omg.org/spec/XMI/20131001',
        'uml': 'http://www.eclipse.org/uml2/5.0.0/UML'
    }

    id_to_name = {}
    for element in root.findall(".//*[@xmi:id]", namespaces):  # 使用命名空间进行查找
        id = element.get('{http://www.omg.org/spec/XMI/20131001}id')
        name = element.get('name')
        if id and name:
            id_to_name[id] = name
    return id_to_name

def read_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        element_ids = {row['ArchitectureElementId']: row['SentenceId'] for row in reader}
        # element_ids = {row['ArchitectureElementId']: row['CodeElementId'] for row in reader}
    return element_ids

def extract_modules(content):
    # 正则表达式模式，匹配模块名和描述
    pattern = r'(?:module|Module) Name:\s*(.*?)(?:,\s*module|,\s*Module|module|Module) Description:(.*?)(?=(?:module|Module) Name:|$)'

    # 查找所有匹配项，支持跨行匹配和忽略大小写
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    # 处理匹配结果，返回模块名称和描述的列表
    modules = [{'module name': name.strip(), 'module description': description.strip()} for name, description in
               matches]

    return modules


# 新的从叙述文本中提取模块名和描述的函数
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


# 根据文本特点选择合适的提取函数
def process_text(text):
    # 将检测逻辑调整为忽略大小写
    if "module name:" in text.lower() or "module description:" in text.lower():
        return extract_modules(text)
    else:
        return extract_modules_from_narrative(text)


# 主处理逻辑
projects = ['teammates', 'bigbluebutton', 'jabref', 'mediastore', 'teastore']
# projects = ['bigbluebutton']
destination_dir = './LLM_responses/gpt-4o/'

for project in projects:
    model = 'gpt-4o'
    csv_file_path = f'data/SAM-Code-goldstandards/goldstandard-{project}.csv'  # 替换为你的CSV文件路径

    # 读取 document 和 model 之间的映射，获得 model 中每个模块id和 document 中句子的映射
    element_ids = read_csv(f'data/SAD-SAM-goldstandards/goldstandard-{project}.csv')

    # 解析 model 文件，获得 model 中每个模块id对应的模块名
    id_to_name = parse_uml(f'data/models/uml/{project}.uml')

    # 从 UML 解析中获取模块名称列表
    uml_module_names = [id_to_name[element_id] for element_id in element_ids if element_id in id_to_name]
    print(uml_module_names)
    # 输出文件所在的目录
    output_dir = f'LLM_responses/{model}/{project}/'

    # 使用 glob 查找所有匹配的输出文件
    pattern = os.path.join(output_dir, 'output_*.txt')
    files = glob.glob(pattern)

    # 提取文件编号
    file_indices = []
    for file in files:
        basename = os.path.basename(file)
        if basename.startswith('output_') and basename.endswith('.txt'):
            num_str = basename[7:-4]  # 'output_' 长度为7，'.txt' 长度为4
            if num_str.isdigit():
                file_indices.append(int(num_str))

    if not file_indices:
        print(f"项目 {project} 中未找到任何输出文件。")
        continue  # 跳过当前项目，继续下一个项目

    # 按编号从大到小排序，并取前10个
    file_indices_sorted = sorted(file_indices, reverse=True)
    last_10_indices = file_indices_sorted[:10]

    print(f"项目 {project} 的处理文件编号: {last_10_indices}")

    # 初始化变量以收集精确度和召回率
    precisions = []
    recalls = []
    f1_scores = []
    file_f1_scores = {}

    # 遍历最后 10 个输出文件，从大到小
    for i in last_10_indices:
        output_file_path = os.path.join(output_dir, f'output_{i}.txt')
        try:
            with open(output_file_path, 'r', encoding='utf-8') as file:
                output_text = file.read()
        except FileNotFoundError:
            print(f"文件未找到: {output_file_path}")
            continue  # 跳过此文件，继续下一个文件
        except Exception as e:
            print(f"读取文件 {output_file_path} 时出错: {e}")
            continue  # 跳过此文件，继续下一个文件

        # 从输出文件中提取模块信息
        extracted_modules = process_text(output_text)

        # 集合用于分类
        similar_names = set()
        only_in_uml = set(uml_module_names)
        only_in_extracted = set(module['module name'] for module in extracted_modules)

        for uml_name in uml_module_names:
            matched = False  # 标记是否已经匹配到
            for extracted_module in extracted_modules:
                if matched:
                    break  # 一旦匹配成功，就跳出循环
                extracted_name = extracted_module['module name']
                if is_similar(uml_name, extracted_name) or share_common_word(uml_name, extracted_name):
                    similar_names.add((uml_name, extracted_name))
                    only_in_uml.discard(uml_name)
                    only_in_extracted.discard(extracted_name)
                    matched = True  # 设定匹配标记

        if len(similar_names) == 0:
            continue  # 如果没有相似的名称，跳过此文件

        # 打印此输出文件的结果
        print(f"\nResults for {output_file_path}:")
        print("Similar Names:")
        for name_pair in similar_names:
            print(name_pair)

        print("\nOnly in GT Model:")
        for name in only_in_uml:
            print(name)

        print("\nOnly in output model of GPT:")
        for name in only_in_extracted:
            print(name)

        # 计算每个文件的精确度和召回率
        precision = len(similar_names) / (len(similar_names) + len(only_in_extracted)) if (len(similar_names) + len(
            only_in_extracted)) > 0 else 0
        recall = len(similar_names) / (len(similar_names) + len(only_in_uml)) if (len(similar_names) + len(
            only_in_uml)) > 0 else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # 收集精确度和召回率数据
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1_score)
        file_f1_scores[output_file_path] = f1_score

    if not f1_scores:
        print(f"项目 {project} 没有有效的评估结果。")
        continue  # 如果没有任何有效的 F1 分数，跳过后续处理

    # 找到最接近平均 F1 分数的文件
    average_f1 = np.mean(f1_scores)
    closest_f1_file = min(file_f1_scores, key=lambda x: abs(file_f1_scores[x] - average_f1))

    # 将选定的文件复制到目标目录，并以项目名称命名
    destination_path = os.path.join(destination_dir, f"{project}.txt")
    try:
        shutil.copy(closest_f1_file, destination_path)
        print(f"已将文件 {closest_f1_file} 复制到 {destination_path}，作为项目 {project} 的最接近平均 F1 分数的文件。")
    except Exception as e:
        print(f"复制文件 {closest_f1_file} 到 {destination_path} 时出错: {e}")

    # 计算平均值和标准差
    average_precision = np.mean(precisions) * 100
    average_recall = np.mean(recalls) * 100
    average_f1_score = np.mean(f1_scores) * 100

    std_dev_precision = np.std(precisions, ddof=1) * 100 if len(precisions) > 1 else 0
    std_dev_recall = np.std(recalls, ddof=1) * 100 if len(recalls) > 1 else 0
    std_dev_f1_score = np.std(f1_scores, ddof=1) * 100 if len(f1_scores) > 1 else 0

    print(f"平均精确度: {average_precision:.2f}%")
    print(f"平均召回率: {average_recall:.2f}%")
    print(f"平均F1分数: {average_f1_score:.2f}%")
    print(f"精确度标准差: {std_dev_precision:.2f}%")
    print(f"召回率标准差: {std_dev_recall:.2f}%")
    print(f"F1分数标准差: {std_dev_f1_score:.2f}%")

    # 将统计数据写入 CSV 文件
    csvfile_path = 'project_statistics-' + model + '.csv'
