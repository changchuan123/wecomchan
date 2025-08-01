#!/usr/bin/env python3
import os

# 获取当前工作目录
cwd = os.getcwd()
print(f"当前工作目录: {cwd}")

# 列出目录中的文件
files = os.listdir(cwd)
print(f"目录中的文件: {files}")

# 确认文件存在
filename = '整体月报数据.py'
if filename in files:
    print(f"找到文件: {filename}")
    
    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 查找并修复语法错误
    if "QTY_COL: 'sum'\n        " in content:
        print("找到需要修复的语法错误")
        fixed_content = content.replace("QTY_COL: 'sum'\n        ", "QTY_COL: 'sum'\n        })\n        ")
        
        # 写入修复后的内容
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(fixed_content)
        print("语法错误已修复")
    else:
        print("未找到需要修复的语法错误模式")
        
        # 尝试查找类似的模式
        import re
        pattern = r"QTY_COL:\s*'sum'[^\)]*\n"
        matches = re.findall(pattern, content)
        if matches:
            print(f"找到类似的模式: {matches}")
            
            # 尝试直接修复第224行
            lines = content.split('\n')
            if len(lines) >= 224:
                print(f"第224行内容: {lines[223]}")
                if "QTY_COL: 'sum'" in lines[223]:
                    lines[223] = lines[223] + "}"
                    fixed_content = '\n'.join(lines)
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(fixed_content)
                    print("直接修复了第224行")
        else:
            print("未找到类似的模式")
else:
    print(f"未找到文件: {filename}")