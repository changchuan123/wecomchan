#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查BC-93LTMPA在matchstore中的情况
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

def check_matchstore_bc93ltmpa():
    """详细检查BC-93LTMPA在matchstore中的情况"""
    try:
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("连接Date数据库成功")
        
        # 查找matchstore表格
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE '%matchstore%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.error("未找到matchstore相关表格")
            return
        
        table_name = tables[0][0]
        logger.info(f"找到matchstore表格: {table_name}")
        
        # 1. 检查是否有BC-93LTMPA的记录（不管映射字段是否为空）
        query_all = f"""
        SELECT *
        FROM `{table_name}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        df_all = pd.read_sql(query_all, connection)
        
        if not df_all.empty:
            logger.info(f"✅ 找到BC-93LTMPA的记录:")
            logger.info(f"记录数: {len(df_all)}")
            logger.info(f"数据: {df_all.to_dict('records')}")
            
            # 检查各个映射字段
            mapping_fields = ['jinrongstore', 'rrsstore', 'tongstore', 'jdstore']
            for field in mapping_fields:
                if field in df_all.columns:
                    value = df_all.iloc[0][field]
                    if pd.notna(value) and str(value).strip() != '' and str(value).strip() != 'nan':
                        logger.info(f"  ✅ {field}: {value}")
                    else:
                        logger.warning(f"  ❌ {field}: 空值或无效值")
                else:
                    logger.warning(f"  ❌ {field}: 字段不存在")
        else:
            logger.warning("❌ 未找到BC-93LTMPA的记录")
            
            # 2. 检查是否有类似的记录
            query_similar = f"""
            SELECT 规格名称, jinrongstore, rrsstore, tongstore, jdstore
            FROM `{table_name}`
            WHERE 规格名称 LIKE '%BC-93LTMPA%'
            OR 规格名称 LIKE '%BC93LTMPA%'
            """
            
            df_similar = pd.read_sql(query_similar, connection)
            if not df_similar.empty:
                logger.info(f"找到类似的规格名称:")
                logger.info(f"数据: {df_similar.to_dict('records')}")
            
            # 3. 检查是否有包含BC-93LTMPA的映射字段
            query_in_mapping = f"""
            SELECT 规格名称, jinrongstore, rrsstore, tongstore, jdstore
            FROM `{table_name}`
            WHERE jinrongstore LIKE '%BC-93LTMPA%'
            OR rrsstore LIKE '%BC-93LTMPA%'
            OR tongstore LIKE '%BC-93LTMPA%'
            OR jdstore LIKE '%BC-93LTMPA%'
            """
            
            df_in_mapping = pd.read_sql(query_in_mapping, connection)
            if not df_in_mapping.empty:
                logger.info(f"在映射字段中找到BC-93LTMPA:")
                logger.info(f"数据: {df_in_mapping.to_dict('records')}")
        
        # 4. 检查matchstore表格的结构
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        logger.info(f"matchstore表格结构:")
        for col in columns:
            logger.info(f"  {col[0]}: {col[1]}")
        
        # 5. 检查matchstore表格的总记录数
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        total_count = cursor.fetchone()[0]
        logger.info(f"matchstore表格总记录数: {total_count}")
        
        # 6. 检查有多少记录有规格名称但没有映射关系
        query_no_mapping = f"""
        SELECT COUNT(*) as count
        FROM `{table_name}`
        WHERE 规格名称 IS NOT NULL 
        AND 规格名称 != ''
        AND 规格名称 != 'nan'
        AND 规格名称 != '规格名称'
        AND (
            jinrongstore IS NULL OR jinrongstore = '' OR jinrongstore = 'nan'
        )
        AND (
            rrsstore IS NULL OR rrsstore = '' OR rrsstore = 'nan'
        )
        AND (
            tongstore IS NULL OR tongstore = '' OR tongstore = 'nan'
        )
        AND (
            jdstore IS NULL OR jdstore = '' OR jdstore = 'nan'
        )
        """
        
        cursor.execute(query_no_mapping)
        no_mapping_count = cursor.fetchone()[0]
        logger.info(f"有规格名称但没有映射关系的记录数: {no_mapping_count}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查matchstore失败: {e}")

def main():
    """主函数"""
    logger.info("🔍 详细检查BC-93LTMPA在matchstore中的情况...")
    check_matchstore_bc93ltmpa()
    logger.info("✅ 检查完成")

if __name__ == "__main__":
    main() 