#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存数据处理脚本 - 严格按照README.md要求实现
功能：从Date数据库获取库存数据，统一处理并推送企业微信消息
"""

import pymysql
import pandas as pd
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class InventoryProcessor:
    def __init__(self):
        self.db_config = {
            'host': '212.64.57.87',
            'user': 'root',
            'password': 'c973ee9b500cc638',
            'database': 'Date',
            'charset': 'utf8mb4'
        }
        
        # 企业微信配置
        self.wework_config = {
            'webhook_url': os.getenv('WEWORK_WEBHOOK_URL', ''),
            'agent_id': os.getenv('WEWORK_AGENT_ID', ''),
            'secret': os.getenv('WEWORK_SECRET', '')
        }
        
        # 库位映射
        self.warehouse_mapping = {
            'jinrongstore': '金融仓',
            'rrsstore': '云仓',
            'tongstore': '统仓',
            'jdstore': '京仓'
        }
        
        # 库存字段映射
        self.stock_field_mapping = {
            'jinrongstore': '数量',
            'rrsstore': '可用库存数量',
            'tongstore': '总可销',  # 需要特殊处理
            'jdstore': '可用库存'
        }
        
        # 型号字段映射
        self.model_field_mapping = {
            'jinrongstore': '型号',
            'rrsstore': '商品编码',
            'tongstore': '商品编码',
            'jdstore': '事业部商品编码'
        }
        
        # 品类字段映射
        self.category_field_mapping = {
            'jinrongstore': None,  # 从matchstore获取
            'rrsstore': '品类描述',
            'tongstore': '品牌',
            'jdstore': '商家商品三级分类'
        }

    def connect_db(self):
        """连接数据库"""
        return pymysql.connect(**self.db_config)

    def get_matchstore_mapping(self) -> Dict[str, Dict]:
        """获取matchstore的型号到规格名称的映射"""
        conn = self.connect_db()
        try:
            # 查询matchstore中的规格映射
            query = """
            SELECT DISTINCT 规格名称, 型号, 品类描述, 品牌
            FROM matchstore 
            WHERE 规格名称 IS NOT NULL AND 规格名称 != ''
            """
            df = pd.read_sql(query, conn)
            
            mapping = {}
            for _, row in df.iterrows():
                model = str(row['型号']).strip()
                mapping[model] = {
                    '规格名称': row['规格名称'],
                    '品类': row['品类描述'] or row['品牌'] or '未分类',
                    '品牌': row['品牌'] or '未知'
                }
            return mapping
        finally:
            conn.close()

    def get_table_data(self, table_name: str) -> pd.DataFrame:
        """获取单个表的库存数据"""
        conn = self.connect_db()
        try:
            if table_name == 'tongstore':
                # tongstore特殊处理：跳过第一行（标题行），从第二行开始
                query = f"""
                SELECT * FROM (
                    SELECT *, ROW_NUMBER() OVER() as row_num FROM {table_name}
                ) t WHERE row_num > 1
                """
            else:
                query = f"SELECT * FROM {table_name}"
            
            df = pd.read_sql(query, conn)
            
            # 清理数据
            df = df.dropna(subset=[self.model_field_mapping[table_name]])
            
            return df
        finally:
            conn.close()

    def extract_stock_quantity(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """提取库存数量"""
        stock_field = self.stock_field_mapping[table_name]
        model_field = self.model_field_mapping[table_name]
        category_field = self.category_field_mapping[table_name]
        
        if stock_field not in df.columns:
            print(f"警告: {table_name} 表中找不到库存字段 {stock_field}")
            return pd.DataFrame()
        
        # 提取数据
        result_df = pd.DataFrame()
        result_df['型号'] = df[model_field].astype(str).str.strip()
        result_df['库位'] = self.warehouse_mapping[table_name]
        result_df['原始库存'] = pd.to_numeric(df[stock_field], errors='coerce').fillna(0)
        
        # 提取品类
        if category_field and category_field in df.columns:
            result_df['品类'] = df[category_field].astype(str).str.strip()
        else:
            result_df['品类'] = None
        
        # 过滤掉库存为0的记录
        result_df = result_df[result_df['原始库存'] > 0]
        
        return result_df

    def process_inventory(self) -> Tuple[pd.DataFrame, List[str]]:
        """处理所有库存数据"""
        # 获取规格映射
        match_mapping = self.get_matchstore_mapping()
        
        all_data = []
        missing_models = set()
        
        # 处理每个表
        tables = ['jinrongstore', 'rrsstore', 'tongstore', 'jdstore']
        
        for table in tables:
            try:
                print(f"处理 {table} 表...")
                df = self.get_table_data(table)
                
                if df.empty:
                    print(f"{table} 表无数据")
                    continue
                
                # 提取库存数据
                stock_df = self.extract_stock_quantity(table, df)
                
                if stock_df.empty:
                    print(f"{table} 表无有效库存数据")
                    continue
                
                # 匹配规格名称
                for _, row in stock_df.iterrows():
                    model = row['型号']
                    
                    if model in match_mapping:
                        spec_info = match_mapping[model]
                        all_data.append({
                            '品类': spec_info['品类'],
                            '型号': spec_info['规格名称'],
                            '库位': row['库位'],
                            '数量': int(row['原始库存'])
                        })
                    else:
                        # 记录未匹配的型号
                        missing_models.add(f"{row['库位']}: {model}")
                        
                        # 使用原始型号
                        category = row['品类'] or '未分类'
                        all_data.append({
                            '品类': category,
                            '型号': model,
                            '库位': row['库位'],
                            '数量': int(row['原始库存'])
                        })
                
                print(f"{table} 表处理完成，共 {len(stock_df)} 条记录")
                
            except Exception as e:
                print(f"处理 {table} 表时出错: {e}")
        
        # 创建最终DataFrame
        final_df = pd.DataFrame(all_data)
        
        # 按品类、规格名称、库位排序
        final_df = final_df.sort_values(['品类', '型号', '库位'])
        
        return final_df, list(missing_models)

    def send_wework_message(self, message: str):
        """发送企业微信消息"""
        if not self.wework_config['webhook_url']:
            print("未配置企业微信webhook，跳过消息推送")
            return
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        try:
            response = requests.post(
                self.wework_config['webhook_url'], 
                headers=headers, 
                data=json.dumps(data)
            )
            response.raise_for_status()
            print("企业微信消息发送成功")
        except Exception as e:
            print(f"发送企业微信消息失败: {e}")

    def generate_html_report(self, df: pd.DataFrame) -> str:
        """生成HTML报告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>库存数据报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .summary { background-color: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>库存数据报告</h1>
            <div class="summary">
                <p><strong>生成时间:</strong> {timestamp}</p>
                <p><strong>总记录数:</strong> {total_records}</p>
            </div>
            {table_html}
        </body>
        </html>
        """
        
        table_html = df.to_html(index=False, classes='table')
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_records=len(df),
            table_html=table_html
        )
        
        return html_content

    def run(self):
        """运行库存处理流程"""
        print("开始处理库存数据...")
        
        try:
            # 处理库存数据
            final_df, missing_models = self.process_inventory()
            
            if final_df.empty:
                print("未获取到任何库存数据")
                return
            
            # 保存结果到文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'inventory_report_{timestamp}.csv'
            final_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"库存报告已保存: {csv_filename}")
            
            # 生成HTML报告
            html_content = self.generate_html_report(final_df)
            html_filename = f'inventory_report_{timestamp}.html'
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML报告已保存: {html_filename}")
            
            # 生成消息内容
            message_parts = []
            message_parts.append("📊 库存数据更新")
            message_parts.append(f"总记录数: {len(final_df)}")
            message_parts.append("")
            
            # 按库位统计
            warehouse_stats = final_df.groupby('库位')['数量'].sum().to_dict()
            for warehouse, total in warehouse_stats.items():
                message_parts.append(f"{warehouse}: {total}")
            
            message_parts.append("")
            message_parts.append("📋 库存明细:")
            
            # 添加前20条记录
            for _, row in final_df.head(20).iterrows():
                message_parts.append(f"{row['品类']} | {row['型号']} | {row['库位']} | {row['数量']}")
            
            if len(final_df) > 20:
                message_parts.append(f"... 还有 {len(final_df) - 20} 条记录")
            
            # 处理缺失型号警告
            if missing_models:
                message_parts.append("")
                message_parts.append("⚠️ 需要维护的型号:")
                for model in missing_models[:10]:  # 只显示前10个
                    message_parts.append(f"  {model}")
                if len(missing_models) > 10:
                    message_parts.append(f"  ... 还有 {len(missing_models) - 10} 个")
            
            full_message = "\n".join(message_parts)
            
            # 发送企业微信消息
            self.send_wework_message(full_message)
            
            # 单独发送缺失型号警告
            if missing_models:
                warning_message = f"⚠️ 库存维护提醒\n以下型号在库存中存在但在matchstore中未匹配到:\n"
                warning_message += "\n".join(missing_models)
                self.send_wework_message(warning_message)
            
            print("库存处理完成")
            
        except Exception as e:
            error_message = f"处理库存数据时出错: {e}"
            print(error_message)
            self.send_wework_message(f"❌ 库存处理失败\n{error_message}")

if __name__ == "__main__":
    processor = InventoryProcessor()
    processor.run()