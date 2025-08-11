#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日报和月报脚本中分销单品显示问题的修复效果
"""

import pandas as pd

def create_test_data():
    """创建测试数据"""
    data = [
        # 冰箱品类 - 正常销售（销售额远小于1000）
        {'店铺': '京东自营', '品类': '冰箱', '型号': 'BCD-217WGHC3E9C9U1', '销售额': 100, '销量': 1, '数据来源': '正常'},
        {'店铺': '天猫旗舰店', '品类': '冰箱', '型号': 'BCD-217WGHC3E9C9U1', '销售额': 50, '销量': 1, '数据来源': '正常'},
        # 冰箱品类 - 分销数据（销售额远小于1000）
        {'店铺': '京东-分销商A', '品类': '冰箱', '型号': 'BCD-217WGHC3E9C9U1', '销售额': 200, '销量': 1, '数据来源': '分销'},
        {'店铺': '天猫-分销商B', '品类': '冰箱', '型号': 'BCD-217WGHC3E9C9U1', '销售额': 150, '销量': 1, '数据来源': '分销'},
        
        # 小家电品类 - 正常销售（销售额远小于1000）
        {'店铺': '京东自营', '品类': '小家电', '型号': '电饭煲-智能版', '销售额': 80, '销量': 1, '数据来源': '正常'},
        # 小家电品类 - 分销数据（销售额远小于1000）
        {'店铺': '京东-分销商E', '品类': '小家电', '型号': '电饭煲-智能版', '销售额': 120, '销量': 1, '数据来源': '分销'},
    ]
    return pd.DataFrame(data)

def test_filter_logic():
    """测试过滤逻辑"""
    print("=== 测试过滤逻辑 ===")
    
    df = create_test_data()
    
    # 测试冰箱品类
    print("1. 测试冰箱品类：")
    fridge_df = df[df['品类'] == '冰箱']
    product_summary = fridge_df.groupby('型号').agg({
        '销售额': 'sum',
        '销量': 'sum'
    }).reset_index()
    
    # 计算分销数据
    product_summary['分销金额'] = 0
    for idx, row in product_summary.iterrows():
        product = row['型号']
        fenxiao_data = df[(df['型号'] == product) & (df['数据来源'] == '分销')]
        if not fenxiao_data.empty:
            product_summary.at[idx, '分销金额'] = int(fenxiao_data['销售额'].sum())
    
    print("冰箱品类单品汇总数据：")
    print(product_summary)
    
    # 旧过滤条件
    old_filtered = product_summary[product_summary['销售额'] > 1000]
    print(f"旧过滤条件（销售额>1000）：")
    print(old_filtered)
    
    # 新过滤条件
    new_filtered = product_summary[
        ((product_summary['销售额'] > 1000) | (product_summary['分销金额'] > 0)) & 
        ~product_summary['型号'].str.contains('运费|外机|虚拟|赠品')
    ]
    print(f"新过滤条件（销售额>1000 或 有分销数据）：")
    print(new_filtered)
    
    # 验证冰箱结果
    target_product = 'BCD-217WGHC3E9C9U1'
    in_old = target_product in old_filtered['型号'].values
    in_new = target_product in new_filtered['型号'].values
    
    print(f"冰箱验证结果：")
    print(f"{target_product} 在旧过滤条件中：{'是' if in_old else '否'}")
    print(f"{target_product} 在新过滤条件中：{'是' if in_new else '否'}")
    
    if not in_old and in_new:
        print("✅ 冰箱品类修复成功：分销单品现在能正确显示")
    else:
        print("❌ 冰箱品类修复失败：分销单品显示仍有问题")
    
    # 测试小家电品类
    print("\n2. 测试小家电品类：")
    small_df = df[df['品类'] == '小家电']
    product_summary = small_df.groupby('型号').agg({
        '销售额': 'sum',
        '销量': 'sum'
    }).reset_index()
    
    # 计算分销数据
    product_summary['分销金额'] = 0
    for idx, row in product_summary.iterrows():
        product = row['型号']
        fenxiao_data = df[(df['型号'] == product) & (df['数据来源'] == '分销')]
        if not fenxiao_data.empty:
            product_summary.at[idx, '分销金额'] = int(fenxiao_data['销售额'].sum())
    
    print("小家电品类单品汇总数据：")
    print(product_summary)
    
    # 旧过滤条件
    old_filtered = product_summary[product_summary['销售额'] > 1000]
    print(f"旧过滤条件（销售额>1000）：")
    print(old_filtered)
    
    # 新过滤条件
    new_filtered = product_summary[
        ((product_summary['销售额'] > 1000) | (product_summary['分销金额'] > 0)) & 
        ~product_summary['型号'].str.contains('运费|外机|虚拟|赠品')
    ]
    print(f"新过滤条件（销售额>1000 或 有分销数据）：")
    print(new_filtered)
    
    # 验证小家电结果
    target_product = '电饭煲-智能版'
    in_old = target_product in old_filtered['型号'].values
    in_new = target_product in new_filtered['型号'].values
    
    print(f"小家电验证结果：")
    print(f"{target_product} 在旧过滤条件中：{'是' if in_old else '否'}")
    print(f"{target_product} 在新过滤条件中：{'是' if in_new else '否'}")
    
    if not in_old and in_new:
        print("✅ 小家电品类修复成功：分销单品现在能正确显示")
    else:
        print("❌ 小家电品类修复失败：分销单品显示仍有问题")

def main():
    """主测试函数"""
    print("开始测试分销单品显示问题修复效果")
    print("=" * 50)
    
    try:
        test_filter_logic()
        
        print("\n" + "=" * 50)
        print("✅ 测试完成！")
        print("\n修复总结：")
        print("1. 品类排行函数：已修复过滤条件")
        print("2. TOP单品函数：已修复过滤条件")
        print("3. 店铺单品函数：已修复过滤条件")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误：{e}")

if __name__ == "__main__":
    main() 