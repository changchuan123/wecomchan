#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构分析脚本
用于详细分析数据库表结构，特别是库存相关表格
"""

import pymysql
import pandas as pd
from datetime import datetime
import json

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

def analyze_wdt_database():
    """分析WDT数据库"""
    print("=== 分析WDT数据库 ===")
    
    try:
        conn = pymysql.connect(**DB_CONFIG_WDT)
        cursor = conn.cursor()
        
        # 检查stock表结构
        print("\n1. WDT.stock表格结构:")
        cursor.execute("DESCRIBE stock")
        stock_columns = cursor.fetchall()
        
        columns_info = []
        for col in stock_columns:
            column_info = {
                'name': col[0],
                'type': col[1],
                'null': col[2],
                'key': col[3],
                'default': col[4],
                'extra': col[5]
            }
            columns_info.append(column_info)
            print(f"  {col[0]}: {col[1]}")
        
        # 检查数据样本
        print("\n2. WDT.stock数据样本:")
        cursor.execute("SELECT goods_name, brand_name, spec_name, stock_num, warehouse_name FROM stock LIMIT 5")
        sample_data = cursor.fetchall()
        for row in sample_data:
            print(f"  货品: {row[0]}, 品牌: {row[1]}, 规格: {row[2]}, 库存: {row[3]}, 仓库: {row[4]}")
        
        # 检查仓库分布
        print("\n3. WDT.stock仓库分布:")
        cursor.execute("SELECT warehouse_name, COUNT(*) as count FROM stock GROUP BY warehouse_name ORDER BY count DESC")
        warehouses = cursor.fetchall()
        for wh, count in warehouses:
            print(f"  {wh}: {count}条记录")
            
        conn.close()
        
        return {
            'table': 'stock',
            'columns': columns_info,
            'sample_data': sample_data
        }
        
    except Exception as e:
        print(f"WDT数据库分析失败: {e}")
        return None

def analyze_date_database():
    """分析Date数据库"""
    print("\n=== 分析Date数据库 ===")
    
    try:
        conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = conn.cursor()
        
        # 获取所有库存相关表
        print("\n1. 查找库存相关表格:")
        cursor.execute("SHOW TABLES LIKE '%store%' OR SHOW TABLES LIKE '%库存%' OR SHOW TABLES LIKE '%stock%'")
        
        # 使用SHOW TABLES LIKE语句分别查询
        cursor.execute("SHOW TABLES LIKE '%store%'")
        store_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%jinrong%'")
        jinrong_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%rrs%'")
        rrs_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%tong%'")
        tong_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%jd%'")
        jd_tables = cursor.fetchall()
        
        all_tables = store_tables + jinrong_tables + rrs_tables + tong_tables + jd_tables
        
        table_structures = {}
        
        for table_tuple in all_tables:
            table_name = table_tuple[0]
            print(f"\n--- 分析表格: {table_name} ---")
            
            try:
                # 获取表结构
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                
                column_info = []
                print("  列结构:")
                for col in columns:
                    print(f"    {col[0]}: {col[1]}")
                    column_info.append({
                        'name': col[0],
                        'type': col[1],
                        'null': col[2],
                        'key': col[3],
                        'default': col[4],
                        'extra': col[5]
                    })
                
                # 检查数据条数
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"  数据条数: {count}")
                
                # 获取前3条数据样本
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                sample_data = cursor.fetchall()
                print(f"  数据样本:")
                for i, row in enumerate(sample_data, 1):
                    print(f"    样本{i}: {row}")
                
                table_structures[table_name] = {
                    'columns': column_info,
                    'count': count,
                    'sample_data': sample_data
                }
                
            except Exception as e:
                print(f"  分析{table_name}失败: {e}")
                continue
        
        conn.close()
        return table_structures
        
    except Exception as e:
        print(f"Date数据库分析失败: {e}")
        return None

def analyze_specific_tables():
    """分析特定表格"""
    print("\n=== 分析特定库存表格 ===")
    
    try:
        conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = conn.cursor()
        
        # 定义要分析的表格
        target_tables = [
            'jinrongstore', 'rrsstore', 'tongstore', 'jdstore',
            'jinrong_store', 'rrs_store', 'tong_store', 'jd_store'
        ]
        
        found_tables = {}
        
        for table_name in target_tables:
            try:
                cursor.execute(f"SHOW TABLES LIKE '%{table_name}%'")
                matches = cursor.fetchall()
                
                if matches:
                    actual_table_name = matches[0][0]
                    print(f"\n找到表格: {actual_table_name}")
                    
                    # 获取详细结构
                    cursor.execute(f"DESCRIBE `{actual_table_name}`")
                    columns = cursor.fetchall()
                    
                    print("  列结构:")
                    column_names = []
                    for col in columns:
                        print(f"    {col[0]}: {col[1]}")
                        column_names.append(col[0])
                    
                    # 检查关键列
                    key_columns = ['货品名称', '品牌名称', '规格名称', '型号', '数量', '库存', '商品名称', '商品编码']
                    found_columns = []
                    for key in key_columns:
                        if key in column_names:
                            found_columns.append(key)
                    
                    print(f"  找到的关键列: {found_columns}")
                    
                    # 获取数据样本
                    cursor.execute(f"SELECT * FROM `{actual_table_name}` LIMIT 2")
                    samples = cursor.fetchall()
                    print(f"  数据样本:")
                    for sample in samples:
                        print(f"    {sample}")
                    
                    found_tables[actual_table_name] = {
                        'columns': column_names,
                        'key_columns': found_columns,
                        'samples': samples
                    }
                
            except Exception as e:
                continue
        
        conn.close()
        return found_tables
        
    except Exception as e:
        print(f"特定表格分析失败: {e}")
        return None

def save_analysis_report(wdt_data, date_data, specific_tables):
    """保存分析报告"""
    report = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'wdt_database': wdt_data,
        'date_database': date_data,
        'specific_tables': specific_tables
    }
    
    with open('database_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 分析报告已保存到 database_analysis_report.json ===")

def main():
    """主函数"""
    print("开始分析数据库结构...")
    
    # 分析WDT数据库
    wdt_data = analyze_wdt_database()
    
    # 分析Date数据库
    date_data = analyze_date_database()
    
    # 分析特定表格
    specific_tables = analyze_specific_tables()
    
    # 保存分析报告
    save_analysis_report(wdt_data, date_data, specific_tables)
    
    print("\n数据库结构分析完成！")

if __name__ == "__main__":
    main()