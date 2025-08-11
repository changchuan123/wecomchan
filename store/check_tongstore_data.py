#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查tongstore表格中的实际数据
专门查看热水器相关产品的数据
"""

import pymysql
import pandas as pd
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tongstore_data_check.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

class TongstoreDataChecker:
    """tongstore数据检查器"""
    
    def __init__(self):
        self.connection = None
        
    def connect_database(self) -> bool:
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def close_database(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def check_tongstore_structure(self):
        """检查tongstore表格结构"""
        if not self.connection:
            logger.error("数据库未连接")
            return
        
        try:
            cursor = self.connection.cursor()
            
            # 获取表格信息
            cursor.execute("SHOW TABLES LIKE '%tongstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到tongstore相关表格")
                return
            
            table_name = tables[0][0]
            logger.info(f"找到tongstore表格: {table_name}")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"tongstore表格列: {columns}")
            
            # 获取前几行数据查看格式
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
            sample_data = cursor.fetchall()
            
            logger.info("前5行数据:")
            for i, row in enumerate(sample_data):
                logger.info(f"  第{i+1}行: {row}")
            
        except Exception as e:
            logger.error(f"检查表格结构失败: {e}")
    
    def search_hot_water_heaters(self):
        """搜索热水器相关产品"""
        if not self.connection:
            logger.error("数据库未连接")
            return
        
        try:
            # 使用正确的列名
            stock_col = '__EMPTY_2'  # 总库存列
            available_col = '__EMPTY_3'  # 总可用库存列
            model_col = '__EMPTY_8'  # 商品型号列
            brand_col = '__EMPTY'  # 品牌列
            product_group_col = '__EMPTY_1'  # 产品组列
            
            # 搜索热水器相关产品
            query = f"""
            SELECT 
                `{model_col}` as 商品型号,
                `{brand_col}` as 品牌,
                `{product_group_col}` as 产品组,
                CAST(`{available_col}` AS SIGNED) as 可用库存,
                CAST(`{stock_col}` AS SIGNED) as 总库存
            FROM tongstore
            WHERE (
                `{model_col}` LIKE '%热水器%' 
                OR `{model_col}` LIKE '%EC%' 
                OR `{model_col}` LIKE '%ES%'
                OR `{model_col}` LIKE '%海尔%'
                OR `{brand_col}` LIKE '%海尔%'
            )
            AND `{model_col}` IS NOT NULL 
            AND `{model_col}` != ''
            AND `{model_col}` != '商品型号'
            AND `{available_col}` IS NOT NULL
            AND CAST(`{available_col}` AS SIGNED) > 0
            ORDER BY `{model_col}`
            LIMIT 50
            """
            
            logger.info("搜索热水器相关产品...")
            df = pd.read_sql(query, self.connection)
            
            if not df.empty:
                logger.info(f"找到 {len(df)} 个热水器相关产品:")
                for _, row in df.iterrows():
                    logger.info(f"  型号: {row['商品型号']}, 品牌: {row['品牌']}, 产品组: {row['产品组']}, 可用库存: {row['可用库存']}")
            else:
                logger.warning("未找到热水器相关产品")
                
        except Exception as e:
            logger.error(f"搜索热水器产品失败: {e}")
    
    def search_specific_models(self):
        """搜索特定的型号"""
        if not self.connection:
            logger.error("数据库未连接")
            return
        
        try:
            # 使用正确的列名
            stock_col = '__EMPTY_2'  # 总库存列
            available_col = '__EMPTY_3'  # 总可用库存列
            model_col = '__EMPTY_8'  # 商品型号列
            brand_col = '__EMPTY'  # 品牌列
            product_group_col = '__EMPTY_1'  # 产品组列
            
            # 搜索特定型号
            target_models = ['EC6002', 'EC8002', 'ES60H', 'EC8003', 'ES7', 'EC6001']
            
            for model in target_models:
                query = f"""
                SELECT 
                    `{model_col}` as 商品型号,
                    `{brand_col}` as 品牌,
                    `{product_group_col}` as 产品组,
                    CAST(`{available_col}` AS SIGNED) as 可用库存,
                    CAST(`{stock_col}` AS SIGNED) as 总库存
                FROM tongstore
                WHERE `{model_col}` LIKE '%{model}%'
                AND `{model_col}` IS NOT NULL 
                AND `{model_col}` != ''
                AND `{model_col}` != '商品型号'
                AND `{available_col}` IS NOT NULL
                AND CAST(`{available_col}` AS SIGNED) > 0
                ORDER BY `{model_col}`
                """
                
                logger.info(f"搜索型号 {model} 相关产品...")
                df = pd.read_sql(query, self.connection)
                
                if not df.empty:
                    logger.info(f"找到 {len(df)} 个 {model} 相关产品:")
                    for _, row in df.iterrows():
                        logger.info(f"  型号: {row['商品型号']}, 品牌: {row['品牌']}, 产品组: {row['产品组']}, 可用库存: {row['可用库存']}")
                else:
                    logger.info(f"未找到 {model} 相关产品")
                    
        except Exception as e:
            logger.error(f"搜索特定型号失败: {e}")
    
    def check_total_records(self):
        """检查总记录数"""
        if not self.connection:
            logger.error("数据库未连接")
            return
        
        try:
            # 检查总记录数
            query = """
            SELECT COUNT(*) as 总记录数
            FROM tongstore
            WHERE `__EMPTY_8` IS NOT NULL 
            AND `__EMPTY_8` != ''
            AND `__EMPTY_8` != '商品型号'
            AND `__EMPTY_3` IS NOT NULL
            AND CAST(`__EMPTY_3` AS SIGNED) > 0
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            
            logger.info(f"tongstore表格有效记录数: {result[0]}")
            
        except Exception as e:
            logger.error(f"检查总记录数失败: {e}")
    
    def run(self):
        """主运行函数"""
        logger.info("🚀 开始检查tongstore数据")
        
        try:
            # 连接数据库
            if not self.connect_database():
                return False
            
            # 检查表格结构
            logger.info("📋 步骤1: 检查表格结构")
            self.check_tongstore_structure()
            
            # 检查总记录数
            logger.info("📋 步骤2: 检查总记录数")
            self.check_total_records()
            
            # 搜索热水器相关产品
            logger.info("📋 步骤3: 搜索热水器相关产品")
            self.search_hot_water_heaters()
            
            # 搜索特定型号
            logger.info("📋 步骤4: 搜索特定型号")
            self.search_specific_models()
            
            logger.info("✅ tongstore数据检查完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 检查过程中发生错误: {e}")
            return False
        finally:
            self.close_database()

def main():
    """主函数"""
    checker = TongstoreDataChecker()
    checker.run()

if __name__ == "__main__":
    main() 