#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存推送脚本
功能：连接Date数据库，获取库存数据，处理格式，推送到企业微信
参考整体日报数据.py的消息推送逻辑
"""

import pymysql
import pandas as pd
import requests
import logging
from datetime import datetime
import os
import json

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
    'charset': 'utf8mb4'
}

# 企业微信配置
WECOM_CONFIG = {
    'webhook_url': 'http://212.64.57.87:5001/send',
    'token': 'weicungang'
}

# 库存表配置
INVENTORY_TABLES = {
    'jinrongstore': {'name': '金融仓', 'category_col': '品类', 'model_col': '型号', 'location_col': '库位', 'quantity_col': '数量'},
    'rrsstore': {'name': '云仓', 'category_col': '品类', 'model_col': '型号', 'location_col': '库位', 'quantity_col': '数量'},
    'tongstore': {'name': '统仓', 'category_col': '品类', 'model_col': '型号', 'location_col': '库位', 'quantity_col': '数量', 'header_row': 1},
    'jdstore': {'name': '京仓', 'category_col': '品类', 'model_col': '型号', 'location_col': '库位', 'quantity_col': '数量'},
    'matchstore': {'name': '匹配表', 'category_col': '品类', 'model_col': '型号', 'location_col': '库位', 'quantity_col': '数量'}
}

class InventoryPusher:
    """库存推送器"""
    
    def __init__(self):
        self.connection_pool = None
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = pymysql.ConnectionPool(
                **DB_CONFIG,
                max_connections=10,
                min_cached=2,
                max_cached=5,
                blocking=True,
                setsession=["SET time_zone = '+8:00'"]
            )
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            self.connection_pool = None
    
    def get_connection(self):
        """从连接池获取连接"""
        if not self.connection_pool:
            logger.error("连接池未初始化")
            return None
        
        try:
            return self.connection_pool.connection()
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            return None
    
    def close_connection(self, connection):
        """关闭数据库连接"""
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.warning(f"关闭数据库连接时出错: {e}")
    
    def get_table_data(self, table_name: str, config: dict) -> pd.DataFrame:
        """获取指定表的数据"""
        connection = None
        try:
            connection = self.get_connection()
            if not connection:
                return pd.DataFrame()
            
            # 处理tongstore表的特殊情况（标题行在第二行）
            if table_name == 'tongstore' and 'header_row' in config:
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, connection)
                
                # 如果数据不为空，跳过第一行，使用第二行作为标题
                if not df.empty and len(df) > 1:
                    # 获取第二行作为列名
                    new_columns = df.iloc[1].values
                    # 从第三行开始作为数据
                    df = df[2:].copy()
                    df.columns = new_columns
                    logger.info(f"处理{table_name}表：跳过标题行，使用第二行作为列名")
                return df
            else:
                query = f"SELECT * FROM {table_name}"
                return pd.read_sql(query, connection)
                
        except Exception as e:
            logger.error(f"获取表{table_name}数据失败: {e}")
            return pd.DataFrame()
        finally:
            self.close_connection(connection)
    
    def standardize_data(self, df: pd.DataFrame, table_name: str, config: dict) -> pd.DataFrame:
        """标准化数据格式"""
        if df.empty:
            return df
        
        try:
            # 标准化列名
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if '品类' in str(col) or 'category' in col_lower or '类别' in str(col):
                    column_mapping[col] = '品类'
                elif '型号' in str(col) or 'model' in col_lower or '规格' in str(col):
                    column_mapping[col] = '型号'
                elif '库位' in str(col) or 'location' in col_lower or '仓库' in str(col):
                    column_mapping[col] = '库位'
                elif '数量' in str(col) or 'quantity' in col_lower or '库存' in str(col):
                    column_mapping[col] = '数量'
            
            df = df.rename(columns=column_mapping)
            
            # 确保必要的列存在
            required_cols = ['品类', '型号', '库位', '数量']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ''
            
            # 添加仓库类型信息
            warehouse_name = INVENTORY_TABLES[table_name]['name']
            df['库位'] = warehouse_name
            
            # 确保数量列为数值类型
            df['数量'] = pd.to_numeric(df['数量'], errors='coerce').fillna(0)
            
            # 只保留需要的列
            result_df = df[['品类', '型号', '库位', '数量']].copy()
            
            # 过滤掉空数据
            result_df = result_df[
                (result_df['品类'].notna()) & 
                (result_df['品类'] != '') & 
                (result_df['数量'] > 0)
            ]
            
            logger.info(f"标准化{table_name}数据完成，共{len(result_df)}条记录")
            return result_df
            
        except Exception as e:
            logger.error(f"标准化{table_name}数据失败: {e}")
            return pd.DataFrame()
    
    def get_all_inventory(self) -> pd.DataFrame:
        """获取所有库存数据"""
        all_data = []
        
        for table_name, config in INVENTORY_TABLES.items():
            logger.info(f"正在处理表: {table_name}")
            
            # 获取数据
            df = self.get_table_data(table_name, config)
            if df.empty:
                logger.warning(f"表{table_name}无数据")
                continue
            
            # 标准化数据
            standardized_df = self.standardize_data(df, table_name, config)
            if not standardized_df.empty:
                all_data.append(standardized_df)
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            logger.info(f"获取所有库存数据完成，共{len(result)}条记录")
            return result
        else:
            logger.warning("未获取到任何库存数据")
            return pd.DataFrame()
    
    def format_inventory_message(self, df: pd.DataFrame) -> str:
        """格式化库存消息"""
        if df.empty:
            return "暂无库存数据"
        
        message = "📦 当前库存统计\n\n"
        
        # 按库位分组统计
        warehouse_summary = df.groupby('库位')['数量'].sum().to_dict()
        
        for warehouse, total in warehouse_summary.items():
            message += f"🏭 {warehouse}: {total}件\n"
        
        message += "\n📊 详细库存信息:\n"
        message += "=" * 50 + "\n"
        
        # 添加详细数据
        for _, row in df.iterrows():
            message += f"品类: {row['品类']} | 型号: {row['型号']} | 库位: {row['库位']} | 数量: {int(row['数量'])}\n"
        
        message += f"\n总计: {len(df)}个型号，{int(df['数量'].sum())}件库存"
        message += f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def send_wecom_message(self, message: str) -> bool:
        """发送企业微信消息"""
        try:
            data = {
                'token': WECOM_CONFIG['token'],
                'message': message
            }
            
            response = requests.post(
                WECOM_CONFIG['webhook_url'],
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"消息发送失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False
    
    def save_inventory_csv(self, df: pd.DataFrame, filename: str = None):
        """保存库存数据到CSV文件"""
        if df.empty:
            return
        
        if not filename:
            filename = f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"库存数据已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
    
    def push_inventory(self) -> bool:
        """推送库存数据"""
        try:
            if not self.connect_database():
                return False
            
            # 获取所有库存数据
            inventory_df = self.get_all_inventory()
            
            if inventory_df.empty:
                logger.warning("无库存数据可推送")
                return False
            
            # 格式化消息
            message = self.format_inventory_message(inventory_df)
            
            # 保存数据
            self.save_inventory_csv(inventory_df)
            
            # 发送消息
            success = self.send_wecom_message(message)
            
            return success
            
        except Exception as e:
            logger.error(f"推送库存失败: {e}")
            return False
        finally:
            self.close_database()
    
    def close_database(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def get_table_columns(self, table_name):
        """获取表结构"""
        if not self.connection:
            logger.error("数据库未连接")
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                return [col[0] for col in columns]
        except Exception as e:
            logger.error(f"获取表{table_name}结构失败: {e}")
            return []
    
    def get_inventory_data(self, table_name, warehouse_type):
        """获取库存数据"""
        if not self.connection:
            logger.error("数据库未连接")
            return pd.DataFrame()
        
        try:
            # 特殊处理tongstore表
            if table_name == 'tongstore':
                # 跳过第一行（标题行在第二行）
                query = f"""
                SELECT * FROM {table_name} LIMIT 1, 1000
                """
                df = pd.read_sql(query, self.connection)
                
                # 重新获取正确的列名
                columns = self.get_table_columns(table_name)
                if len(columns) > 0 and len(df) > 0:
                    # 使用正确的列名重新查询
                    query = f"""
                    SELECT * FROM {table_name} LIMIT 1, 1000
                    """
                    df = pd.read_sql(query, self.connection)
                    # 手动设置列名
                    df.columns = columns
                    # 跳过第一行数据（因为第一行是标题）
                    df = df.iloc[1:].reset_index(drop=True)
            else:
                query = f"""
                SELECT * FROM {table_name} LIMIT 1000
                """
                df = pd.read_sql(query, self.connection)
            
            # 添加库位信息
            df['库位'] = warehouse_type
            return df
            
        except Exception as e:
            logger.error(f"获取{table_name}数据失败: {e}")
            return pd.DataFrame()
    
    def process_inventory_data(self):
        """处理库存数据"""
        inventory_mapping = {
            'jdstore': '京仓',
            'rrsstore': '云仓',
            'tongstore': '统仓',
            'jinrongstore': '金融仓',
            'matchstore': '匹配仓'
        }
        
        all_data = []
        
        for table_name, warehouse_type in inventory_mapping.items():
            logger.info(f"处理表: {table_name}")
            df = self.get_inventory_data(table_name, warehouse_type)
            
            if df.empty:
                logger.warning(f"表{table_name}无数据")
                continue
            
            # 标准化列名
            columns = df.columns.tolist()
            
            # 寻找对应的列名
            category_col = None
            model_col = None
            quantity_col = None
            
            for col in columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['品类', '分类', 'category', 'type']):
                    category_col = col
                elif any(keyword in col_lower for keyword in ['型号', 'model', '规格', 'spec']):
                    model_col = col
                elif any(keyword in col_lower for keyword in ['数量', '库存', 'quantity', 'stock', 'num']):
                    quantity_col = col
            
            # 如果没有找到对应列，使用前几列
            if category_col is None and len(columns) >= 1:
                category_col = columns[0]
            if model_col is None and len(columns) >= 2:
                model_col = columns[1]
            if quantity_col is None and len(columns) >= 3:
                quantity_col = columns[2]
            
            # 提取数据
            if category_col and model_col and quantity_col:
                temp_df = df[[category_col, model_col, quantity_col]].copy()
                temp_df.columns = ['品类', '型号', '数量']
                temp_df['库位'] = warehouse_type
                
                # 清理数据
                temp_df = temp_df.dropna()
                temp_df['数量'] = pd.to_numeric(temp_df['数量'], errors='coerce')
                temp_df = temp_df[temp_df['数量'] > 0]
                
                all_data.append(temp_df)
        
        if all_data:
            result_df = pd.concat(all_data, ignore_index=True)
            return result_df
        else:
            return pd.DataFrame(columns=['品类', '型号', '库位', '数量'])
    
    def send_wecom_message(self, message):
        """发送企业微信消息"""
        try:
            headers = {'Content-Type': 'application/json'}
            data = {
                'msgtype': 'text',
                'text': {
                    'content': message
                }
            }
            
            response = requests.post(
                WECOM_CONFIG['webhook_url'],
                headers=headers,
                json=data,
                params={'token': WECOM_CONFIG['token']}
            )
            
            if response.status_code == 200:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"消息发送失败: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False
    
    def format_inventory_message(self, df):
        """格式化库存消息"""
        if df.empty:
            return "暂无库存数据"
        
        message = "📦 库存数据推送\n\n"
        
        # 按库位分组统计
        summary = df.groupby('库位').agg({
            '数量': 'sum',
            '型号': 'count'
        }).rename(columns={'型号': '商品数'})
        
        message += "【库存总览】\n"
        for warehouse, data in summary.iterrows():
            message += f"{warehouse}: 商品{data['商品数']}个, 总数量{data['数量']}件\n"
        
        message += "\n【详细数据】\n"
        
        # 显示前20条记录
        display_df = df.head(20)
        for _, row in display_df.iterrows():
            message += f"{row['品类']} | {row['型号']} | {row['库位']} | {row['数量']}\n"
        
        if len(df) > 20:
            message += f"...\n共{len(df)}条记录"
        
        return message
    
    def run(self):
        """运行库存推送"""
        logger.info("开始库存推送任务")
        
        if not self.connect_database():
            return False
        
        try:
            # 获取并处理库存数据
            inventory_df = self.process_inventory_data()
            
            # 格式化消息
            message = self.format_inventory_message(inventory_df)
            
            # 发送消息
            success = self.send_wecom_message(message)
            
            # 保存数据到文件
            if not inventory_df.empty:
                filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                inventory_df.to_csv(filename, index=False, encoding='utf-8-sig')
                logger.info(f"数据已保存到: {filename}")
            
            return success
            
        finally:
            self.close_database()

if __name__ == "__main__":
    pusher = InventoryPusher()
    pusher.run()