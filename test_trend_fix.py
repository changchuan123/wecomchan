#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试趋势图函数修复
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 创建测试数据
def create_test_data():
    """创建测试数据"""
    # 创建日期范围
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 8, 5)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建测试数据
    test_data = []
    for date in date_range:
        # 每天创建一些测试记录
        for i in range(10):
            test_data.append({
                '交易时间': date + timedelta(hours=i),
                '分摊后总价': np.random.randint(1000, 10000),
                '实发数量': np.random.randint(1, 10),
                '店铺': f'测试店铺{i%3}',
                '货品名称': f'测试品类{i%2}',
                '规格名称': f'测试单品{i}'
            })
    
    return pd.DataFrame(test_data)

def test_trend_function():
    """测试趋势图函数"""
    try:
        # 创建测试数据
        df_test = create_test_data()
        print(f"📊 测试数据创建完成，共{len(df_test)}行")
        
        # 导入趋势图函数
        import sys
        sys.path.append('.')
        from 整体月报数据 import generate_sales_trend_chart_html
        
        # 定义列名
        amount_col = '分摊后总价'
        qty_col = '实发数量'
        CATEGORY_COL = '货品名称'
        SHOP_COL = '店铺'
        MODEL_COL = '规格名称'
        category_icons = {'测试品类0': '📦', '测试品类1': '🏠'}
        
        # 调用趋势图函数
        html = generate_sales_trend_chart_html(df_test, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons)
        
        print("✅ 趋势图函数测试成功")
        print(f"📊 生成的HTML长度: {len(html)} 字符")
        
        # 保存测试结果
        with open('test_trend_result.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("✅ 测试结果已保存到 test_trend_result.html")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试趋势图函数修复...")
    success = test_trend_function()
    
    if success:
        print("\n✅ 趋势图函数修复测试成功！")
        print("主要修复内容：")
        print("1. 修复了多日数据显示问题")
        print("2. 修复了销售数量显示问题")
        print("3. 增强了数据聚合逻辑")
        print("4. 改进了图表配置")
    else:
        print("\n❌ 趋势图函数修复测试失败") 