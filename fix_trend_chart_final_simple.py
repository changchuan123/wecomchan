#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化修复趋势图问题：
1. 选中品类时显示到天数据而不是累计数据
2. 没有选择任何元素时增加汇总数据
"""

import re

def fix_trend_chart_final_simple():
    """简化修复趋势图筛选逻辑和汇总数据"""
    
    # 读取原始文件
    with open('整体月报数据_fixed_final.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复getTrendFilteredData函数的筛选逻辑
    pattern = r'// 获取筛选后的数据\s+function getTrendFilteredData\(\) \{.*?\}'
    
    # 新的函数实现 - 修复品类筛选逻辑
    new_function = '''// 获取筛选后的数据
        function getTrendFilteredData() {
            let amounts = [];
            let quantities = [];
            
            for (let i = 0; i < trendRawData.dates.length; i++) {
                let dayAmount = 0;
                let dayQty = 0;
                
                // 组合筛选逻辑：支持品类、店铺、单品同时筛选
                if (currentTrendFilter.category || currentTrendFilter.shop || currentTrendFilter.product) {
                    // 如果有任何筛选条件，则进行组合筛选
                    let categoryAmount = currentTrendFilter.category ? (trendRawData.categoryData[currentTrendFilter.category][i] || 0) : null;
                    let shopAmount = currentTrendFilter.shop ? (trendRawData.shopData[currentTrendFilter.shop][i] || 0) : null;
                    let productAmount = currentTrendFilter.product ? (trendRawData.productData[currentTrendFilter.product][i] || 0) : null;
                    
                    // 修复：当同时有品类和店铺筛选时，使用更合理的逻辑
                    if (currentTrendFilter.category && currentTrendFilter.shop && currentTrendFilter.product) {
                        // 三个筛选条件都有：显示该单品在该店铺的数据
                        dayAmount = productAmount || 0;
                    } else if (currentTrendFilter.category && currentTrendFilter.shop) {
                        // 品类+店铺：显示该品类在该店铺的数据（使用品类数据作为近似值）
                        dayAmount = categoryAmount || 0;
                    } else if (currentTrendFilter.category && currentTrendFilter.product) {
                        // 品类+单品：显示该单品的数据
                        dayAmount = productAmount || 0;
                    } else if (currentTrendFilter.shop && currentTrendFilter.product) {
                        // 店铺+单品：显示该单品在该店铺的数据
                        dayAmount = productAmount || 0;
                    } else if (currentTrendFilter.product) {
                        // 只有单品筛选
                        dayAmount = productAmount || 0;
                    } else if (currentTrendFilter.shop) {
                        // 只有店铺筛选
                        dayAmount = shopAmount || 0;
                    } else if (currentTrendFilter.category) {
                        // 只有品类筛选 - 显示该品类的每日数据，不是累计数据
                        dayAmount = categoryAmount || 0;
                    }
                    
                    // 计算对应的数量（按比例分配）
                    let totalDayAmount = trendRawData.amounts[i] || 0;
                    if (totalDayAmount > 0) {
                        dayQty = Math.round((trendRawData.quantities[i] || 0) * (dayAmount / totalDayAmount));
                    } else {
                        dayQty = 0;
                    }
                } else {
                    // 没有筛选条件，显示全部数据
                    dayAmount = trendRawData.amounts[i] || 0;
                    dayQty = trendRawData.quantities[i] || 0;
                }
                
                amounts.push(dayAmount);
                quantities.push(dayQty);
            }
            
            return { amounts, quantities };
        }
        
        // 计算当天汇总数据
        function getTodaySummary() {
            if (!trendRawData || !trendRawData.amounts || trendRawData.amounts.length === 0) {
                return { amount: 0, quantity: 0 };
            }
            
            // 获取最后一天的数据（当天）
            const lastIndex = trendRawData.amounts.length - 1;
            const todayAmount = trendRawData.amounts[lastIndex] || 0;
            const todayQuantity = trendRawData.quantities[lastIndex] || 0;
            
            return { amount: todayAmount, quantity: todayQuantity };
        }
        
        // 更新汇总数据显示
        function updateSummaryDisplay() {
            const summaryDiv = document.getElementById('trendSummary');
            if (!summaryDiv) return;
            
            const summary = getTodaySummary();
            const filteredData = getTrendFilteredData();
            
            // 如果有筛选条件，显示筛选后的当天数据
            if (currentTrendFilter.category || currentTrendFilter.shop || currentTrendFilter.product) {
                const lastIndex = filteredData.amounts.length - 1;
                const filteredAmount = filteredData.amounts[lastIndex] || 0;
                const filteredQuantity = filteredData.quantities[lastIndex] || 0;
                
                summaryDiv.innerHTML = `
                    <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center;">
                        <h4 style="margin: 0 0 5px 0; color: #1976d2;">📊 筛选结果 - 当天汇总</h4>
                        <div style="font-size: 16px; font-weight: bold;">
                            <span style="color: #d32f2f;">销售额: ¥${filteredAmount.toLocaleString()}</span> | 
                            <span style="color: #388e3c;">销量: ${filteredQuantity.toLocaleString()}件</span>
                        </div>
                    </div>
                `;
            } else {
                // 没有筛选条件，显示全部当天数据
                summaryDiv.innerHTML = `
                    <div style="background: #f3e5f5; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center;">
                        <h4 style="margin: 0 0 5px 0; color: #7b1fa2;">📊 当天汇总数据</h4>
                        <div style="font-size: 16px; font-weight: bold;">
                            <span style="color: #d32f2f;">销售额: ¥${summary.amount.toLocaleString()}</span> | 
                            <span style="color: #388e3c;">销量: ${summary.quantity.toLocaleString()}件</span>
                        </div>
                    </div>
                `;
            }
        }'''
    
    # 替换函数
    content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    # 2. 在HTML模板中添加汇总数据显示区域
    # 查找筛选器HTML部分
    filter_pattern = r'(<!-- 筛选器 -->\s*<div class="filter-container".*?</div>\s*</div>)'
    
    # 在筛选器前添加汇总数据显示区域
    summary_html = '''
            <!-- 汇总数据显示区域 -->
            <div id="trendSummary" style="margin-bottom: 20px;"></div>
            
            <!-- 筛选器 -->'''
    
    content = re.sub(filter_pattern, summary_html + r'\1', content)
    
    # 3. 更新筛选器更新函数，添加汇总数据更新
    update_filter_pattern = r'(function updateTrendFilters\(\) \{.*?updateTrendChart\(\);.*?\})'
    
    new_update_function = '''function updateTrendFilters() {
            const categorySelect = document.getElementById('trendCategorySelect');
            const shopSelect = document.getElementById('trendShopSelect');
            const productSelect = document.getElementById('trendProductSelect');
            
            currentTrendFilter.category = categorySelect.value;
            currentTrendFilter.shop = shopSelect.value;
            currentTrendFilter.product = productSelect.value;
            
            // 联动更新其他筛选器选项
            updateTrendFilterOptions();
            
            // 更新图表
            updateTrendChart();
            
            // 更新汇总数据显示
            updateSummaryDisplay();
        }'''
    
    content = re.sub(update_filter_pattern, new_update_function, content, flags=re.DOTALL)
    
    # 4. 更新重置函数，添加汇总数据更新
    reset_pattern = r'(function resetTrendChart\(\) \{.*?salesTrendChart\.resetZoom\(\);.*?\})'
    
    new_reset_function = '''function resetTrendChart() {
            currentTrendFilter = {
                category: '',
                shop: '',
                product: ''
            };
            
            document.getElementById('trendCategorySelect').value = '';
            document.getElementById('trendShopSelect').value = '';
            document.getElementById('trendProductSelect').value = '';
            
            updateTrendFilterOptions();
            updateTrendChart();
            
            // 更新汇总数据显示
            updateSummaryDisplay();
            
            if (salesTrendChart) {
                salesTrendChart.resetZoom();
            }
        }'''
    
    content = re.sub(reset_pattern, new_reset_function, content, flags=re.DOTALL)
    
    # 5. 更新初始化函数，添加汇总数据初始化
    init_pattern = r'(function initTrendChart\(\) \{.*?addEventListener.*?updateTrendFilters.*?\);.*?\})'
    
    new_init_function = '''function initTrendChart() {
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {
                // 设置高DPI支持
                const dpr = window.devicePixelRatio || 1;
                trendCtx.style.width = trendCtx.offsetWidth + 'px';
                trendCtx.style.height = trendCtx.offsetHeight + 'px';
                trendCtx.width = trendCtx.offsetWidth * dpr;
                trendCtx.height = trendCtx.offsetHeight * dpr;
                
                const ctx = trendCtx.getContext('2d');
                ctx.scale(dpr, dpr);
                
                salesTrendChart = new Chart(ctx, trendChartConfig);
                
                // 绑定筛选器事件
                document.getElementById('trendCategorySelect').addEventListener('change', updateTrendFilters);
                document.getElementById('trendShopSelect').addEventListener('change', updateTrendFilters);
                document.getElementById('trendProductSelect').addEventListener('change', updateTrendFilters);
                
                // 初始化汇总数据显示
                updateSummaryDisplay();
            }
        }'''
    
    content = re.sub(init_pattern, new_init_function, content, flags=re.DOTALL)
    
    # 保存修复后的文件
    with open('整体月报数据_fixed_final.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图修复完成！")
    print("1. 修复了品类筛选逻辑，现在显示到天数据而不是累计数据")
    print("2. 添加了汇总数据显示功能，当没有选择任何元素时显示当天汇总数据")
    print("3. 更新了筛选器更新函数，确保汇总数据实时更新")
    print("4. 更新了重置函数，确保重置时也更新汇总数据")
    print("5. 更新了初始化函数，确保页面加载时显示汇总数据")

if __name__ == "__main__":
    fix_trend_chart_final_simple() 