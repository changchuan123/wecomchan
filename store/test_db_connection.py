#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
"""

import pymysql
import pandas as pd
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'wdt',
    'charset': 'utf8mb4'
}

DATE_DB_CONFIG = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

def test_wdt_connection():
    """测试wdt数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        logger.info("wdt数据库连接成功")
        
        # 测试查询
        query = "SELECT COUNT(*) as count FROM stock"
        df = pd.read_sql(query, connection)
        logger.info(f"wdt.stock表记录数: {df['count'].iloc[0]}")
        
        # 查看仓库名称
        query = "SELECT DISTINCT warehouse_name FROM stock LIMIT 10"
        df = pd.read_sql(query, connection)
        logger.info("仓库名称示例:")
        for name in df['warehouse_name']:
            logger.info(f"  - {name}")
        
        connection.close()
        return True
    except Exception as e:
        logger.error(f"wdt数据库连接失败: {e}")
        return False

def test_date_connection():
    """测试Date数据库连接"""
    try:
        connection = pymysql.connect(**DATE_DB_CONFIG)
        logger.info("Date数据库连接成功")
        
        # 查看所有表
        query = "SHOW TABLES"
        df = pd.read_sql(query, connection)
        logger.info("Date数据库中的表:")
        for table in df.iloc[:, 0]:
            logger.info(f"  - {table}")
        
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Date数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始测试数据库连接")
    
    # 测试wdt数据库
    wdt_success = test_wdt_connection()
    
    # 测试Date数据库
    date_success = test_date_connection()
    
    if wdt_success and date_success:
        logger.info("所有数据库连接测试成功")
    else:
        logger.error("数据库连接测试失败")

if __name__ == "__main__":
    main() 