#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存分析脚本
功能：从多个数据库表格获取库存数据，按仓库类型聚合，生成报告并推送到企业微信
"""

import pymysql
import pandas as pd
import json
import requests
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple
import numpy as np
import time
import subprocess
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('库存分析.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
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

# 企业微信配置
WECOM_CONFIG = {
    'corpid': os.getenv('WECOM_CID', ''),
    'corpsecret': os.getenv('WECOM_SECRET', ''),
    'agentid': os.getenv('WECOM_AID', ''),
    'touser': os.getenv('WECOM_TOUID', 'weicungang')
}

# EdgeOne部署配置
EDGEONE_CONFIG = {
    'cli_path': "/Users/weixiaogang/.npm-global/bin/edgeone",
    'token': "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=",
    'project_name': "sales-report",
    'domain': "edge.haierht.cn"
}

class InventoryAnalyzer:
    """库存分析器"""
    
    def __init__(self):
        self.wdt_connection = None
        self.date_connection = None
        
    def connect_databases(self) -> bool:
        """连接数据库"""
        try:
            self.wdt_connection = pymysql.connect(**DB_CONFIG_WDT)
            self.date_connection = pymysql.connect(**DB_CONFIG_DATE)
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def close_databases(self):
        """关闭数据库连接"""
        if self.wdt_connection:
            self.wdt_connection.close()
        if self.date_connection:
            self.date_connection.close()
        logger.info("数据库连接已关闭")
    
    def get_wdt_stock_data(self, spec_mapping: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """获取wdt数据库的stock表格数据，根据规格名称映射查询"""
        if not self.wdt_connection:
            logger.error("wdt数据库未连接")
            return pd.DataFrame()
        
        if not spec_mapping:
            logger.warning("没有规格名称映射，无法查询wdt数据")
            return pd.DataFrame()
        
        try:
            # 获取所有有效的规格名称
            spec_names = list(spec_mapping.keys())
            
            if not spec_names:
                logger.warning("没有有效的规格名称")
                return pd.DataFrame()
            
            # 构建批量查询 - 使用字符串拼接而不是参数化查询
            spec_names_str = "','".join(spec_names)
            query = f"""
            SELECT 
                spec_name as 规格名称,
                stock_num as 数量,
                CASE 
                    WHEN warehouse_name = '常规仓' THEN '常规仓'
                    WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                    ELSE '忽略'
                END as 仓库类型
            FROM stock 
            WHERE spec_name IN ('{spec_names_str}')
            AND (warehouse_name = '常规仓' OR warehouse_name LIKE '%顺丰%')
            AND stock_num > 0
            """
            
            df = pd.read_sql(query, self.wdt_connection)
            
            if not df.empty:
                logger.info(f"从wdt.stock获取数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("未从wdt.stock获取到任何数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取wdt数据失败: {e}")
            return pd.DataFrame()
    
    def get_jinrongstore_data(self, spec_mapping: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """获取jinrongstore数据：根据规格名称映射查询"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        if not spec_mapping:
            logger.warning("没有规格名称映射，无法查询jinrongstore数据")
            return pd.DataFrame()
        
        try:
            # 获取所有表格
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%jinrongstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到jinrongstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到jinrongstore表格: {table_name}")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"jinrongstore表格列: {columns}")
            
            # 精确查找列名
            model_col = '型号'
            quantity_col = '数量'
            redeemed_col = '已赎货'
            
            # 验证列是否存在
            if model_col not in columns or quantity_col not in columns or redeemed_col not in columns:
                logger.warning("jinrongstore表格中缺少必要列")
                return pd.DataFrame()
            
            # 获取所有jinrongstore对应的名称
            jinrong_names = []
            spec_name_mapping = {}
            
            for spec_name, warehouse_names in spec_mapping.items():
                if 'jinrongstore' in warehouse_names:
                    jinrong_name = warehouse_names['jinrongstore']
                    jinrong_names.append(jinrong_name)
                    spec_name_mapping[jinrong_name] = spec_name
            
            if not jinrong_names:
                logger.warning("没有找到jinrongstore对应的名称")
                return pd.DataFrame()
            
            # 构建批量查询
            jinrong_names_str = "','".join(jinrong_names)
            query = f"""
            SELECT 
                `{model_col}` as 对应名称,
                (`{quantity_col}` - `{redeemed_col}`) as 数量
            FROM `{table_name}`
            WHERE `{model_col}` IN ('{jinrong_names_str}')
            AND (`{quantity_col}` - `{redeemed_col}`) > 0
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            if not df.empty:
                # 添加规格名称和仓库类型
                df['规格名称'] = df['对应名称'].map(spec_name_mapping)
                df['仓库类型'] = '金融仓'
                df = df.drop('对应名称', axis=1)
                
                logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("未从jinrongstore获取到任何数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取jinrongstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_rrsstore_data(self, spec_mapping: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """获取rrsstore数据：根据规格名称映射查询"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        if not spec_mapping:
            logger.warning("没有规格名称映射，无法查询rrsstore数据")
            return pd.DataFrame()
        
        try:
            # 获取所有表格
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%rrsstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到rrsstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到rrsstore表格: {table_name}")
            
            # 精确使用指定的列名
            model_col = '商品编码'
            quantity_col = '可用库存数量'
            
            # 获取表结构验证
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"rrsstore表格列: {columns}")
            
            # 如果指定列不存在，使用实际存在的列
            if model_col not in columns:
                model_col = '社会化物料编码'  # 备选
            if quantity_col not in columns:
                quantity_col = '可用库存'  # 备选
            
            if model_col not in columns or quantity_col not in columns:
                logger.warning("rrsstore表格中缺少必要列")
                return pd.DataFrame()
            
            # 获取所有rrsstore对应的名称
            rrs_names = []
            spec_name_mapping = {}
            
            for spec_name, warehouse_names in spec_mapping.items():
                if 'rrsstore' in warehouse_names:
                    rrs_name = warehouse_names['rrsstore']
                    rrs_names.append(rrs_name)
                    spec_name_mapping[rrs_name] = spec_name
            
            if not rrs_names:
                logger.warning("没有找到rrsstore对应的名称")
                return pd.DataFrame()
            
            # 构建批量查询
            rrs_names_str = "','".join(rrs_names)
            query = f"""
            SELECT 
                `{model_col}` as 对应名称,
                CAST(`{quantity_col}` AS SIGNED) as 数量
            FROM `{table_name}`
            WHERE `{model_col}` IN ('{rrs_names_str}')
            AND CAST(`{quantity_col}` AS SIGNED) > 0
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            if not df.empty:
                # 添加规格名称和仓库类型
                df['规格名称'] = df['对应名称'].map(spec_name_mapping)
                df['仓库类型'] = '云仓'
                df = df.drop('对应名称', axis=1)
                
                logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("未从rrsstore获取到任何数据")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取rrsstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_tongstore_data(self, spec_mapping: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """获取tongstore数据：根据规格名称映射查询"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        if not spec_mapping:
            logger.warning("没有规格名称映射，无法查询tongstore数据")
            return pd.DataFrame()
        
        try:
            # 获取所有表格
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%tongstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到tongstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到tongstore表格: {table_name}")
            
            # 获取前10行数据来分析结构
            query_sample = f"SELECT * FROM `{table_name}` LIMIT 10"
            df_sample = pd.read_sql(query_sample, self.date_connection)
            
            logger.info(f"tongstore数据预览: \n{df_sample.to_string()}")
            
            # 根据实际数据结构确定列名
            columns = df_sample.columns.tolist()
            logger.info(f"tongstore所有列: {columns}")
            
            # 根据数据预览，确定正确的列名
            # 从预览数据看，商品名称在__EMPTY_1列，数量在__EMPTY_2列
            product_col_actual = '__EMPTY_1'  # 商品名称列
            quantity_col_actual = '__EMPTY_2'  # 数量列
            
            logger.info(f"使用列: {product_col_actual} 作为商品名称, {quantity_col_actual} 作为数量")
            
            # 获取所有tongstore对应的名称
            tong_names = []
            spec_name_mapping = {}
            
            for spec_name, warehouse_names in spec_mapping.items():
                if 'tongstore' in warehouse_names:
                    tong_name = warehouse_names['tongstore']
                    tong_names.append(tong_name)
                    spec_name_mapping[tong_name] = spec_name
            
            if not tong_names:
                logger.warning("没有找到tongstore对应的名称")
                return pd.DataFrame()
            
            # 构建批量查询
            tong_names_str = "','".join(tong_names)
            query = f"""
            SELECT 
                `{product_col_actual}` as 对应名称,
                CAST(`{quantity_col_actual}` AS SIGNED) as 数量
            FROM `{table_name}`
            WHERE `{product_col_actual}` IN ('{tong_names_str}')
            AND `{product_col_actual}` IS NOT NULL 
            AND `{product_col_actual}` != ''
            AND `{product_col_actual}` != '_EMPTY_7'
            AND `{quantity_col_actual}` IS NOT NULL
            AND CAST(`{quantity_col_actual}` AS SIGNED) > 0
            AND `{product_col_actual}` != '商品名称'  -- 排除标题行
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            if not df.empty:
                # 添加规格名称和仓库类型
                df['规格名称'] = df['对应名称'].map(spec_name_mapping)
                df['仓库类型'] = '统仓'
                df = df.drop('对应名称', axis=1)
                
                logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("未从tongstore获取到任何数据")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取tongstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_jdstore_data(self, spec_mapping: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """获取jdstore数据：根据规格名称映射查询"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        if not spec_mapping:
            logger.warning("没有规格名称映射，无法查询jdstore数据")
            return pd.DataFrame()
        
        try:
            # 获取所有表格
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%jdstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到jdstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到jdstore表格: {table_name}")
            
            # 精确使用指定的列名
            model_col = '事业部商品编码'
            quantity_col = '可用库存'
            
            # 获取表结构验证
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"jdstore表格列: {columns}")
            
            # 验证列是否存在
            if model_col not in columns or quantity_col not in columns:
                logger.warning("jdstore表格中缺少必要列")
                return pd.DataFrame()
            
            # 获取所有jdstore对应的名称
            jd_names = []
            spec_name_mapping = {}
            
            for spec_name, warehouse_names in spec_mapping.items():
                if 'jdstore' in warehouse_names:
                    jd_name = warehouse_names['jdstore']
                    jd_names.append(jd_name)
                    spec_name_mapping[jd_name] = spec_name
            
            if not jd_names:
                logger.warning("没有找到jdstore对应的名称")
                return pd.DataFrame()
            
            # 构建批量查询
            jd_names_str = "','".join(jd_names)
            query = f"""
            SELECT 
                `{model_col}` as 对应名称,
                CAST(`{quantity_col}` AS SIGNED) as 数量
            FROM `{table_name}`
            WHERE `{model_col}` IN ('{jd_names_str}')
            AND CAST(`{quantity_col}` AS SIGNED) > 0
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            if not df.empty:
                # 添加规格名称和仓库类型
                df['规格名称'] = df['对应名称'].map(spec_name_mapping)
                df['仓库类型'] = '京仓'
                df = df.drop('对应名称', axis=1)
                
                logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("未从jdstore获取到任何数据")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取jdstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_matchstore_mapping(self) -> Dict[str, Dict[str, str]]:
        """获取matchstore映射关系：规格名称作为最终产品名，返回每个规格名称在各个库位的对应名称"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return {}
        
        try:
            # 获取所有表格
            cursor = self.date_connection.cursor()
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
            
            # 使用规格名称作为最终产品名，并建立映射关系
            mapping = {}
            
            # 精确查找列名
            spec_col = '规格名称'
            
            # 需要映射的列 - 使用实际的列名
            mapping_columns = {
                'jinrongstore': 'jinrongstore',
                'tongstore': 'tongstore', 
                'jdstore': 'jdstore',
                'rrsstore': 'rrsstore'
            }
            
            # 验证列是否存在
            available_columns = [col for col in mapping_columns.keys() if col in columns]
            if spec_col not in columns or not available_columns:
                logger.warning("matchstore表格中缺少必要列")
                return {}
            
            # 构建查询 - 只获取有规格名称的记录
            select_cols = ', '.join([f'`{col}`' for col in available_columns])
            query = f"""
            SELECT `{spec_col}`, {select_cols}
            FROM `{table_name}`
            WHERE `{spec_col}` IS NOT NULL AND `{spec_col}` != '' AND `{spec_col}` != 'nan'
            AND `{spec_col}` != 'None' AND `{spec_col}` != '规格名称'
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            # 建立映射：对于每个规格名称，记录它在各个库位的对应名称
            for _, row in df.iterrows():
                spec_name = str(row[spec_col]).strip()
                
                # 只有当规格名称有效时才建立映射
                if spec_name and spec_name != 'nan' and spec_name != 'None' and spec_name != '规格名称':
                    # 为每个规格名称创建一个字典，记录它在各个库位的对应名称
                    spec_mapping = {}
                    
                    for col in available_columns:
                        value = str(row[col]).strip() if pd.notna(row[col]) and str(row[col]).strip() != '' else None
                        if value and value != 'nan' and value != 'None' and value != col:
                            spec_mapping[col] = value
                    
                    # 只有当至少有一个库位有对应名称时，才添加到映射中
                    if spec_mapping:
                        mapping[spec_name] = spec_mapping
            
            logger.info(f"获取matchstore映射成功，共 {len(mapping)} 个规格名称的映射关系")
            return mapping
            
        except Exception as e:
            logger.error(f"获取matchstore数据失败: {e}")
            return {}
    
    def unify_product_names(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """统一产品名称：使用规格名称作为最终产品名，只保留有映射关系的数据"""
        if df.empty:
            return df
        
        # 只保留有映射关系的数据
        if mapping:
            # 创建映射后的数据框
            mapped_data = []
            for _, row in df.iterrows():
                product_name = str(row['产品名称']).strip()
                # 严格匹配：只有完全匹配的数据才保留
                if product_name in mapping:
                    # 只保留有映射关系的数据
                    new_row = row.copy()
                    new_row['规格名称'] = mapping[product_name]
                    mapped_data.append(new_row)
            
            if mapped_data:
                result_df = pd.DataFrame(mapped_data)
                logger.info(f"统一产品名称完成，保留 {len(result_df)} 条有映射关系的数据")
                return result_df
            else:
                logger.warning("没有找到任何有映射关系的数据")
                return pd.DataFrame()
        else:
            # 如果没有映射关系，返回空数据框
            logger.warning("没有映射关系，返回空数据")
            return pd.DataFrame()
    
    def aggregate_inventory_data(self) -> pd.DataFrame:
        """聚合所有库存数据：只统计有映射关系的数据"""
        logger.info("开始聚合库存数据")
        
        # 获取映射关系
        mapping = self.get_matchstore_mapping()
        
        if not mapping:
            logger.warning("没有获取到有效的映射关系，无法进行数据聚合")
            return pd.DataFrame()
        
        # 获取各仓库数据
        all_data = []
        
        # wdt数据
        wdt_data = self.get_wdt_stock_data(mapping)
        if not wdt_data.empty:
            all_data.append(wdt_data)
        
        # jinrongstore数据
        jinrong_data = self.get_jinrongstore_data(mapping)
        if not jinrong_data.empty:
            all_data.append(jinrong_data)
        
        # rrsstore数据
        rrs_data = self.get_rrsstore_data(mapping)
        if not rrs_data.empty:
            all_data.append(rrs_data)
        
        # tongstore数据
        tong_data = self.get_tongstore_data(mapping)
        if not tong_data.empty:
            all_data.append(tong_data)
        
        # jdstore数据
        jd_data = self.get_jdstore_data(mapping)
        if not jd_data.empty:
            all_data.append(jd_data)
        
        if not all_data:
            logger.warning("未获取到任何有效的库存数据")
            return pd.DataFrame()
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 确保数量列是数值类型
        combined_df['数量'] = pd.to_numeric(combined_df['数量'], errors='coerce').fillna(0)
        
        # 按规格名称、仓库类型聚合
        result_df = combined_df.groupby(['规格名称', '仓库类型']).agg({
            '数量': 'sum'
        }).reset_index()
        
        # 计算合计数量（只统计有映射关系的数据）
        total_df = result_df.groupby(['规格名称']).agg({
            '数量': 'sum'
        }).reset_index()
        total_df = total_df.rename(columns={'数量': '合计数量'})
        
        # 合并数据
        final_df = result_df.merge(total_df, on=['规格名称'], how='left')
        
        # 重命名数量列为到仓位数量
        final_df = final_df.rename(columns={'数量': '到仓位数量'})
        
        # 重新排序列
        final_df = final_df[['规格名称', '仓库类型', '合计数量', '到仓位数量']]
        
        # 确保数值列是数值类型
        final_df['合计数量'] = pd.to_numeric(final_df['合计数量'], errors='coerce').fillna(0)
        final_df['到仓位数量'] = pd.to_numeric(final_df['到仓位数量'], errors='coerce').fillna(0)
        
        logger.info(f"聚合完成，共 {len(final_df)} 条记录（只包含有映射关系的数据）")
        return final_df
    
    def get_category_mapping(self) -> Dict[str, str]:
        """获取品类映射关系"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return {}
        
        try:
            # 获取matchstore表格
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%matchstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到matchstore相关表格")
                return {}
            
            table_name = tables[0][0]
            
            # 获取品类映射
            query = f"""
            SELECT 规格名称, 品类
            FROM `{table_name}`
            WHERE 规格名称 IS NOT NULL AND 规格名称 != ''
            AND 品类 IS NOT NULL AND 品类 != ''
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            # 建立映射
            category_mapping = {}
            for _, row in df.iterrows():
                spec_name = str(row['规格名称']).strip()
                category = str(row['品类']).strip()
                if spec_name and category and category != 'nan':
                    category_mapping[spec_name] = category
            
            logger.info(f"获取品类映射成功，共 {len(category_mapping)} 条映射关系")
            return category_mapping
            
        except Exception as e:
            logger.error(f"获取品类映射失败: {e}")
            return {}
    
    def create_summary_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建汇总表格：按品类和型号汇总，仓库类型作为列"""
        if df.empty:
            return pd.DataFrame()
        
        # 获取品类映射
        category_mapping = self.get_category_mapping()
        
        # 添加品类信息
        df['品类'] = df['规格名称'].apply(lambda x: category_mapping.get(str(x).strip(), '其他'))
        
        # 将仓库类型转换为列
        pivot_df = df.pivot_table(
            index=['品类', '规格名称'],
            columns='仓库类型',
            values='到仓位数量',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # 计算合计库存
        warehouse_columns = ['常规仓', '顺丰仓', '京仓', '云仓', '统仓', '金融仓']
        for col in warehouse_columns:
            if col not in pivot_df.columns:
                pivot_df[col] = 0
        
        pivot_df['合计库存'] = pivot_df[warehouse_columns].sum(axis=1)
        
        # 重新排序列
        columns = ['品类', '规格名称', '合计库存'] + warehouse_columns
        pivot_df = pivot_df[columns]
        
        # 重命名列 - 统一使用规格名称
        pivot_df = pivot_df.rename(columns={'规格名称': '规格名称'})
        
        # 按合计数量排序：先按品类合计数量排序，再按单品合计数量排序
        # 计算每个品类的合计数量
        category_totals = pivot_df.groupby('品类')['合计库存'].sum().sort_values(ascending=False)
        
        # 按品类合计数量排序，然后按单品合计数量排序
        pivot_df['品类排序'] = pivot_df['品类'].map(category_totals)
        pivot_df = pivot_df.sort_values(['品类排序', '合计库存'], ascending=[False, False])
        pivot_df = pivot_df.drop('品类排序', axis=1)
        
        logger.info(f"汇总表格创建完成，共 {len(pivot_df)} 条记录")
        return pivot_df
    
    def generate_report(self, df: pd.DataFrame) -> str:
        """生成报告"""
        if df.empty:
            return "暂无库存数据"
        
        # 创建汇总表格
        summary_df = self.create_summary_table(df)
        
        # 获取所有品类
        categories = summary_df['品类'].unique().tolist()
        
        # 生成HTML表格
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>库存分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                .filters {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                .filters label {{ margin-right: 15px; font-weight: bold; }}
                .filters select {{ padding: 5px; margin-right: 20px; border: 1px solid #ddd; border-radius: 3px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 12px; }}
                th {{ background-color: #f2f2f2; font-weight: bold; position: sticky; top: 0; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .number {{ text-align: right; font-family: monospace; }}
                .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-style: italic; }}
                .category-row {{ background-color: #e3f2fd !important; font-weight: bold; }}
                .product-row {{ display: table-row; }}
                .hidden {{ display: none; }}
            </style>
            <script>
                // 存储所有数据
                let allData = {summary_df.to_dict('records')};
                
                function updateProductFilter() {{
                    const categoryFilter = document.getElementById('categoryFilter').value;
                    const productFilter = document.getElementById('productFilter');
                    
                    // 清空产品筛选
                    productFilter.innerHTML = '<option value="">全部规格名称</option>';
                    
                    if (categoryFilter) {{
                        // 获取该品类下的所有产品，按数量排序
                        const categoryProducts = allData
                            .filter(item => item.品类 === categoryFilter)
                            .sort((a, b) => b.合计库存 - a.合计库存);
                        
                        categoryProducts.forEach(item => {{
                            const option = document.createElement('option');
                            option.value = item.规格名称;
                            option.textContent = `${{item.规格名称}} (${{item.合计库存.toLocaleString()}})`;
                            productFilter.appendChild(option);
                        }});
                    }}
                    
                    filterTable();
                }}
                
                function filterTable() {{
                    const categoryFilter = document.getElementById('categoryFilter').value;
                    const productFilter = document.getElementById('productFilter').value;
                    const rows = document.querySelectorAll('tbody tr');
                    let visibleCount = 0;
                    
                    rows.forEach(row => {{
                        const categoryCell = row.cells[0];
                        const productCell = row.cells[1];
                        
                        if (!categoryCell || !productCell) return;
                        
                        const category = categoryCell.textContent.trim();
                        const product = productCell.textContent.trim();
                        
                        // 检查是否是品类行（包含"小计"字样）
                        const isCategoryRow = category.includes('小计');
                        
                        if (isCategoryRow) {{
                            // 品类行的处理逻辑
                            const categoryName = category.replace(' (小计)', '');
                            const categoryMatch = categoryFilter === '' || categoryName === categoryFilter;
                            
                            if (categoryMatch) {{
                                row.style.display = '';
                                visibleCount++;
                            }} else {{
                                row.style.display = 'none';
                            }}
                        }} else {{
                            // 产品行的处理逻辑
                            const categoryMatch = categoryFilter === '' || category === categoryFilter;
                            const productMatch = productFilter === '' || product === productFilter;
                            
                            if (categoryMatch && productMatch) {{
                                row.style.display = '';
                                visibleCount++;
                            }} else {{
                                row.style.display = 'none';
                            }}
                        }}
                    }});
                    
                    // 更新显示信息
                    document.getElementById('visibleCount').textContent = visibleCount;
                }}
                
                function resetFilters() {{
                    document.getElementById('categoryFilter').value = '';
                    document.getElementById('productFilter').innerHTML = '<option value="">全部规格名称</option>';
                    
                    // 显示所有行
                    const rows = document.querySelectorAll('tbody tr');
                    rows.forEach(row => {{
                        row.style.display = '';
                    }});
                    
                    filterTable();
                }}
                
                // 页面加载时初始化筛选
                window.onload = function() {{
                    filterTable();
                }};
            </script>
        </head>
        <body>
            <div class="container">
                <h1>📦 库存分析报告</h1>
                
                <div class="filters">
                    <label>品类筛选:</label>
                    <select id="categoryFilter" onchange="updateProductFilter()">
                        <option value="">全部品类</option>
                        {''.join([f'<option value="{cat}">{cat}</option>' for cat in categories])}
                    </select>
                    
                    <label>规格名称筛选:</label>
                    <select id="productFilter" onchange="filterTable()">
                        <option value="">全部规格名称</option>
                    </select>
                    
                    <button onclick="resetFilters()" style="padding: 5px 10px; margin-left: 10px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">重置筛选</button>
                    
                    <span style="margin-left: 20px; color: #666;">显示记录数: <span id="visibleCount">0</span></span>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>品类</th>
                            <th>规格名称</th>
                            <th>合计库存</th>
                            <th>常规仓</th>
                            <th>顺丰仓</th>
                            <th>京仓</th>
                            <th>云仓</th>
                            <th>统仓</th>
                            <th>金融仓</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 按品类分组显示
        for category in categories:
            category_data = summary_df[summary_df['品类'] == category]
            
            # 添加品类小计行
            category_total = category_data['合计库存'].sum()
            category_warehouse_totals = category_data[['常规仓', '顺丰仓', '京仓', '云仓', '统仓', '金融仓']].sum()
            
            html_content += f"""
                        <tr class="category-row">
                            <td>{category} (小计)</td>
                            <td></td>
                            <td class="number">{category_total:,.0f}</td>
                            <td class="number">{category_warehouse_totals['常规仓']:,.0f}</td>
                            <td class="number">{category_warehouse_totals['顺丰仓']:,.0f}</td>
                            <td class="number">{category_warehouse_totals['京仓']:,.0f}</td>
                            <td class="number">{category_warehouse_totals['云仓']:,.0f}</td>
                            <td class="number">{category_warehouse_totals['统仓']:,.0f}</td>
                            <td class="number">{category_warehouse_totals['金融仓']:,.0f}</td>
                        </tr>
            """
            
            # 添加该品类的所有规格名称
            for _, row in category_data.iterrows():
                html_content += f"""
                        <tr>
                            <td>{category}</td>
                            <td>{row['规格名称']}</td>
                            <td class="number">{row['合计库存']:,.0f}</td>
                            <td class="number">{row['常规仓']:,.0f}</td>
                            <td class="number">{row['顺丰仓']:,.0f}</td>
                            <td class="number">{row['京仓']:,.0f}</td>
                            <td class="number">{row['云仓']:,.0f}</td>
                            <td class="number">{row['统仓']:,.0f}</td>
                            <td class="number">{row['金融仓']:,.0f}</td>
                        </tr>
                """
        
        # 添加总计行
        total_row = summary_df.sum(numeric_only=True)
        html_content += f"""
                        <tr style="background-color: #ffeb3b; font-weight: bold;">
                            <td colspan="2">总计</td>
                            <td class="number">{total_row['合计库存']:,.0f}</td>
                            <td class="number">{total_row['常规仓']:,.0f}</td>
                            <td class="number">{total_row['顺丰仓']:,.0f}</td>
                            <td class="number">{total_row['京仓']:,.0f}</td>
                            <td class="number">{total_row['云仓']:,.0f}</td>
                            <td class="number">{total_row['统仓']:,.0f}</td>
                            <td class="number">{total_row['金融仓']:,.0f}</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="timestamp">
                    📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def save_to_csv(self, df: pd.DataFrame) -> str:
        """保存为CSV文件"""
        filename = f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到 {filename}")
        return filename
    
    def _simple_verify_url(self, public_url: str) -> str:
        """严格验证URL是否可访问"""
        logger.info(f"🔍 正在验证URL: {public_url}")
        
        # 等待CDN同步，最多重试5次
        for attempt in range(5):
            try:
                time.sleep(3)  # 等待CDN同步
                response = requests.head(public_url, timeout=15)
                
                if response.status_code == 200:
                    logger.info(f"✅ URL验证成功，文件可正常访问: {public_url}")
                    return public_url
                elif response.status_code == 404:
                    logger.info(f"⚠️ 第{attempt+1}次验证失败，文件不存在 (404)，等待CDN同步...")
                else:
                    logger.info(f"⚠️ 第{attempt+1}次验证失败，状态码: {response.status_code}")
                    
            except Exception as verify_e:
                logger.info(f"⚠️ 第{attempt+1}次验证异常: {verify_e}")
        
        logger.error(f"❌ URL验证失败，经过5次重试仍无法访问，不返回URL")
        return None
    
    def deploy_to_edgeone(self, html_content: str, filename: str) -> str:
        """部署到EdgeOne Pages - 使用整体日报数据.py的部署方式"""
        try:
            logger.info("🚀 开始部署到EdgeOne Pages...")
            
            # 创建reports目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            reports_dir = os.path.join(script_dir, "reports")
            
            # 确保reports目录存在
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir, exist_ok=True)
                logger.info(f"📁 创建reports目录: {reports_dir}")
            else:
                logger.info(f"📁 使用现有reports目录: {reports_dir}")
            
            # 将HTML内容写入到reports目录
            file_path = os.path.join(reports_dir, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"💾 HTML文件已保存到: {file_path}")
                
                # 验证文件是否成功写入
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"✅ 文件写入成功，大小: {file_size:,} 字节")
                else:
                    logger.error(f"❌ 文件写入失败，文件不存在: {file_path}")
                    return None
                    
            except Exception as write_error:
                logger.error(f"❌ 文件写入异常: {write_error}")
                return None
            
            # 检查目录中是否有文件
            files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
            if not files:
                logger.error(f"❌ 部署目录中没有HTML文件: {reports_dir}")
                return None
            
            logger.info(f"📄 找到 {len(files)} 个HTML文件")
            
            # 使用绝对路径部署
            deploy_path = os.path.abspath(reports_dir)
            logger.info(f"🔧 使用绝对路径部署: {deploy_path}")
            
            # 使用EdgeOne CLI部署
            edgeone_cli_path = EDGEONE_CONFIG['cli_path']
            logger.info(f"🔧 使用EdgeOne CLI路径: {edgeone_cli_path}")
            
            # 检查CLI是否存在
            if not os.path.exists(edgeone_cli_path):
                logger.warning(f"❌ EdgeOne CLI不存在: {edgeone_cli_path}")
                # 尝试使用环境变量中的edgeone
                edgeone_cli_path = "edgeone"
                logger.info(f"🔧 尝试使用环境变量: {edgeone_cli_path}")
            
            # 构建部署命令
            project_name = EDGEONE_CONFIG['project_name']
            token = EDGEONE_CONFIG['token']
            
            # 执行部署命令
            cmd = [
                edgeone_cli_path,
                "pages",
                "deploy",
                deploy_path,  # 使用目录路径
                "-n", project_name,  # 项目名称
                "-t", token  # token
            ]
            
            logger.info(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 执行部署命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=reports_dir
            )
            
            if result.returncode == 0:
                logger.info("✅ EdgeOne Pages 部署成功！")
                logger.info(f"📤 部署输出: {result.stdout}")
                
                # 构建URL
                domain = EDGEONE_CONFIG['domain']
                public_url = f"https://{domain}/{filename}"
                
                # 验证URL
                verified_url = self._simple_verify_url(public_url)
                if verified_url:
                    logger.info(f"✅ 部署成功，可访问URL: {verified_url}")
                    return verified_url
                else:
                    logger.error("❌ URL验证失败，不返回URL")
                    return None
            else:
                logger.error(f"❌ 部署失败: {result.stderr}")
                logger.error(f"📤 部署输出: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 部署超时（5分钟）")
            return None
        except Exception as e:
            logger.error(f"❌ 部署异常: {e}")
            return None
    
    def send_wechat_message(self, summary: str, edgeone_url: str = None) -> bool:
        """发送企业微信消息 - 使用WecomChan服务器，配置企业微信凭证"""
        try:
            # 使用WecomChan服务器直接发送，配置企业微信凭证
            url = "http://212.64.57.87:5001/send"
            token = "wecomchan_token"
            
            # 配置企业微信凭证（直接使用提供的凭证）
            corp_id = "ww5396d87e63595849"
            agent_id = "1000011"
            secret = "HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II"
            
            # 构建消息内容
            content = summary
            if edgeone_url:
                content += f"\n\n🌐 在线报告: {edgeone_url}"
            
            # 分段发送长消息
            max_length = 1000
            messages = []
            
            if len(content) <= max_length:
                messages = [content]
            else:
                # 按段落分割
                paragraphs = content.split('\n\n')
                current_msg = ""
                
                for para in paragraphs:
                    if len(current_msg + para + '\n\n') <= max_length:
                        current_msg += para + '\n\n'
                    else:
                        if current_msg:
                            messages.append(current_msg.strip())
                        current_msg = para + '\n\n'
                
                if current_msg:
                    messages.append(current_msg.strip())
            
            # 发送所有分段
            for msg in messages:
                data = {
                    "msg": msg,
                    "token": token,
                    "to_user": "weicungang",
                    "cid": corp_id,
                    "aid": agent_id,
                    "secret": secret
                }
                
                max_retries = 5
                retry_delay = 3
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(url, json=data, timeout=30)
                        
                        if "errcode" in response.text and "0" in response.text:
                            logger.info(f"消息发送成功 (分段 {messages.index(msg)+1}/{len(messages)})")
                            break
                        elif "500" in response.text or "error" in response.text.lower():
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                    except requests.exceptions.ConnectTimeout:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error("连接超时，发送失败")
                            return False
                    except requests.exceptions.Timeout:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error("请求超时，发送失败")
                            return False
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error(f"发送异常: {e}")
                            return False
                
                # 分段之间稍作间隔
                if len(messages) > 1:
                    time.sleep(1)
            
            logger.info("企业微信消息发送成功")
            return True
                
        except Exception as e:
            logger.error(f"发送企业微信消息异常: {e}")
            return False
    
    def generate_summary(self, df: pd.DataFrame) -> str:
        """生成摘要信息"""
        if df.empty:
            return "📦 库存分析报告\n\n❌ 暂无库存数据"
        
        # 统计信息
        total_items = len(df)
        total_quantity = df['到仓位数量'].sum()
        unique_products = df['规格名称'].nunique()
        
        # 按仓库类型统计
        location_stats = df.groupby('仓库类型')['到仓位数量'].sum()
        
        summary = f"""📦 库存分析报告

📊 总体概况:
• 总记录数: {total_items:,}
• 总库存数量: {total_quantity:,.0f}
• 产品种类: {unique_products:,}

🏪 各仓库类型库存分布:"""
        
        for location, quantity in location_stats.items():
            summary += f"\n• {location}: {quantity:,.0f}"
        
        summary += f"\n\n📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary
    
    def run(self):
        """主运行函数"""
        logger.info("开始执行库存分析")
        
        try:
            # 连接数据库
            if not self.connect_databases():
                return False
            
            # 聚合所有库存数据
            inventory_df = self.aggregate_inventory_data()
            if inventory_df.empty:
                logger.warning("未获取到库存数据")
                return False
            
            # 生成报告
            html_report = self.generate_report(inventory_df)
            html_filename = f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # 部署到EdgeOne Pages
            edgeone_url = self.deploy_to_edgeone(html_report, html_filename)
            
            # 生成摘要
            summary = self.generate_summary(inventory_df)
            
            # 发送企业微信消息
            self.send_wechat_message(summary, edgeone_url)
            
            logger.info("库存分析完成")
            return True
            
        except Exception as e:
            logger.error(f"库存分析异常: {e}")
            return False
        finally:
            self.close_databases()

def main():
    """主函数"""
    analyzer = InventoryAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main()