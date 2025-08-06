#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================
📦 库存数据推送系统
==============================================
功能：连接数据库获取库存数据并推送到企业微信
数据源：库存系统
更新时间：按需执行
==============================================
"""

import pymysql
import pandas as pd
import requests
import json
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_push.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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
    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
    'key': 'your_webhook_key'  # 需要替换为实际的webhook key
}

class InventoryPusher:
    def __init__(self):
        self.connection = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            logging.info("✅ 数据库连接成功")
            return True
        except Exception as e:
            logging.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def close_db(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logging.info("📴 数据库连接已关闭")
    
    def get_table_structure(self, table_name):
        """获取表结构信息"""
        try:
            with self.connection.cursor() as cursor:
                sql = f"DESCRIBE {table_name}"
                cursor.execute(sql)
                columns = cursor.fetchall()
                return [col[0] for col in columns]
        except Exception as e:
            logging.error(f"获取表{table_name}结构失败: {e}")
            return []
    
    def get_inventory_data(self, table_name):
        """获取库存数据，处理特殊情况"""
        try:
            if table_name == 'tongstore':
                # tongstore表格特殊处理，跳过第一行
                query = f"SELECT * FROM {table_name} LIMIT 100"
                df = pd.read_sql(query, self.connection)
                
                if not df.empty:
                    # 假设第二行开始是有效数据
                    df = df.iloc[1:]  # 跳过第一行
                    
                    # 标准化列名
                    if len(df.columns) >= 4:
                        df.columns = ['品类', '型号', '数量', '库位'] + list(df.columns[4:])
                        
                    # 根据表名设置库位
                    location_map = {
                        'jdstore': '京仓',
                        'rrsstore': '云仓',
                        'tongstore': '统仓',
                        'jinrongstore': '金融仓',
                        'matchstore': '匹配仓'
                    }
                    
                    location = location_map.get(table_name, '未知库位')
                    if '库位' not in df.columns or df['库位'].isna().all():
                        df['库位'] = location
                        
                    return df[['品类', '型号', '库位', '数量']]
            else:
                # 其他表格正常处理
                columns = self.get_table_structure(table_name)
                if not columns:
                    return pd.DataFrame()
                
                # 尝试识别关键字段
                category_col = next((col for col in columns if any(keyword in col.lower() 
                    for keyword in ['品类', 'category', '产品', 'product'])), columns[0])
                model_col = next((col for col in columns if any(keyword in col.lower() 
                    for keyword in ['型号', 'model', '规格', 'spec']), columns[1] if len(columns) > 1 else columns[0])
                quantity_col = next((col for col in columns if any(keyword in col.lower() 
                    for keyword in ['数量', 'qty', '库存', 'stock']), columns[2] if len(columns) > 2 else columns[0])
                location_col = next((col for col in columns if any(keyword in col.lower() 
                    for keyword in ['库位', 'location', '仓库', 'warehouse']), None)
                
                query = f"SELECT {category_col}, {model_col}, {quantity_col}"
                if location_col:
                    query += f", {location_col}"
                query += f" FROM {table_name} WHERE {quantity_col} IS NOT NULL"
                
                df = pd.read_sql(query, self.connection)
                
                # 重命名列
                rename_map = {
                    category_col: '品类',
                    model_col: '型号',
                    quantity_col: '数量'
                }
                if location_col:
                    rename_map[location_col] = '库位'
                
                df = df.rename(columns=rename_map)
                
                # 设置默认库位
                location_map = {
                    'jdstore': '京仓',
                    'rrsstore': '云仓',
                    'tongstore': '统仓',
                    'jinrongstore': '金融仓',
                    'matchstore': '匹配仓'
                }
                
                if '库位' not in df.columns or df['库位'].isna().all():
                    location = location_map.get(table_name, '未知库位')
                    df['库位'] = location
                
                return df[['品类', '型号', '库位', '数量']]
                
        except Exception as e:
            logging.error(f"获取{table_name}数据失败: {e}")
            return pd.DataFrame()
    
    def format_inventory_message(self, all_data):
        """格式化库存消息"""
        if all_data.empty:
            return "暂无库存数据"
        
        message = f"📦 库存报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 按库位分组统计
        location_summary = all_data.groupby(['库位', '品类'])['数量'].sum().reset_index()
        
        for location in ['京仓', '云仓', '统仓', '金融仓']:
            location_data = location_summary[location_summary['库位'] == location]
            if not location_data.empty:
                message += f"🏪 {location}:\n"
                for _, row in location_data.iterrows():
                    message += f"   {row['品类']}: {int(row['数量'])}件\n"
                message += "\n"
        
        # 添加详细信息表格
        message += "\n📊 详细库存:\n"
        message += "品类 | 型号 | 库位 | 数量\n"
        message += "---|---|---|---\n"
        
        for _, row in all_data.head(20).iterrows():
            message += f"{row['品类']} | {row['型号']} | {row['库位']} | {int(row['数量'])}\n"
        
        if len(all_data) > 20:
            message += f"... 共{len(all_data)}条记录\n"
        
        return message
    
    def send_wechat_message(self, message):
        """发送企业微信消息"""
        try:
            # 检查消息长度，企业微信限制2048字符
            if len(message) > 2048:
                message = message[:2045] + "..."
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            
            # 使用webhook方式发送
            webhook_url = "http://212.64.57.87:5001/send"
            response = requests.post(webhook_url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logging.info("✅ 企业微信消息发送成功")
                    return True
                else:
                    logging.error(f"❌ 企业微信消息发送失败: {result}")
                    return False
            else:
                logging.error(f"❌ HTTP请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ 发送消息异常: {e}")
            return False
    
    def run(self):
        """主运行函数"""
        logging.info("🚀 开始执行库存数据推送...")
        
        if not self.connect_db():
            return False
        
        try:
            # 需要查询的表
            tables = ['jinrongstore', 'rrsstore', 'tongstore', 'jdstore', 'matchstore']
            all_data = []
            
            for table in tables:
                logging.info(f"📊 正在处理表: {table}")
                df = self.get_inventory_data(table)
                if not df.empty:
                    logging.info(f"✅ 从{table}获取到{len(df)}条数据")
                    all_data.append(df)
                else:
                    logging.warning(f"⚠️ {table}表无数据")
            
            if all_data:
                # 合并所有数据
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # 数据清洗
                combined_df = combined_df.dropna(subset=['品类', '型号', '数量'])
                combined_df['数量'] = pd.to_numeric(combined_df['数量'], errors='coerce').fillna(0)
                combined_df = combined_df[combined_df['数量'] > 0]
                
                # 格式化消息
                message = self.format_inventory_message(combined_df)
                
                # 发送消息
                if self.send_wechat_message(message):
                    logging.info("✅ 库存推送完成")
                    
                    # 保存到文件
                    combined_df.to_csv(f'inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 
                                     index=False, encoding='utf-8-sig')
                    logging.info("📁 数据已保存到CSV文件")
                    
                    return True
                else:
                    logging.error("❌ 消息发送失败")
                    return False
            else:
                logging.warning("⚠️ 没有获取到任何库存数据")
                return False
                
        except Exception as e:
            logging.error(f"❌ 执行过程出错: {e}")
            return False
        finally:
            self.close_db()

if __name__ == "__main__":
    pusher = InventoryPusher()
    success = pusher.run()
    
    if success:
        print("✅ 库存推送脚本执行成功")
    else:
        print("❌ 库存推送脚本执行失败")
        exit(1)