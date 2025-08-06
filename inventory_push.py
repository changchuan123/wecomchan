#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存推送脚本
功能：连接数据库获取库存数据，处理后推送到企业微信
参考：整体日报数据.py的消息推送逻辑
"""

import pymysql
import pandas as pd
import requests
import json
import logging
from datetime import datetime
import time
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_push.log', encoding='utf-8'),
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
    'port': 3306,
    'charset': 'utf8mb4'
}

# 企业微信配置
WECOM_CONFIG = {
    'webhook_url': 'http://212.64.57.87:5001/send',
    'token': 'weicungang',
    'max_retries': 5,
    'retry_delay': 2
}

class InventoryPusher:
    def __init__(self):
        self.connection = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
            
    def close_db(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
            
    def get_table_structure(self, table_name):
        """获取表结构信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                return [col[0] for col in columns]
        except Exception as e:
            logger.error(f"获取表{table_name}结构失败: {e}")
            return []
            
    def get_inventory_data(self, table_name):
        """获取库存数据，处理tongstore的特殊情况"""
        try:
            with self.connection.cursor() as cursor:
                if table_name == 'tongstore':
                    # tongstore特殊处理：跳过第一行无效标题
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                    sample_data = cursor.fetchall()
                    
                    if sample_data:
                        # 获取列名
                        columns = self.get_table_structure(table_name)
                        
                        # 重新查询，跳过第一行
                        cursor.execute(f"SELECT * FROM {table_name} WHERE 1=1")
                        all_data = cursor.fetchall()
                        
                        # 创建DataFrame，跳过第一行
                        df = pd.DataFrame(all_data[1:] if len(all_data) > 1 else all_data, 
                                        columns=columns)
                        return df
                else:
                    # 其他表格正常处理
                    query = f"SELECT * FROM {table_name}"
                    df = pd.read_sql(query, self.connection)
                    return df
                    
        except Exception as e:
            logger.error(f"获取{table_name}数据失败: {e}")
            return pd.DataFrame()
            
    def process_inventory_data(self):
        """处理库存数据，统一格式"""
        inventory_tables = ['jdstore', 'rrsstore', 'tongstore', 'jinrongstore', 'matchstore']
        all_inventory = []
        
        for table in inventory_tables:
            logger.info(f"正在处理表: {table}")
            
            # 获取数据
            df = self.get_inventory_data(table)
            if df.empty:
                logger.warning(f"表{table}无数据，跳过")
                continue
                
            # 获取表结构
            columns = self.get_table_structure(table)
            logger.info(f"表{table}的列: {columns}")
            
            # 标准化列名
            df.columns = [col.lower() for col in df.columns]
            
            # 根据表名确定库位类型
            warehouse_map = {
                'jdstore': '京仓',
                'rrsstore': '云仓',
                'tongstore': '统仓',
                'jinrongstore': '金融仓',
                'matchstore': '匹配库'
            }
            
            warehouse_type = warehouse_map.get(table, '未知库位')
            
            # 提取关键字段（根据实际列名调整）
            # 尝试识别品类、型号、数量字段
            category_col = None
            model_col = None
            quantity_col = None
            location_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['品类', 'category', 'cat', 'type']):
                    category_col = col
                elif any(keyword in col_lower for keyword in ['型号', 'model', '规格', 'sku', 'product']):
                    model_col = col
                elif any(keyword in col_lower for keyword in ['数量', 'quantity', 'qty', 'count', '库存']):
                    quantity_col = col
                elif any(keyword in col_lower for keyword in ['库位', 'location', '仓库', 'warehouse']):
                    location_col = col
            
            # 如果找不到明确字段，使用前几个字段
            if not category_col and len(df.columns) > 0:
                category_col = df.columns[0]
            if not model_col and len(df.columns) > 1:
                model_col = df.columns[1]
            if not quantity_col and len(df.columns) > 2:
                quantity_col = df.columns[2]
                
            # 创建标准化数据
            temp_df = pd.DataFrame()
            temp_df['品类'] = df[category_col] if category_col in df.columns else '未知品类'
            temp_df['型号'] = df[model_col] if model_col in df.columns else '未知型号'
            temp_df['数量'] = pd.to_numeric(df[quantity_col], errors='coerce').fillna(0) if quantity_col in df.columns else 0
            temp_df['库位'] = warehouse_type
            
            # 如果有库位字段，使用具体库位
            if location_col and location_col in df.columns:
                temp_df['库位'] = df[location_col].fillna(warehouse_type)
            
            all_inventory.append(temp_df)
            
        if not all_inventory:
            logger.error("没有获取到任何库存数据")
            return pd.DataFrame()
            
        # 合并所有数据
        final_df = pd.concat(all_inventory, ignore_index=True)
        
        # 数据清洗
        final_df = final_df.dropna(subset=['型号'])
        final_df = final_df[final_df['型号'] != '未知型号']
        final_df = final_df[final_df['数量'] > 0]
        
        # 按品类、型号、库位汇总
        summary_df = final_df.groupby(['品类', '型号', '库位']).agg({
            '数量': 'sum'
        }).reset_index()
        
        return summary_df
        
    def format_inventory_message(self, df):
        """格式化库存消息"""
        if df.empty:
            return "暂无库存数据"
            
        message = f"📦 库存报告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n"
        
        # 按库位分组统计
        warehouse_summary = df.groupby('库位')['数量'].sum().to_dict()
        
        message += "📊 库存汇总:\n"
        for warehouse, total in warehouse_summary.items():
            message += f"• {warehouse}: {int(total)}\n"
        
        message += "\n📋 详细库存:\n"
        
        # 限制显示条数，避免消息过长
        display_limit = 50
        if len(df) > display_limit:
            df_display = df.head(display_limit)
            message += f"(显示前{display_limit}条，共{len(df)}条)\n\n"
        else:
            df_display = df
            
        for _, row in df_display.iterrows():
            message += f"{row['品类']} | {row['型号']} | {row['库位']} | {int(row['数量'])}\n"
            
        if len(df) > display_limit:
            message += f"\n... 共{len(df)}条记录"
            
        return message
        
    def send_wechat_message(self, message):
        """发送企业微信消息"""
        url = WECOM_CONFIG['webhook_url']
        data = {
            'token': WECOM_CONFIG['token'],
            'content': message
        }
        
        for attempt in range(WECOM_CONFIG['max_retries']):
            try:
                response = requests.post(url, json=data, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('errcode') == 0:
                        logger.info("消息发送成功")
                        return True
                    else:
                        logger.warning(f"消息发送失败: {result}")
                        if attempt < WECOM_CONFIG['max_retries'] - 1:
                            time.sleep(WECOM_CONFIG['retry_delay'] * (2 ** attempt))
                            continue
                else:
                    logger.error(f"HTTP错误: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"发送消息异常: {e}")
                if attempt < WECOM_CONFIG['max_retries'] - 1:
                    time.sleep(WECOM_CONFIG['retry_delay'] * (2 ** attempt))
                    continue
                    
        logger.error("消息发送失败，已达最大重试次数")
        return False
        
    def run(self):
        """运行库存推送"""
        logger.info("开始执行库存推送任务")
        
        if not self.connect_db():
            return False
            
        try:
            # 处理库存数据
            inventory_df = self.process_inventory_data()
            
            if inventory_df.empty:
                logger.warning("没有库存数据可推送")
                message = "📦 库存报告\n\n暂无库存数据"
            else:
                # 格式化消息
                message = self.format_inventory_message(inventory_df)
                
            # 保存结果到文件
            inventory_df.to_csv(f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 
                              index=False, encoding='utf-8')
            logger.info("库存数据已保存到CSV文件")
            
            # 发送消息
            success = self.send_wechat_message(message)
            
            if success:
                logger.info("库存推送任务完成")
                return True
            else:
                logger.error("库存推送任务失败")
                return False
                
        finally:
            self.close_db()

if __name__ == "__main__":
    pusher = InventoryPusher()
    success = pusher.run()
    sys.exit(0 if success else 1)