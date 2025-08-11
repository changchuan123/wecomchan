#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统仓匹配问题调试脚本
专门用于排查指定热水器产品在统仓中的匹配问题
"""

import pymysql
import pandas as pd
import logging
from typing import Dict, List, Tuple
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tongstore_debug.log', encoding='utf-8'),
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

# 需要排查的热水器产品
TARGET_PRODUCTS = [
    'EC6002-PT5U1',
    'EC8002H-PT5U1', 
    'ES60H-GD5(A)U1',
    'EC6001-PA6Pro',
    'EC8003-PV3U1',
    'ES7-Super2A'
]

class TongstoreDebugger:
    """统仓匹配调试器"""
    
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
    
    def get_matchstore_mapping(self) -> Dict[str, Dict[str, str]]:
        """获取matchstore映射关系"""
        if not self.connection:
            logger.error("数据库未连接")
            return {}
        
        try:
            # 获取matchstore表格
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%matchstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到matchstore相关表格")
                return {}
            
            table_name = tables[0][0]
            logger.info(f"找到matchstore表格: {table_name}")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"matchstore表格列: {columns}")
            
            # 构建查询 - 查找目标产品的映射关系
            target_products_str = "','".join(TARGET_PRODUCTS)
            query = f"""
            SELECT 规格名称, tongstore, 品类, 品牌
            FROM `{table_name}`
            WHERE 规格名称 IN ('{target_products_str}')
            AND tongstore IS NOT NULL AND tongstore != ''
            """
            
            df = pd.read_sql(query, self.connection)
            
            # 建立映射
            mapping = {}
            for _, row in df.iterrows():
                spec_name = str(row['规格名称']).strip()
                tong_name = str(row['tongstore']).strip()
                category = str(row['品类']).strip() if pd.notna(row['品类']) else ''
                brand = str(row['品牌']).strip() if pd.notna(row['品牌']) else ''
                
                if spec_name and tong_name:
                    mapping[spec_name] = {
                        'tongstore': tong_name,
                        '品类': category,
                        '品牌': brand
                    }
            
            logger.info(f"获取matchstore映射成功，共 {len(mapping)} 个目标产品的映射关系")
            return mapping
            
        except Exception as e:
            logger.error(f"获取matchstore映射失败: {e}")
            return {}
    
    def get_tongstore_table_info(self) -> Tuple[str, List[str]]:
        """获取tongstore表格信息"""
        if not self.connection:
            logger.error("数据库未连接")
            return "", []
        
        try:
            # 获取tongstore表格
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%tongstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到tongstore相关表格")
                return "", []
            
            table_name = tables[0][0]
            logger.info(f"找到tongstore表格: {table_name}")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"tongstore表格列: {columns}")
            
            return table_name, columns
            
        except Exception as e:
            logger.error(f"获取tongstore表格信息失败: {e}")
            return "", []
    
    def search_tongstore_data(self, table_name: str, target_names: List[str]) -> pd.DataFrame:
        """在tongstore中搜索目标产品数据"""
        if not self.connection or not table_name:
            logger.error("数据库未连接或表格名无效")
            return pd.DataFrame()
        
        try:
            # 使用正确的列名
            stock_col = '__EMPTY_2'  # 总库存列
            available_col = '__EMPTY_3'  # 总可用库存列
            model_col = '__EMPTY_8'  # 商品型号列
            brand_col = '__EMPTY'  # 品牌列
            product_group_col = '__EMPTY_1'  # 产品组列
            
            # 构建搜索条件 - 使用多种匹配方式
            search_conditions = []
            for name in target_names:
                # 转义特殊字符
                escaped_name = name.replace("'", "''").replace("%", "\\%").replace("_", "\\_")
                # 使用多种匹配方式
                search_conditions.append(f"(`{model_col}` = '{escaped_name}' OR `{model_col}` LIKE '%{escaped_name}%' OR `{model_col}` LIKE '%{name}%')")
            
            conditions_str = " OR ".join(search_conditions)
            query = f"""
            SELECT 
                `{model_col}` as 对应名称,
                `{brand_col}` as 品牌,
                `{product_group_col}` as 产品组,
                CAST(`{available_col}` AS SIGNED) as 可用库存,
                CAST(`{stock_col}` AS SIGNED) as 总库存
            FROM `{table_name}`
            WHERE ({conditions_str})
            AND `{model_col}` IS NOT NULL 
            AND `{model_col}` != ''
            AND `{model_col}` != '商品型号'
            AND `{available_col}` IS NOT NULL
            AND CAST(`{available_col}` AS SIGNED) > 0
            AND `{model_col}` NOT LIKE '%商品型号%'
            ORDER BY `{model_col}`
            """
            
            logger.info(f"执行tongstore搜索查询...")
            df = pd.read_sql(query, self.connection)
            
            if not df.empty:
                logger.info(f"tongstore搜索成功，找到 {len(df)} 条记录")
                return df
            else:
                logger.warning("tongstore搜索未找到任何匹配数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"tongstore搜索失败: {e}")
            return pd.DataFrame()
    
    def analyze_matching_issues(self):
        """分析匹配问题"""
        logger.info("🔍 开始分析统仓匹配问题...")
        
        # 1. 获取matchstore映射关系
        logger.info("📋 步骤1: 获取matchstore映射关系")
        mapping = self.get_matchstore_mapping()
        
        if not mapping:
            logger.error("❌ 未获取到任何目标产品的映射关系")
            return
        
        logger.info("✅ 获取到的映射关系:")
        for spec_name, info in mapping.items():
            logger.info(f"  {spec_name} -> tongstore: {info['tongstore']}, 品类: {info['品类']}, 品牌: {info['品牌']}")
        
        # 2. 获取tongstore表格信息
        logger.info("📋 步骤2: 获取tongstore表格信息")
        table_name, columns = self.get_tongstore_table_info()
        
        if not table_name:
            logger.error("❌ 未找到tongstore表格")
            return
        
        # 3. 搜索tongstore中的目标产品
        logger.info("📋 步骤3: 在tongstore中搜索目标产品")
        target_names = [info['tongstore'] for info in mapping.values()]
        tongstore_data = self.search_tongstore_data(table_name, target_names)
        
        if not tongstore_data.empty:
            logger.info("✅ 在tongstore中找到的数据:")
            for _, row in tongstore_data.iterrows():
                logger.info(f"  型号: {row['对应名称']}, 品牌: {row['品牌']}, 产品组: {row['产品组']}, 可用库存: {row['可用库存']}")
        else:
            logger.warning("⚠️ 在tongstore中未找到任何目标产品数据")
        
        # 4. 分析匹配问题
        logger.info("📋 步骤4: 分析匹配问题")
        
        # 检查每个目标产品
        for spec_name, info in mapping.items():
            logger.info(f"\n🔍 分析产品: {spec_name}")
            logger.info(f"  映射的tongstore名称: {info['tongstore']}")
            logger.info(f"  品类: {info['品类']}")
            logger.info(f"  品牌: {info['品牌']}")
            
            # 在tongstore数据中查找
            found = False
            for _, row in tongstore_data.iterrows():
                model_name = str(row['对应名称']).strip()
                if (model_name == info['tongstore'] or 
                    info['tongstore'] in model_name or 
                    model_name in info['tongstore']):
                    logger.info(f"  ✅ 找到匹配: {model_name} (可用库存: {row['可用库存']})")
                    found = True
                    break
            
            if not found:
                logger.warning(f"  ❌ 未找到匹配")
        
        # 5. 提供解决方案建议
        logger.info("\n📋 步骤5: 提供解决方案建议")
        
        if not tongstore_data.empty:
            logger.info("💡 建议:")
            logger.info("1. 检查matchstore中的tongstore映射是否正确")
            logger.info("2. 检查tongstore表格中的商品型号格式是否一致")
            logger.info("3. 考虑添加模糊匹配逻辑")
        else:
            logger.info("💡 建议:")
            logger.info("1. 检查这些产品是否在tongstore表格中存在")
            logger.info("2. 检查商品型号的命名规则是否一致")
            logger.info("3. 可能需要更新matchstore中的映射关系")
    
    def run(self):
        """主运行函数"""
        logger.info("🚀 开始统仓匹配问题调试")
        
        try:
            # 连接数据库
            if not self.connect_database():
                return False
            
            # 分析匹配问题
            self.analyze_matching_issues()
            
            logger.info("✅ 统仓匹配问题调试完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 调试过程中发生错误: {e}")
            return False
        finally:
            self.close_database()

def main():
    """主函数"""
    debugger = TongstoreDebugger()
    debugger.run()

if __name__ == "__main__":
    main() 