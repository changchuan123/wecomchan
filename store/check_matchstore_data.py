#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查matchstore表的数据结构和品类映射
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
DB_CONFIG_DATE = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

def check_matchstore_data():
    """检查matchstore表的数据"""
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("✅ Date数据库连接成功")
        
        # 检查表结构
        cursor = connection.cursor()
        cursor.execute("DESCRIBE matchstore")
        columns = cursor.fetchall()
        
        logger.info("📋 matchstore表结构:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} ({col[2]})")
        
        # 检查数据总量
        cursor.execute("SELECT COUNT(*) FROM matchstore")
        total_count = cursor.fetchone()[0]
        logger.info(f"📊 matchstore表总记录数: {total_count}")
        
        # 检查品类字段的唯一值
        cursor.execute("SELECT DISTINCT 品类 FROM matchstore WHERE 品类 IS NOT NULL AND 品类 != ''")
        categories = cursor.fetchall()
        logger.info(f"🏷️ 品类唯一值数量: {len(categories)}")
        logger.info("📝 品类列表:")
        for cat in categories[:20]:  # 只显示前20个
            logger.info(f"  - {cat[0]}")
        
        # 检查规格名称字段
        cursor.execute("SELECT COUNT(*) FROM matchstore WHERE 规格名称 IS NOT NULL AND 规格名称 != ''")
        spec_count = cursor.fetchone()[0]
        logger.info(f"📦 有规格名称的记录数: {spec_count}")
        
        # 检查品类映射的完整性
        cursor.execute("""
            SELECT COUNT(*) 
            FROM matchstore 
            WHERE 规格名称 IS NOT NULL AND 规格名称 != ''
            AND 品类 IS NOT NULL AND 品类 != ''
        """)
        mapped_count = cursor.fetchone()[0]
        logger.info(f"🔗 有完整品类映射的记录数: {mapped_count}")
        
        # 检查一些具体的映射示例
        cursor.execute("""
            SELECT 规格名称, 品类 
            FROM matchstore 
            WHERE 规格名称 IS NOT NULL AND 规格名称 != ''
            AND 品类 IS NOT NULL AND 品类 != ''
            LIMIT 10
        """)
        examples = cursor.fetchall()
        logger.info("📋 品类映射示例:")
        for spec, cat in examples:
            logger.info(f"  - {spec} -> {cat}")
        
        # 检查是否有"洗衣机"品类
        cursor.execute("SELECT COUNT(*) FROM matchstore WHERE 品类 = '洗衣机'")
        washing_machine_count = cursor.fetchone()[0]
        logger.info(f"🧺 洗衣机品类记录数: {washing_machine_count}")
        
        if washing_machine_count > 0:
            cursor.execute("""
                SELECT 规格名称, 品类 
                FROM matchstore 
                WHERE 品类 = '洗衣机'
                LIMIT 5
            """)
            washing_machine_examples = cursor.fetchall()
            logger.info("🧺 洗衣机品类示例:")
            for spec, cat in washing_machine_examples:
                logger.info(f"  - {spec} -> {cat}")
        
        connection.close()
        logger.info("✅ 检查完成")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_matchstore_data() 