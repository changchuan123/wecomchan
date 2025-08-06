#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存分析新格式脚本
功能：按goods_name作为品类汇总分析，增加线上线下区分，剔除异常数据
最终格式：总体概况、品类分类、TOP型号、匹配失败预警
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
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('库存分析新格式.log', encoding='utf-8'),
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

class NewInventoryAnalyzer:
    """新格式库存分析器"""
    
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
    
    def get_wdt_stock_data(self) -> pd.DataFrame:
        """获取wdt数据库的stock表格数据，按需求筛选仓库和字段"""
        if not self.wdt_connection:
            logger.error("wdt数据库未连接")
            return pd.DataFrame()
        
        try:
            # 首先检查表结构
            cursor = self.wdt_connection.cursor()
            cursor.execute("DESCRIBE stock")
            columns = [col[0] for col in cursor.fetchall()]
            
            # 检查必要列是否存在
            required_columns = {'goods_name', 'brand_name', 'spec_name', 'stock_num', 'warehouse_name'}
            available_columns = set(columns)
            missing_columns = required_columns - available_columns
            
            if missing_columns:
                logger.warning(f"wdt.stock表格中缺少列: {missing_columns}")
                logger.info(f"实际列名: {columns}")
                return pd.DataFrame()
            
            query = """
            SELECT 
                goods_name as 品类,
                brand_name as 品牌,
                spec_name as 规格名称,
                CAST(stock_num AS DECIMAL) as 库存量,
                CASE 
                    WHEN warehouse_name = '常规仓' THEN '线下'
                    WHEN warehouse_name LIKE '%顺丰%' THEN '线上'
                    ELSE '其他'
                END as 渠道类型
            FROM stock 
            WHERE (warehouse_name = '常规仓' OR warehouse_name LIKE '%顺丰%')
            AND CAST(stock_num AS DECIMAL) > 0
            AND goods_name IS NOT NULL
            AND goods_name != ''
            AND goods_name NOT LIKE '%运费%'
            AND goods_name NOT LIKE '%虚拟%'
            AND goods_name NOT LIKE '%赠品%'
            """
            
            df = pd.read_sql(query, self.wdt_connection)
            logger.info(f"从wdt.stock获取数据成功，共 {len(df)} 条记录")
            return df
        except Exception as e:
            logger.error(f"获取wdt.stock数据失败: {e}")
            return pd.DataFrame()
    
    def get_jinrongstore_data(self) -> pd.DataFrame:
        """获取jinrongstore数据：数量-已赎货"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        try:
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
            
            # 根据实际数据库结构定义列名
            model_col = '型号'
            quantity_col = '数量'
            redeemed_col = '已赎货'
            
            # 检查必要列是否存在
            required_cols = [model_col, quantity_col, redeemed_col]
            missing_cols = [col for col in required_cols if col not in columns]
            
            if missing_cols:
                logger.warning(f"jinrongstore表格中缺少必要列: {missing_cols}")
                logger.info(f"实际列名: {columns}")
                return pd.DataFrame()
            
            # 使用型号作为规格名称，由于没有货品名称和品牌名称，使用型号作为品类
            query = f"""
            SELECT 
                `型号` as 品类,
                '其他' as 品牌,
                `型号` as 规格名称,
                (CAST(`{quantity_col}` AS DECIMAL) - CAST(`{redeemed_col}` AS DECIMAL)) as 库存量,
                '线下' as 渠道类型
            FROM `{table_name}`
            WHERE (CAST(`{quantity_col}` AS DECIMAL) - CAST(`{redeemed_col}` AS DECIMAL)) > 0
            AND `型号` IS NOT NULL 
            AND `型号` != ''
            AND `型号` NOT LIKE '%运费%'
            AND `型号` NOT LIKE '%虚拟%'
            AND `型号` NOT LIKE '%赠品%'
            """
            
            df = pd.read_sql(query, self.date_connection)
            logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取jinrongstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_rrsstore_data(self) -> pd.DataFrame:
        """获取rrsstore数据：可用库存数量"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        try:
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%rrsstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到rrsstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到rrsstore表格: {table_name}")
            
            # 根据实际数据库结构定义列名
            model_col = '商品编码'
            quantity_col = '可用库存数量'
            product_name_col = '商品名称'
            
            # 获取表结构验证
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            
            # 检查所有必要列是否存在
            available_columns = set(columns)
            required_columns = {model_col, quantity_col, product_name_col}
            missing_columns = required_columns - available_columns
            
            if missing_columns:
                logger.warning(f"rrsstore表格中缺少列: {missing_columns}")
                logger.info(f"实际列名: {columns}")
                return pd.DataFrame()
            
            # 使用商品名称作为品类
            query = f"""
            SELECT 
                `{product_name_col}` as 品类,
                '其他' as 品牌,
                `{model_col}` as 规格名称,
                CAST(`{quantity_col}` AS DECIMAL) as 库存量,
                '线上' as 渠道类型
            FROM `{table_name}`
            WHERE `{quantity_col}` IS NOT NULL 
            AND CAST(`{quantity_col}` AS DECIMAL) > 0
            AND `{model_col}` IS NOT NULL 
            AND `{model_col}` != ''
            AND `{model_col}` != '商品编码'
            AND `{model_col}` != '商品名称'
            """
            
            df = pd.read_sql(query, self.date_connection)
            logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取rrsstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_tongstore_data(self) -> pd.DataFrame:
        """获取tongstore数据"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        try:
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%tongstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到tongstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到tongstore表格: {table_name}")
            
            # tongstore表结构特殊，列名是__EMPTY_1, __EMPTY_2等
            # 根据分析，我们需要跳过第一行（表头）
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
            sample_data = cursor.fetchall()
            
            if len(sample_data) < 2:
                logger.warning("tongstore表格数据不足")
                return pd.DataFrame()
            
            # 跳过第一行（表头），从第二行开始
            # 根据实际数据：__EMPTY_1=商品编码, __EMPTY_2=商品名称, __EMPTY_3=总数量
            query = f"""
            SELECT 
                t2.__EMPTY_2 as 品类,
                '其他' as 品牌,
                t2.__EMPTY_1 as 规格名称,
                CAST(t2.__EMPTY_3 AS DECIMAL) as 库存量,
                '线下' as 渠道类型
            FROM (
                SELECT * FROM `{table_name}` LIMIT 100 OFFSET 2
            ) t2
            WHERE t2.__EMPTY_1 IS NOT NULL 
            AND t2.__EMPTY_1 != ''
            AND t2.__EMPTY_1 != '商品编码'
            AND t2.__EMPTY_1 != '合计'
            AND CAST(t2.__EMPTY_3 AS DECIMAL) > 0
            """
            
            df = pd.read_sql(query, self.date_connection)
            
            # 如果上述方法失败，尝试更直接的方法
            if df.empty:
                cursor.execute(f"SELECT __EMPTY_2, __EMPTY_1, __EMPTY_3 FROM `{table_name}` WHERE __EMPTY_1 != '商品编码' AND __EMPTY_1 IS NOT NULL AND __EMPTY_1 != '' AND __EMPTY_1 != '合计' LIMIT 100 OFFSET 2")
                rows = cursor.fetchall()
                
                if rows:
                    data = []
                    for row in rows:
                        try:
                            quantity = float(row[2]) if row[2] and str(row[2]).strip() else 0
                            if quantity > 0:
                                data.append({
                                    '品类': str(row[0]) if row[0] else '未知商品',
                                    '品牌': '其他',
                                    '规格名称': str(row[1]) if row[1] else '未知规格',
                                    '库存量': quantity,
                                    '渠道类型': '线下'
                                })
                        except Exception as e:
                            logger.warning(f"处理tongstore行数据失败: {e}")
                            continue
                    
                    df = pd.DataFrame(data)
                    logger.info(f"从{table_name}获取数据成功（备用方法），共 {len(df)} 条记录")
                else:
                    logger.warning("tongstore表格中没有有效数据")
                    return pd.DataFrame()
            else:
                logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            logger.error(f"获取tongstore数据失败: {e}")
            return pd.DataFrame()
    
    def get_jdstore_data(self) -> pd.DataFrame:
        """获取jdstore数据"""
        if not self.date_connection:
            logger.error("date数据库未连接")
            return pd.DataFrame()
        
        try:
            cursor = self.date_connection.cursor()
            cursor.execute("SHOW TABLES LIKE '%jdstore%'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("未找到jdstore相关表格")
                return pd.DataFrame()
            
            table_name = tables[0][0]
            logger.info(f"找到jdstore表格: {table_name}")
            
            # 根据实际数据库结构定义列名
            model_col = '事业部商品编码'
            quantity_col = '可用库存'
            product_name_col = '事业部商品名称'
            
            # 获取表结构验证
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            
            # 检查所有必要列是否存在
            available_columns = set(columns)
            required_columns = {model_col, quantity_col, product_name_col}
            missing_columns = required_columns - available_columns
            
            if missing_columns:
                logger.warning(f"jdstore表格中缺少列: {missing_columns}")
                logger.info(f"实际列名: {columns}")
                return pd.DataFrame()
            
            # 使用商品名称作为品类
            query = f"""
            SELECT 
                `{product_name_col}` as 品类,
                '其他' as 品牌,
                `{model_col}` as 规格名称,
                CAST(`{quantity_col}` AS DECIMAL) as 库存量,
                '线上' as 渠道类型
            FROM `{table_name}`
            WHERE `{quantity_col}` IS NOT NULL 
            AND CAST(`{quantity_col}` AS DECIMAL) > 0
            AND `{model_col}` IS NOT NULL 
            AND `{model_col}` != ''
            """
            
            df = pd.read_sql(query, self.date_connection)
            logger.info(f"从{table_name}获取数据成功，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取jdstore数据失败: {e}")
            return pd.DataFrame()
    
    def categorize_by_goods_name(self, goods_name: str) -> str:
        """根据goods_name识别品类"""
        if not goods_name:
            return "其他"
        
        goods_name = str(goods_name).upper()
        
        # 冰箱类
        if any(keyword in goods_name for keyword in ['冰箱', 'BCD', 'BC/', 'BD/']):
            return "冰箱"
        
        # 洗衣机类
        if any(keyword in goods_name for keyword in ['洗衣机', 'XQG', 'XQB', '滚筒', '波轮']):
            return "洗衣机"
        
        # 空调类
        if any(keyword in goods_name for keyword in ['空调', 'KFR', 'KF-', '挂机', '柜机']):
            if '商用' in goods_name or '多联' in goods_name:
                return "商用空调"
            else:
                return "家用空调"
        
        # 热水器类
        if any(keyword in goods_name for keyword in ['热水器', 'JSQ', 'ES']):
            return "热水器"
        
        # 厨电类
        if any(keyword in goods_name for keyword in ['洗碗机', '消毒柜', '油烟机', '燃气灶']):
            return "厨电"
        
        # 冷柜类
        if any(keyword in goods_name for keyword in ['冷柜', '冰柜', 'SC/SD']):
            return "冷柜"
        
        return "其他"
    
    def aggregate_inventory_data(self) -> pd.DataFrame:
        """聚合所有库存数据"""
        logger.info("开始聚合库存数据")
        
        # 获取各仓库数据
        all_data = []
        
        # wdt数据
        wdt_data = self.get_wdt_stock_data()
        if not wdt_data.empty:
            all_data.append(wdt_data)
        
        # jinrongstore数据
        jinrong_data = self.get_jinrongstore_data()
        if not jinrong_data.empty:
            all_data.append(jinrong_data)
        
        # rrsstore数据
        rrs_data = self.get_rrsstore_data()
        if not rrs_data.empty:
            all_data.append(rrs_data)
        
        # tongstore数据
        tong_data = self.get_tongstore_data()
        if not tong_data.empty:
            all_data.append(tong_data)
        
        # jdstore数据
        jd_data = self.get_jdstore_data()
        if not jd_data.empty:
            all_data.append(jd_data)
        
        if not all_data:
            logger.warning("未获取到任何库存数据")
            return pd.DataFrame()
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 标准化品类名称
        combined_df['标准化品类'] = combined_df['品类'].apply(self.categorize_by_goods_name)
        
        # 确保数量列是数值类型
        combined_df['库存量'] = pd.to_numeric(combined_df['库存量'], errors='coerce').fillna(0)
        
        # 过滤异常数据
        logger.info(f"聚合数据列名: {combined_df.columns.tolist()}")
        logger.info(f"聚合数据前5行: {combined_df.head().to_dict()}")
        
        # 确保规格名称列存在
        if '规格名称' not in combined_df.columns:
            logger.error("规格名称列不存在")
            return pd.DataFrame()
            
        combined_df = combined_df[
            ~combined_df['规格名称'].astype(str).str.contains('运费|虚拟|赠品', na=False, case=False) &
            combined_df['库存量'] > 0
        ]
        
        # 按品类、渠道类型、品牌聚合
        result_df = combined_df.groupby(['标准化品类', '渠道类型', '品牌']).agg({
            '库存量': 'sum'
        }).reset_index()
        
        # 计算每个品类的合计
        category_total = combined_df.groupby(['标准化品类']).agg({
            '库存量': 'sum'
        }).reset_index()
        category_total = category_total.rename(columns={'库存量': '品类合计'})
        
        # 合并数据
        final_df = result_df.merge(category_total, on=['标准化品类'], how='left')
        
        # 重新排序
        final_df = final_df[['标准化品类', '品牌', '渠道类型', '品类合计', '库存量']]
        
        # 确保数值列是数值类型
        final_df['品类合计'] = pd.to_numeric(final_df['品类合计'], errors='coerce').fillna(0)
        final_df['库存量'] = pd.to_numeric(final_df['库存量'], errors='coerce').fillna(0)
        
        logger.info(f"聚合完成，共 {len(final_df)} 条记录")
        return final_df
    
    def identify_online_offline(self, df: pd.DataFrame) -> pd.DataFrame:
        """识别线上线下渠道"""
        if df.empty:
            return df
        
        # 为冰箱和洗衣机区分线上线下
        df['渠道细分'] = df.apply(lambda row: 
            f"{row['渠道类型']}-{row['标准化品类']}" 
            if row['标准化品类'] in ['冰箱', '洗衣机'] 
            else row['渠道类型'], axis=1)
        
        return df
    
    def generate_new_format_report(self, df: pd.DataFrame) -> str:
        """生成新格式的报告"""
        try:
            if df.empty:
                return "暂无库存数据"
            
            # 检查DataFrame列名
            logger.info(f"报告生成时DataFrame列名: {df.columns.tolist()}")
            
            # 确保所有必要列存在
            required_columns = ['标准化品类', '规格名称', '库存量', '品牌', '渠道类型']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"缺少必要列: {missing_columns}")
                return f"报告生成失败：缺少列 {missing_columns}"
            
            # 获取匹配失败的数据
            failed_df = df[df['标准化品类'] == '其他']
            failed_matches = failed_df['规格名称'].dropna().unique() if '规格名称' in failed_df.columns else []
            
            # 总体概况
            total_inventory = df['库存量'].sum()
            total_categories = df['标准化品类'].nunique()
            total_brands = df['品牌'].nunique()
            
            # 按品类汇总
            category_summary = df.groupby('标准化品类').agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False)
            
            # 按渠道汇总
            channel_summary = df.groupby('渠道类型').agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False)
            
            # TOP10型号（按库存量排序）
            top_models = df.groupby(['标准化品类', '规格名称']).agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False).head(10)
            
            html_content = f"
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>库存分析报告 - 新格式</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #333; text-align: center; }}
                .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
                .summary-item {{ text-align: center; }}
                .summary-item h3 {{ margin: 0; font-size: 2em; }}
                .summary-item p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .number {{ text-align: right; font-family: monospace; }}
                .warning {{ background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-style: italic; }}
                .category-section {{ margin: 20px 0; }}
                .channel-section {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📦 库存分析报告 - 新格式</h1>
                
                <!-- 总体概况 -->
                <div class="summary-card">
                    <h2>📊 总体概况</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <h3>{total_inventory:,}</h3>
                            <p>总库存量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_categories}</h3>
                            <p>品类数量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_brands}</h3>
                            <p>品牌数量</p>
                        </div>
                    </div>
                </div>
                
                <!-- 品类分类 -->
                <div class="category-section">
                    <h2>🏆 品类分类汇总</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>品类</th>
                                <th>库存量</th>
                                <th>占比</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in category_summary.iterrows():
            category = row['标准化品类']
            inventory = row['库存量']
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            
            html_content += f"""
                        <tr>
                            <td>{category}</td>
                            <td class="number">{inventory:,}</td>
                            <td class="number">{percentage:.1f}%</td>
                        </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
                
                <!-- 渠道分析 -->
                <div class="channel-section">
                    <h2>📊 线上线下渠道分析</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>渠道类型</th>
                                <th>库存量</th>
                                <th>占比</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in channel_summary.iterrows():
            channel = row['渠道类型']
            inventory = row['库存量']
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            
            html_content += f"""
                        <tr>
                            <td>{channel}</td>
                            <td class="number">{inventory:,}</td>
                            <td class="number">{percentage:.1f}%</td>
                        </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
                
                <!-- TOP型号 -->
                <div class="category-section">
                    <h2>💎 TOP10型号</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>品类</th>
                                <th>规格名称</th>
                                <th>库存量</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for idx, (_, row) in enumerate(top_models.iterrows(), 1):
            category = row['标准化品类']
            model = row['规格名称']
            inventory = row['库存量']
            
            html_content += f"""
                        <tr>
                            <td>{category}</td>
                            <td>{model}</td>
                            <td class="number">{inventory:,}</td>
                        </tr>
            """
        
        # 匹配失败预警
        if len(failed_matches) > 0:
            html_content += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="warning">
                <h3>⚠️ 匹配失败预警</h3>
                <p>以下规格名称未能成功匹配到标准化品类：</p>
                <ul>
            """
            
            for match in failed_matches[:10]:  # 显示前10个
                html_content += f"<li>{match}</li>"
            
            if len(failed_matches) > 10:
                html_content += f"<li>... 共{len(failed_matches)}个未匹配项</li>"
            
            html_content += """
                </ul>
            </div>
            """
        
        html_content += f"""
                <div class="timestamp">
                    📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_summary_message(self, df: pd.DataFrame) -> str:
        """生成摘要消息"""
        if df.empty:
            return "📦 库存分析报告\n\n❌ 暂无库存数据"
        
        # 总体统计
        total_inventory = df['库存量'].sum()
        total_categories = df['标准化品类'].nunique()
        
        # 按品类统计
        category_stats = df.groupby('标准化品类')['库存量'].sum().sort_values(ascending=False)
        
        # 按渠道统计
        channel_stats = df.groupby('渠道类型')['库存量'].sum()
        
        # 获取匹配失败的数量
        failed_count = len(df[df['标准化品类'] == '其他'])
        
        summary = f"""📦 库存分析报告 - 新格式

📊 总体概况:
• 总库存量: {total_inventory:,}
• 品类数量: {total_categories:,}
• 匹配失败项: {failed_count:,}

🏆 品类排行:"""
        
        for category, inventory in category_stats.head(5).items():
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            summary += f"\n• {category}: {inventory:,} ({percentage:.1f}%)"
        
        summary += f"\n\n📱 渠道分布:"
        for channel, inventory in channel_stats.items():
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            summary += f"\n• {channel}: {inventory:,} ({percentage:.1f}%)"
        
        summary += f"\n\n📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary
    
    def save_to_csv(self, df: pd.DataFrame) -> str:
        """保存为CSV文件"""
        filename = f"库存分析新格式_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到 {filename}")
        return filename
    
    def send_wechat_message(self, summary: str, csv_file: str = None) -> bool:
        """发送企业微信消息"""
        try:
            url = "http://212.64.57.87:5001/send"
            token = "wecomchan_token"
            
            # 配置企业微信凭证
            corp_id = "ww5396d87e63595849"
            agent_id = "1000011"
            secret = "HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II"
            
            content = summary
            if csv_file:
                content += f"\n\n📊 详细数据: {csv_file}"
            
            # 分段发送
            max_length = 1000
            messages = []
            
            if len(content) <= max_length:
                messages = [content]
            else:
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
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        else:
                            logger.error(f"发送异常: {e}")
                            return False
                
                if len(messages) > 1:
                    time.sleep(1)
            
            logger.info("企业微信消息发送成功")
            return True
                
        except Exception as e:
            logger.error(f"发送企业微信消息异常: {e}")
            return False
    
    def run(self):
        """主运行函数"""
        logger.info("开始执行新格式库存分析")
        
        try:
            # 连接数据库
            if not self.connect_databases():
                return False
            
            # 聚合所有库存数据
            inventory_df = self.aggregate_inventory_data()
            if inventory_df.empty:
                logger.warning("未获取到库存数据")
                return False
            
            # 识别线上线下渠道
            inventory_df = self.identify_online_offline(inventory_df)
            
            # 保存为CSV
            csv_file = self.save_to_csv(inventory_df)
            
            # 生成新格式报告
            html_report = self.generate_new_format_report(inventory_df)
            with open(f"库存分析新格式_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # 生成摘要
            summary = self.generate_summary_message(inventory_df)
            
            # 发送企业微信消息
            self.send_wechat_message(summary, csv_file)
            
            logger.info("新格式库存分析完成")
            return True
            
        except Exception as e:
            logger.error(f"新格式库存分析异常: {e}")
            return False
        finally:
            self.close_databases()

def main():
    """主函数"""
    import time
    analyzer = NewInventoryAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main()