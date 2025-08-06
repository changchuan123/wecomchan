#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的JavaScript修复脚本
"""

def simple_js_fix():
    """简单的JavaScript修复"""
    
    # 读取原文件
    with open('整体月报数据.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 将复杂的f-string替换为简单的字符串拼接
    # 找到包含复杂JavaScript的f-string并替换
    
    # 替换包含复杂JavaScript的f-string
    old_fstring = '''        // 图表配置
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
        };'''
    
    new_js = '''        // 图表配置
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
        };'''
    
    content = content.replace(old_fstring, new_js)
    
    # 修复CSS媒体查询
    content = content.replace(
        '@media (max-width: 600px) { body { padding: 0.5em; font-size: 10.5pt; } h1 { font-size: 14pt; } }',
        '@media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}'
    )
    
    # 写入修复后的文件
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 简单JavaScript修复完成")

if __name__ == "__main__":
    simple_js_fix() 