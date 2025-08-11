#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证测试脚本
用于验证库存数据匹配逻辑是否正确
"""

import pymysql
import pandas as pd
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def test_wdt_data():
    """测试wdt数据库数据"""
    logger.info("=== 测试wdt数据库数据 ===")
    
    try:
        wdt_conn = pymysql.connect(**DB_CONFIG_WDT)
        
        # 查询BC-93LTMPA和BCD-539WGHTDEDSDU1在wdt.stock中的数据
        query = """
        SELECT spec_name, warehouse_name, stock_num
        FROM stock 
        WHERE spec_name IN ('BC-93LTMPA', 'BCD-539WGHTDEDSDU1')
        AND stock_num > 0
        ORDER BY spec_name, warehouse_name
        """
        
        df = pd.read_sql(query, wdt_conn)
        print("wdt.stock 原始数据:")
        print(df.to_string(index=False))
        
        # 测试修复后的查询逻辑
        query_fixed = """
        SELECT 
            spec_name as 规格名称,
            stock_num as 数量,
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END as 仓库类型
        FROM stock 
        WHERE spec_name IN ('BC-93LTMPA', 'BCD-539WGHTDEDSDU1')
        AND (
            warehouse_name = '常规仓' 
            OR warehouse_name LIKE '%顺丰%'
        )
        AND stock_num > 0
        """
        
        df_fixed = pd.read_sql(query_fixed, wdt_conn)
        print("\n修复后的wdt查询结果:")
        print(df_fixed.to_string(index=False))
        
        wdt_conn.close()
        
    except Exception as e:
        logger.error(f"wdt数据库测试失败: {e}")

def test_date_data():
    """测试Date数据库数据"""
    logger.info("=== 测试Date数据库数据 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询matchstore映射关系
        cursor.execute("SHOW TABLES LIKE '%matchstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到matchstore表格: {table_name}")
            
            query = f"""
            SELECT 规格名称, jinrongstore, tongstore, jdstore, rrsstore
            FROM `{table_name}`
            WHERE 规格名称 IN ('BC-93LTMPA', 'BCD-539WGHTDEDSDU1')
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 映射关系:")
            print(df.to_string(index=False))
        
        # 查询jdstore数据
        cursor.execute("SHOW TABLES LIKE '%jdstore%'")
        jd_tables = cursor.fetchall()
        
        if jd_tables:
            jd_table = jd_tables[0][0]
            logger.info(f"找到jdstore表格: {jd_table}")
            
            # 先查看表结构
            cursor.execute(f"DESCRIBE `{jd_table}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{jd_table} 表结构: {columns}")
            
            # 查询数据
            query = f"""
            SELECT 事业部商品编码, 可用库存
            FROM `{jd_table}`
            WHERE 事业部商品编码 LIKE '%BC-93LTMPA%'
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{jd_table} 数据:")
            print(df.to_string(index=False))
        
        # 查询rrsstore数据
        cursor.execute("SHOW TABLES LIKE '%rrsstore%'")
        rrs_tables = cursor.fetchall()
        
        if rrs_tables:
            rrs_table = rrs_tables[0][0]
            logger.info(f"找到rrsstore表格: {rrs_table}")
            
            # 先查看表结构
            cursor.execute(f"DESCRIBE `{rrs_table}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{rrs_table} 表结构: {columns}")
            
            # 查询数据
            query = f"""
            SELECT 商品编码, 可用库存数量
            FROM `{rrs_table}`
            WHERE 商品编码 LIKE '%BCD-539WGHTDEDSDU1%'
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{rrs_table} 数据:")
            print(df.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"Date数据库测试失败: {e}")

def main():
    """主函数"""
    logger.info("开始数据验证测试")
    
    test_wdt_data()
    test_date_data()
    
    logger.info("数据验证测试完成")

if __name__ == "__main__":
    main() 