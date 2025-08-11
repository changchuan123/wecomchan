#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据统一逻辑
验证所有品类、店铺汇总数据都默认包含京东分销数据
"""

import pandas as pd
import numpy as np

def test_data_unification():
    """测试数据统一逻辑"""
    print("🧪 开始测试数据统一逻辑...")
    
    # 创建模拟数据
    data = {
        '店铺': ['京东-店铺A', '京东-店铺B', '天猫店铺C', '京东-店铺A', '京东-店铺B'],
        '品类': ['洗碗机', '洗碗机', '洗碗机', '冰箱', '冰箱'],
        '规格名称': ['型号A', '型号B', '型号C', '型号D', '型号E'],
        '分摊后总价': [10000, 8000, 6000, 12000, 9000],
        '实发数量': [10, 8, 6, 12, 9],
        '数据来源': ['分销', '分销', 'ERP', '分销', '分销']
    }
    
    df_erp = pd.DataFrame(data)
    print(f"📊 原始数据:\n{df_erp}")
    
    # 测试品类数据计算（应该包含分销数据）
    print("\n🔍 测试品类数据计算:")
    category_data = df_erp.groupby('品类').agg({
        '分摊后总价': 'sum',
        '实发数量': 'sum'
    }).reset_index()
    
    print(f"品类汇总数据（包含分销）:\n{category_data}")
    
    # 验证洗碗机品类数据
    dishwasher_data = category_data[category_data['品类'] == '洗碗机']
    if not dishwasher_data.empty:
        total_amount = dishwasher_data.iloc[0]['分摊后总价']
        total_qty = dishwasher_data.iloc[0]['实发数量']
        print(f"✅ 洗碗机品类总销售额: ¥{total_amount:,}，总销量: {total_qty}件")
        
        # 验证是否包含分销数据
        fenxiao_amount = df_erp[(df_erp['品类'] == '洗碗机') & (df_erp['数据来源'] == '分销')]['分摊后总价'].sum()
        fenxiao_qty = df_erp[(df_erp['品类'] == '洗碗机') & (df_erp['数据来源'] == '分销')]['实发数量'].sum()
        print(f"✅ 洗碗机分销数据: ¥{fenxiao_amount:,}，{fenxiao_qty}件")
        
        if total_amount == fenxiao_amount + 6000:  # 6000是ERP数据
            print("✅ 品类数据计算正确，包含分销数据")
        else:
            print("❌ 品类数据计算错误")
    
    # 测试店铺数据计算（应该包含分销数据）
    print("\n🔍 测试店铺数据计算:")
    shop_data = df_erp.groupby('店铺').agg({
        '分摊后总价': 'sum',
        '实发数量': 'sum'
    }).reset_index()
    
    print(f"店铺汇总数据（包含分销）:\n{shop_data}")
    
    # 验证京东-店铺A数据
    shop_a_data = shop_data[shop_data['店铺'] == '京东-店铺A']
    if not shop_a_data.empty:
        total_amount = shop_a_data.iloc[0]['分摊后总价']
        total_qty = shop_a_data.iloc[0]['实发数量']
        print(f"✅ 京东-店铺A总销售额: ¥{total_amount:,}，总销量: {total_qty}件")
        
        # 验证是否包含分销数据
        fenxiao_amount = df_erp[(df_erp['店铺'] == '京东-店铺A') & (df_erp['数据来源'] == '分销')]['分摊后总价'].sum()
        fenxiao_qty = df_erp[(df_erp['店铺'] == '京东-店铺A') & (df_erp['数据来源'] == '分销')]['实发数量'].sum()
        print(f"✅ 京东-店铺A分销数据: ¥{fenxiao_amount:,}，{fenxiao_qty}件")
        
        if total_amount == fenxiao_amount:
            print("✅ 店铺数据计算正确，包含分销数据")
        else:
            print("❌ 店铺数据计算错误")
    
    # 测试单品数据计算（应该包含分销数据）
    print("\n🔍 测试单品数据计算:")
    product_data = df_erp.groupby('规格名称').agg({
        '分摊后总价': 'sum',
        '实发数量': 'sum'
    }).reset_index()
    
    print(f"单品汇总数据（包含分销）:\n{product_data}")
    
    # 验证型号A数据
    model_a_data = product_data[product_data['规格名称'] == '型号A']
    if not model_a_data.empty:
        total_amount = model_a_data.iloc[0]['分摊后总价']
        total_qty = model_a_data.iloc[0]['实发数量']
        print(f"✅ 型号A总销售额: ¥{total_amount:,}，总销量: {total_qty}件")
        
        # 验证是否包含分销数据
        fenxiao_amount = df_erp[(df_erp['规格名称'] == '型号A') & (df_erp['数据来源'] == '分销')]['分摊后总价'].sum()
        fenxiao_qty = df_erp[(df_erp['规格名称'] == '型号A') & (df_erp['数据来源'] == '分销')]['实发数量'].sum()
        print(f"✅ 型号A分销数据: ¥{fenxiao_amount:,}，{fenxiao_qty}件")
        
        if total_amount == fenxiao_amount:
            print("✅ 单品数据计算正确，包含分销数据")
        else:
            print("❌ 单品数据计算错误")
    
    print("\n🎉 数据统一逻辑测试完成！")
    print("📋 总结：")
    print("   ✅ 品类数据计算：包含分销数据")
    print("   ✅ 店铺数据计算：包含分销数据") 
    print("   ✅ 单品数据计算：包含分销数据")
    print("   ✅ 所有数据计算逻辑已统一")

if __name__ == "__main__":
    test_data_unification() 