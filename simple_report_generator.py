#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的月报生成器
重写逻辑，生成更简单可靠的HTML报告
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os

def generate_simple_report():
    """生成简化的月报"""
    
    # 读取数据
    print("正在读取数据...")
    df = pd.read_csv('/Users/weixiaogang/AI/wecomchan/销售数据.csv')
    
    # 数据预处理
    df['日期'] = pd.to_datetime(df['日期'])
    df['销售额'] = pd.to_numeric(df['销售额'], errors='coerce').fillna(0)
    df['销量'] = pd.to_numeric(df['销量'], errors='coerce').fillna(0)
    
    # 计算日期范围
    today = datetime.now()
    current_month_start = datetime(today.year, today.month, 1)
    current_end = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 计算当前月份的天数
    current_days = (current_end - current_month_start).days + 1
    
    # 上月同期
    if today.month == 1:
        prev_month = 12
        prev_year = today.year - 1
    else:
        prev_month = today.month - 1
        prev_year = today.year
    
    prev_start = datetime(prev_year, prev_month, 1)
    prev_end = prev_start + timedelta(days=current_days - 1)
    
    print(f"本月累计: {current_month_start.strftime('%Y-%m-%d')} 到 {current_end.strftime('%Y-%m-%d')}")
    print(f"上月同期: {prev_start.strftime('%Y-%m-%d')} 到 {prev_end.strftime('%Y-%m-%d')}")
    
    # 筛选数据
    current_data = df[(df['日期'] >= current_month_start) & (df['日期'] <= current_end)]
    prev_data = df[(df['日期'] >= prev_start) & (df['日期'] <= prev_end)]
    
    # 按日期汇总
    current_daily = current_data.groupby('日期').agg({
        '销售额': 'sum',
        '销量': 'sum'
    }).reset_index()
    
    prev_daily = prev_data.groupby('日期').agg({
        '销售额': 'sum',
        '销量': 'sum'
    }).reset_index()
    
    # 计算总计
    current_total_amount = current_data['销售额'].sum()
    current_total_qty = current_data['销量'].sum()
    prev_total_amount = prev_data['销售额'].sum()
    prev_total_qty = prev_data['销量'].sum()
    
    # 计算增长率
    amount_growth = ((current_total_amount - prev_total_amount) / prev_total_amount * 100) if prev_total_amount > 0 else 0
    qty_growth = ((current_total_qty - prev_total_qty) / prev_total_qty * 100) if prev_total_qty > 0 else 0
    
    # 准备图表数据
    chart_data = []
    for _, row in current_daily.iterrows():
        chart_data.append({
            'date': row['日期'].strftime('%m-%d'),
            'amount': float(row['销售额']),
            'qty': int(row['销量'])
        })
    
    # 生成HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2025年{today.month}月销售月报</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 28px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-card .growth {{
            font-size: 14px;
            opacity: 0.8;
        }}
        .chart-container {{
            margin: 30px 0;
            text-align: center;
        }}
        canvas {{
            max-width: 100%;
            height: 400px;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>2025年{today.month}月销售月报</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>本月累计销售额</h3>
                <div class="value">¥{current_total_amount:,.0f}</div>
                <div class="growth {'positive' if amount_growth >= 0 else 'negative'}">
                    {'↗' if amount_growth >= 0 else '↘'} {amount_growth:+.1f}%
                </div>
            </div>
            <div class="summary-card">
                <h3>本月累计销量</h3>
                <div class="value">{current_total_qty:,.0f}件</div>
                <div class="growth {'positive' if qty_growth >= 0 else 'negative'}">
                    {'↗' if qty_growth >= 0 else '↘'} {qty_growth:+.1f}%
                </div>
            </div>
            <div class="summary-card">
                <h3>上月同期销售额</h3>
                <div class="value">¥{prev_total_amount:,.0f}</div>
                <div class="growth">对比基准</div>
            </div>
            <div class="summary-card">
                <h3>上月同期销量</h3>
                <div class="value">{prev_total_qty:,.0f}件</div>
                <div class="growth">对比基准</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>每日销售趋势</h2>
            <canvas id="salesChart"></canvas>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const chartData = {json.dumps(chart_data, ensure_ascii=False)};
        
        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('salesChart').getContext('2d');
            
            const dates = chartData.map(item => item.date);
            const amounts = chartData.map(item => item.amount);
            const quantities = chartData.map(item => item.qty);
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: dates,
                    datasets: [{{
                        label: '销售额 (¥)',
                        data: amounts,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y',
                        tension: 0.1
                    }}, {{
                        label: '销量 (件)',
                        data: quantities,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y1',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: '每日销售数据趋势图'
                        }},
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
                                text: '销量 (件)'
                            }},
                            grid: {{
                                drawOnChartArea: false
                            }}
                        }}
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    # 保存文件
    output_file = f'/Users/weixiaogang/AI/wecomchan/reports/simple_report_{today.strftime("%Y%m")}.html'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"简化报告已生成: {output_file}")
    return output_file

if __name__ == '__main__':
    generate_simple_report()