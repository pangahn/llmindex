# -*- coding: utf-8 -*-
import os
from pathlib import Path

import tinify
from dotenv import load_dotenv
from tabulate import tabulate
from tqdm import tqdm

load_dotenv()
tinify.key = os.getenv("TINIFY_KEY")


current_folder = Path(__file__).resolve().parent.parent
source_folder = current_folder / "resources/source"
target_folder = current_folder / "resources/images"

if not os.path.exists(target_folder):
    os.makedirs(target_folder)

png_files = [f for f in os.listdir(source_folder) if f.endswith(".png")]

results = []

for filename in tqdm(png_files, desc="处理图片", unit="file"):
    source_file_path = os.path.join(source_folder, filename)
    target_file_path = os.path.join(target_folder, filename)

    original_size = os.path.getsize(source_file_path)

    if os.path.exists(target_file_path):
        pass
    else:
        source = tinify.from_file(source_file_path)
        source.to_file(target_file_path)
        compressed_size = os.path.getsize(target_file_path)
        compression_ratio = (1 - (compressed_size / original_size)) * 100
        results.append([filename, original_size, compressed_size, f"{compression_ratio:.2f}%", "新压缩"])

headers = ["文件名", "原始大小 (字节)", "压缩后大小 (字节)", "压缩率 (%)", "状态"]
print(tabulate(results, headers=headers, tablefmt="grid"))

print("处理完成")
