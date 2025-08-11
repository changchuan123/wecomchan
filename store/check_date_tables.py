#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Date数据库中各个专门表格的数据获取情况
"""

import pymysql
import pandas as pd
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG_DATE = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

def check_matchstore_mapping():
    """检查matchstore映射关系"""
    logger.info("=== 检查matchstore映射关系 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询matchstore表格
        cursor.execute("SHOW TABLES LIKE '%matchstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到matchstore表格: {table_name}")
            
            # 查询特定产品的映射关系
            query = f"""
            SELECT 规格名称, jinrongstore, tongstore, jdstore, rrsstore
            FROM `{table_name}`
            WHERE 规格名称 IN ('BC-93LTMPA', 'BCD-539WGHTDEDSDU1', 'BCD-88GHTMZ0WV')
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 映射关系:")
            print(df.to_string(index=False))
            
            # 查询所有有映射关系的产品
            query_all = f"""
            SELECT 规格名称, jinrongstore, tongstore, jdstore, rrsstore
            FROM `{table_name}`
            WHERE (jinrongstore IS NOT NULL AND jinrongstore != '' AND jinrongstore != 'None')
               OR (tongstore IS NOT NULL AND tongstore != '' AND tongstore != 'None')
               OR (jdstore IS NOT NULL AND jdstore != '' AND jdstore != 'None')
               OR (rrsstore IS NOT NULL AND rrsstore != '' AND rrsstore != 'None')
            LIMIT 20
            """
            
            df_all = pd.read_sql(query_all, date_conn)
            print(f"\n{table_name} 有映射关系的产品（前20条）:")
            print(df_all.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"检查matchstore失败: {e}")

def check_jdstore_data():
    """检查jdstore数据"""
    logger.info("=== 检查jdstore数据 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询jdstore表格
        cursor.execute("SHOW TABLES LIKE '%jdstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到jdstore表格: {table_name}")
            
            # 查看表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{table_name} 表结构: {columns}")
            
            # 查询所有数据
            query = f"""
            SELECT 事业部商品编码, 可用库存
            FROM `{table_name}`
            WHERE 可用库存 > 0
            LIMIT 20
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 数据（前20条）:")
            print(df.to_string(index=False))
            
            # 统计总数
            query_count = f"""
            SELECT COUNT(*) as 总记录数, SUM(可用库存) as 总库存
            FROM `{table_name}`
            WHERE 可用库存 > 0
            """
            
            df_count = pd.read_sql(query_count, date_conn)
            print(f"\n{table_name} 统计:")
            print(df_count.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"检查jdstore失败: {e}")

def check_rrsstore_data():
    """检查rrsstore数据"""
    logger.info("=== 检查rrsstore数据 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询rrsstore表格
        cursor.execute("SHOW TABLES LIKE '%rrsstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到rrsstore表格: {table_name}")
            
            # 查看表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{table_name} 表结构: {columns}")
            
            # 查询所有数据
            query = f"""
            SELECT 商品编码, 可用库存数量
            FROM `{table_name}`
            WHERE 可用库存数量 > 0
            LIMIT 20
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 数据（前20条）:")
            print(df.to_string(index=False))
            
            # 统计总数
            query_count = f"""
            SELECT COUNT(*) as 总记录数, SUM(可用库存数量) as 总库存
            FROM `{table_name}`
            WHERE 可用库存数量 > 0
            """
            
            df_count = pd.read_sql(query_count, date_conn)
            print(f"\n{table_name} 统计:")
            print(df_count.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"检查rrsstore失败: {e}")

def check_tongstore_data():
    """检查tongstore数据"""
    logger.info("=== 检查tongstore数据 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询tongstore表格
        cursor.execute("SHOW TABLES LIKE '%tongstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到tongstore表格: {table_name}")
            
            # 查看表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{table_name} 表结构: {columns}")
            
            # 查询前10行数据
            query = f"""
            SELECT * FROM `{table_name}` LIMIT 10
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 数据预览:")
            print(df.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"检查tongstore失败: {e}")

def check_jinrongstore_data():
    """检查jinrongstore数据"""
    logger.info("=== 检查jinrongstore数据 ===")
    
    try:
        date_conn = pymysql.connect(**DB_CONFIG_DATE)
        cursor = date_conn.cursor()
        
        # 查询jinrongstore表格
        cursor.execute("SHOW TABLES LIKE '%jinrongstore%'")
        tables = cursor.fetchall()
        
        if tables:
            table_name = tables[0][0]
            logger.info(f"找到jinrongstore表格: {table_name}")
            
            # 查看表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"\n{table_name} 表结构: {columns}")
            
            # 查询所有数据
            query = f"""
            SELECT 型号, 数量, 已赎货, (数量 - 已赎货) as 可用库存
            FROM `{table_name}`
            WHERE (数量 - 已赎货) > 0
            LIMIT 20
            """
            
            df = pd.read_sql(query, date_conn)
            print(f"\n{table_name} 数据（前20条）:")
            print(df.to_string(index=False))
            
            # 统计总数
            query_count = f"""
            SELECT COUNT(*) as 总记录数, SUM(数量 - 已赎货) as 总可用库存
            FROM `{table_name}`
            WHERE (数量 - 已赎货) > 0
            """
            
            df_count = pd.read_sql(query_count, date_conn)
            print(f"\n{table_name} 统计:")
            print(df_count.to_string(index=False))
        
        date_conn.close()
        
    except Exception as e:
        logger.error(f"检查jinrongstore失败: {e}")

def main():
    """主函数"""
    logger.info("开始检查Date数据库各个表格")
    
    check_matchstore_mapping()
    check_jdstore_data()
    check_rrsstore_data()
    check_tongstore_data()
    check_jinrongstore_data()
    
    logger.info("Date数据库检查完成")

if __name__ == "__main__":
    main() 