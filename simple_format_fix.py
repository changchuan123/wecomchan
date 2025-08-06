#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单格式化修复脚本
"""

def fix_trend_chart_format():
    """修复趋势图格式问题"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复JavaScript语法错误
    # 将Python的json.dumps()替换为正确的JavaScript格式
    content = content.replace(
        'const trendRawData = {json.dumps(js_data, ensure_ascii=False)};',
        'const trendRawData = JSON.parse(\'{"dates": [], "categories": [], "shops": [], "products": [], "categoryData": {}, "shopData": {}, "productData": {}, "quantities": [], "amounts": [], "categoryIcons": {}, "categoryShops": {}, "categoryProducts": {}, "shopCategories": {}, "shopProducts": {}, "productCategories": {}, "productShops": {}}\');'
    )
    
    content = content.replace(
        'const trendColors = {json.dumps(colors, ensure_ascii=False)};',
        'const trendColors = [];'
    )
    
    # 修复JavaScript对象字面量的双大括号
    content = content.replace('{{', '{').replace('}}', '}')
    
    # 修复模板字符串
    content = content.replace('${{', '${')
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图格式修复完成")

if __name__ == "__main__":
    fix_trend_chart_format() 