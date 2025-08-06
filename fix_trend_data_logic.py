#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势图数据逻辑修复脚本
修复整体月报数据.py中的趋势图相关问题和筛选逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

def normalize_date_format(date_str):
    """
    增强的日期格式处理函数
    支持多种日期格式的标准化
    """
    if pd.isna(date_str) or date_str is None:
        return pd.NaT
    
    try:
        # 如果是datetime对象，直接返回
        if isinstance(date_str, (datetime, pd.Timestamp)):
            return pd.Timestamp(date_str)
        
        # 转换为字符串
        date_str = str(date_str).strip()
        
        # 处理空字符串
        if not date_str or date_str == '' or date_str.lower() in ['nan', 'none', 'null']:
            return pd.NaT
        
        # 尝试多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y.%m.%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%Y.%m.%d %H:%M',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y年%m月%d日',
            '%Y年%m月%d日 %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except (ValueError, TypeError):
                continue
        
        # 如果所有格式都失败，尝试pandas的自动解析
        try:
            return pd.to_datetime(date_str)
        except (ValueError, TypeError):
            print(f"⚠️ 无法解析日期格式: {date_str}")
            return pd.NaT
            
    except Exception as e:
        print(f"⚠️ 日期处理异常: {date_str}, 错误: {e}")
        return pd.NaT

def get_trend_data_with_filters_enhanced(df_erp, start_date, end_date, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL):
    """
    增强版趋势图数据获取函数
    修复了日期处理、数据筛选和京东分销汇总逻辑
    """
    try:
        # 数据预处理
        df_copy = df_erp.copy()
        
        # 增强的日期格式处理
        print(f"📊 开始处理日期格式，原始数据行数: {len(df_copy)}")
        
        # 检查交易时间列的原始格式
        sample_dates = df_copy['交易时间'].head(10).tolist()
        print(f"📊 日期格式样本: {sample_dates}")
        
        # 使用增强的日期格式处理函数
        df_copy['交易时间'] = df_copy['交易时间'].apply(normalize_date_format)
        
        # 统计处理结果
        valid_dates = df_copy['交易时间'].notna().sum()
        total_dates = len(df_copy)
        print(f"📊 日期格式处理结果: 有效日期 {valid_dates}/{total_dates}")
        
        # 移除无效日期的行
        df_copy = df_copy.dropna(subset=['交易时间'])
        print(f"📊 移除无效日期后数据行数: {len(df_copy)}")
        
        if df_copy.empty:
            print("❌ 警告：所有日期数据都无效，无法生成趋势图")
            return pd.DataFrame()
        
        # 转换为datetime类型
        df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'])
        
        # 显示日期范围
        min_date = df_copy['交易时间'].min()
        max_date = df_copy['交易时间'].max()
        print(f"📊 数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
        
        # 筛选日期范围
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        print(f"📊 筛选日期范围: {start_datetime.strftime('%Y-%m-%d')} 至 {end_datetime.strftime('%Y-%m-%d')}")
        
        df_filtered = df_copy[(df_copy['交易时间'] >= start_datetime) & (df_copy['交易时间'] <= end_datetime)].copy()
        
        print(f"📊 趋势图数据筛选: {start_date} 至 {end_date}, 共{len(df_filtered)}行")
        
        # 显示筛选后的日期分布
        if not df_filtered.empty:
            filtered_dates = df_filtered['交易时间'].dt.strftime('%Y-%m-%d').value_counts().sort_index()
            print(f"📊 筛选后日期分布 (前10个):")
            for date, count in filtered_dates.head(10).items():
                print(f"   {date}: {count}条记录")
        
        # 京东分销数据汇总处理
        jingdong_data = df_filtered[df_filtered['店铺'].str.contains('京东', na=False)]
        if not jingdong_data.empty:
            print(f"📊 京东分销数据: {len(jingdong_data)}行")
            # 对京东数据进行汇总
            jingdong_summary = jingdong_data.groupby(['交易时间', CATEGORY_COL]).agg({
                amount_col: 'sum',
                qty_col: 'sum'
            }).reset_index()
            jingdong_summary['店铺'] = '京东分销汇总'
            jingdong_summary[SHOP_COL] = '京东分销汇总'
            
            # 将汇总数据添加到原数据中
            df_filtered = pd.concat([df_filtered, jingdong_summary], ignore_index=True)
            print(f"📊 添加京东汇总后总行数: {len(df_filtered)}")
        
        return df_filtered
        
    except Exception as e:
        print(f"❌ 趋势图数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def generate_sales_trend_chart_html_enhanced(df_erp, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons):
    """
    增强版销售趋势图HTML生成函数
    修复了日期处理、数据筛选和图表生成逻辑
    """
    try:
        # 数据预处理 - 确保df_copy被正确定义
        df_copy = df_erp.copy()
        if df_copy is None or df_copy.empty:
            print("❌ 警告：输入数据为空，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无销售数据</div>'
        
        # 增强的日期格式处理
        print(f"📊 开始处理销售趋势图日期格式，原始数据行数: {len(df_copy)}")
        
        # 检查原始日期格式
        sample_dates = df_copy['交易时间'].head(10).tolist()
        print(f"📊 原始日期格式样本: {sample_dates}")
        
        # 使用增强的日期格式处理函数
        df_copy['交易时间'] = df_copy['交易时间'].apply(normalize_date_format)
        
        # 统计处理结果
        valid_dates = df_copy['交易时间'].notna().sum()
        total_dates = len(df_copy)
        print(f"📊 日期格式处理结果: 有效日期 {valid_dates}/{total_dates}")
        
        # 移除无效日期的行
        df_copy = df_copy.dropna(subset=['交易时间'])
        print(f"📊 移除无效日期后数据行数: {len(df_copy)}")
        
        if df_copy.empty:
            print("❌ 警告：所有日期数据都无效，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无有效的销售数据</div>'
        
        # 确保日期列是datetime类型后再使用.dt访问器
        if not pd.api.types.is_datetime64_any_dtype(df_copy['交易时间']):
            df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
            df_copy = df_copy.dropna(subset=['交易时间'])
        
        # 显示处理后的日期范围
        min_data_date = df_copy['交易时间'].min()
        max_data_date = df_copy['交易时间'].max()
        print(f"📊 处理后数据日期范围: {min_data_date.strftime('%Y-%m-%d')} 至 {max_data_date.strftime('%Y-%m-%d')}")
        
        # 修改：使用与月报相同的逻辑，从当月1号开始取数
        today = datetime.now()
        yesterday = today - timedelta(days=1)  # T-1天
        
        # 基于T-1天获取所在月份的整月数据
        target_month_start = yesterday.replace(day=1)
        # 获取T-1天所在月份的最后一天
        if yesterday.month == 12:
            next_month = yesterday.replace(year=yesterday.year + 1, month=1, day=1)
        else:
            next_month = yesterday.replace(month=yesterday.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
        
        start_date = target_month_start
        end_date = yesterday  # 截止到T-1天
        
        print(f"📊 使用当月累计数据: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
            
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"📊 销售趋势图数据范围: {start_date_str} 至 {end_date_str}")
        
        # 筛选日期范围 - 使用更精确的日期范围筛选
        start_datetime = pd.to_datetime(start_date_str)
        end_datetime = pd.to_datetime(end_date_str) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # 包含整个结束日期
        
        print(f"📊 筛选日期范围: {start_datetime.strftime('%Y-%m-%d')} 至 {end_datetime.strftime('%Y-%m-%d')}")
        
        df_month_data = df_copy[(df_copy['交易时间'] >= start_datetime) & (df_copy['交易时间'] <= end_datetime)].copy()
        
        print(f"📊 筛选后数据行数: {len(df_month_data)}")
        
        if df_month_data.empty:
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无当月销售数据</div>'
        
        # 显示筛选后的日期分布
        filtered_dates = df_month_data['交易时间'].dt.strftime('%Y-%m-%d').value_counts().sort_index()
        print(f"📊 筛选后日期分布 (前10个):")
        for date, count in filtered_dates.head(10).items():
            print(f"   {date}: {count}条记录")
        
        df_month_data['日期'] = df_month_data['交易时间'].dt.strftime('%Y-%m-%d')
        
        # 按日期、品类、店铺、单品聚合数据
        daily_data = df_month_data.groupby(['日期', CATEGORY_COL, SHOP_COL, MODEL_COL]).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        
        # 添加调试信息，检查BCD-501WLHTD58B9U1的数据
        bcd_data = df_month_data[df_month_data[MODEL_COL] == 'BCD-501WLHTD58B9U1']
        if not bcd_data.empty:
            print(f"🔍 BCD-501WLHTD58B9U1 原始数据检查:")
            print(f"   总记录数: {len(bcd_data)}")
            print(f"   日期分布:")
            date_counts = bcd_data['日期'].value_counts().sort_index()
            for date, count in date_counts.items():
                print(f"     {date}: {count}条记录")
            print(f"   总数量: {bcd_data[qty_col].sum()}")
            print(f"   总金额: {bcd_data[amount_col].sum()}")
        
        # 检查聚合后的数据
        bcd_agg_data = daily_data[daily_data[MODEL_COL] == 'BCD-501WLHTD58B9U1']
        if not bcd_agg_data.empty:
            print(f"🔍 BCD-501WLHTD58B9U1 聚合后数据检查:")
            for _, row in bcd_agg_data.iterrows():
                print(f"   {row['日期']} - {row[SHOP_COL]}: {row[qty_col]}件, ¥{row[amount_col]}")
        
        # 获取所有日期范围（从当月1号到T-1天）
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        all_dates = [d.strftime('%Y-%m-%d') for d in date_range]
        
        print(f"📊 趋势图日期范围: {all_dates[0]} 至 {all_dates[-1]}, 共{len(all_dates)}天")
        
        # 获取品类、店铺、单品列表
        # 按品类当月总销售额排序，只取TOP10
        category_totals = daily_data.groupby(CATEGORY_COL)[amount_col].sum().sort_values(ascending=False)
        sorted_categories = category_totals.head(10).index.tolist()
        
        # 按店铺当月总销售额排序，只取TOP20
        shop_totals = daily_data.groupby(SHOP_COL)[amount_col].sum().sort_values(ascending=False)
        sorted_shops = shop_totals.head(20).index.tolist()
        
        # 按单品当月总销售额排序，显示所有单品（移除TOP30限制）
        product_totals = daily_data.groupby(MODEL_COL)[amount_col].sum().sort_values(ascending=False)
        sorted_products = product_totals.index.tolist()  # 移除.head(30)限制，显示所有单品
        
        # 为HTML模板定义变量（解决NameError）
        shops = sorted_shops
        products = sorted_products
        
        # 生成HTML选项变量
        category_options = '\n'.join([f'<option value="{cat}">{category_icons.get(cat, "📦")} {cat}</option>' for cat in sorted_categories])
        shop_options = '\n'.join([f'<option value="{shop}">{shop}</option>' for shop in shops])
        product_options = '\n'.join([f'<option value="{product}">{product}</option>' for product in products])
        
        # 生成颜色
        def generate_colors(count):
            """生成颜色数组"""
            colors = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
                '#A9CCE3', '#F9E79F', '#D5A6BD', '#A3E4D7', '#FAD7A0'
            ]
            return colors[:count] + [colors[i % len(colors)] for i in range(count - len(colors))]
        
        # 生成完整的HTML
        html = f'''
        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px; color: #333;">📈 销售趋势分析</h3>
            
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
            <div style="position: relative; height: 500px; margin-bottom: 20px;">
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
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">品类</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">店铺</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">单品</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">数量</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">金额</th>
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
            dates: {all_dates},
            dailyData: {daily_data.to_dict('records')},
            categories: {sorted_categories},
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
                
                // 筛选数据
                let filteredData = trendData.dailyData;
                if (selectedCategory) {{
                    filteredData = filteredData.filter(item => item['{CATEGORY_COL}'] === selectedCategory);
                }}
                if (selectedShop) {{
                    filteredData = filteredData.filter(item => item['{SHOP_COL}'] === selectedShop);
                }}
                if (selectedProduct) {{
                    filteredData = filteredData.filter(item => item['{MODEL_COL}'] === selectedProduct);
                }}
                
                // 按日期聚合数据
                const dateGroups = {{}};
                filteredData.forEach(item => {{
                    const date = item['日期'];
                    if (!dateGroups[date]) {{
                        dateGroups[date] = {{ amounts: [], quantities: [] }};
                    }}
                    dateGroups[date].amounts.push(item['{amount_col}']);
                    dateGroups[date].quantities.push(item['{qty_col}']);
                }});
                
                // 准备图表数据
                const chartDates = trendData.dates.filter(date => dateGroups[date]);
                const chartAmounts = chartDates.map(date => dateGroups[date].amounts.reduce((a, b) => a + b, 0));
                const chartQuantities = chartDates.map(date => dateGroups[date].quantities.reduce((a, b) => a + b, 0));
                
                // 更新数据表格
                updateDataTable(filteredData);
                
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
        
        function updateDataTable(data) {{
            const tbody = document.getElementById('trendDataTableBody');
            tbody.innerHTML = '';
            
            data.forEach(item => {{
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{item['日期']}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{item['{CATEGORY_COL}']}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{item['{SHOP_COL}']}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{item['{MODEL_COL}']}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{item['{qty_col}']}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">¥${{item['{amount_col}'].toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</td>
                `;
                tbody.appendChild(row);
            }});
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
        return f'<div style="color: #d32f2f; text-align: center; padding: 20px;">❌ 趋势图生成失败: {str(e)}</div>'

def apply_fixes_to_main_file():
    """
    将修复应用到主文件
    """
    try:
        print("🔧 开始应用趋势图数据逻辑修复...")
        
        # 读取主文件
        with open('整体月报数据.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换get_trend_data_with_filters函数
        old_function_start = content.find('def get_trend_data_with_filters(df_erp, start_date, end_date, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL):')
        if old_function_start != -1:
            # 找到函数结束位置
            old_function_end = content.find('\n\n', old_function_start)
            if old_function_end == -1:
                old_function_end = len(content)
            
            # 获取新的函数内容
            new_function = get_trend_data_with_filters_enhanced.__code__.co_consts[0]
            
            # 替换函数
            content = content[:old_function_start] + new_function + content[old_function_end:]
            print("✅ 已替换 get_trend_data_with_filters 函数")
        
        # 替换generate_sales_trend_chart_html函数
        old_trend_function_start = content.find('def generate_sales_trend_chart_html(df_erp, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons):')
        if old_trend_function_start != -1:
            # 找到函数结束位置
            old_trend_function_end = content.find('\n\n', old_trend_function_start)
            if old_trend_function_end == -1:
                old_trend_function_end = len(content)
            
            # 获取新的函数内容
            new_trend_function = generate_sales_trend_chart_html_enhanced.__code__.co_consts[0]
            
            # 替换函数
            content = content[:old_trend_function_start] + new_trend_function + content[old_trend_function_end:]
            print("✅ 已替换 generate_sales_trend_chart_html 函数")
        
        # 写回文件
        with open('整体月报数据.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 趋势图数据逻辑修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复应用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 趋势图数据逻辑修复脚本")
    print("=" * 50)
    
    # 这里可以添加测试代码
    print("✅ 修复函数已定义，可以应用到主文件中") 