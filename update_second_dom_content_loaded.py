#!/usr/bin/env python3

import re

# 读取文件内容
with open('整体月报数据.py', 'r') as f:
    content = f.read()

# 定义替换模式
pattern = r"document\.addEventListener\('DOMContentLoaded', function\(\) \{\{\s+initChart\(\);\s+updateChart\(\);\s+// 初始化默认数据表格\s+updateDefaultDataTable\(\);"

# 替换内容
replacement = "document.addEventListener('DOMContentLoaded', function() {{\n            initChart();\n            updateChart();\n            // 初始化默认数据表格\n            updateDefaultDataTable();\n            switchGlobalRankingType('shop'); // 确保页面加载时默认显示店铺排行"

# 执行替换
new_content = re.sub(pattern, replacement, content)

# 写回文件
with open('整体月报数据.py', 'w') as f:
    f.write(new_content)

print("文件已更新")
