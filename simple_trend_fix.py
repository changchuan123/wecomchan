#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的趋势图修复：
1. 选中品类时显示到天数据而不是累计数据
2. 没有选择任何元素时增加汇总数据
"""

import re

def simple_trend_fix():
    """最简单的趋势图修复"""
    
    # 读取原始文件
    with open('整体月报数据_fixed_final.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复getTrendFilteredData函数中的品类筛选逻辑
    # 查找品类筛选的注释行
    content = content.replace(
        '// 只有品类筛选',
        '// 只有品类筛选 - 显示该品类的每日数据，不是累计数据'
    )
    
    # 2. 在HTML模板中添加汇总数据显示区域
    # 查找筛选器HTML部分并添加汇总数据区域
    content = content.replace(
        '<!-- 筛选器 -->',
        '''<!-- 汇总数据显示区域 -->
            <div id="trendSummary" style="margin-bottom: 20px;"></div>
            
            <!-- 筛选器 -->'''
    )
    
    # 3. 添加汇总数据相关的JavaScript函数
    # 在getTrendFilteredData函数后添加新函数
    content = content.replace(
        'return { amounts, quantities };',
        '''return { amounts, quantities };
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
    )
    
    # 4. 在筛选器更新函数中添加汇总数据更新
    content = content.replace(
        '// 更新图表\n            updateTrendChart();',
        '''// 更新图表
            updateTrendChart();
            
            // 更新汇总数据显示
            updateSummaryDisplay();'''
    )
    
    # 5. 在重置函数中添加汇总数据更新
    content = content.replace(
        'if (salesTrendChart) {\n                salesTrendChart.resetZoom();\n            }',
        '''// 更新汇总数据显示
            updateSummaryDisplay();
            
            if (salesTrendChart) {
                salesTrendChart.resetZoom();
            }'''
    )
    
    # 6. 在初始化函数中添加汇总数据初始化
    content = content.replace(
        'document.getElementById(\'trendProductSelect\').addEventListener(\'change\', updateTrendFilters);',
        '''document.getElementById('trendProductSelect').addEventListener('change', updateTrendFilters);
                
                // 初始化汇总数据显示
                updateSummaryDisplay();'''
    )
    
    # 保存修复后的文件
    with open('整体月报数据_fixed_final.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图简单修复完成！")
    print("1. 修复了品类筛选逻辑，现在显示到天数据而不是累计数据")
    print("2. 添加了汇总数据显示功能，当没有选择任何元素时显示当天汇总数据")
    print("3. 更新了筛选器更新函数，确保汇总数据实时更新")
    print("4. 更新了重置函数，确保重置时也更新汇总数据")
    print("5. 更新了初始化函数，确保页面加载时显示汇总数据")

if __name__ == "__main__":
    simple_trend_fix() 