#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存数据处理脚本 - 完整版
功能：从wdt和Date数据库获取库存数据，生成报告并推送到企业微信
支持Web页面展示和EdgeOne部署
"""

import pymysql
import pandas as pd
import json
import requests
import logging
import os
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('库存数据处理.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'wdt',
    'charset': 'utf8mb4'
}

DATE_DB_CONFIG = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}

# 企业微信配置
WECOM_CONFIG = {
    'corpid': 'ww5396d87e63595849',
    'corpsecret': 'HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II',
    'agentid': '1000011',
    'touser': '@all'
}

# 仓库分类配置
WAREHOUSE_CONFIG = {
    'regular_warehouses': ['常规仓'],
    'sf_warehouses': ['能良顺丰东莞仓', '能良顺丰武汉仓', '能良顺丰武汉金融仓', '能良顺丰金华仓']
}

class InventoryProcessor:
    """库存数据处理器"""
    
    def __init__(self):
        self.wdt_connection = None
        self.date_connection = None
        
    def connect_databases(self) -> bool:
        """连接数据库"""
        try:
            # 连接wdt数据库
            self.wdt_connection = pymysql.connect(**DB_CONFIG)
            logger.info("wdt数据库连接成功")
            
            # 连接Date数据库
            self.date_connection = pymysql.connect(**DATE_DB_CONFIG)
            logger.info("Date数据库连接成功")
            
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def close_databases(self):
        """关闭数据库连接"""
        if self.wdt_connection:
            self.wdt_connection.close()
            logger.info("wdt数据库连接已关闭")
        if self.date_connection:
            self.date_connection.close()
            logger.info("Date数据库连接已关闭")
    
    def get_wdt_stock_data(self) -> pd.DataFrame:
        """获取wdt数据库stock表格数据"""
        if not self.wdt_connection:
            logger.error("wdt数据库未连接")
            return pd.DataFrame()
        
        try:
            # 获取常规仓和顺丰仓数据
            sql = """
            SELECT 
                spec_name as 规格名称,
                stock_num as 库存量,
                warehouse_name as 仓库名称
            FROM stock 
            WHERE warehouse_name IN ('常规仓', '能良顺丰东莞仓', '能良顺丰武汉仓', '能良顺丰武汉金融仓', '能良顺丰金华仓')
            """
            
            df = pd.read_sql(sql, self.wdt_connection)
            logger.info(f"wdt数据库获取到 {len(df)} 条库存记录")
            return df
            
        except Exception as e:
            logger.error(f"获取wdt库存数据失败: {e}")
            return pd.DataFrame()
    
    def get_date_store_data(self) -> Dict[str, pd.DataFrame]:
        """获取Date数据库各个store表格数据"""
        if not self.date_connection:
            logger.error("Date数据库未连接")
            return {}
        
        store_data = {}
        
        try:
            # 获取jinrongstore数据
            sql_jinrong = """
            SELECT 
                型号,
                数量 - 已赎货 as 可用库存
            FROM jinrongstore
            """
            store_data['jinrongstore'] = pd.read_sql(sql_jinrong, self.date_connection)
            logger.info(f"jinrongstore获取到 {len(store_data['jinrongstore'])} 条记录")
            
            # 先检查rrsstore表结构
            cursor = self.date_connection.cursor()
            cursor.execute("DESCRIBE rrsstore")
            rrs_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"rrsstore表字段: {rrs_columns}")
            
            # 根据实际字段名构建SQL
            if '可用库存' in rrs_columns:
                stock_col = '可用库存'
            elif '可用库存数量' in rrs_columns:
                stock_col = '可用库存数量'
            elif '库存' in rrs_columns:
                stock_col = '库存'
            else:
                stock_col = rrs_columns[1] if len(rrs_columns) > 1 else rrs_columns[0]
            
            sql_rrs = f"""
            SELECT 
                商品编码,
                {stock_col} as 可用库存
            FROM rrsstore
            """
            store_data['rrsstore'] = pd.read_sql(sql_rrs, self.date_connection)
            logger.info(f"rrsstore获取到 {len(store_data['rrsstore'])} 条记录")
            
            # 获取tongstore数据（跳过第一行）
            # 先检查tongstore表结构
            cursor.execute("DESCRIBE tongstore")
            tong_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"tongstore表字段: {tong_columns}")
            
            # 根据实际字段名构建SQL
            if '商品名称' in tong_columns:
                name_col = '商品名称'
            elif '名称' in tong_columns:
                name_col = '名称'
            else:
                name_col = tong_columns[1] if len(tong_columns) > 1 else tong_columns[0]
            
            if '可用库存' in tong_columns:
                stock_col = '可用库存'
            elif '库存' in tong_columns:
                stock_col = '库存'
            else:
                stock_col = tong_columns[2] if len(tong_columns) > 2 else tong_columns[1]
            
            sql_tong = f"""
            SELECT 
                {name_col} as 商品名称,
                {stock_col} as 可用库存
            FROM tongstore
            LIMIT 1000 OFFSET 1
            """
            store_data['tongstore'] = pd.read_sql(sql_tong, self.date_connection)
            logger.info(f"tongstore获取到 {len(store_data['tongstore'])} 条记录")
            
            # 获取jdstore数据
            sql_jd = """
            SELECT 
                事业部商品编码,
                可用库存
            FROM jdstore
            """
            store_data['jdstore'] = pd.read_sql(sql_jd, self.date_connection)
            logger.info(f"jdstore获取到 {len(store_data['jdstore'])} 条记录")
            
            # 获取matchstore数据
            # 先检查matchstore表结构
            cursor.execute("DESCRIBE matchstore")
            match_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"matchstore表字段: {match_columns}")
            
            # 根据实际字段名构建SQL
            if '规格名称' in match_columns:
                spec_col = '规格名称'
            else:
                spec_col = match_columns[0] if match_columns else '规格名称'
            
            if '型号' in match_columns:
                model_col = '型号'
            else:
                model_col = match_columns[1] if len(match_columns) > 1 else '型号'
            
            if '商品名称' in match_columns:
                name_col = '商品名称'
            else:
                name_col = match_columns[2] if len(match_columns) > 2 else '商品名称'
            
            if '事业部商品编码' in match_columns:
                jd_code_col = '事业部商品编码'
            else:
                jd_code_col = match_columns[3] if len(match_columns) > 3 else '事业部商品编码'
            
            if '商品编码' in match_columns:
                code_col = '商品编码'
            else:
                code_col = match_columns[4] if len(match_columns) > 4 else '商品编码'
            
            sql_match = f"""
            SELECT 
                {spec_col} as 规格名称,
                {model_col} as 型号,
                {name_col} as 商品名称,
                {jd_code_col} as 事业部商品编码,
                {code_col} as 商品编码
            FROM matchstore
            """
            store_data['matchstore'] = pd.read_sql(sql_match, self.date_connection)
            logger.info(f"matchstore获取到 {len(store_data['matchstore'])} 条记录")
            
        except Exception as e:
            logger.error(f"获取Date数据库数据失败: {e}")
        
        return store_data
    
    def categorize_product(self, goods_name: str) -> str:
        """商品分类"""
        if not goods_name:
            return "其他"
        
        goods_name = goods_name.lower()
        
        if any(keyword in goods_name for keyword in ['冰箱', '冰柜', '冷柜']):
            return "冰箱冷柜"
        elif any(keyword in goods_name for keyword in ['洗衣机', '洗烘']):
            return "洗衣机"
        elif any(keyword in goods_name for keyword in ['家用空调', '挂机', '柜机']):
            return "家用空调"
        elif any(keyword in goods_name for keyword in ['商用空调', '中央空调', '商用']):
            return "商用空调"
        elif any(keyword in goods_name for keyword in ['热水器', '热水']):
            return "热水器"
        elif any(keyword in goods_name for keyword in ['厨电', '油烟机', '燃气灶', '消毒柜']):
            return "厨电"
        elif any(keyword in goods_name for keyword in ['洗碗机']):
            return "洗碗机"
        else:
            return "其他"
    
    def should_split_online_offline(self, category: str) -> bool:
        """判断是否需要拆分线上线下"""
        # 冰箱、冷柜、洗衣机、厨电、洗碗机拆分线上线下
        # 家用空调、商用空调不拆分
        return category in ["冰箱冷柜", "洗衣机", "厨电", "洗碗机", "热水器"]
    
    def match_store_data(self, store_df: pd.DataFrame, goods_no: str, match_column: str) -> float:
        """匹配store数据"""
        if store_df.empty or not goods_no:
            return 0.0
        
        # 精确匹配
        match_result = store_df[store_df[match_column] == goods_no]
        if not match_result.empty:
            return float(match_result.iloc[0]['可用库存'])
        
        # 模糊匹配
        for _, row in store_df.iterrows():
            if goods_no in str(row[match_column]) or str(row[match_column]) in goods_no:
                return float(row['可用库存'])
        
        return 0.0
    
    def process_inventory_data(self, wdt_df: pd.DataFrame, store_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """处理库存数据 - 统一统计所有表格内的型号信息"""
        if wdt_df.empty and not store_data:
            logger.warning("所有数据源都为空")
            return pd.DataFrame()
        
        # 初始化结果列表
        result_data = []
        
        # 1. 处理wdt数据库数据
        if not wdt_df.empty:
            logger.info("处理wdt数据库数据...")
            for _, row in wdt_df.iterrows():
                spec_name = row['规格名称']
                stock_num = row['库存量']
                warehouse_name = row['仓库名称']
                
                # 分类
                category = self.categorize_product(spec_name)
                if category == "其他":
                    continue
                
                # 确定仓库类型
                if warehouse_name == "常规仓":
                    warehouse_type = "常规仓"
                elif "顺丰" in warehouse_name:
                    warehouse_type = "顺丰仓"
                else:
                    continue
                
                # 计算各仓库库存
                regular_stock = stock_num if warehouse_type == "常规仓" else 0
                sf_stock = stock_num if warehouse_type == "顺丰仓" else 0
                
                total_stock = regular_stock + sf_stock
                
                # 过滤异常数据
                if total_stock > 2000:
                    logger.warning(f"过滤异常库存数据: {spec_name}, 库存量: {total_stock}")
                    continue
                
                result_data.append({
                    '品类': category,
                    '型号': spec_name,
                    '常规仓': regular_stock,
                    '顺丰仓': sf_stock,
                    '京仓': 0,
                    '云仓': 0,
                    '统仓': 0,
                    '金融仓': 0,
                    '合计数量': total_stock
                })
        
        # 2. 处理Date数据库数据
        logger.info("处理Date数据库数据...")
        
        # 处理jinrongstore数据
        if 'jinrongstore' in store_data and not store_data['jinrongstore'].empty:
            logger.info("处理jinrongstore数据...")
            for _, row in store_data['jinrongstore'].iterrows():
                model_name = row['型号']
                stock_num = row['可用库存']
                
                # 分类
                category = self.categorize_product(model_name)
                if category == "其他":
                    continue
                
                # 过滤异常数据
                if stock_num > 2000:
                    logger.warning(f"过滤异常库存数据: {model_name}, 库存量: {stock_num}")
                    continue
                
                result_data.append({
                    '品类': category,
                    '型号': model_name,
                    '常规仓': 0,
                    '顺丰仓': 0,
                    '京仓': 0,
                    '云仓': 0,
                    '统仓': 0,
                    '金融仓': stock_num,
                    '合计数量': stock_num
                })
        
        # 处理rrsstore数据
        if 'rrsstore' in store_data and not store_data['rrsstore'].empty:
            logger.info("处理rrsstore数据...")
            for _, row in store_data['rrsstore'].iterrows():
                code_name = row['商品编码']
                stock_num = row['可用库存']
                
                # 分类
                category = self.categorize_product(code_name)
                if category == "其他":
                    continue
                
                # 过滤异常数据
                if stock_num > 2000:
                    logger.warning(f"过滤异常库存数据: {code_name}, 库存量: {stock_num}")
                    continue
                
                result_data.append({
                    '品类': category,
                    '型号': code_name,
                    '常规仓': 0,
                    '顺丰仓': 0,
                    '京仓': 0,
                    '云仓': stock_num,  # rrsstore作为云仓
                    '统仓': 0,
                    '金融仓': 0,
                    '合计数量': stock_num
                })
        
        # 处理tongstore数据
        if 'tongstore' in store_data and not store_data['tongstore'].empty:
            logger.info("处理tongstore数据...")
            for _, row in store_data['tongstore'].iterrows():
                product_name = row['商品名称']
                stock_num = row['可用库存']
                
                # 分类
                category = self.categorize_product(product_name)
                if category == "其他":
                    continue
                
                # 过滤异常数据
                if stock_num > 2000:
                    logger.warning(f"过滤异常库存数据: {product_name}, 库存量: {stock_num}")
                    continue
                
                result_data.append({
                    '品类': category,
                    '型号': product_name,
                    '常规仓': 0,
                    '顺丰仓': 0,
                    '京仓': 0,
                    '云仓': 0,
                    '统仓': stock_num,
                    '金融仓': 0,
                    '合计数量': stock_num
                })
        
        # 处理jdstore数据
        if 'jdstore' in store_data and not store_data['jdstore'].empty:
            logger.info("处理jdstore数据...")
            for _, row in store_data['jdstore'].iterrows():
                jd_code = row['事业部商品编码']
                stock_num = row['可用库存']
                
                # 分类
                category = self.categorize_product(jd_code)
                if category == "其他":
                    continue
                
                # 过滤异常数据
                if stock_num > 2000:
                    logger.warning(f"过滤异常库存数据: {jd_code}, 库存量: {stock_num}")
                    continue
                
                result_data.append({
                    '品类': category,
                    '型号': jd_code,
                    '常规仓': 0,
                    '顺丰仓': 0,
                    '京仓': stock_num,
                    '云仓': 0,
                    '统仓': 0,
                    '金融仓': 0,
                    '合计数量': stock_num
                })
        
        result_df = pd.DataFrame(result_data)
        
        if result_df.empty:
            logger.warning("处理后没有有效数据")
            return result_df
        
        # 按品类和型号分组汇总
        result_df = result_df.groupby(['品类', '型号']).agg({
            '常规仓': 'sum',
            '顺丰仓': 'sum',
            '京仓': 'sum',
            '云仓': 'sum',
            '统仓': 'sum',
            '金融仓': 'sum',
            '合计数量': 'sum'
        }).reset_index()
        
        logger.info(f"处理完成，共 {len(result_df)} 条有效记录")
        return result_df
    
    def generate_html_report(self, result_df: pd.DataFrame) -> str:
        """生成HTML报告"""
        if result_df.empty:
            return "<html><body><h1>暂无库存数据</h1></body></html>"
        
        # 计算汇总数据
        total_summary = {
            'total_stock': result_df['合计数量'].sum(),
            'regular_warehouse': result_df['常规仓'].sum(),
            'sf_warehouse': result_df['顺丰仓'].sum(),
            'jd_warehouse': result_df['京仓'].sum(),
            'cloud_warehouse': result_df['云仓'].sum(),
            'tong_warehouse': result_df['统仓'].sum(),
            'jinrong_warehouse': result_df['金融仓'].sum(),
            'total_products': result_df['型号'].nunique(),
            'total_categories': result_df['品类'].nunique()
        }
        
        # 按品类统计
        category_summary = result_df.groupby('品类').agg({
            '合计数量': 'sum',
            '常规仓': 'sum',
            '顺丰仓': 'sum',
            '京仓': 'sum',
            '云仓': 'sum',
            '统仓': 'sum',
            '金融仓': 'sum'
        }).reset_index()
        
        # 计算线上线下
        category_summary['线上库存'] = category_summary['京仓'] + category_summary['云仓'] + category_summary['统仓'] + category_summary['金融仓']
        category_summary['线下库存'] = category_summary['常规仓'] + category_summary['顺丰仓']
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>库存数据报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .summary-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        .summary-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .warehouse-section {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .warehouse-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .warehouse-item {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }}
        .warehouse-item h4 {{
            margin: 0 0 8px 0;
            color: #666;
            font-size: 0.9em;
        }}
        .warehouse-item .number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .category-section {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .category-item {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .category-item:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
        }}
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .category-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}
        .category-total {{
            font-size: 1.1em;
            color: #666;
        }}
        .category-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}
        .detail-item {{
            text-align: center;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }}
        .detail-label {{
            font-size: 0.8em;
            color: #666;
            margin-bottom: 4px;
        }}
        .detail-value {{
            font-weight: bold;
            color: #333;
        }}
        .product-list {{
            display: none;
            background: white;
            border-radius: 6px;
            padding: 15px;
            margin-top: 15px;
        }}
        .product-item {{
            display: grid;
            grid-template-columns: 1fr repeat(6, 80px);
            gap: 10px;
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
        }}
        .product-item:last-child {{
            border-bottom: none;
        }}
        .product-header {{
            font-weight: bold;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        .expand-icon {{
            font-size: 1.2em;
            color: #666;
            transition: transform 0.3s ease;
        }}
        .expanded .expand-icon {{
            transform: rotate(180deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 库存数据报告</h1>
            <p>实时库存监控与分析</p>
        </div>
        
        <div class="content">
            <div class="summary-section">
                <h2>📈 总体概况</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>总库存量</h3>
                        <div class="number">{total_summary['total_stock']:,.0f}</div>
                    </div>
                    <div class="summary-card">
                        <h3>商品种类</h3>
                        <div class="number">{total_summary['total_products']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>品类数量</h3>
                        <div class="number">{total_summary['total_categories']}</div>
                    </div>
                </div>
            </div>
            
            <div class="warehouse-section">
                <h2>🏪 仓库分布</h2>
                <div class="warehouse-grid">
                    <div class="warehouse-item">
                        <h4>常规仓</h4>
                        <div class="number">{total_summary['regular_warehouse']:,.0f}</div>
                    </div>
                    <div class="warehouse-item">
                        <h4>顺丰仓</h4>
                        <div class="number">{total_summary['sf_warehouse']:,.0f}</div>
                    </div>
                    <div class="warehouse-item">
                        <h4>京仓</h4>
                        <div class="number">{total_summary['jd_warehouse']:,.0f}</div>
                    </div>
                    <div class="warehouse-item">
                        <h4>云仓</h4>
                        <div class="number">{total_summary['cloud_warehouse']:,.0f}</div>
                    </div>
                    <div class="warehouse-item">
                        <h4>统仓</h4>
                        <div class="number">{total_summary['tong_warehouse']:,.0f}</div>
                    </div>
                    <div class="warehouse-item">
                        <h4>金融仓</h4>
                        <div class="number">{total_summary['jinrong_warehouse']:,.0f}</div>
                    </div>
                </div>
            </div>
            
            <div class="category-section">
                <h2>📋 品类细分</h2>
"""
        
        # 添加品类数据
        for _, row in category_summary.iterrows():
            category = row['品类']
            total_qty = row['合计数量']
            
            # 判断是否需要显示线上线下
            should_split = self.should_split_online_offline(category)
            
            if should_split:
                online_stock = row['线上库存']
                offline_stock = row['线下库存']
                stock_info = f"线上:{online_stock:,.0f}, 线下:{offline_stock:,.0f}"
            else:
                stock_info = f"总计:{total_qty:,.0f}"
            
            # 获取该品类的产品列表
            category_products = result_df[result_df['品类'] == category]
            
            html_content += f"""
                <div class="category-item" onclick="toggleProducts('{category}')">
                    <div class="category-header">
                        <div class="category-name">{category}</div>
                        <div class="category-total">{total_qty:,.0f} 台</div>
                        <div class="expand-icon">▼</div>
                    </div>
                    <div class="category-details">
                        <div class="detail-item">
                            <div class="detail-label">常规仓</div>
                            <div class="detail-value">{row['常规仓']:,.0f}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">顺丰仓</div>
                            <div class="detail-value">{row['顺丰仓']:,.0f}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">京仓</div>
                            <div class="detail-value">{row['京仓']:,.0f}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">云仓</div>
                            <div class="detail-value">{row['云仓']:,.0f}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">统仓</div>
                            <div class="detail-value">{row['统仓']:,.0f}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">金融仓</div>
                            <div class="detail-value">{row['金融仓']:,.0f}</div>
                        </div>
                    </div>
                    <div class="product-list" id="products-{category}">
                        <div class="product-item product-header">
                            <div>型号</div>
                            <div>常规仓</div>
                            <div>顺丰仓</div>
                            <div>京仓</div>
                            <div>云仓</div>
                            <div>统仓</div>
                            <div>金融仓</div>
                        </div>
"""
            
            # 添加产品详情
            for _, product in category_products.iterrows():
                html_content += f"""
                        <div class="product-item">
                            <div>{product['型号']}</div>
                            <div>{product['常规仓']:,.0f}</div>
                            <div>{product['顺丰仓']:,.0f}</div>
                            <div>{product['京仓']:,.0f}</div>
                            <div>{product['云仓']:,.0f}</div>
                            <div>{product['统仓']:,.0f}</div>
                            <div>{product['金融仓']:,.0f}</div>
                        </div>
"""
            
            html_content += """
                    </div>
                </div>
"""
        
        html_content += f"""
            </div>
            
            <div class="timestamp">
                更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </div>
    
    <script>
        function toggleProducts(category) {{
            const productList = document.getElementById('products-' + category);
            const categoryItem = productList.parentElement;
            
            if (productList.style.display === 'none' || productList.style.display === '') {{
                productList.style.display = 'block';
                categoryItem.classList.add('expanded');
            }} else {{
                productList.style.display = 'none';
                categoryItem.classList.remove('expanded');
            }}
        }}
    </script>
</body>
</html>
"""
        
        return html_content
    
    def deploy_to_edgeone(self, reports_dir):
        """部署到EdgeOne Pages（函数方式）"""
        try:
            logger.info("🚀 开始部署到EdgeOne Pages...")
            logger.info(f"📁 部署目录: {reports_dir}")
            
            # 检查部署目录是否存在
            if not os.path.exists(reports_dir):
                logger.error(f"❌ 部署目录不存在: {reports_dir}")
                return False
            
            # 检查目录中是否有文件
            files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
            if not files:
                logger.error(f"❌ 部署目录中没有HTML文件: {reports_dir}")
                return False
            
            logger.info(f"📄 找到 {len(files)} 个HTML文件")
            
            # 获取最新的HTML文件内容
            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(reports_dir, x)))
            html_file_path = os.path.join(reports_dir, latest_file)
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 创建函数文件
            functions_dir = os.path.join(reports_dir, "functions")
            if not os.path.exists(functions_dir):
                os.makedirs(functions_dir, exist_ok=True)
            
            # 创建HTML函数
            html_function_path = os.path.join(functions_dir, "inventory.js")
            html_function_content = f"""
export function onRequest(context) {{
  const html = `{html_content.replace('`', '\\`')}`;
  return new Response(html, {{
    headers: {{
      'content-type': 'text/html; charset=utf-8',
    }},
  }});
}}
"""
            
            with open(html_function_path, 'w', encoding='utf-8') as f:
                f.write(html_function_content)
            
            logger.info(f"📄 创建HTML函数: {html_function_path}")
            
            # 使用绝对路径
            deploy_path = os.path.abspath(reports_dir)
            logger.info(f"🔧 使用绝对路径部署: {deploy_path}")
            
            # 多环境EdgeOne CLI路径检测
            edgeone_cli_path = self._get_edgeone_cli_path()
            logger.info(f"🔧 使用EdgeOne CLI路径: {edgeone_cli_path}")
            
            # 执行部署命令
            result = subprocess.run([
                edgeone_cli_path, "pages", "deploy", deploy_path,
                "-n", "inventory-report",
                "-t", "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ EdgeOne Pages 自动部署成功！")
                logger.info(f"📤 部署输出: {result.stdout}")
                return True
            else:
                logger.error(f"❌ EdgeOne Pages 部署失败：{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ 部署超时")
            return False
        except Exception as e:
            logger.error(f"❌ 部署异常: {e}")
            return False
    
    def _get_edgeone_cli_path(self):
        """获取EdgeOne CLI路径（多环境适配）"""
        import platform
        
        # 检测操作系统
        system = platform.system().lower()
        logger.info(f"🔍 检测到操作系统: {system}")
        
        # 定义可能的CLI路径
        possible_paths = []
        
        if system == "windows":
            # Windows环境路径
            possible_paths = [
                r"C:\Users\weicu\AppData\Roaming\npm\edgeone.cmd",
                r"C:\Users\weicu\AppData\Roaming\npm\edgeone.exe",
                r"C:\Program Files\nodejs\node_modules\npm\bin\edgeone.cmd",
                "edgeone.cmd",
                "edgeone"
            ]
        elif system == "darwin":  # macOS
            # macOS环境路径
            possible_paths = [
                "/Users/weixiaogang/.npm-global/bin/edgeone",  # 用户npm全局安装
                "/usr/local/bin/edgeone",
                "/opt/homebrew/bin/edgeone",
                "/usr/bin/edgeone",
                "edgeone"
            ]
        else:  # Linux或其他
            # Linux环境路径
            possible_paths = [
                "/usr/local/bin/edgeone",
                "/usr/bin/edgeone",
                "edgeone"
            ]
        
        # 检查路径是否存在
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ 找到EdgeOne CLI: {path}")
                return path
        
        # 如果都找不到，使用环境变量中的edgeone
        logger.warning("⚠️ 未找到EdgeOne CLI，尝试使用环境变量")
        return "edgeone"
    
    def _simple_verify_url(self, public_url):
        """验证URL是否可访问"""
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
                    logger.warning(f"⚠️ 第{attempt+1}次验证失败，文件不存在 (404)，等待CDN同步...")
                else:
                    logger.warning(f"⚠️ 第{attempt+1}次验证失败，状态码: {response.status_code}")
                    
            except Exception as verify_e:
                logger.warning(f"⚠️ 第{attempt+1}次验证异常: {verify_e}")
        
        logger.error(f"❌ URL验证失败，经过5次重试仍无法访问，不返回URL")
        return None
    
    def upload_html_and_get_url(self, filename, html_content):
        """通过远程5002端口部署HTML内容"""
        try:
            logger.info(f"\n🌐 正在生成HTML内容: {filename}")
            
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
            
            # 通过5002端口部署到远程服务器
            try:
                import requests
                import json
                
                # 部署URL
                deploy_url = "http://212.64.57.87:5002/deploy_html"
                
                # 准备部署数据
                deploy_data = {
                    "filename": filename,
                    "content": html_content
                }
                
                logger.info(f"🚀 正在部署到远程服务器: {deploy_url}")
                
                # 发送部署请求
                response = requests.post(
                    deploy_url,
                    json=deploy_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('success'):
                        public_url = response_data.get('url')
                        logger.info(f"✅ 远程部署成功！公网链接: {public_url}")
                        return public_url
                    else:
                        logger.error(f"❌ 远程部署失败: {response_data.get('message', '未知错误')}")
                        return None
                else:
                    logger.error(f"❌ 远程部署请求失败，状态码: {response.status_code}")
                    return None
                    
            except Exception as deploy_error:
                logger.error(f"❌ 远程部署异常: {deploy_error}")
                return None
                    
        except Exception as e:
            logger.error(f"❌ 生成HTML文件异常: {e}")
            return None
    
    def send_wechat_message(self, message: str, url: str = None) -> bool:
        """通过远程5001端口发送企业微信消息"""
        try:
            import requests
            import json
            
            # 消息服务器URL
            message_url = "http://212.64.57.87:5001/send_message"
            
            # 准备消息数据
            message_data = {
                "message": message,
                "url": url
            }
            
            logger.info(f"📤 正在发送企业微信消息到: {message_url}")
            
            # 发送消息请求
            response = requests.post(
                message_url,
                json=message_data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    logger.info("✅ 企业微信消息发送成功")
                    return True
                else:
                    logger.error(f"❌ 企业微信消息发送失败: {response_data.get('message', '未知错误')}")
                    return False
            else:
                logger.error(f"❌ 企业微信消息请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送企业微信消息异常: {e}")
            return False
    
    def generate_summary_message(self, result_df: pd.DataFrame) -> str:
        """生成摘要消息 - 统一显示所有数据"""
        if result_df.empty:
            return "📦 库存数据报告\n\n❌ 暂无库存数据"
        
        # 按品类统计
        category_summary = result_df.groupby('品类').agg({
            '合计数量': 'sum',
            '常规仓': 'sum',
            '顺丰仓': 'sum',
            '京仓': 'sum',
            '云仓': 'sum',
            '统仓': 'sum',
            '金融仓': 'sum'
        }).reset_index()
        
        # 计算总计
        total_summary = {
            'total_stock': result_df['合计数量'].sum(),
            'regular_warehouse': result_df['常规仓'].sum(),
            'sf_warehouse': result_df['顺丰仓'].sum(),
            'jd_warehouse': result_df['京仓'].sum(),
            'cloud_warehouse': result_df['云仓'].sum(),
            'tong_warehouse': result_df['统仓'].sum(),
            'jinrong_warehouse': result_df['金融仓'].sum(),
            'total_products': result_df['型号'].nunique(),
            'total_categories': result_df['品类'].nunique()
        }
        
        message = f"""📦 库存数据报告

📊 总体概况:
• 总库存量: {total_summary['total_stock']:,.0f}
• 商品种类: {total_summary['total_products']}
• 品类数量: {total_summary['total_categories']}

🏪 仓库分布:"""
        
        if total_summary['regular_warehouse'] > 0:
            message += f"\n• 常规仓: {total_summary['regular_warehouse']:,.0f}"
        if total_summary['sf_warehouse'] > 0:
            message += f"\n• 顺丰仓: {total_summary['sf_warehouse']:,.0f}"
        if total_summary['jd_warehouse'] > 0:
            message += f"\n• 京仓: {total_summary['jd_warehouse']:,.0f}"
        if total_summary['cloud_warehouse'] > 0:
            message += f"\n• 云仓: {total_summary['cloud_warehouse']:,.0f}"
        if total_summary['tong_warehouse'] > 0:
            message += f"\n• 统仓: {total_summary['tong_warehouse']:,.0f}"
        if total_summary['jinrong_warehouse'] > 0:
            message += f"\n• 金融仓: {total_summary['jinrong_warehouse']:,.0f}"
        
        message += "\n\n📋 品类细分:"
        for _, row in category_summary.iterrows():
            category = row['品类']
            total_qty = row['合计数量']
            
            # 统一显示所有数据，不区分线上线下
            message += f"\n• {category}: {total_qty:,.0f}"
        
        message += f"\n\n📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def save_to_csv(self, result_df: pd.DataFrame):
        """保存结果到CSV文件"""
        if result_df.empty:
            logger.warning("没有数据可保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"库存分析新格式_{timestamp}.csv"
        
        try:
            result_df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
    
    def save_html_report(self, html_content: str):
        """保存HTML报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"库存分析_{timestamp}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML报告已保存: {filename}")
        except Exception as e:
            logger.error(f"保存HTML报告失败: {e}")
    
    def run(self):
        """主运行函数"""
        logger.info("开始执行库存数据处理")
        
        try:
            # 连接数据库
            if not self.connect_databases():
                logger.error("数据库连接失败，程序退出")
                return
            
            # 获取wdt数据库数据
            wdt_df = self.get_wdt_stock_data()
            if wdt_df.empty:
                logger.error("wdt数据库没有数据")
                return
            
            # 获取Date数据库数据
            store_data = self.get_date_store_data()
            if not store_data:
                logger.error("Date数据库没有数据")
                return
            
            # 处理库存数据
            result_df = self.process_inventory_data(wdt_df, store_data)
            if result_df.empty:
                logger.error("处理后没有有效数据")
                return
            
            # 保存CSV报告
            self.save_to_csv(result_df)
            
            # 生成HTML报告
            html_content = self.generate_html_report(result_df)
            self.save_html_report(html_content)
            
            # 部署到EdgeOne并获取URL
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"库存分析_{timestamp}.html"
            public_url = self.upload_html_and_get_url(filename, html_content)
            
            # 生成摘要消息
            summary_message = self.generate_summary_message(result_df)
            
            # 发送企业微信消息
            self.send_wechat_message(summary_message, public_url)
            
            logger.info("库存数据处理完成")
            
        except Exception as e:
            logger.error(f"处理过程中出现异常: {e}")
        finally:
            self.close_databases()

def main():
    """主函数"""
    processor = InventoryProcessor()
    processor.run()

if __name__ == "__main__":
    main()