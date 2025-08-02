#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确修复JavaScript函数中的双大括号问题
"""

def fix_js_functions():
    """修复JavaScript函数中的双大括号"""
    print("🔧 开始精确修复JavaScript函数...")
    
    # 读取文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复特定的JavaScript函数
    fixed_lines = []
    for line in lines:
        # 只修复JavaScript函数中的双大括号
        if 'function' in line and '{{' in line:
            line = line.replace('{{', '{')
        if '}}' in line and ('function' in line or 'if (' in line or 'document.addEventListener' in line):
            line = line.replace('}}', '}')
        if '{{' in line and ('function' in line or 'if (' in line or 'document.addEventListener' in line):
            line = line.replace('{{', '{')
        
        fixed_lines.append(line)
    
    # 写回文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ JavaScript函数修复完成")

if __name__ == "__main__":
    fix_js_functions() 