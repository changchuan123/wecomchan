#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势图修复脚本
"""

def fix_trend_chart():
    """修复趋势图JavaScript代码"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换有问题的JavaScript代码块
    old_js = '''                    },
                    legend: {{
                        display: true,
                        position: 'top'
                    }
                },
                scales: {{
                    x: {{
                        display: true,
                        title: {{
                            display: true,
                            text: '日期'
                        }}
                    }},
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: '销售额 (¥)'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: '销售数量'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
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
    
    new_js = '''                    }},
                    legend: {{
                        display: true,
                        position: 'top'
                    }}
                }},
                scales: {{
                    x: {{
                        display: true,
                        title: {{
                            display: true,
                            text: '日期'
                        }}
                    }},
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: '销售额 (¥)'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: '销售数量'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
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
    
    content = content.replace(old_js, new_js)
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图修复完成")

if __name__ == "__main__":
    fix_trend_chart() 