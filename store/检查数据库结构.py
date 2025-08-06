#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库结构脚本
用于调试和查看数据库表格结构
"""

import pymysql
import logging

# 数据库配置
DB_CONFIG_WDT = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'wdt',
    'charset': 'utf8mb4'
}

DB_CONFIG_DATE = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

def check_database_structure():
    """检查数据库结构"""
    
    # 连接wdt数据库
    print("=== 检查WDT数据库 ===")
    try:
        conn = pymysql.connect(**DB_CONFIG_WDT)
        cursor = conn.cursor()
        
        # 检查stock表结构
        cursor.execute("DESCRIBE stock")
        stock_columns = cursor.fetchall()
        print("stock表格结构:")
        for col in stock_columns:
            print(f"  {col[0]}: {col[1]}")
        
        # 检查数据示例
        cursor.execute("SELECT warehouse_name, COUNT(*) FROM stock GROUP BY warehouse_name")
        warehouses = cursor.fetchall()
        print("\n仓库列表:")
        for wh, count in warehouses:
            print(f"  {wh}: {count}条记录")
            
        conn.close()
    except Exception as e:
        print(f"WDT数据库检查失败: {e}")
    
    # 连接Date数据库
    print("\n=== 检查Date数据库 ===")
    try:
        conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SHOW TABLES")
        all_tables = cursor.fetchall()
        print("所有表格:")
        for table in all_tables:
            table_name = table[0]
            print(f"\n--- {table_name} ---")
            
            # 检查表结构
            try:
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                print("列结构:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]}")
                
                # 检查数据条数
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"数据条数: {count}")
                
                # 检查前5条数据示例
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
                sample_data = cursor.fetchall()
                if sample_data:
                    print("前5条数据示例:")
                    for row in sample_data:
                        print(f"  {row}")
                        
            except Exception as e:
                print(f"检查{table_name}失败: {e}")
        
        conn.close()
    except Exception as e:
        print(f"Date数据库检查失败: {e}")

if __name__ == "__main__":
    check_database_structure()