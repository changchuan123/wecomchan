#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试品类筛选功能
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

def test_category_filter():
    """测试品类筛选功能"""
    try:
        # 连接数据库
        wdt_connection = pymysql.connect(**DB_CONFIG_WDT)
        date_connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("✅ 数据库连接成功")
        
        # 1. 获取matchstore中的洗衣机品类映射
        query_matchstore = """
        SELECT 规格名称, 品类
        FROM matchstore 
        WHERE 品类 = '洗衣机'
        LIMIT 10
        """
        
        df_matchstore = pd.read_sql(query_matchstore, date_connection)
        logger.info(f"🧺 matchstore中的洗衣机品类记录数: {len(df_matchstore)}")
        
        # 2. 检查这些规格名称在wdt.stock中是否有库存
        for _, row in df_matchstore.iterrows():
            spec_name = row['规格名称']
            query_stock = f"""
            SELECT spec_name, SUM(stock_num) as total_stock
            FROM stock 
            WHERE spec_name = '{spec_name}' AND stock_num > 0
            GROUP BY spec_name
            """
            
            df_stock = pd.read_sql(query_stock, wdt_connection)
            if not df_stock.empty:
                logger.info(f"✅ {spec_name}: {df_stock.iloc[0]['total_stock']} 件库存")
            else:
                logger.info(f"❌ {spec_name}: 无库存")
        
        # 3. 测试完整的品类筛选逻辑
        logger.info("🔍 测试完整的品类筛选逻辑:")
        
        # 获取品类映射
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
        
        # 获取wdt.stock中的库存数据
        query_wdt = """
        SELECT 
            spec_name,
            SUM(stock_num) as total_stock,
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                WHEN warehouse_name LIKE '%京东%' OR warehouse_name LIKE '%JD%' THEN '京仓'
                WHEN warehouse_name LIKE '%云仓%' OR warehouse_name LIKE '%日日顺云仓%' THEN '云仓'
                WHEN warehouse_name = '统仓' THEN '统仓'
                WHEN warehouse_name LIKE '%金融%' THEN '金融仓'
                WHEN warehouse_name IN ('外部仓', '工程仓', '样品仓', '京东大件仓', '维修工厂不良品仓', '不良品仓', '礼品仓', '样壳仓', '周转机') THEN '常规仓'
                ELSE '常规仓'
            END as 仓库类型
        FROM stock 
        WHERE stock_num > 0
        AND spec_name IS NOT NULL AND spec_name != ''
        GROUP BY spec_name, 仓库类型
        """
        
        df_wdt = pd.read_sql(query_wdt, wdt_connection)
        logger.info(f"📦 wdt.stock库存数据总数: {len(df_wdt)}")
        
        # 添加品类信息
        df_wdt['品类'] = df_wdt['spec_name'].apply(lambda x: category_mapping.get(str(x).strip(), '其他'))
        
        # 测试洗衣机品类筛选
        washing_machine_data = df_wdt[df_wdt['品类'] == '洗衣机']
        logger.info(f"🧺 洗衣机品类数据: {len(washing_machine_data)} 条记录")
        
        if not washing_machine_data.empty:
            logger.info("🧺 洗衣机品类示例:")
            for _, row in washing_machine_data.head(5).iterrows():
                logger.info(f"  - {row['spec_name']}: {row['total_stock']} 件 ({row['仓库类型']})")
        
        # 测试其他品类
        categories = df_wdt['品类'].unique()
        logger.info(f"🏷️ 所有品类: {list(categories)}")
        
        for category in ['冰箱', '空调', '电视']:
            category_data = df_wdt[df_wdt['品类'] == category]
            logger.info(f"📦 {category}品类数据: {len(category_data)} 条记录")
        
        wdt_connection.close()
        date_connection.close()
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_category_filter() 