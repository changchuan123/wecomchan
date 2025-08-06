#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单修复脚本
"""

def simple_fix():
    """简单修复"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复JavaScript中的大括号问题
    content = content.replace('plugins: {{', 'plugins: {')
    content = content.replace('title: {{', 'title: {')
    content = content.replace('legend: {{', 'legend: {')
    content = content.replace('scales: {{', 'scales: {')
    content = content.replace('x: {{', 'x: {')
    content = content.replace('y: {{', 'y: {')
    content = content.replace('y1: {{', 'y1: {')
    content = content.replace('grid: {{', 'grid: {')
    
    # 修复JavaScript函数定义
    content = content.replace('function() {{', 'function() {')
    content = content.replace('initTrendChart() {{', 'initTrendChart() {')
    content = content.replace('if (trendCtx) {{', 'if (trendCtx) {')
    
    # 修复JavaScript对象结束的大括号
    content = content.replace('                    }}', '                    }')
    content = content.replace('                }}', '                }')
    content = content.replace('            }}', '            }')
    content = content.replace('        }}', '        }')
    
    # 修复CSS媒体查询
    content = content.replace(
        '@media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}',
        '@media (max-width: 600px) { body { padding: 0.5em; font-size: 10.5pt; } h1 { font-size: 14pt; } }'
    )
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 简单修复完成")

if __name__ == "__main__":
    simple_fix() 