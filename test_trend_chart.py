#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试趋势图功能
"""

import pandas as pd
from datetime import datetime, timedelta
import json

# 创建测试数据
def create_test_data():
    """创建测试数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    data = []
    
    for date in dates:
        data.append({
            '交易时间': date,
            '销售额': 1000 + (date.day * 100),
            '数量': 10 + date.day,
            '品类': '测试品类',
            '店铺': '测试店铺',
            '单品': '测试单品'
        })
    
    return pd.DataFrame(data)

def test_trend_chart():
    """测试趋势图生成"""
    # 创建测试数据
    df = create_test_data()
    
    # 模拟趋势图HTML生成
    html_template = '''
    <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
        <h3 style="margin-bottom: 15px; color: #333;">📈 销售趋势图</h3>
        <div style="position: relative; height: 400px; margin-bottom: 20px;">
            <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    // 销售趋势图数据
    const trendData = {
        dates: ['2024-01-01', '2024-01-02', '2024-01-03'],
        amounts: [1100, 1200, 1300],
        quantities: [11, 12, 13]
    };
    
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
    
    // 初始化图表
    let salesTrendChart;
    
    function initTrendChart() {
        const trendCtx = document.getElementById('salesTrendChart');
        if (trendCtx) {
            salesTrendChart = new Chart(trendCtx, trendChartConfig);
        }
    }
    
    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(initTrendChart, 100);
    });
    </script>
    '''
    
    # 保存测试HTML文件
    with open('test_trend_chart.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ 测试趋势图HTML生成成功")
    print("📁 测试文件已保存: test_trend_chart.html")
    print("🌐 请在浏览器中打开 test_trend_chart.html 查看趋势图")

if __name__ == "__main__":
    test_trend_chart() 