#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查库存数据中的规格名称格式，并与matchstore表进行对比
"""

import pymysql
import pandas as pd
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

def check_inventory_spec_names():
    """检查库存数据中的规格名称格式"""
    try:
        # 连接数据库
        wdt_connection = pymysql.connect(**DB_CONFIG_WDT)
        date_connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("✅ 数据库连接成功")
        
        # 检查wdt.stock表中的规格名称
        query_wdt = """
        SELECT spec_name, COUNT(*) as count
        FROM stock 
        WHERE spec_name IS NOT NULL AND spec_name != ''
        GROUP BY spec_name 
        ORDER BY count DESC 
        LIMIT 20
        """
        
        df_wdt = pd.read_sql(query_wdt, wdt_connection)
        logger.info("📦 wdt.stock表中的规格名称示例:")
        for _, row in df_wdt.iterrows():
            logger.info(f"  - {row['spec_name']}: {row['count']}条记录")
        
        # 检查matchstore表中的洗衣机规格名称
        query_matchstore = """
        SELECT 规格名称, 品类
        FROM matchstore 
        WHERE 品类 = '洗衣机'
        LIMIT 10
        """
        
        df_matchstore = pd.read_sql(query_matchstore, date_connection)
        logger.info("🧺 matchstore表中的洗衣机规格名称示例:")
        for _, row in df_matchstore.iterrows():
            logger.info(f"  - {row['规格名称']} -> {row['品类']}")
        
        # 检查是否有匹配的记录
        # 获取wdt.stock中所有洗衣机相关的规格名称
        query_wdt_washing = """
        SELECT spec_name, COUNT(*) as count
        FROM stock 
        WHERE spec_name LIKE '%洗衣机%' OR spec_name LIKE '%TQG%' OR spec_name LIKE '%@G%'
        GROUP BY spec_name 
        ORDER BY count DESC 
        LIMIT 10
        """
        
        df_wdt_washing = pd.read_sql(query_wdt_washing, wdt_connection)
        logger.info("🧺 wdt.stock中的洗衣机相关规格名称:")
        for _, row in df_wdt_washing.iterrows():
            logger.info(f"  - {row['spec_name']}: {row['count']}条记录")
        
        # 尝试直接匹配
        logger.info("🔍 尝试直接匹配测试:")
        
        # 获取matchstore中的洗衣机规格名称
        query_matchstore_specs = """
        SELECT 规格名称
        FROM matchstore 
        WHERE 品类 = '洗衣机'
        LIMIT 5
        """
        
        cursor = date_connection.cursor()
        cursor.execute(query_matchstore_specs)
        matchstore_specs = [row[0] for row in cursor.fetchall()]
        
        for spec in matchstore_specs:
            # 在wdt.stock中查找匹配的记录
            query_match = f"""
            SELECT spec_name, COUNT(*) as count
            FROM stock 
            WHERE spec_name = '{spec}'
            """
            
            cursor_wdt = wdt_connection.cursor()
            cursor_wdt.execute(query_match)
            result = cursor_wdt.fetchone()
            
            if result and result[1] > 0:
                logger.info(f"✅ 找到匹配: {spec} -> {result[1]}条记录")
            else:
                logger.info(f"❌ 未找到匹配: {spec}")
        
        # 检查wdt.stock表中的仓库信息
        query_warehouse = """
        SELECT warehouse_name, COUNT(*) as count
        FROM stock 
        WHERE warehouse_name IS NOT NULL AND warehouse_name != ''
        GROUP BY warehouse_name 
        ORDER BY count DESC
        """
        
        df_warehouse = pd.read_sql(query_warehouse, wdt_connection)
        logger.info("🏪 wdt.stock表中的仓库类型:")
        for _, row in df_warehouse.iterrows():
            logger.info(f"  - {row['warehouse_name']}: {row['count']}条记录")
        
        wdt_connection.close()
        date_connection.close()
        logger.info("✅ 检查完成")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_inventory_spec_names() 