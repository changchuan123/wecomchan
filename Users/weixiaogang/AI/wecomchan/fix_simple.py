#!/usr/bin/env python3

with open('整体月报数据.py', 'r') as file:
    content = file.read()

# 修复语法错误，在QTY_COL: 'sum'后添加右括号
fixed_content = content.replace("QTY_COL: 'sum'\n        ", "QTY_COL: 'sum'\n        })\n        ")

with open('整体月报数据.py', 'w') as file:
    file.write(fixed_content)

print("语法错误已修复")