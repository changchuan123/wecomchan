#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 直接修复format调用中的问题
with open('整体月报数据.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找format调用并修复
import re

# 找到format调用的位置
format_pattern = r'return chart_html\.format\(([^)]+)\)'
match = re.search(format_pattern, content)

if match:
    print("找到format调用，正在修复...")
    
    # 替换为简单的字符串拼接
    new_format = '''return chart_html.replace('{categories}', categories).replace('{shops}', shops).replace('{products}', products).replace('{DATE_COL}', DATE_COL).replace('{CATEGORY_COL}', CATEGORY_COL).replace('{AMOUNT_COL}', AMOUNT_COL).replace('{QTY_COL}', QTY_COL).replace('{SHOP_COL}', SHOP_COL).replace('{MODEL_COL}', MODEL_COL).replace('{dates_json}', json.dumps(dates)).replace('{amounts_json}', json.dumps(amounts)).replace('{quantities_json}', json.dumps(quantities)).replace('{categoryData}', json.dumps(category_data)).replace('{daily_category_sales_json}', json.dumps(convert_dataframe_to_serializable(daily_category_sales_str))).replace('{daily_shop_sales_json}', json.dumps(convert_dataframe_to_serializable(daily_shop_sales_str))).replace('{daily_product_sales_json}', json.dumps(convert_dataframe_to_serializable(daily_product_sales_str))).replace('{categories_json}', json.dumps(categories)).replace('{shops_json}', json.dumps(shops)).replace('{products_json}', json.dumps(products)).replace('{rawData}', json.dumps({'dates': dates, 'dailyCategorySales': convert_dataframe_to_serializable(daily_category_sales_str), 'dailyShopSales': convert_dataframe_to_serializable(daily_shop_sales_str), 'dailyProductSales': convert_dataframe_to_serializable(daily_product_sales_str), 'categories': categories, 'shops': shops, 'products': products, 'categoryData': category_data, 'quantities': quantities}))'''
    
    content = re.sub(format_pattern, new_format, content)
    
    with open('整体月报数据.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ format调用修复完成")
else:
    print("❌ 未找到format调用") 