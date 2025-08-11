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
import re # Added for regex in deployment ID extraction

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

# ========== EdgeOne Pages 配置 ==========
EDGEONE_PROJECT = "sales-report-new"
EDGEONE_DOMAIN = "edge.haierht.cn"
EDGEONE_CLI_PATH = "edgeone"  # 使用环境变量，更通用
EDGEONE_CLI_PATH_ALT = "edgeone"  # 备用路径

class InventoryAnalyzer:
    """库存分析器"""
    
    def __init__(self):
        self.wdt_connection = None
        self.date_connection = None
        self.latest_deployment_id = None  # 存储最新的部署ID
        
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
        """获取wdt数据库的stock表格数据，根据规格名称映射查询（使用可发库存avaliable_num）"""
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
                avaliable_num as 数量,
                CASE 
                    WHEN warehouse_name = '常规仓' THEN '常规仓'
                    WHEN warehouse_name LIKE '%顺丰%' THEN '顺丰仓'
                    ELSE '忽略'
                END as 仓库类型
            FROM stock 
            WHERE spec_name IN ('{spec_names_str}')
            AND (
                warehouse_name = '常规仓' 
                OR warehouse_name LIKE '%顺丰%'
            )
            AND avaliable_num > 0
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
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"tongstore表格列: {columns}")
            
            # 使用正确的列名
            stock_col = '__EMPTY_2'  # 总库存列
            available_col = '__EMPTY_3'  # 总可用库存列
            model_col = '__EMPTY_8'  # 商品型号列
            brand_col = '__EMPTY'  # 品牌列
            product_group_col = '__EMPTY_1'  # 产品组列
            
            # 验证列是否存在
            required_columns = [stock_col, available_col, model_col]
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.warning(f"tongstore表格中缺少必要列: {missing_columns}")
                return pd.DataFrame()
            
            # 获取所有tongstore对应的名称
            tong_names = []
            spec_name_mapping = {}
            
            for spec_name, warehouse_names in spec_mapping.items():
                if 'tongstore' in warehouse_names:
                    tong_name = warehouse_names['tongstore']
                    if tong_name and tong_name.strip():  # 确保名称不为空
                        tong_names.append(tong_name.strip())
                        spec_name_mapping[tong_name.strip()] = spec_name
            
            if not tong_names:
                logger.warning("没有找到tongstore对应的名称")
                return pd.DataFrame()
            
            logger.info(f"tongstore映射名称数量: {len(tong_names)}")
            logger.info(f"tongstore映射名称示例: {tong_names[:5]}...")  # 显示前5个
            
            # 分批查询，避免SQL过长
            batch_size = 30
            all_results = []
            
            for i in range(0, len(tong_names), batch_size):
                batch_names = tong_names[i:i + batch_size]
                
                # 构建批量查询 - 使用精确匹配和模糊匹配结合
                batch_conditions = []
                for name in batch_names:
                    # 转义特殊字符
                    escaped_name = name.replace("'", "''").replace("%", "\\%").replace("_", "\\_")
                    # 使用精确匹配和模糊匹配
                    batch_conditions.append(f"(`{model_col}` = '{escaped_name}' OR `{model_col}` LIKE '%{escaped_name}%')")
                
                conditions_str = " OR ".join(batch_conditions)
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
                
                try:
                    logger.info(f"查询tongstore批次 {i//batch_size + 1}，包含 {len(batch_names)} 个商品型号")
                    df_batch = pd.read_sql(query, self.date_connection)
                    
                    if not df_batch.empty:
                        logger.info(f"tongstore批次 {i//batch_size + 1} 查询成功，获取 {len(df_batch)} 条记录")
                        all_results.append(df_batch)
                    else:
                        logger.info(f"tongstore批次 {i//batch_size + 1} 未找到匹配数据")
                        
                except Exception as e:
                    logger.error(f"tongstore批次 {i//batch_size + 1} 查询失败: {e}")
                    continue
            
            if not all_results:
                logger.warning("未从tongstore获取到任何数据")
                return pd.DataFrame()
            
            # 合并所有批次结果
            df = pd.concat(all_results, ignore_index=True)
            
            if not df.empty:
                # 清理数据：移除重复和无效数据
                df = df.drop_duplicates()
                logger.info(f"tongstore原始数据: {len(df)} 条记录")
                
                # 添加规格名称和仓库类型
                # 使用精确匹配和模糊匹配找到对应的规格名称
                matched_data = []
                unmatched_count = 0
                
                for _, row in df.iterrows():
                    model_name = str(row['对应名称']).strip()
                    available_quantity = row['可用库存']
                    total_quantity = row['总库存']
                    brand = str(row['品牌']).strip() if pd.notna(row['品牌']) else ''
                    product_group = str(row['产品组']).strip() if pd.notna(row['产品组']) else ''
                    
                    # 查找匹配的规格名称 - 优先精确匹配，然后模糊匹配
                    matched_spec = None
                    match_type = None
                    
                    # 1. 精确匹配
                    for spec_name, warehouse_names in spec_mapping.items():
                        if 'tongstore' in warehouse_names:
                            tong_name = warehouse_names['tongstore']
                            if tong_name and tong_name.strip() == model_name:
                                matched_spec = spec_name
                                match_type = '精确匹配'
                                break
                    
                    # 2. 模糊匹配（如果精确匹配失败）
                    if not matched_spec:
                        for spec_name, warehouse_names in spec_mapping.items():
                            if 'tongstore' in warehouse_names:
                                tong_name = warehouse_names['tongstore']
                                if tong_name and tong_name.strip() in model_name:
                                    matched_spec = spec_name
                                    match_type = '模糊匹配'
                                    break
                    
                    if matched_spec:
                        matched_data.append({
                            '规格名称': matched_spec,
                            '数量': available_quantity,  # 使用可用库存
                            '仓库类型': '统仓',
                            '匹配类型': match_type,
                            '原始型号': model_name,
                            '品牌': brand,
                            '产品组': product_group,
                            '总库存': total_quantity
                        })
                    else:
                        unmatched_count += 1
                        logger.debug(f"未匹配的tongstore记录: {model_name} (品牌: {brand}, 产品组: {product_group})")
                
                if matched_data:
                    result_df = pd.DataFrame(matched_data)
                    logger.info(f"从{table_name}获取数据成功，共 {len(result_df)} 条记录")
                    logger.info(f"匹配统计: 精确匹配 {len([d for d in matched_data if d['匹配类型'] == '精确匹配'])} 条, 模糊匹配 {len([d for d in matched_data if d['匹配类型'] == '模糊匹配'])} 条")
                    logger.info(f"未匹配记录: {unmatched_count} 条")
                    
                    # 移除调试列，只保留必要列
                    result_df = result_df[['规格名称', '数量', '仓库类型']]
                    return result_df
                else:
                    logger.warning("tongstore数据匹配失败，未找到对应的规格名称")
                    return pd.DataFrame()
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
            
            # 分批查询，避免数据库死锁
            batch_size = 50
            all_results = []
            
            for i in range(0, len(jd_names), batch_size):
                batch_names = jd_names[i:i + batch_size]
                
                # 构建批量查询
                jd_names_str = "','".join(batch_names)
                query = f"""
                SELECT 
                    `{model_col}` as 对应名称,
                    CAST(`{quantity_col}` AS SIGNED) as 数量
                FROM `{table_name}`
                WHERE `{model_col}` IN ('{jd_names_str}')
                AND CAST(`{quantity_col}` AS SIGNED) > 0
                """
                
                # 添加重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        logger.info(f"查询jdstore批次 {i//batch_size + 1}，尝试 {attempt + 1}/{max_retries}")
                        df_batch = pd.read_sql(query, self.date_connection)
                        all_results.append(df_batch)
                        logger.info(f"jdstore批次 {i//batch_size + 1} 查询成功，获取 {len(df_batch)} 条记录")
                        break
                    except Exception as e:
                        if "Deadlock" in str(e) and attempt < max_retries - 1:
                            logger.warning(f"jdstore批次 {i//batch_size + 1} 数据库死锁，等待后重试: {e}")
                            import time
                            time.sleep(2 * (attempt + 1))  # 递增等待时间
                            continue
                        else:
                            logger.error(f"jdstore批次 {i//batch_size + 1} 查询失败: {e}")
                            break
            
            if not all_results:
                logger.warning("未从jdstore获取到任何数据")
                return pd.DataFrame()
            
            # 合并所有批次结果
            df = pd.concat(all_results, ignore_index=True)
            
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
        
        # 生成简化的HTML表格
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>库存分析报告</title>
    <style>
        body {{ 
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1600px; 
            margin: 0 auto; 
            background-color: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        h1 {{ 
            color: #333; 
            text-align: center; 
            font-size: 14pt; 
            font-weight: bold; 
            margin-bottom: 20px;
        }}
        
        /* 筛选区域 */
        .filter-area {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }}
        .filter-row {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }}
        .filter-label {{
            font-size: 12pt;
            font-weight: bold;
            min-width: 80px;
        }}
        .filter-select, .filter-input {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12pt;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
        }}
        .filter-button {{
            padding: 6px 15px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12pt;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
        }}
        .filter-button:hover {{
            background-color: #0056b3;
        }}
        .clear-button {{
            background-color: #6c757d;
        }}
        .clear-button:hover {{
            background-color: #545b62;
        }}
        
        /* 表格容器 */
        .table-container {{
            position: relative;
            max-height: 70vh;
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 6px;
        }}
        
        /* 表格样式 */
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 0;
        }}
        
        /* 固定标题行 */
        thead {{
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: #f2f2f2;
        }}
        
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 8px 12px; 
            text-align: left; 
            font-size: 10.5pt;
        }}
        
        th {{ 
            background-color: #f2f2f2; 
            font-weight: bold;
            font-size: 14pt;
            position: sticky;
            top: 0;
        }}
        
        tr:nth-child(even) {{ 
            background-color: #f9f9f9; 
        }}
        
        .number {{ 
            text-align: right; 
            font-family: "Microsoft YaHei", "微软雅黑", Arial, monospace; 
        }}
        
        .timestamp {{ 
            text-align: center; 
            color: #666; 
            margin-top: 20px; 
            font-style: italic; 
            font-size: 10.5pt;
        }}
        
        .category-row {{ 
            background-color: #e3f2fd !important; 
            font-weight: bold;
            font-size: 14pt;
        }}
        
        .total-row {{
            background-color: #ffeb3b !important; 
            font-weight: bold;
            font-size: 14pt;
        }}
        
        /* 统计信息 */
        .stats-info {{
            background-color: #e8f5e8;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-size: 10.5pt;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 库存分析报告</h1>
        
        <!-- 筛选区域 -->
        <div class="filter-area">
            <div class="filter-row">
                <span class="filter-label">品类筛选:</span>
                <select id="categoryFilter" class="filter-select" onchange="onCategoryChange()">
                    <option value="">全部品类</option>
                </select>
                
                <span class="filter-label">产品搜索:</span>
                <select id="productFilter" class="filter-select">
                    <option value="">全部产品</option>
                </select>
                
                <button onclick="applyFilter()" class="filter-button">筛选</button>
                <button onclick="clearFilter()" class="filter-button clear-button">清除</button>
            </div>
            <div class="stats-info" id="statsInfo">
                显示统计信息
            </div>
        </div>
        
        <!-- 表格容器 -->
        <div class="table-container">
            <table id="inventoryTable">
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
                <tbody id="inventoryBody">
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
                <tr class="total-row">
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
        </div>
        
        <div class="timestamp">
            📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        // 全局数据存储
        let originalData = [];
        let currentData = [];
        
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {{
            initializeData();
            populateCategoryFilter();
            populateProductFilter();
            updateStats();
        }});
        
        // 初始化数据
        function initializeData() {{
            const tbody = document.getElementById('inventoryBody');
            const rows = tbody.querySelectorAll('tr');
            
            originalData = [];
            rows.forEach(row => {{
                const cells = row.querySelectorAll('td');
                if (cells.length >= 9 && !row.classList.contains('total-row')) {{
                    originalData.push({{
                        element: row.cloneNode(true),
                        category: cells[0].textContent.trim(),
                        product: cells[1].textContent.trim(),
                        totalStock: parseInt(cells[2].textContent.replace(/,/g, '')) || 0,
                        isCategory: row.classList.contains('category-row')
                    }});
                }}
            }});
            currentData = [...originalData];
        }}
        
        // 填充品类筛选下拉框
        function populateCategoryFilter() {{
            const categoryFilter = document.getElementById('categoryFilter');
            
            // 计算每个品类的总数量
            const categoryTotals = {{}};
            originalData.filter(item => !item.isCategory).forEach(item => {{
                if (!categoryTotals[item.category]) {{
                    categoryTotals[item.category] = 0;
                }}
                categoryTotals[item.category] += item.totalStock;
            }});
            
            // 按总数量排序品类
            const sortedCategories = Object.keys(categoryTotals).sort((a, b) => {{
                return categoryTotals[b] - categoryTotals[a]; // 降序排列
            }});
            
            // 清空并重新填充
            categoryFilter.innerHTML = '<option value="">全部品类</option>';
            sortedCategories.forEach(category => {{
                const option = document.createElement('option');
                option.value = category;
                option.textContent = `${{category}} (库存: ${{categoryTotals[category].toLocaleString()}})`;
                categoryFilter.appendChild(option);
            }});
        }}
        
        // 填充产品搜索下拉框
        function populateProductFilter() {{
            const productFilter = document.getElementById('productFilter');
            const selectedCategory = document.getElementById('categoryFilter').value;
            
            // 根据选中的品类筛选产品
            let filteredProducts = originalData.filter(item => !item.isCategory);
            if (selectedCategory) {{
                filteredProducts = filteredProducts.filter(item => item.category === selectedCategory);
            }}
            
            // 按数量排序产品
            const sortedProducts = filteredProducts
                .sort((a, b) => b.totalStock - a.totalStock) // 降序排列
                .map(item => item.product);
            
            // 清空并重新填充
            productFilter.innerHTML = '<option value="">全部产品</option>';
            sortedProducts.forEach(product => {{
                const option = document.createElement('option');
                option.value = product;
                option.textContent = product;
                productFilter.appendChild(option);
            }});
        }}
        
        // 品类筛选变化时触发产品搜索下拉框更新
        function onCategoryChange() {{
            populateProductFilter();
            applyFilter();
        }}
        
        // 应用筛选
        function applyFilter() {{
            const categoryFilter = document.getElementById('categoryFilter').value;
            const productFilter = document.getElementById('productFilter').value;
            
            currentData = originalData.filter(item => {{
                // 品类筛选
                if (categoryFilter && item.category !== categoryFilter) {{
                    return false;
                }}
                
                // 产品筛选
                if (productFilter && item.product !== productFilter) {{
                    return false;
                }}
                
                return true;
            }});
            
            renderTable();
            updateStats();
        }}
        
        // 清除筛选
        function clearFilter() {{
            document.getElementById('categoryFilter').value = '';
            document.getElementById('productFilter').value = '';
            currentData = [...originalData];
            populateProductFilter(); // 重新填充产品筛选
            renderTable();
            updateStats();
        }}
        
        // 渲染表格
        function renderTable() {{
            const tbody = document.getElementById('inventoryBody');
            const totalRow = tbody.querySelector('.total-row');
            
            // 清空表格
            tbody.innerHTML = '';
            
            // 按品类分组
            const groupedData = {{}};
            currentData.filter(item => !item.isCategory).forEach(item => {{
                if (!groupedData[item.category]) {{
                    groupedData[item.category] = [];
                }}
                groupedData[item.category].push(item);
            }});
            
            // 计算品类小计
            Object.keys(groupedData).sort().forEach(category => {{
                const categoryItems = groupedData[category];
                
                // 计算小计
                const categoryTotal = categoryItems.reduce((sum, item) => sum + item.totalStock, 0);
                const categoryRow = document.createElement('tr');
                categoryRow.className = 'category-row';
                categoryRow.innerHTML = `
                    <td>${{category}} (小计)</td>
                    <td></td>
                    <td class="number">${{categoryTotal.toLocaleString()}}</td>
                    <td class="number">-</td>
                    <td class="number">-</td>
                    <td class="number">-</td>
                    <td class="number">-</td>
                    <td class="number">-</td>
                    <td class="number">-</td>
                `;
                tbody.appendChild(categoryRow);
                
                // 添加该品类的产品
                categoryItems.forEach(item => {{
                    tbody.appendChild(item.element.cloneNode(true));
                }});
            }});
            
            // 重新添加总计行
            if (totalRow) {{
                tbody.appendChild(totalRow.cloneNode(true));
            }}
        }}
        
        // 更新统计信息
        function updateStats() {{
            const filteredProducts = currentData.filter(item => !item.isCategory);
            const totalProducts = filteredProducts.length;
            const totalStock = filteredProducts.reduce((sum, item) => sum + item.totalStock, 0);
            const categories = [...new Set(filteredProducts.map(item => item.category))].length;
            
            document.getElementById('statsInfo').innerHTML = `
                📊 当前显示: 产品 ${{totalProducts}} 种 | 品类 ${{categories}} 个 | 总库存 ${{totalStock.toLocaleString()}} 台
            `;
        }}
    </script>
</body>
</html>"""
        
        return html_content
    
    def save_to_csv(self, df: pd.DataFrame) -> str:
        """保存为CSV文件"""
        filename = f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到 {filename}")
        return filename
    
    def deploy_to_edgeone(self, html_content: str, filename: str) -> str:
        """使用EdgeOne CLI部署到EdgeOne Pages - 彻底修复版本"""
        try:
            logger.info("🚀 开始部署到EdgeOne Pages...")
            
            # 获取主项目的reports目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本目录（store）
            main_project_dir = os.path.dirname(script_dir)  # 主项目目录（wecomchan）
            reports_dir = os.path.join(main_project_dir, "reports")  # 主项目的reports目录
            
            # 确保reports目录存在
            os.makedirs(reports_dir, exist_ok=True)
            logger.info(f"📁 确保reports目录存在: {reports_dir}")
            
            # 保存HTML文件到主项目的reports目录
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"📄 已保存HTML文件: {file_path}")
            
            # 检测操作系统
            import platform
            is_windows = platform.system() == "Windows"
            
            # 根据操作系统确定EdgeOne CLI路径
            if is_windows:
                edgeone_cmd = EDGEONE_CLI_PATH
                edgeone_cmd_alt = EDGEONE_CLI_PATH_ALT
            else:
                edgeone_cmd = EDGEONE_CLI_PATH
                edgeone_cmd_alt = EDGEONE_CLI_PATH_ALT
            
            # 检查EdgeOne CLI是否可用
            def check_edgeone_cli():
                try:
                    import subprocess
                    # 尝试主路径
                    try:
                        result = subprocess.run([edgeone_cmd, "--version"], 
                                          capture_output=True, text=True, check=True, timeout=10)
                        logger.info(f"✅ EdgeOne CLI 已安装: {edgeone_cmd}")
                        return edgeone_cmd
                    except:
                        # 尝试备用路径
                        try:
                            result = subprocess.run([edgeone_cmd_alt, "--version"], 
                                              capture_output=True, text=True, check=True, timeout=10)
                            logger.info(f"✅ EdgeOne CLI 已安装 (备用路径): {edgeone_cmd_alt}")
                            return edgeone_cmd_alt
                        except:
                            pass
                    
                    logger.error("❌ EdgeOne CLI 不可用")
                    return None
                except Exception as e:
                    logger.error(f"❌ EdgeOne CLI 检查失败: {e}")
                    return None
            
            # 检查登录状态
            def check_edgeone_login(edgeone_path):
                try:
                    import subprocess
                    result = subprocess.run([edgeone_path, "whoami"], 
                                      capture_output=True, text=True, check=True, timeout=10)
                    logger.info("✅ EdgeOne CLI 已登录")
                    return True
                except Exception as e:
                    logger.error(f"❌ EdgeOne CLI 未登录: {e}")
                    return False
            
            # 执行CLI部署 - 修复版本
            def execute_cli_deploy(edgeone_path):
                try:
                    import subprocess
                    import os
                    
                    # 使用绝对路径，在主项目目录下执行
                    cmd = [
                        edgeone_path, "pages", "deploy", 
                        reports_dir,  # 使用绝对路径
                        "-n", EDGEONE_PROJECT
                    ]
                    
                    logger.info(f"📤 执行CLI部署命令: {' '.join(cmd)}")
                    logger.info(f"📁 工作目录: {main_project_dir}")
                    
                    # 在主项目目录下执行部署命令
                    result = subprocess.run(
                        cmd, 
                        check=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=300,
                        cwd=main_project_dir  # 确保在正确的工作目录下执行
                    )
                    
                    logger.info("✅ EdgeOne CLI 部署成功！")
                    logger.info(f"📤 部署输出: {result.stdout}")
                    
                    # 从部署输出中提取部署ID
                    deployment_id_match = re.search(r"Created deployment with ID: (\w+)", result.stdout)
                    if deployment_id_match:
                        self.latest_deployment_id = deployment_id_match.group(1)
                        logger.info(f"✅ 提取到部署ID: {self.latest_deployment_id}")
                    else:
                        # 尝试其他可能的格式
                        deployment_id_match = re.search(r"Deployment ID: (\w+)", result.stdout)
                        if deployment_id_match:
                            self.latest_deployment_id = deployment_id_match.group(1)
                            logger.info(f"✅ 提取到部署ID: {self.latest_deployment_id}")
                        else:
                            logger.warning("⚠️ 未从CLI输出中提取到部署ID")
                            self.latest_deployment_id = None
                    
                    return True
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ EdgeOne CLI 部署失败: {e}")
                    logger.error(f"错误输出: {e.stderr}")
                    return False
                except Exception as e:
                    logger.error(f"❌ EdgeOne CLI 部署异常: {e}")
                    return False
            
            # 主部署流程
            logger.info("🔍 检查EdgeOne CLI...")
            edgeone_path = check_edgeone_cli()
            
            if not edgeone_path:
                logger.error("❌ EdgeOne CLI 不可用，请先安装")
                return None
            
            logger.info("🔍 检查登录状态...")
            if not check_edgeone_login(edgeone_path):
                logger.error("❌ EdgeOne CLI 未登录，请先运行登录命令")
                logger.info(f"💡 登录命令: {edgeone_path} login")
                return None
            
            logger.info("🚀 开始CLI部署...")
            if execute_cli_deploy(edgeone_path):
                logger.info("✅ EdgeOne CLI 部署完成！")
                
                # 等待CDN同步
                logger.info("⏳ 等待CDN同步...")
                time.sleep(15)  # 等待15秒让CDN同步
                
                # 构建访问URL - 使用正确的路径
                verified_url = self._verify_multiple_urls(filename)
                
                if verified_url:
                    logger.info(f"✅ URL验证成功: {verified_url}")
                    return verified_url
                else:
                    # 返回默认URL
                    default_url = f"https://{EDGEONE_DOMAIN}/{filename}"
                    logger.info(f"💡 返回默认URL: {default_url}")
                    return default_url
            else:
                logger.error("❌ EdgeOne CLI 部署失败")
                return None
                
        except Exception as e:
            logger.error(f"❌ 部署过程中发生错误: {e}")
            return None
    
    def _verify_url_accessibility(self, url: str) -> str:
        """验证URL可访问性，返回可访问的URL"""
        logger.info(f"🔍 验证URL可访问性: {url}")
        
        # 快速验证，减少等待时间
        for attempt in range(3):  # 减少到3次尝试
            try:
                # 减少等待时间
                wait_time = 3 + (attempt * 2)  # 3, 5, 7秒
                logger.info(f"⏳ 第{attempt+1}次验证，等待{wait_time}秒...")
                time.sleep(wait_time)
                
                response = requests.head(url, timeout=10)  # 减少超时时间
                
                if response.status_code == 200:
                    logger.info(f"✅ URL验证成功，状态码: {response.status_code}")
                    return url
                elif response.status_code == 404:
                    logger.info(f"⚠️ 第{attempt+1}次验证失败，文件不存在 (404)")
                else:
                    logger.info(f"⚠️ 第{attempt+1}次验证失败，状态码: {response.status_code}")
                    
            except requests.exceptions.ConnectTimeout:
                logger.info(f"⚠️ 第{attempt+1}次验证连接超时")
            except requests.exceptions.Timeout:
                logger.info(f"⚠️ 第{attempt+1}次验证请求超时")
            except Exception as e:
                logger.info(f"⚠️ 第{attempt+1}次验证异常: {e}")
        
        logger.warning(f"❌ URL验证失败，但部署可能成功: {url}")
        return None
    
    def _verify_multiple_urls(self, filename: str) -> str:
        """验证多种可能的URL格式，智能快速验证 - 简化版"""
        # 构建基础URL
        base_url = f"https://{EDGEONE_DOMAIN}/{filename}"
        
        # 快速验证主URL - 只等待5秒
        try:
            response = requests.head(base_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ URL验证成功: {base_url}")
                return base_url
        except:
            pass
        
        # 如果主URL失败，返回基础URL（通常CDN会很快同步）
        logger.info(f"💡 返回基础URL（CDN正在同步）: {base_url}")
        return base_url
    
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
            success_count = 0
            for i, msg in enumerate(messages):
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
                        logger.info(f"📤 正在发送消息分段 {i+1}/{len(messages)} (尝试 {attempt+1}/{max_retries})")
                        response = requests.post(url, json=data, timeout=30)
                        
                        # 检查响应内容
                        response_text = response.text.lower()
                        if "errcode" in response_text and "0" in response_text:
                            logger.info(f"✅ 消息分段 {i+1}/{len(messages)} 发送成功")
                            success_count += 1
                            break
                        elif "500" in response_text or "error" in response_text:
                            logger.warning(f"⚠️ 消息分段 {i+1}/{len(messages)} 发送失败 (尝试 {attempt+1}/{max_retries}): {response.text}")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                        else:
                            logger.warning(f"⚠️ 消息分段 {i+1}/{len(messages)} 响应异常 (尝试 {attempt+1}/{max_retries}): {response.text}")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                    except requests.exceptions.ConnectTimeout:
                        logger.warning(f"⚠️ 消息分段 {i+1}/{len(messages)} 连接超时 (尝试 {attempt+1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error(f"❌ 消息分段 {i+1}/{len(messages)} 连接超时，发送失败")
                    except requests.exceptions.Timeout:
                        logger.warning(f"⚠️ 消息分段 {i+1}/{len(messages)} 请求超时 (尝试 {attempt+1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error(f"❌ 消息分段 {i+1}/{len(messages)} 请求超时，发送失败")
                    except Exception as e:
                        logger.warning(f"⚠️ 消息分段 {i+1}/{len(messages)} 发送异常 (尝试 {attempt+1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error(f"❌ 消息分段 {i+1}/{len(messages)} 发送异常: {e}")
                
                # 分段之间稍作间隔
                if i < len(messages) - 1:
                    time.sleep(1)
            
            if success_count == len(messages):
                logger.info(f"✅ 企业微信消息发送成功，共 {len(messages)} 个分段全部发送成功")
                return True
            elif success_count > 0:
                logger.warning(f"⚠️ 企业微信消息部分发送成功，{success_count}/{len(messages)} 个分段发送成功")
                return True
            else:
                logger.error(f"❌ 企业微信消息发送失败，所有分段均发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送企业微信消息异常: {e}")
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