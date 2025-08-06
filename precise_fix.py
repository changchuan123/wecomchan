#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确的修复脚本
"""

def precise_fix():
    """精确修复f-string中的大括号问题"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复第1931行附近的问题
    # 将JavaScript代码从f-string中提取出来
    
    # 找到包含JavaScript的f-string并替换
    old_js_block = '''                }}
            }
        };
        
        // 初始化图表
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
    
    new_js_block = '''                }}
            }}
        }};
        
        // 初始化图表
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
    
    content = content.replace(old_js_block, new_js_block)
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 精确修复完成")

if __name__ == "__main__":
    precise_fix() 