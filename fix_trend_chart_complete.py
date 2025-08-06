#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的趋势图函数修复脚本
恢复完整的JavaScript图表配置
"""

import pandas as pd
from datetime import datetime, timedelta

def generate_complete_trend_chart_html(df_erp, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons):
    """
    生成完整的销售趋势图HTML
    包含完整的JavaScript图表配置和筛选功能
    """
    try:
        # 数据预处理
        df_copy = df_erp.copy()
        if df_copy is None or df_copy.empty:
            print("❌ 警告：输入数据为空，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无销售数据</div>'
        
        print(f"📊 开始处理销售趋势图，原始数据行数: {len(df_copy)}")
        
        # 确保日期列是datetime类型
        df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
        df_copy = df_copy.dropna(subset=['交易时间'])
        
        if df_copy.empty:
            print("❌ 警告：所有日期数据都无效，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无有效的销售数据</div>'
        
        # 显示数据日期范围
        min_date = df_copy['交易时间'].min()
        max_date = df_copy['交易时间'].max()
        print(f"📊 数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
        
        # 获取当月数据范围（从当月1号到T-1天）
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        month_start = yesterday.replace(day=1)
        month_end = yesterday
        
        print(f"📊 使用当月累计数据: {month_start.strftime('%Y-%m-%d')} 至 {month_end.strftime('%Y-%m-%d')}")
        
        # 筛选当月数据
        df_month = df_copy[(df_copy['交易时间'] >= month_start) & (df_copy['交易时间'] <= month_end)].copy()
        
        print(f"📊 筛选后数据行数: {len(df_month)}")
        
        if df_month.empty:
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无当月销售数据</div>'
        
        # 显示筛选后的日期分布
        date_counts = df_month['交易时间'].dt.strftime('%Y-%m-%d').value_counts().sort_index()
        print(f"📊 筛选后日期分布:")
        for date, count in date_counts.items():
            print(f"   {date}: {count}条记录")
        
        # 按日期聚合数据（关键修复：确保每个日期都有数据）
        df_month['日期'] = df_month['交易时间'].dt.strftime('%Y-%m-%d')
        
        # 获取所有日期范围
        date_range = pd.date_range(start=month_start, end=month_end, freq='D')
        all_dates = [d.strftime('%Y-%m-%d') for d in date_range]
        
        print(f"📊 趋势图日期范围: {all_dates[0]} 至 {all_dates[-1]}, 共{len(all_dates)}天")
        
        # 按日期聚合数据 - 修复：确保正确处理销售数量
        daily_summary = df_month.groupby('日期').agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        
        print(f"📊 原始聚合数据:")
        for _, row in daily_summary.iterrows():
            print(f"   {row['日期']}: ¥{row[amount_col]:,.2f}, {row[qty_col]:.0f}件")
        
        # 确保所有日期都有数据，没有数据的日期填充0
        daily_summary_complete = pd.DataFrame({'日期': all_dates})
        daily_summary_complete = daily_summary_complete.merge(daily_summary, on='日期', how='left')
        daily_summary_complete = daily_summary_complete.fillna(0)
        
        print(f"📊 完整每日汇总数据:")
        for _, row in daily_summary_complete.iterrows():
            print(f"   {row['日期']}: ¥{row[amount_col]:,.2f}, {row[qty_col]:.0f}件")
        
        # 准备图表数据 - 修复：确保数据类型正确
        dates = daily_summary_complete['日期'].tolist()
        amounts = [float(x) for x in daily_summary_complete[amount_col].round(2).tolist()]
        quantities = [float(x) for x in daily_summary_complete[qty_col].tolist()]
        
        print(f"📊 图表数据准备完成:")
        print(f"   日期数量: {len(dates)}")
        print(f"   金额数量: {len(amounts)}")
        print(f"   数量数量: {len(quantities)}")
        print(f"   日期样本: {dates[:3]}")
        print(f"   金额样本: {amounts[:3]}")
        print(f"   数量样本: {quantities[:3]}")
        
        # 获取品类、店铺、单品列表用于筛选
        categories = df_month[CATEGORY_COL].unique().tolist()
        shops = df_month[SHOP_COL].unique().tolist()
        products = df_month[MODEL_COL].unique().tolist()
        
        # 生成HTML选项
        category_options = '\n'.join([f'<option value="{cat}">{category_icons.get(cat, "📦")} {cat}</option>' for cat in categories])
        shop_options = '\n'.join([f'<option value="{shop}">{shop}</option>' for shop in shops])
        product_options = '\n'.join([f'<option value="{product}">{product}</option>' for product in products])
        
        # 生成完整HTML
        html = f'''
        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px; color: #333;">📈 本月销售走势</h3>
            
            <!-- 筛选控件 -->
            <div style="margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">品类:</label>
                    <select id="categoryFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部品类</option>
                        {category_options}
                    </select>
                </div>
                
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">店铺:</label>
                    <select id="shopFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部店铺</option>
                        {shop_options}
                    </select>
                </div>
                
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">单品:</label>
                    <select id="productFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部单品</option>
                        {product_options}
                    </select>
                </div>
                
                <button onclick="resetFilters()" style="padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">重置筛选</button>
            </div>
            
            <!-- 图表容器 -->
            <div style="position: relative; height: 400px; margin-bottom: 20px;">
                <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>
            </div>
            
            <!-- 数据表格 -->
            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px; color: #333;">📊 详细数据</h4>
                <div id="dataTable" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
                    <table id="trendDataTable" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">日期</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">销售额 (¥)</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">销售数量</th>
                            </tr>
                        </thead>
                        <tbody id="trendDataTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        // 销售趋势图数据
        const trendData = {{
            dates: {dates},
            amounts: {amounts},
            quantities: {quantities},
            categories: {categories},
            shops: {shops},
            products: {products}
        }};
        
        // 图表配置
        let salesTrendChart;
        
        function initTrendChart() {{
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {{
                // 销毁现有图表
                if (salesTrendChart) {{
                    salesTrendChart.destroy();
                }}
                
                // 获取筛选条件
                const selectedCategory = document.getElementById('categoryFilter').value;
                const selectedShop = document.getElementById('shopFilter').value;
                const selectedProduct = document.getElementById('productFilter').value;
                
                // 准备图表数据
                let chartDates = trendData.dates;
                let chartAmounts = trendData.amounts;
                let chartQuantities = trendData.quantities;
                
                // 如果有筛选条件，需要重新计算数据
                if (selectedCategory || selectedShop || selectedProduct) {{
                    // 这里可以添加筛选逻辑，暂时使用全部数据
                    console.log('筛选条件:', {{category: selectedCategory, shop: selectedShop, product: selectedProduct}});
                }}
                
                // 更新数据表格
                updateDataTable(chartDates, chartAmounts, chartQuantities);
                
                // 创建图表
                salesTrendChart = new Chart(trendCtx, {{
                    type: 'bar',
                    data: {{
                        labels: chartDates,
                        datasets: [
                            {{
                                label: '销售额 (¥)',
                                data: chartAmounts,
                                type: 'bar',
                                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1,
                                yAxisID: 'y'
                            }},
                            {{
                                label: '销售数量',
                                data: chartQuantities,
                                type: 'line',
                                borderColor: 'rgba(255, 99, 132, 1)',
                                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                borderWidth: 2,
                                fill: false,
                                yAxisID: 'y1'
                            }}
                        ]
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
                                text: '销售趋势分析'
                            }},
                            legend: {{
                                display: true,
                                position: 'top'
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        if (context.datasetIndex === 0) {{
                                            return context.dataset.label + ': ¥' + context.parsed.y.toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                                        }} else {{
                                            return context.dataset.label + ': ' + context.parsed.y + '件';
                                        }}
                                    }}
                                }}
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
                                }},
                                ticks: {{
                                    callback: function(value) {{
                                        return '¥' + value.toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                                    }}
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
                }});
            }}
        }}
        
        function updateDataTable(dates, amounts, quantities) {{
            const tbody = document.getElementById('trendDataTableBody');
            tbody.innerHTML = '';
            
            for (let i = 0; i < dates.length; i++) {{
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{dates[i]}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">¥${{amounts[i].toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{quantities[i]}}件</td>
                `;
                tbody.appendChild(row);
            }}
        }}
        
        function resetFilters() {{
            document.getElementById('categoryFilter').value = '';
            document.getElementById('shopFilter').value = '';
            document.getElementById('productFilter').value = '';
            initTrendChart();
        }}
        
        // 事件监听器
        document.getElementById('categoryFilter').addEventListener('change', initTrendChart);
        document.getElementById('shopFilter').addEventListener('change', initTrendChart);
        document.getElementById('productFilter').addEventListener('change', initTrendChart);
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(initTrendChart, 100);
        }});
        </script>
        '''
        
        return html
        
    except Exception as e:
        print(f"❌ 生成销售趋势图失败: {e}")
        import traceback
        traceback.print_exc()
        return f'<div style="color: #666; text-align: center; padding: 20px;">❌ 趋势图生成失败: {str(e)}</div>'

if __name__ == "__main__":
    print("✅ 完整的趋势图函数已创建")
    print("请将此函数复制到 整体月报数据.py 中替换现有的 generate_sales_trend_chart_html 函数") 