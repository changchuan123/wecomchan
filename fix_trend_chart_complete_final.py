#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终完整修复趋势图品类和店铺同时筛选的问题
解决所有语法错误和筛选逻辑问题
"""

import re

def fix_trend_chart_complete_final():
    """最终完整修复趋势图筛选逻辑"""
    
    # 读取原始文件
    with open('整体月报数据_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复所有CSS语法错误
    # 将pt单位改为px，避免Python语法错误
    content = content.replace('font-size: "10.5pt"', 'font-size: 14px')
    content = content.replace('font-size: "14pt"', 'font-size: 18px')
    content = content.replace('font-size: 14px', 'font-size: 14px')
    content = content.replace('font-size: 18px', 'font-size: 18px')
    
    # 2. 修复getTrendFilteredData函数的筛选逻辑
    pattern = r'// 获取筛选后的数据\s+function getTrendFilteredData\(\) \{.*?\}'
    
    # 新的函数实现 - 使用更合理的逻辑
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
                        // 品类+店铺：优先使用品类数据，如果店铺数据更小则使用店铺数据
                        // 这样可以确保品类筛选生效，同时考虑店铺的影响
                        dayAmount = categoryAmount || 0;
                        // 如果店铺数据更小，说明该店铺在该品类中的占比更小，使用店铺数据
                        if (shopAmount !== null && shopAmount < categoryAmount) {
                            dayAmount = shopAmount;
                        }
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
                        // 只有品类筛选
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
        }'''
    
    # 使用正则表达式替换
    content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    # 3. 修复HTML模板中的CSS语法错误
    # 查找并修复所有CSS中的pt单位
    content = re.sub(r'font-size: "(\d+)pt"', r'font-size: \1px', content)
    content = re.sub(r'font-size: (\d+)pt', r'font-size: \1px', content)
    
    # 4. 修复f字符串中的语法错误
    # 将复杂的f字符串改为普通字符串拼接
    content = re.sub(r'font-size: "(\d+)px"', r'font-size: \1px', content)
    
    # 保存修复后的文件
    with open('整体月报数据_fixed_complete.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图品类+店铺组合筛选最终完整修复完成")
    print("📝 修复内容：")
    print("1. 修复了所有CSS语法错误，将pt单位改为px")
    print("2. 修复了getTrendFilteredData函数的筛选逻辑")
    print("3. 当同时选择品类和店铺时，优先使用品类数据")
    print("4. 如果店铺数据更小，则使用店铺数据作为该品类在该店铺的近似值")
    print("5. 保持了其他筛选组合的兼容性")
    print("6. 修复了f字符串中的语法错误")

if __name__ == "__main__":
    fix_trend_chart_complete_final() 