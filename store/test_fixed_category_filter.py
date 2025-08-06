#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的品类筛选功能
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

def test_fixed_category_filter():
    """测试修复后的品类筛选功能"""
    try:
        # 连接数据库
        wdt_connection = pymysql.connect(**DB_CONFIG_WDT)
        date_connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("✅ 数据库连接成功")
        
        # 1. 测试wdt.stock数据获取（按照原始需求）
        query_wdt = """
        SELECT 
            spec_name,
            SUM(stock_num) as total_stock,
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END as 仓库类型
        FROM stock 
        WHERE (warehouse_name = '常规仓' OR warehouse_name LIKE '%顺丰%')
        AND stock_num > 0
        AND spec_name IS NOT NULL AND spec_name != ''
        GROUP BY spec_name, 仓库类型
        """
        
        df_wdt = pd.read_sql(query_wdt, wdt_connection)
        logger.info(f"📦 wdt.stock数据（按原始需求）: {len(df_wdt)} 条记录")
        
        # 2. 获取品类映射
        query_mapping = """
        SELECT 规格名称, 品类
        FROM matchstore 
        WHERE 规格名称 IS NOT NULL AND 规格名称 != ''
        AND 品类 IS NOT NULL AND 品类 != ''
        """
        
        df_mapping = pd.read_sql(query_mapping, date_connection)
        category_mapping = {}
        for _, row in df_mapping.iterrows():
            spec_name = str(row['规格名称']).strip()
            category = str(row['品类']).strip()
            if spec_name and category and category != 'nan':
                category_mapping[spec_name] = category
        
        logger.info(f"📋 品类映射总数: {len(category_mapping)}")
        
        # 3. 添加品类信息到wdt数据
        df_wdt['品类'] = df_wdt['spec_name'].apply(lambda x: category_mapping.get(str(x).strip(), '其他'))
        
        # 4. 测试各品类数据
        categories = df_wdt['品类'].unique()
        logger.info(f"🏷️ 所有品类: {list(categories)}")
        
        # 测试主要品类
        test_categories = ['洗衣机', '冰箱', '空调', '电视']
        for category in test_categories:
            category_data = df_wdt[df_wdt['品类'] == category]
            logger.info(f"📦 {category}品类数据: {len(category_data)} 条记录")
            
            if not category_data.empty:
                logger.info(f"  📋 {category}品类示例:")
                for _, row in category_data.head(3).iterrows():
                    logger.info(f"    - {row['spec_name']}: {row['total_stock']} 件 ({row['仓库类型']})")
        
        # 5. 测试其他仓库数据
        logger.info("🔍 测试其他仓库数据:")
        
        # jinrongstore
        query_jinrong = """
        SELECT 型号, (数量 - 已赎货) as 可用库存
        FROM jinrongstore 
        WHERE (数量 - 已赎货) > 0
        """
        df_jinrong = pd.read_sql(query_jinrong, date_connection)
        logger.info(f"💰 jinrongstore数据: {len(df_jinrong)} 条记录")
        
        # rrsstore
        query_rrs = """
        SELECT 商品编码, 可用库存数量
        FROM rrsstore 
        WHERE 可用库存数量 > 0
        """
        df_rrs = pd.read_sql(query_rrs, date_connection)
        logger.info(f"☁️ rrsstore数据: {len(df_rrs)} 条记录")
        
        # jdstore
        query_jd = """
        SELECT 事业部商品编码, 可用库存
        FROM jdstore 
        WHERE 可用库存 > 0
        """
        df_jd = pd.read_sql(query_jd, date_connection)
        logger.info(f"🛒 jdstore数据: {len(df_jd)} 条记录")
        
        wdt_connection.close()
        date_connection.close()
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_fixed_category_filter() 