#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终解决方案
"""

def final_solution():
    """最终解决方案"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 将包含JavaScript的f-string替换为普通字符串
    # 找到包含JavaScript的f-string并替换
    
    # 替换包含JavaScript的f-string
    old_fstring = '''        // 初始化图表
        let salesTrendChart;
        
        function initTrendChart() {{
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {{
                salesTrendChart = new Chart(trendCtx, trendChartConfig);
            }}
        }}
        
        
    
    
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(initTrendChart, 100);
        }});
        </script>
        ''''''
    
    new_string = '''        // 初始化图表
        let salesTrendChart;
        
        function initTrendChart() {{
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {{
                salesTrendChart = new Chart(trendCtx, trendChartConfig);
            }}
        }}
        
        
    
    
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(initTrendChart, 100);
        }});
        </script>
        ''''''
    
    content = content.replace(old_fstring, new_string)
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 最终解决方案完成")

if __name__ == "__main__":
    final_solution() 