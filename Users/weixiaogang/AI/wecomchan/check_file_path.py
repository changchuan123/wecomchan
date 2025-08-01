#!/usr/bin/env python3
import os

# 获取当前工作目录
cwd = os.getcwd()
print(f"当前工作目录: {cwd}")

# 检查文件是否存在
filename = '整体月报数据.py'
full_path = os.path.join(cwd, filename)
print(f"完整路径: {full_path}")
print(f"文件是否存在: {os.path.exists(full_path)}")

# 如果文件存在，读取第224行
if os.path.exists(full_path):
    with open(full_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if len(lines) >= 224:
            print(f"第224行内容: {lines[223].strip()}")
            
            # 修复第224行
            lines[223] = lines[223].rstrip() + "})\n"
            print(f"修复后的第224行: {lines[223].strip()}")
            
            # 写入修复后的内容
            with open(full_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            print("语法错误已修复")