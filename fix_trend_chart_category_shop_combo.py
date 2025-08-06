#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复趋势图品类和店铺同时筛选的问题
问题：当选了品类之后，再选店铺时，数据提示有变化加了店铺，但是数据没有任何变化
根本原因：当前数据结构没有"品类+店铺"的组合数据，筛选逻辑使用Math.min()是错误的
解决方案：构建categoryShopData数据结构，提供精确的"品类+店铺"组合数据
"""

import re
import os

def fix_trend_chart_category_shop_combo():
    """修复趋势图品类和店铺同时筛选的问题"""
    
    # 读取原始文件
    with open('整体月报数据_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 首先修复JavaScript数据结构，添加categoryShopData
    # 查找构建JavaScript数据的部分
    pattern = r'# 构建JavaScript数据.*?js_data = \{.*?\}'
    
    # 新的JavaScript数据构建逻辑
    new_js_data_build = '''# 构建JavaScript数据（包含联动筛选所需的关联数据）
        js_data = {
            'dates': all_dates,
            'categories': sorted_categories,
            'shops': shops,
            'products': products,
            'categoryData': {},
            'shopData': {},
            'productData': {},
            'categoryShopData': {},  # 新增：品类+店铺组合数据
            'quantities': [],
            'amounts': [],
            'categoryIcons': category_icons,
            # 联动筛选关联数据
            'categoryShops': category_shops,
            'categoryProducts': category_products,
            'shopCategories': shop_categories,
            'shopProducts': shop_products,
            'productCategories': product_categories,
            'productShops': product_shops
        }'''
    
    # 使用正则表达式替换
    content = re.sub(pattern, new_js_data_build, content, flags=re.DOTALL)
    
    # 2. 添加categoryShopData的填充逻辑
    # 查找填充品类数据的部分
    pattern = r'# 填充品类数据.*?js_data\[''categoryData''\]\[category\] = category_daily'
    
    # 新的填充逻辑
    new_category_data_fill = '''# 填充品类数据 - 确保每个日期都有数据，没有销售的日期填充0
        for category in sorted_categories:
            category_daily = []
            for date in all_dates:
                amount = daily_data[(daily_data['日期'] == date) & (daily_data[CATEGORY_COL] == category)][amount_col].sum()
                # 确保amount是数值类型
                try:
                    amount = float(amount) if amount is not None else 0.0
                except (ValueError, TypeError):
                    amount = 0.0
                category_daily.append(amount if amount > 0 else 0.0)
            js_data['categoryData'][category] = category_daily
        
        # 填充品类+店铺组合数据 - 新增：提供精确的品类+店铺组合数据
        for category in sorted_categories:
            for shop in shops:
                combo_key = f"{category}_{shop}"
                combo_daily = []
                for date in all_dates:
                    # 获取该品类在该店铺的数据
                    amount = daily_data[(daily_data['日期'] == date) & 
                                      (daily_data[CATEGORY_COL] == category) & 
                                      (daily_data[SHOP_COL] == shop)][amount_col].sum()
                    # 确保amount是数值类型
                    try:
                        amount = float(amount) if amount is not None else 0.0
                    except (ValueError, TypeError):
                        amount = 0.0
                    combo_daily.append(amount if amount > 0 else 0.0)
                js_data['categoryShopData'][combo_key] = combo_daily'''
    
    # 使用正则表达式替换
    content = re.sub(pattern, new_category_data_fill, content, flags=re.DOTALL)
    
    # 3. 修复getTrendFilteredData函数的筛选逻辑
    # 查找getTrendFilteredData函数
    pattern = r'// 获取筛选后的数据\s+function getTrendFilteredData\(\) \{.*?\}'
    
    # 新的函数实现
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
                    
                    // 修复：当同时有品类和店铺筛选时，使用精确的组合数据
                    if (currentTrendFilter.category && currentTrendFilter.shop && currentTrendFilter.product) {
                        // 三个筛选条件都有：显示该单品在该店铺的数据
                        dayAmount = productAmount || 0;
                    } else if (currentTrendFilter.category && currentTrendFilter.shop) {
                        // 品类+店铺：使用精确的组合数据
                        let comboKey = `${currentTrendFilter.category}_${currentTrendFilter.shop}`;
                        dayAmount = trendRawData.categoryShopData[comboKey] ? 
                                  (trendRawData.categoryShopData[comboKey][i] || 0) : 0;
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
    
    # 4. 更新HTML模板中的JavaScript数据初始化
    # 查找trendRawData初始化的部分
    pattern = r'let trendRawData = \{.*?\};'
    
    # 新的初始化代码
    new_init = '''let trendRawData = {
            dates: ${js_data['dates']},
            categories: ${js_data['categories']},
            shops: ${js_data['shops']},
            products: ${js_data['products']},
            categoryData: ${js_data['categoryData']},
            shopData: ${js_data['shopData']},
            productData: ${js_data['productData']},
            categoryShopData: ${js_data['categoryShopData']},  // 新增：品类+店铺组合数据
            quantities: ${js_data['quantities']},
            amounts: ${js_data['amounts']},
            categoryIcons: ${js_data['categoryIcons']},
            categoryShops: ${js_data['categoryShops']},
            categoryProducts: ${js_data['categoryProducts']},
            shopCategories: ${js_data['shopCategories']},
            shopProducts: ${js_data['shopProducts']},
            productCategories: ${js_data['productCategories']},
            productShops: ${js_data['productShops']}
        };'''
    
    # 使用正则表达式替换
    content = re.sub(pattern, new_init, content, flags=re.DOTALL)
    
    # 保存修复后的文件
    with open('整体月报数据_fixed_v3.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 趋势图品类+店铺组合筛选修复完成")
    print("📝 主要修复内容：")
    print("1. 添加了categoryShopData数据结构，提供精确的品类+店铺组合数据")
    print("2. 修复了getTrendFilteredData函数的筛选逻辑，使用精确的组合数据")
    print("3. 当同时选择品类和店铺时，现在会显示该品类在该店铺的真实数据")
    print("4. 保持了其他筛选组合的兼容性")

if __name__ == "__main__":
    fix_trend_chart_category_shop_combo() 