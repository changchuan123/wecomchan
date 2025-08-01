#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def fix_js_functions():
    # 读取文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复店铺排行函数的语法错误
    # 将错误的 </div> 标签修复为正确的 </summary></details>
    content = re.sub(
        r'(<summary>🏪 \$\{\{index \+ 1\}\}\. \$\{\{shop\}\} ─[^<]+)</div>\s*</div>',
        r'\1</summary></details>',
        content
    )
    
    # 修复单品排行函数的语法错误
    content = re.sub(
        r'(<summary>📦 \$\{\{index \+ 1\}\}\. \$\{\{product\}\} ─[^<]+)</div>\s*</div>',
        r'\1</summary></details>',
        content
    )
    
    # 将details标签改为div标签，去掉折叠功能
    content = re.sub(
        r'<details style="([^"]+)">\s*<summary>([^<]+)</summary>\s*</details>',
        r'<div style="\1">\2</div>',
        content
    )
    
    # 写回文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('JavaScript函数语法错误修复完成！')

if __name__ == '__main__':
    fix_js_functions()