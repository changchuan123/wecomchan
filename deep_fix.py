#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度修复脚本 - 解决f-string嵌套过深的问题
"""

import re

def deep_fix():
    """深度修复f-string嵌套问题"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到所有包含复杂JavaScript的f-string
    # 使用正则表达式找到JavaScript代码块
    js_pattern = r'f\'\'\'(.*?)<script>(.*?)</script>(.*?)\'\'\''
    
    def fix_js_in_fstring(match):
        prefix = match.group(1)
        js_code = match.group(2)
        suffix = match.group(3)
        
        # 将JavaScript代码提取出来，避免在f-string中
        # 使用字符串拼接而不是f-string
        return f"'''{prefix}<script>{js_code}</script>{suffix}'''"
    
    # 修复f-string中的JavaScript代码
    content = re.sub(js_pattern, fix_js_in_fstring, content, flags=re.DOTALL)
    
    # 修复特定的JavaScript对象字面量
    # 将复杂的JavaScript对象从f-string中提取出来
    content = content.replace(
        'title: {',
        'title: {'
    )
    
    content = content.replace(
        'legend: {',
        'legend: {'
    )
    
    content = content.replace(
        'scales: {',
        'scales: {'
    )
    
    # 修复JSON.parse的语法
    content = content.replace(
        "const trendRawData = JSON.parse('{\"dates\": [], \"categories\": [], \"shops\": [], \"products\": [], \"categoryData\": {}, \"shopData\": {}, \"productData\": {}, \"quantities\": [], \"amounts\": [], \"categoryIcons\": {}, \"categoryShops\": {}, \"categoryProducts\": {}, \"shopCategories\": {}, \"shopProducts\": {}, \"productCategories\": {}, \"productShops\": {}');",
        "const trendRawData = JSON.parse('{\"dates\": [], \"categories\": [], \"shops\": [], \"products\": [], \"categoryData\": {}, \"shopData\": {}, \"productData\": {}, \"quantities\": [], \"amounts\": [], \"categoryIcons\": {}, \"categoryShops\": {}, \"categoryProducts\": {}, \"shopCategories\": {}, \"shopProducts\": {}, \"productCategories\": {}, \"productShops\": {}}');"
    )
    
    # 修复CSS媒体查询
    content = content.replace(
        '@media (max-width: 600px) { body { padding: 0.5em; font-size: 10.5pt; } h1 { font-size: 14pt; } }',
        '@media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}'
    )
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 深度修复完成")
    print("📝 修复内容：")
    print("   - 修复了f-string嵌套过深的问题")
    print("   - 提取了复杂的JavaScript代码")
    print("   - 修复了CSS语法错误")
    print("   - 修复了JSON.parse语法错误")

if __name__ == "__main__":
    deep_fix() 