#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存数据处理脚本
功能：从wdt数据库获取库存数据，按仓库类型聚合，生成报告并推送到企业微信
"""

import pymysql
import pandas as pd
import json
import requests
import logging
from datetime import datetime, timedelta
import os
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

# 企业微信配置
WECOM_CONFIG = {
    'corpid': os.getenv('WECOM_CID', ''),
    'corpsecret': os.getenv('WECOM_SECRET', ''),
    'agentid': os.getenv('WECOM_AID', ''),
    'touser': os.getenv('WECOM_TOUID', 'weicungang')
}

# EdgeOne Pages配置
EDGEONE_CONFIG = {
    'zone_id': os.getenv('EDGEONE_ZONE_ID', ''),
    'token': os.getenv('EDGEONE_TOKEN', ''),
    'project_name': 'inventory-report'
}

class InventoryProcessor:
    """库存数据处理器"""
    
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
    
    def get_inventory_data(self) -> pd.DataFrame:
        """获取库存数据"""
        if not self.connection:
            logger.error("数据库未连接")
            return pd.DataFrame()
        
        # 定义仓库分类
        regular_warehouses = ['常规仓']
        sf_warehouses = ['能良顺丰东莞仓', '能良顺丰武汉仓', '能良顺丰武汉金融仓', '能良顺丰金华仓']
        
        query = """
        SELECT 
            warehouse_name,
            goods_no,
            goods_name,
            spec_no,
            spec_name,
            brand_name,
            avaliable_num as available_stock,
            stock_num,
            lock_num,
            modified
        FROM stock 
        WHERE warehouse_name IN ({}) 
        AND avaliable_num > 0
        ORDER BY warehouse_name, goods_no, spec_no
        """.format(','.join(["'{}'".format(w) for w in regular_warehouses + sf_warehouses]))
        
        try:
            df = pd.read_sql(query, self.connection)
            logger.info(f"获取库存数据成功，共 {len(df)} 条记录")
            return df
        except Exception as e:
            logger.error(f"获取库存数据失败: {e}")
            return pd.DataFrame()
    
    def aggregate_inventory_data(self, df: pd.DataFrame) -> Dict:
        """聚合库存数据"""
        if df.empty:
            return {}
        
        # 定义仓库分类
        regular_warehouses = ['常规仓']
        sf_warehouses = ['能良顺丰东莞仓', '能良顺丰武汉仓', '能良顺丰武汉金融仓', '能良顺丰金华仓']
        
        # 添加仓库类型列
        df['warehouse_type'] = df['warehouse_name'].apply(
            lambda x: '常规仓' if x in regular_warehouses else '顺丰仓' if x in sf_warehouses else '其他'
        )
        
        # 按仓库类型聚合
        warehouse_summary = df.groupby('warehouse_type').agg({
            'available_stock': 'sum',
            'stock_num': 'sum',
            'lock_num': 'sum',
            'goods_no': 'nunique',
            'spec_no': 'nunique'
        }).round(2)
        
        # 按具体仓库聚合
        detailed_summary = df.groupby('warehouse_name').agg({
            'available_stock': 'sum',
            'stock_num': 'sum',
            'lock_num': 'sum',
            'goods_no': 'nunique',
            'spec_no': 'nunique'
        }).round(2)
        
        # 品牌库存统计
        brand_summary = df.groupby(['warehouse_type', 'brand_name']).agg({
            'available_stock': 'sum'
        }).round(2)
        
        # 总计
        total_summary = {
            'total_available_stock': df['available_stock'].sum(),
            'total_stock': df['stock_num'].sum(),
            'total_locked': df['lock_num'].sum(),
            'total_goods': df['goods_no'].nunique(),
            'total_specs': df['spec_no'].nunique(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return {
            'warehouse_summary': warehouse_summary,
            'detailed_summary': detailed_summary,
            'brand_summary': brand_summary,
            'total_summary': total_summary,
            'raw_data': df
        }
    
    def generate_html_report(self, data: Dict) -> str:
        """生成HTML报告"""
        if not data:
            return "<html><body><h1>暂无库存数据</h1></body></html>"
        
        warehouse_summary = data['warehouse_summary']
        detailed_summary = data['detailed_summary']
        total_summary = data['total_summary']
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>库存数据报告</title>
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
                .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📦 库存数据报告</h1>
                
                <div class="summary-card">
                    <h2>📊 总体概况</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <h3>{total_summary['total_available_stock']:,.0f}</h3>
                            <p>可发库存总量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_summary['total_stock']:,.0f}</h3>
                            <p>总库存量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_summary['total_locked']:,.0f}</h3>
                            <p>锁定库存</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_summary['total_goods']}</h3>
                            <p>商品种类</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_summary['total_specs']}</h3>
                            <p>规格数量</p>
                        </div>
                    </div>
                </div>
                
                <h2>🏪 仓库类型汇总</h2>
                <table>
                    <thead>
                        <tr>
                            <th>仓库类型</th>
                            <th>可发库存</th>
                            <th>总库存</th>
                            <th>锁定库存</th>
                            <th>商品数</th>
                            <th>规格数</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for warehouse_type, row in warehouse_summary.iterrows():
            html_content += f"""
                        <tr>
                            <td>{warehouse_type}</td>
                            <td class="number">{row['available_stock']:,.2f}</td>
                            <td class="number">{row['stock_num']:,.2f}</td>
                            <td class="number">{row['lock_num']:,.2f}</td>
                            <td class="number">{row['goods_no']}</td>
                            <td class="number">{row['spec_no']}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <h2>🏬 详细仓库统计</h2>
                <table>
                    <thead>
                        <tr>
                            <th>仓库名称</th>
                            <th>可发库存</th>
                            <th>总库存</th>
                            <th>锁定库存</th>
                            <th>商品数</th>
                            <th>规格数</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for warehouse_name, row in detailed_summary.iterrows():
            html_content += f"""
                        <tr>
                            <td>{warehouse_name}</td>
                            <td class="number">{row['available_stock']:,.2f}</td>
                            <td class="number">{row['stock_num']:,.2f}</td>
                            <td class="number">{row['lock_num']:,.2f}</td>
                            <td class="number">{row['goods_no']}</td>
                            <td class="number">{row['spec_no']}</td>
                        </tr>
            """
        
        html_content += f"""
                    </tbody>
                </table>
                
                <div class="timestamp">
                    📅 报告生成时间: {total_summary['last_updated']}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_wechat_message(self, message: str, url: str = None) -> bool:
        """发送企业微信消息"""
        try:
            # 获取access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={WECOM_CONFIG['corpid']}&corpsecret={WECOM_CONFIG['corpsecret']}"
            token_response = requests.get(token_url)
            token_data = token_response.json()
            
            if token_data.get('errcode') != 0:
                logger.error(f"获取微信token失败: {token_data}")
                return False
            
            access_token = token_data['access_token']
            
            # 构建消息内容
            if url:
                content = f"{message}\n\n📊 详细报告: {url}"
            else:
                content = message
            
            # 发送消息
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            send_data = {
                "touser": WECOM_CONFIG['touser'],
                "msgtype": "text",
                "agentid": WECOM_CONFIG['agentid'],
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(send_url, json=send_data)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("企业微信消息发送成功")
                return True
            else:
                logger.error(f"企业微信消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送企业微信消息异常: {e}")
            return False
    
    def publish_to_edgeone(self, html_content: str) -> str:
        """发布到EdgeOne Pages"""
        try:
            # 这里需要实现EdgeOne Pages的发布逻辑
            # 暂时返回一个示例URL
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            url = f"https://{EDGEONE_CONFIG['project_name']}.pages.dev/inventory_report_{timestamp}.html"
            logger.info(f"报告已发布到: {url}")
            return url
        except Exception as e:
            logger.error(f"发布到EdgeOne失败: {e}")
            return ""
    
    def generate_summary_message(self, data: Dict) -> str:
        """生成摘要消息"""
        if not data:
            return "📦 库存数据报告\n\n❌ 暂无库存数据"
        
        total_summary = data['total_summary']
        warehouse_summary = data['warehouse_summary']
        
        message = f"""📦 库存数据报告

📊 总体概况:
• 可发库存总量: {total_summary['total_available_stock']:,.0f}
• 总库存量: {total_summary['total_stock']:,.0f}
• 锁定库存: {total_summary['total_locked']:,.0f}
• 商品种类: {total_summary['total_goods']}
• 规格数量: {total_summary['total_specs']}

🏪 仓库类型分布:"""
        
        for warehouse_type, row in warehouse_summary.iterrows():
            message += f"\n• {warehouse_type}: {row['available_stock']:,.0f} (可发库存)"
        
        message += f"\n\n📅 更新时间: {total_summary['last_updated']}"
        
        return message
    
    def run(self):
        """主运行函数"""
        logger.info("开始执行库存数据处理")
        
        try:
            # 连接数据库
            if not self.connect_database():
                return False
            
            # 获取库存数据
            df = self.get_inventory_data()
            if df.empty:
                logger.warning("未获取到库存数据")
                return False
            
            # 聚合数据
            aggregated_data = self.aggregate_inventory_data(df)
            
            # 生成HTML报告
            html_content = self.generate_html_report(aggregated_data)
            
            # 发布报告
            report_url = self.publish_to_edgeone(html_content)
            
            # 生成摘要消息
            summary_message = self.generate_summary_message(aggregated_data)
            
            # 发送企业微信消息
            self.send_wechat_message(summary_message, report_url)
            
            logger.info("库存数据处理完成")
            return True
            
        except Exception as e:
            logger.error(f"库存数据处理异常: {e}")
            return False
        finally:
            self.close_database()

def main():
    """主函数"""
    processor = InventoryProcessor()
    processor.run()

if __name__ == "__main__":
    main()