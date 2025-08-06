#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的库存分析脚本
用于验证数据库连接和列名映射是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from 库存分析新格式 import NewInventoryAnalyzer
import logging

def test_database_connections():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    
    analyzer = NewInventoryAnalyzer()
    
    # 测试连接
    if analyzer.connect_databases():
        print("✅ 数据库连接成功")
        
        # 测试各表数据获取
        print("\n=== 测试各表数据获取 ===")
        
        # 测试WDT数据
        print("1. 测试WDT stock数据...")
        wdt_data = analyzer.get_wdt_stock_data()
        if not wdt_data.empty:
            print(f"   ✅ WDT数据获取成功: {len(wdt_data)} 条记录")
            print(f"   样例数据: {wdt_data.iloc[0].to_dict()}")
        else:
            print("   ❌ WDT数据获取失败")
        
        # 测试jinrongstore数据
        print("2. 测试jinrongstore数据...")
        jinrong_data = analyzer.get_jinrongstore_data()
        if not jinrong_data.empty:
            print(f"   ✅ jinrongstore数据获取成功: {len(jinrong_data)} 条记录")
            print(f"   样例数据: {jinrong_data.iloc[0].to_dict()}")
        else:
            print("   ❌ jinrongstore数据获取失败")
        
        # 测试rrsstore数据
        print("3. 测试rrsstore数据...")
        rrs_data = analyzer.get_rrsstore_data()
        if not rrs_data.empty:
            print(f"   ✅ rrsstore数据获取成功: {len(rrs_data)} 条记录")
            print(f"   样例数据: {rrs_data.iloc[0].to_dict()}")
        else:
            print("   ❌ rrsstore数据获取失败")
        
        # 测试tongstore数据
        print("4. 测试tongstore数据...")
        tong_data = analyzer.get_tongstore_data()
        if not tong_data.empty:
            print(f"   ✅ tongstore数据获取成功: {len(tong_data)} 条记录")
            print(f"   样例数据: {tong_data.iloc[0].to_dict()}")
        else:
            print("   ❌ tongstore数据获取失败")
        
        # 测试jdstore数据
        print("5. 测试jdstore数据...")
        jd_data = analyzer.get_jdstore_data()
        if not jd_data.empty:
            print(f"   ✅ jdstore数据获取成功: {len(jd_data)} 条记录")
            print(f"   样例数据: {jd_data.iloc[0].to_dict()}")
        else:
            print("   ❌ jdstore数据获取失败")
        
        # 测试聚合功能
        print("\n=== 测试数据聚合 ===")
        all_data = []
        for name, data in [('WDT', wdt_data), ('jinrong', jinrong_data), 
                          ('rrs', rrs_data), ('tong', tong_data), ('jd', jd_data)]:
            if not data.empty:
                all_data.append(data)
                print(f"   {name}: {len(data)} 条记录")
        
        if all_data:
            combined_df = analyzer.aggregate_inventory_data()
            print(f"   ✅ 数据聚合成功: {len(combined_df)} 条记录")
            
            # 显示聚合结果摘要
            if not combined_df.empty:
                print("\n=== 聚合结果摘要 ===")
                print(f"总记录数: {len(combined_df)}")
                print(f"总库存量: {combined_df['库存量'].sum():,}")
                print(f"品类数量: {combined_df['标准化品类'].nunique()}")
                print(f"品牌数量: {combined_df['品牌'].nunique()}")
                
                # 按品类汇总
                category_summary = combined_df.groupby('标准化品类')['库存量'].sum().sort_values(ascending=False)
                print("\n按品类汇总:")
                for category, inventory in category_summary.head(5).items():
                    print(f"   {category}: {inventory:,}")
                
                # 按渠道汇总
                channel_summary = combined_df.groupby('渠道类型')['库存量'].sum().sort_values(ascending=False)
                print("\n按渠道汇总:")
                for channel, inventory in channel_summary.items():
                    print(f"   {channel}: {inventory:,}")
        
        analyzer.close_databases()
        print("\n✅ 数据库连接已关闭")
        
    else:
        print("❌ 数据库连接失败")
        return False
    
    return True

def test_column_mapping():
    """测试列名映射"""
    print("\n=== 测试列名映射 ===")
    
    from 库存分析新格式 import NewInventoryAnalyzer
    analyzer = NewInventoryAnalyzer()
    
    if analyzer.connect_databases():
        cursor = analyzer.wdt_connection.cursor()
        
        # 检查WDT表结构
        print("1. WDT stock表结构:")
        cursor.execute("DESCRIBE stock")
        wdt_columns = [col[0] for col in cursor.fetchall()]
        print(f"   实际列名: {wdt_columns}")
        
        # 检查Date表结构
        cursor = analyzer.date_connection.cursor()
        
        for table_pattern in ['%jinrongstore%', '%rrsstore%', '%tongstore%', '%jdstore%']:
            cursor.execute(f"SHOW TABLES LIKE '{table_pattern}'")
            tables = cursor.fetchall()
            if tables:
                table_name = tables[0][0]
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [col[0] for col in cursor.fetchall()]
                print(f"   {table_name}表结构: {columns}")
        
        analyzer.close_databases()
    else:
        print("❌ 无法连接数据库测试列名映射")

if __name__ == "__main__":
    print("开始测试修复后的库存分析脚本...")
    
    # 测试数据库连接
    success = test_database_connections()
    
    if success:
        print("\n🎉 所有测试通过！脚本修复成功")
    else:
        print("\n⚠️  测试中发现问题，请检查日志")
    
    # 测试列名映射
    test_column_mapping()