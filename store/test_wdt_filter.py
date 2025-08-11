#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wdt数据库筛选逻辑测试脚本
确保只获取常规仓和顺丰仓数据，其他所有仓位都被排除
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

def test_all_warehouse_types():
    """测试所有仓位类型的筛选逻辑"""
    logger.info("=== 测试wdt数据库所有仓位类型筛选 ===")
    
    try:
        wdt_conn = pymysql.connect(**DB_CONFIG_WDT)
        
        # 1. 查看所有仓位类型
        query_all = """
        SELECT DISTINCT warehouse_name, COUNT(*) as 记录数
        FROM stock 
        WHERE stock_num > 0
        GROUP BY warehouse_name
        ORDER BY warehouse_name
        """
        
        df_all = pd.read_sql(query_all, wdt_conn)
        print("=== wdt.stock 所有仓位类型 ===")
        print(df_all.to_string(index=False))
        
        # 2. 测试修复后的筛选逻辑
        query_fixed = """
        SELECT 
            spec_name as 规格名称,
            warehouse_name as 原始仓位名称,
            stock_num as 数量,
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END as 仓库类型
        FROM stock 
        WHERE stock_num > 0
        AND (
            warehouse_name = '常规仓' 
            OR warehouse_name LIKE '%顺丰%'
        )
        ORDER BY warehouse_name, spec_name
        LIMIT 50
        """
        
        df_fixed = pd.read_sql(query_fixed, wdt_conn)
        print("\n=== 修复后的筛选结果（前50条）===")
        print(df_fixed.to_string(index=False))
        
        # 3. 统计筛选结果
        query_stats = """
        SELECT 
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END as 仓库类型,
            COUNT(*) as 记录数,
            SUM(stock_num) as 总库存
        FROM stock 
        WHERE stock_num > 0
        AND (
            warehouse_name = '常规仓' 
            OR warehouse_name LIKE '%顺丰%'
        )
        GROUP BY 
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END
        ORDER BY 仓库类型
        """
        
        df_stats = pd.read_sql(query_stats, wdt_conn)
        print("\n=== 筛选结果统计 ===")
        print(df_stats.to_string(index=False))
        
        # 4. 检查是否还有京仓、云仓等数据被错误包含
        query_check = """
        SELECT 
            spec_name as 规格名称,
            warehouse_name as 原始仓位名称,
            stock_num as 数量
        FROM stock 
        WHERE stock_num > 0
        AND (
            warehouse_name = '常规仓' 
            OR warehouse_name LIKE '%顺丰%'
        )
        AND (
            warehouse_name LIKE '%京东%' 
            OR warehouse_name LIKE '%京仓%'
            OR warehouse_name LIKE '%云仓%'
            OR warehouse_name LIKE '%日日顺%'
        )
        ORDER BY warehouse_name, spec_name
        """
        
        df_check = pd.read_sql(query_check, wdt_conn)
        print("\n=== 检查是否还有京仓、云仓数据被错误包含 ===")
        if df_check.empty:
            print("✅ 没有京仓、云仓数据被错误包含")
        else:
            print("❌ 发现京仓、云仓数据被错误包含:")
            print(df_check.to_string(index=False))
        
        # 5. 检查具体问题产品的筛选结果
        query_specific = """
        SELECT 
            spec_name as 规格名称,
            warehouse_name as 原始仓位名称,
            stock_num as 数量,
            CASE 
                WHEN warehouse_name = '常规仓' THEN '常规仓'
                WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                ELSE '忽略'
            END as 仓库类型
        FROM stock 
        WHERE spec_name IN ('BC-93LTMPA', 'BCD-539WGHTDEDSDU1')
        AND stock_num > 0
        ORDER BY spec_name, warehouse_name
        """
        
        df_specific = pd.read_sql(query_specific, wdt_conn)
        print("\n=== 具体问题产品的筛选结果 ===")
        print(df_specific.to_string(index=False))
        
        wdt_conn.close()
        
    except Exception as e:
        logger.error(f"wdt数据库测试失败: {e}")

def main():
    """主函数"""
    logger.info("开始wdt数据库筛选逻辑测试")
    
    test_all_warehouse_types()
    
    logger.info("wdt数据库筛选逻辑测试完成")

if __name__ == "__main__":
    main() 