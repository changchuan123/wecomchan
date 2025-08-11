#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门检查BC-93LTMPA型号的数据情况
检查映射关系和各个数据库中的库存数据
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

def check_matchstore_mapping():
    """检查BC-93LTMPA在matchstore中的映射关系"""
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
        
        # 查询BC-93LTMPA的映射关系
        query = f"""
        SELECT *
        FROM `{table_name}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        df = pd.read_sql(query, connection)
        
        if not df.empty:
            logger.info(f"✅ 找到BC-93LTMPA的映射关系:")
            logger.info(f"数据: {df.to_dict('records')}")
            
            # 检查各个库位的映射
            for col in df.columns:
                value = df.iloc[0][col]
                if pd.notna(value) and str(value).strip() != '' and str(value).strip() != 'nan':
                    logger.info(f"  {col}: {value}")
        else:
            logger.warning("❌ 未找到BC-93LTMPA的映射关系")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查matchstore映射失败: {e}")

def check_wdt_stock():
    """检查BC-93LTMPA在wdt.stock中的数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG_WDT)
        logger.info("连接wdt数据库成功")
        
        # 直接查询BC-93LTMPA
        query = """
        SELECT spec_name, avaliable_num, warehouse_name
        FROM stock 
        WHERE spec_name = 'BC-93LTMPA'
        AND avaliable_num > 0
        """
        
        df = pd.read_sql(query, connection)
        
        if not df.empty:
            logger.info(f"✅ 在wdt.stock中找到BC-93LTMPA数据:")
            logger.info(f"数据: {df.to_dict('records')}")
        else:
            logger.warning("❌ 在wdt.stock中未找到BC-93LTMPA数据")
            
            # 检查是否有类似的数据
            query_similar = """
            SELECT spec_name, avaliable_num, warehouse_name
            FROM stock 
            WHERE spec_name LIKE '%BC-93LTMPA%'
            """
            
            df_similar = pd.read_sql(query_similar, connection)
            if not df_similar.empty:
                logger.info(f"找到类似的规格名称: {df_similar.to_dict('records')}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查wdt.stock失败: {e}")

def check_jinrongstore():
    """检查BC-93LTMPA在jinrongstore中的数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("连接Date数据库成功")
        
        # 查找jinrongstore表格
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE '%jinrongstore%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("未找到jinrongstore相关表格")
            return
        
        table_name = tables[0][0]
        logger.info(f"找到jinrongstore表格: {table_name}")
        
        # 先获取映射关系
        mapping_query = f"""
        SELECT jinrongstore
        FROM `{table_name.replace('jinrongstore', 'matchstore')}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        try:
            mapping_df = pd.read_sql(mapping_query, connection)
            if not mapping_df.empty:
                jinrong_name = mapping_df.iloc[0]['jinrongstore']
                logger.info(f"BC-93LTMPA对应的jinrongstore名称: {jinrong_name}")
                
                # 查询jinrongstore数据
                query = f"""
                SELECT *
                FROM `{table_name}`
                WHERE 型号 = '{jinrong_name}'
                """
                
                df = pd.read_sql(query, connection)
                
                if not df.empty:
                    logger.info(f"✅ 在jinrongstore中找到数据:")
                    logger.info(f"数据: {df.to_dict('records')}")
                else:
                    logger.warning(f"❌ 在jinrongstore中未找到名称 '{jinrong_name}' 的数据")
            else:
                logger.warning("❌ 未找到BC-93LTMPA的jinrongstore映射")
        except Exception as e:
            logger.error(f"查询jinrongstore映射失败: {e}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查jinrongstore失败: {e}")

def check_jdstore():
    """检查BC-93LTMPA在jdstore中的数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("连接Date数据库成功")
        
        # 查找jdstore表格
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE '%jdstore%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("未找到jdstore相关表格")
            return
        
        table_name = tables[0][0]
        logger.info(f"找到jdstore表格: {table_name}")
        
        # 先获取映射关系
        mapping_query = f"""
        SELECT jdstore
        FROM `{table_name.replace('jdstore', 'matchstore')}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        try:
            mapping_df = pd.read_sql(mapping_query, connection)
            if not mapping_df.empty:
                jd_name = mapping_df.iloc[0]['jdstore']
                logger.info(f"BC-93LTMPA对应的jdstore名称: {jd_name}")
                
                # 查询jdstore数据
                query = f"""
                SELECT *
                FROM `{table_name}`
                WHERE 事业部商品编码 = '{jd_name}'
                """
                
                df = pd.read_sql(query, connection)
                
                if not df.empty:
                    logger.info(f"✅ 在jdstore中找到数据:")
                    logger.info(f"数据: {df.to_dict('records')}")
                else:
                    logger.warning(f"❌ 在jdstore中未找到名称 '{jd_name}' 的数据")
            else:
                logger.warning("❌ 未找到BC-93LTMPA的jdstore映射")
        except Exception as e:
            logger.error(f"查询jdstore映射失败: {e}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查jdstore失败: {e}")

def check_rrsstore():
    """检查BC-93LTMPA在rrsstore中的数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("连接Date数据库成功")
        
        # 查找rrsstore表格
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE '%rrsstore%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("未找到rrsstore相关表格")
            return
        
        table_name = tables[0][0]
        logger.info(f"找到rrsstore表格: {table_name}")
        
        # 先获取映射关系
        mapping_query = f"""
        SELECT rrsstore
        FROM `{table_name.replace('rrsstore', 'matchstore')}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        try:
            mapping_df = pd.read_sql(mapping_query, connection)
            if not mapping_df.empty:
                rrs_name = mapping_df.iloc[0]['rrsstore']
                logger.info(f"BC-93LTMPA对应的rrsstore名称: {rrs_name}")
                
                # 查询rrsstore数据
                query = f"""
                SELECT *
                FROM `{table_name}`
                WHERE 商品编码 = '{rrs_name}'
                """
                
                df = pd.read_sql(query, connection)
                
                if not df.empty:
                    logger.info(f"✅ 在rrsstore中找到数据:")
                    logger.info(f"数据: {df.to_dict('records')}")
                else:
                    logger.warning(f"❌ 在rrsstore中未找到名称 '{rrs_name}' 的数据")
            else:
                logger.warning("❌ 未找到BC-93LTMPA的rrsstore映射")
        except Exception as e:
            logger.error(f"查询rrsstore映射失败: {e}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查rrsstore失败: {e}")

def check_tongstore():
    """检查BC-93LTMPA在tongstore中的数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG_DATE)
        logger.info("连接Date数据库成功")
        
        # 查找tongstore表格
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE '%tongstore%'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("未找到tongstore相关表格")
            return
        
        table_name = tables[0][0]
        logger.info(f"找到tongstore表格: {table_name}")
        
        # 先获取映射关系
        mapping_query = f"""
        SELECT tongstore
        FROM `{table_name.replace('tongstore', 'matchstore')}`
        WHERE 规格名称 = 'BC-93LTMPA'
        """
        
        try:
            mapping_df = pd.read_sql(mapping_query, connection)
            if not mapping_df.empty:
                tong_name = mapping_df.iloc[0]['tongstore']
                logger.info(f"BC-93LTMPA对应的tongstore名称: {tong_name}")
                
                # 查询tongstore数据
                query = f"""
                SELECT *
                FROM `{table_name}`
                WHERE __EMPTY_8 = '{tong_name}'
                """
                
                df = pd.read_sql(query, connection)
                
                if not df.empty:
                    logger.info(f"✅ 在tongstore中找到数据:")
                    logger.info(f"数据: {df.to_dict('records')}")
                else:
                    logger.warning(f"❌ 在tongstore中未找到名称 '{tong_name}' 的数据")
                    
                    # 尝试模糊匹配
                    query_fuzzy = f"""
                    SELECT *
                    FROM `{table_name}`
                    WHERE __EMPTY_8 LIKE '%{tong_name}%'
                    """
                    
                    df_fuzzy = pd.read_sql(query_fuzzy, connection)
                    if not df_fuzzy.empty:
                        logger.info(f"找到模糊匹配的数据: {df_fuzzy.to_dict('records')}")
            else:
                logger.warning("❌ 未找到BC-93LTMPA的tongstore映射")
        except Exception as e:
            logger.error(f"查询tongstore映射失败: {e}")
        
        connection.close()
        
    except Exception as e:
        logger.error(f"检查tongstore失败: {e}")

def main():
    """主函数"""
    logger.info("🔍 开始检查BC-93LTMPA型号的数据情况...")
    
    # 1. 检查映射关系
    logger.info("\n" + "="*50)
    logger.info("1. 检查matchstore映射关系")
    check_matchstore_mapping()
    
    # 2. 检查各个数据库
    logger.info("\n" + "="*50)
    logger.info("2. 检查wdt.stock数据")
    check_wdt_stock()
    
    logger.info("\n" + "="*50)
    logger.info("3. 检查jinrongstore数据")
    check_jinrongstore()
    
    logger.info("\n" + "="*50)
    logger.info("4. 检查jdstore数据")
    check_jdstore()
    
    logger.info("\n" + "="*50)
    logger.info("5. 检查rrsstore数据")
    check_rrsstore()
    
    logger.info("\n" + "="*50)
    logger.info("6. 检查tongstore数据")
    check_tongstore()
    
    logger.info("\n" + "="*50)
    logger.info("✅ 检查完成")

if __name__ == "__main__":
    main() 