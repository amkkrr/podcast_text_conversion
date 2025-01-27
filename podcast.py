# coding: utf-8
import requests
import sys
import os
import glob
import argparse
from tqdm import tqdm
from dotenv import load_dotenv

end_space = "\n\n\n\n\n"
load_dotenv()

def get_ai_response(api_key, query_file, user_id="python-api", min_chars=300):
    """
    获取AI处理结果
    :param api_key: API密钥
    :param query_file: 包含查询内容的文件路径
    :param user_id: 用户ID，默认为"python-api"
    :param min_chars: 最小字符数，低于此值的文件将被忽略
    :return: 返回AI处理结果的字典
    """
    # 检查文件字符数
    with open(query_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if len(content) < min_chars:
            print(f"文件 {os.path.basename(query_file)} 字符数少于 {min_chars}，已跳过" + end_space)
            return {'answer': f"文件 {os.path.basename(query_file)} 字符数少于 {min_chars}，已跳过"}
    url: str = os.getenv('API_URL')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {},
        "query": open(query_file, 'r', encoding='utf-8').read(),
        "response_mode": "blocking",
        "conversation_id": "",
        "user": user_id,
    }

    # 显示单个文件处理进度
    with tqdm(total=1, desc=f"处理文件 {os.path.basename(query_file)}", unit="file") as pbar:
        response = requests.post(url, headers=headers, json=payload)
        response.encoding = 'utf-8'
        pbar.update(1)
        return response.json()

def save_result(output_file, content):
    """
    保存处理结果到文件
    :param output_file: 输出文件路径
    :param content: 要保存的内容
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def save_combined_result(output_file, content, mode='a'):
    """
    保存处理结果到文件
    :param output_file: 输出文件路径
    :param content: 要保存的内容
    :param mode: 文件打开模式，'w'为覆盖，'a'为追加
    """
    with open(output_file, mode, encoding='utf-8') as f:
        f.write(content + end_space)

def sort_files(files):
    """
    对文件列表进行排序
    :param files: 文件路径列表
    :return: 排序后的文件列表
    """
    # 将toc_html.txt和toc前缀的文件放在最前面
    toc_files = [f for f in files if os.path.basename(f) == 'toc_html.txt' or 
                os.path.basename(f).startswith('toc_')]
    # 其余文件按字母顺序排序
    other_files = sorted([f for f in files if f not in toc_files], 
                        key=lambda x: os.path.basename(x))
    return toc_files + other_files

def process_directory(api_key, directory, output_suffix=None, combined_output=None, min_chars=300):
    """
    处理目录中的所有txt文件
    :param api_key: API密钥
    :param directory: 要处理的目录路径
    :param output_suffix: 输出文件后缀
    :param combined_output: 合并输出文件路径，未指定时默认生成以目录名命名的合并文件
    """
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    if not txt_files:
        print(f"目录 {directory} 中没有找到txt文件" + "\n")
        return
        
    # 对文件进行排序
    txt_files = sort_files(txt_files)
    
    # 未指定合并输出文件时，使用目录名生成默认合并文件名
    if combined_output is None:
        dir_name = os.path.basename(os.path.normpath(directory))
        combined_output = os.path.join(directory, f"{dir_name}_combined_processed{output_suffix if output_suffix else ''}.txt")
        
    # 显示目录处理的总体进度
    for txt_file in tqdm(txt_files, desc="处理目录", unit="file"):
        print(f"\n正在处理文件: {txt_file}" + "\n")
        result = get_ai_response(api_key, txt_file, min_chars=min_chars)
        content = result.get('answer', 'No answer available')
        
        if combined_output:
            # 立即保存处理结果
            save_combined_result(combined_output, content)
            print(f"结果已追加保存到: {combined_output}" + "\n")
        else:
            # 生成输出文件名
            base_name = os.path.basename(txt_file)
            name, ext = os.path.splitext(base_name)
            dir_name = os.path.basename(os.path.normpath(directory))
            output_file = f"{dir_name}_{name}_processed{output_suffix if output_suffix else ''}.txt"
            output_path = os.path.join(directory, output_file)
            
            # 保存处理结果
            save_result(output_path, content)
            print(f"结果已保存到: {output_path}" + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理文本文件或目录")
    parser.add_argument("path", help="文件路径或目录路径")
    parser.add_argument("-o", "--output-suffix", help="输出文件后缀")
    parser.add_argument("-c", "--combined-output", help="合并输出文件路径")
    parser.add_argument("--min-chars", type=int, default=200,
                        help="最小字符数，低于此值的文件将被忽略")
    args = parser.parse_args()

    api_key = os.getenv('API_KEY')
    
    if os.path.isfile(args.path):
        if not args.path.endswith('.txt'):
            print("错误：只支持处理txt文件" + "\n")
            sys.exit(1)
        result = get_ai_response(api_key, args.path, min_chars=args.min_chars)
        print(result)
    elif os.path.isdir(args.path):
        process_directory(api_key, args.path, args.output_suffix, args.combined_output, args.min_chars)
    else:
        print(f"错误：路径 {args.path} 不存在" + "\n")
        sys.exit(1)
