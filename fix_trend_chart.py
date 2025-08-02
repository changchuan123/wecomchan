#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复趋势图JavaScript代码中的双大括号问题
"""

import re

def fix_js_braces_precisely(content):
    """
    精确修复JavaScript代码中的双大括号，不影响f-string和CSS
    """
    # 找到所有JavaScript代码块
    js_pattern = r'<script>(.*?)</script>'
    
    def fix_js_block(match):
        js_code = match.group(1)
        # 只在JavaScript代码中替换双大括号
        js_code = js_code.replace('{{', '{').replace('}}', '}')
        return f'<script>{js_code}</script>'
    
    return re.sub(js_pattern, fix_js_block, content, flags=re.DOTALL)

def main():
    """主修复函数"""
    print("🔧 开始修复趋势图JavaScript代码...")
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复JavaScript代码
    fixed_content = fix_js_braces_precisely(content)
    
    # 写回文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ JavaScript代码修复完成")
    print("📝 修复内容：")
    print("   - 将JavaScript代码中的双大括号{{}}改为单大括号{}")
    print("   - 保持f-string和CSS代码不变")
    print("   - 确保趋势图能正常加载")

if __name__ == "__main__":
    main() 