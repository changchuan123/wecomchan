#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单趋势图测试脚本
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """创建测试数据"""
    # 创建测试数据
    dates = pd.date_range(start='2025-08-01', end='2025-08-05', freq='D')
    test_data = []
    
    for date in dates:
        # 模拟销售数据
        amount = 10000 + (date.day * 500) + (date.day % 7 * 1000)  # 模拟波动
        qty = 50 + (date.day * 2) + (date.day % 5 * 10)
        
        test_data.append({
            '交易时间': date,
            '分摊后总价': amount,
            '实发数量': qty,
            '品类': '冰箱',
            '店铺': '测试店铺',
            '规格名称': '测试单品',
            '数据来源': '正常'
        })
    
    return pd.DataFrame(test_data)

def test_trend_chart():
    """测试趋势图生成"""
    print("🧪 开始测试趋势图修复效果...")
    
    # 创建测试数据
    df_test = create_test_data()
    print(f"📊 测试数据行数: {len(df_test)}")
    
    # 测试参数
    amount_col = '分摊后总价'
    qty_col = '实发数量'
    CATEGORY_COL = '品类'
    SHOP_COL = '店铺'
    MODEL_COL = '规格名称'
    category_icons = {'冰箱': '❄️'}
    
    try:
        # 导入趋势图函数
        from 整体月报数据 import generate_sales_trend_chart_html
        
        # 生成趋势图HTML
        print("🔧 正在生成趋势图HTML...")
        html = generate_sales_trend_chart_html(
            df_test, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons
        )
        
        # 保存测试结果
        test_filename = 'simple_trend_test_result.html'
        with open(test_filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 趋势图HTML已生成并保存到: {test_filename}")
        print(f"📏 HTML长度: {len(html)} 字符")
        
        # 检查关键元素
        if 'salesTrendChart' in html:
            print("✅ 图表容器ID存在")
        else:
            print("❌ 图表容器ID缺失")
            
        if 'Chart.js' in html:
            print("✅ Chart.js库引用存在")
        else:
            print("❌ Chart.js库引用缺失")
            
        if 'initTrendChart' in html:
            print("✅ 图表初始化函数存在")
        else:
            print("❌ 图表初始化函数缺失")
            
        if 'categoryFilter' in html and 'shopFilter' in html and 'productFilter' in html:
            print("✅ 筛选控件存在")
        else:
            print("❌ 筛选控件缺失")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trend_chart()
    if success:
        print("\n🎉 趋势图修复测试通过！")
        print("📋 请打开 simple_trend_test_result.html 查看效果")
    else:
        print("\n💥 趋势图修复测试失败！") 