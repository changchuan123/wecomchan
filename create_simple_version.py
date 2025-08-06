#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建简化版本的修复脚本
"""

def create_simple_version():
    """创建简化版本，避免f-string嵌套问题"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 将复杂的f-string替换为字符串拼接
    # 找到包含JavaScript的f-string并替换
    
    # 替换包含复杂JavaScript的部分
    content = content.replace(
        'f\'\'\'\n        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">\n            <h3 style="margin-bottom: 15px; color: #333;">📈 销售趋势图（近31天）</h3>\n            <div style="position: relative; height: 400px; margin-bottom: 20px;">\n                <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>\n            </div>\n        </div>\n        \n        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n        <script>\n        // 销售趋势图数据\n        const trendData = {',
        'f\'\'\'\n        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">\n            <h3 style="margin-bottom: 15px; color: #333;">📈 销售趋势图（近31天）</h3>\n            <div style="position: relative; height: 400px; margin-bottom: 20px;">\n                <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>\n            </div>\n        </div>\n        \n        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n        <script>\n        // 销售趋势图数据\n        const trendData = {'
    )
    
    # 修复CSS媒体查询
    content = content.replace(
        '@media (max-width: 600px) { body { padding: 0.5em; font-size: 10.5pt; } h1 { font-size: 14pt; } }',
        '@media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}'
    )
    
    # 修复JSON.parse语法
    content = content.replace(
        "const trendRawData = JSON.parse('{\"dates\": [], \"categories\": [], \"shops\": [], \"products\": [], \"categoryData\": {}, \"shopData\": {}, \"productData\": {}, \"quantities\": [], \"amounts\": [], \"categoryIcons\": {}, \"categoryShops\": {}, \"categoryProducts\": {}, \"shopCategories\": {}, \"shopProducts\": {}, \"productCategories\": {}, \"productShops\": {}');",
        "const trendRawData = JSON.parse('{\"dates\": [], \"categories\": [], \"shops\": [], \"products\": [], \"categoryData\": {}, \"shopData\": {}, \"productData\": {}, \"quantities\": [], \"amounts\": [], \"categoryIcons\": {}, \"categoryShops\": {}, \"categoryProducts\": {}, \"shopCategories\": {}, \"shopProducts\": {}, \"productCategories\": {}, \"productShops\": {}}');"
    )
    
    # 写入修复后的文件
    with open('整体月报数据_simple.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 简化版本创建完成")
    print("📁 新文件: 整体月报数据_simple.py")

if __name__ == "__main__":
    create_simple_version() 