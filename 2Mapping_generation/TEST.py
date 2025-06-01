import os
import shutil

# 设置根目录路径
base_path = 'LLM-S'

# 文件保留列表（以重命名后的名称为准）
keep_files = {
    'updated_module_info.txt',
    'call_deepseek.log',
    'module_mapping_scores.csv',
    'LLM-S_mapping.json'
}
keep_dirs = {
    'deepseek_response_forFile'
}

def clean_removed_folders(base_path):
    # 遍历 IP-RAG-A 下的项目子目录
    for project in os.listdir(base_path):
        project_path = os.path.join(base_path, project)
        if not os.path.isdir(project_path):
            continue

        for sub in os.listdir(project_path):
            sub_path = os.path.join(project_path, sub)

            if os.path.isdir(sub_path) and sub.startswith('removed_'):
                print(f'处理文件夹：{sub_path}')
                for item in os.listdir(sub_path):
                    item_path = os.path.join(sub_path, item)

                    # 特别处理 clustering_before_feedback.json -> IP-RAG-A_mapping.json
                    if item == 'clustering_before_feedback.json':
                        new_path = os.path.join(sub_path, 'LLM-S_mapping.json')
                        try:
                            os.rename(item_path, new_path)
                            print(f'已重命名：{item_path} -> {new_path}')
                        except Exception as e:
                            print(f'重命名失败：{item_path}，错误：{e}')
                        continue

                    # 特别处理 few-shot_mapping.json -> IP-R.json
                    if item == 'few-shot_mapping.json':
                        new_path = os.path.join(sub_path, 'IP-R.json')
                        try:
                            os.rename(item_path, new_path)
                            print(f'已重命名：{item_path} -> {new_path}')
                        except Exception as e:
                            print(f'重命名失败：{item_path}，错误：{e}')
                        continue

                    # 删除不在保留列表中的内容
                    if (os.path.isfile(item_path) and item not in keep_files) or \
                       (os.path.isdir(item_path) and item not in keep_dirs):
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                                print(f'已删除文件夹：{item_path}')
                            else:
                                os.remove(item_path)
                                print(f'已删除文件：{item_path}')
                        except Exception as e:
                            print(f'删除 {item_path} 时出错：{e}')

if __name__ == '__main__':
    clean_removed_folders(base_path)
