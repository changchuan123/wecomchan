#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Daysales表中仓库字段的所有唯一值
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta

# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

def check_warehouse_values():
    """检查Daysales表中仓库字段的所有唯一值"""
    print("🔍 开始检查Daysales表中仓库字段的唯一值...")
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        
        cursor = conn.cursor()
        
        # 获取仓库字段的所有唯一值
        cursor.execute("SELECT DISTINCT 仓库 FROM Daysales WHERE 仓库 IS NOT NULL AND 仓库 != '' ORDER BY 仓库")
        warehouse_values = cursor.fetchall()
        
        print(f"\n📊 仓库字段唯一值 (共{len(warehouse_values)}个):")
        print("="*60)
        
        # 分类统计
        warehouse_stats = {}
        for value in warehouse_values:
            warehouse_name = value[0]
            if warehouse_name:
                # 统计每个仓库的记录数
                cursor.execute("SELECT COUNT(*) FROM Daysales WHERE 仓库 = %s", (warehouse_name,))
                count = cursor.fetchone()[0]
                warehouse_stats[warehouse_name] = count
                print(f"  {warehouse_name:<30} ({count}条记录)")
        
        # 检查是否包含"菜鸟仓自流转"
        print("\n🔍 检查是否包含'菜鸟仓自流转':")
        if '菜鸟仓自流转' in warehouse_stats:
            print(f"  ✅ 找到'菜鸟仓自流转': {warehouse_stats['菜鸟仓自流转']}条记录")
        else:
            print("  ❌ 未找到'菜鸟仓自流转'")
            
        # 检查包含"菜鸟仓"的仓库
        print("\n🔍 检查包含'菜鸟仓'的仓库:")
        cainiao_warehouses = [name for name in warehouse_stats.keys() if '菜鸟仓' in name]
        if cainiao_warehouses:
            for warehouse in cainiao_warehouses:
                print(f"  ✅ {warehouse}: {warehouse_stats[warehouse]}条记录")
        else:
            print("  ❌ 未找到包含'菜鸟仓'的仓库")
            
        # 检查包含"分销"的仓库
        print("\n🔍 检查包含'分销'的仓库:")
        fenxiao_warehouses = [name for name in warehouse_stats.keys() if '分销' in name]
        if fenxiao_warehouses:
            for warehouse in fenxiao_warehouses:
                print(f"  ✅ {warehouse}: {warehouse_stats[warehouse]}条记录")
        else:
            print("  ❌ 未找到包含'分销'的仓库")
            
        # 检查包含"自流转"的仓库
        print("\n🔍 检查包含'自流转'的仓库:")
        ziliuzhuan_warehouses = [name for name in warehouse_stats.keys() if '自流转' in name]
        if ziliuzhuan_warehouses:
            for warehouse in ziliuzhuan_warehouses:
                print(f"  ✅ {warehouse}: {warehouse_stats[warehouse]}条记录")
        else:
            print("  ❌ 未找到包含'自流转'的仓库")
        
        # 获取一些样本数据来验证
        print("\n📝 获取包含'菜鸟仓'的样本数据:")
        cursor.execute("SELECT 店铺, 仓库, 订单编号, 交易时间 FROM Daysales WHERE 仓库 LIKE '%菜鸟仓%' LIMIT 5")
        sample_data = cursor.fetchall()
        if sample_data:
            for i, row in enumerate(sample_data, 1):
                print(f"  记录{i}: 店铺={row[0]}, 仓库={row[1]}, 订单号={row[2]}, 时间={row[3]}")
        else:
            print("  未找到包含'菜鸟仓'的数据")
        
        conn.close()
        print("\n✅ 检查完成")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_warehouse_values() 