import os
import shutil
import zipfile

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

def zip_dir(source_dir, zip_path):
    """将指定目录压缩为 zip 文件"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, start=source_dir)
                zipf.write(abs_path, rel_path)
    print(f'已压缩目录：{source_dir} -> {zip_path}')

def clean_removed_folders(base_path):
    # 遍历 LLM-S 下的项目子目录
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

                    # 压缩并删除 deepseek_response_forFile
                    if item == 'deepseek_response_forFile' and os.path.isdir(item_path):
                        zip_path = os.path.join(sub_path, 'deepseek_response_forFile.zip')
                        if not os.path.exists(zip_path):
                            try:
                                zip_dir(item_path, zip_path)
                                shutil.rmtree(item_path)
                                print(f'已删除原始目录：{item_path}')
                            except Exception as e:
                                print(f'压缩或删除失败：{item_path}，错误：{e}')
                        else:
                            print(f'压缩文件已存在，跳过：{zip_path}')
                            shutil.rmtree(item_path)
                            print(f'已删除原始目录：{item_path}')


if __name__ == '__main__':
    clean_removed_folders(base_path)
