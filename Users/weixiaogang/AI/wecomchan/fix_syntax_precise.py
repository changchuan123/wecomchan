#!/usr/bin/env python3

# 读取文件内容
with open('整体月报数据.py', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 修复第224行
if len(lines) >= 224 and "QTY_COL: 'sum'" in lines[223]:
    lines[223] = lines[223].rstrip() + "})\n"
    print(f"修复后的第224行: {lines[223]}")

    # 写入修复后的内容
    with open('整体月报数据.py', 'w', encoding='utf-8') as file:
        file.writelines(lines)
    print("语法错误已修复")
else:
    print(f"第224行内容: {lines[223] if len(lines) >= 224 else '行不存在'}")
    print("未找到需要修复的内容")