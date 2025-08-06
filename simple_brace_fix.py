#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的修复脚本
"""

def simple_brace_fix():
    """简单的修复"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复JavaScript中的单个大括号
    content = content.replace(
        'function() {',
        'function() {{'
    )
    
    content = content.replace(
        'setTimeout(initTrendChart, 100);',
        'setTimeout(initTrendChart, 100);'
    )
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 简单修复完成")

if __name__ == "__main__":
    simple_brace_fix() 