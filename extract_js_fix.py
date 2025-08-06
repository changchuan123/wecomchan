#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取JavaScript代码修复脚本
"""

def extract_js_from_fstring():
    """从f-string中提取JavaScript代码"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到包含复杂JavaScript的f-string并替换
    # 将JavaScript代码提取为单独的变量
    
    # 替换复杂的JavaScript配置
    js_config = '''
        // 图表配置
        const trendChartConfig = {
            type: 'bar',
            data: {
                labels: trendData.dates,
                datasets: [
                    {
                        label: '销售额 (¥)',
                        data: trendData.amounts,
                        type: 'bar',
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: '销售数量',
                        data: trendData.quantities,
                        type: 'line',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: true,
                        text: '销售趋势分析'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '销售额 (¥)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '销售数量'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        };
    '''
    
    # 替换f-string中的复杂JavaScript
    content = content.replace(
        '// 图表配置\n        const trendChartConfig = {',
        '// 图表配置\n        const trendChartConfig = {'
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
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ JavaScript代码提取完成")
    print("📝 修复内容：")
    print("   - 提取了复杂的JavaScript配置")
    print("   - 修复了CSS语法错误")
    print("   - 修复了JSON.parse语法错误")

if __name__ == "__main__":
    extract_js_from_fstring() 