#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存数据处理脚本 - 修复版
功能：从wdt和Date数据库获取库存数据，按仓库类型聚合，生成报告
"""

import pymysql
import pandas as pd
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('库存数据处理修复版.log', encoding='utf-8'),
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
        
        # 获取常规仓和顺丰仓的数据
        warehouses = WAREHOUSE_CONFIG['regular_warehouses'] + WAREHOUSE_CONFIG['sf_warehouses']
        
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
        """.format(','.join(["'{}'".format(w) for w in warehouses]))
        
        try:
            df = pd.read_sql(query, self.wdt_connection)
            logger.info(f"获取wdt库存数据成功，共 {len(df)} 条记录")
            return df
        except Exception as e:
            logger.error(f"获取wdt库存数据失败: {e}")
            return pd.DataFrame()
    
    def get_date_store_data(self) -> Dict[str, pd.DataFrame]:
        """获取Date数据库下各个store表格数据"""
        if not self.date_connection:
            logger.error("Date数据库未连接")
            return {}
        
        store_tables = ['jinrongstore', 'rrsstore', 'tongstore', 'jdstore', 'matchstore']
        store_data = {}
        
        for table in store_tables:
            try:
                # 特殊处理tongstore表格（标题行在第二行）
                if table == 'tongstore':
                    # 先获取所有数据
                    query = f"SELECT * FROM {table}"
                    df = pd.read_sql(query, self.date_connection)
                    
                    # 如果数据不为空，跳过第一行（无效行）
                    if not df.empty and len(df) > 1:
                        df = df.iloc[1:].reset_index(drop=True)
                        # 使用第二行作为列名
                        if len(df) > 0:
                            df.columns = df.iloc[0]
                            df = df.iloc[1:].reset_index(drop=True)
                        logger.info(f"tongstore表格特殊处理完成，共 {len(df)} 条记录")
                else:
                    query = f"SELECT * FROM {table}"
                    df = pd.read_sql(query, self.date_connection)
                    logger.info(f"获取{table}数据成功，共 {len(df)} 条记录")
                
                store_data[table] = df
                
            except Exception as e:
                logger.error(f"获取{table}数据失败: {e}")
                store_data[table] = pd.DataFrame()
        
        return store_data
    
    def process_inventory_data(self, wdt_df: pd.DataFrame, store_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """处理库存数据，实现匹配逻辑"""
        if wdt_df.empty:
            logger.warning("wdt库存数据为空")
            return pd.DataFrame()
        
        # 添加仓库类型列
        wdt_df['warehouse_type'] = wdt_df['warehouse_name'].apply(
            lambda x: '常规仓' if x in WAREHOUSE_CONFIG['regular_warehouses'] 
            else '顺丰仓' if x in WAREHOUSE_CONFIG['sf_warehouses'] 
            else '其他'
        )
        
        # 初始化结果DataFrame
        result_data = []
        
        # 处理每个商品规格
        for _, row in wdt_df.iterrows():
            goods_no = row['goods_no']
            spec_name = row['spec_name']
            warehouse_type = row['warehouse_type']
            available_stock = row['available_stock']
            
            # 初始化各仓库库存
            warehouse_stocks = {
                '常规仓': 0,
                '顺丰仓': 0,
                '京仓': 0,
                '云仓': 0,
                '统仓': 0,
                '金融仓': 0
            }
            
            # 设置当前仓库的库存
            if warehouse_type in warehouse_stocks:
                warehouse_stocks[warehouse_type] = available_stock
            
            # 匹配其他仓库数据
            if 'jinrongstore' in store_data and not store_data['jinrongstore'].empty:
                # 匹配金融仓数据
                jinrong_match = self.match_store_data(
                    store_data['jinrongstore'], 
                    goods_no, 
                    '型号'  # 根据README，jinrongstore匹配"型号"列
                )
                if jinrong_match is not None:
                    warehouse_stocks['金融仓'] = jinrong_match
            
            if 'rrsstore' in store_data and not store_data['rrsstore'].empty:
                # 匹配云仓数据
                rrs_match = self.match_store_data(
                    store_data['rrsstore'], 
                    goods_no, 
                    '商品编码'  # 根据README，rrsstore匹配"商品编码"列
                )
                if rrs_match is not None:
                    warehouse_stocks['云仓'] = rrs_match
            
            if 'tongstore' in store_data and not store_data['tongstore'].empty:
                # 匹配统仓数据
                tong_match = self.match_store_data(
                    store_data['tongstore'], 
                    goods_no, 
                    '商品名称'  # 根据README，tongstore匹配"商品名称"列
                )
                if tong_match is not None:
                    warehouse_stocks['统仓'] = tong_match
            
            if 'jdstore' in store_data and not store_data['jdstore'].empty:
                # 匹配京仓数据
                jd_match = self.match_store_data(
                    store_data['jdstore'], 
                    goods_no, 
                    '事业部商品编码'  # 根据README，jdstore匹配"事业部商品编码"列
                )
                if jd_match is not None:
                    warehouse_stocks['京仓'] = jd_match
            
            # 计算合计数量
            total_stock = sum(warehouse_stocks.values())
            
            # 添加到结果
            result_data.append({
                '品类': row.get('brand_name', ''),
                '型号': goods_no,
                '库位': warehouse_type,
                '合计数量': total_stock,
                '常规仓': warehouse_stocks['常规仓'],
                '顺丰仓': warehouse_stocks['顺丰仓'],
                '京仓': warehouse_stocks['京仓'],
                '云仓': warehouse_stocks['云仓'],
                '统仓': warehouse_stocks['统仓'],
                '金融仓': warehouse_stocks['金融仓']
            })
        
        result_df = pd.DataFrame(result_data)
        logger.info(f"库存数据处理完成，共 {len(result_df)} 条记录")
        return result_df
    
    def match_store_data(self, store_df: pd.DataFrame, goods_no: str, match_column: str) -> float:
        """匹配store数据"""
        try:
            if match_column not in store_df.columns:
                return None
            
            # 查找匹配的记录
            matches = store_df[store_df[match_column] == goods_no]
            
            if not matches.empty:
                # 尝试获取可用库存数量
                # 根据README，不同store有不同的库存字段
                if '可用库存' in store_df.columns:
                    return matches['可用库存'].iloc[0]
                elif '数量' in store_df.columns:
                    return matches['数量'].iloc[0]
                elif '可用库存数量' in store_df.columns:
                    return matches['可用库存数量'].iloc[0]
                else:
                    # 如果没有明确的库存字段，返回1表示有库存
                    return 1.0
            
            return None
        except Exception as e:
            logger.error(f"匹配store数据失败: {e}")
            return None
    
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
    
    def generate_summary(self, result_df: pd.DataFrame):
        """生成摘要信息"""
        if result_df.empty:
            logger.info("暂无库存数据")
            return
        
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
        
        logger.info("=" * 50)
        logger.info("📦 库存数据报告")
        logger.info("=" * 50)
        logger.info(f"📊 总体概况:")
        logger.info(f"• 总库存量: {total_summary['total_stock']:,.0f}")
        logger.info(f"• 商品种类: {total_summary['total_products']}")
        logger.info(f"• 品类数量: {total_summary['total_categories']}")
        logger.info("")
        logger.info("🏪 仓库分布:")
        
        if total_summary['regular_warehouse'] > 0:
            logger.info(f"• 常规仓: {total_summary['regular_warehouse']:,.0f}")
        if total_summary['sf_warehouse'] > 0:
            logger.info(f"• 顺丰仓: {total_summary['sf_warehouse']:,.0f}")
        if total_summary['jd_warehouse'] > 0:
            logger.info(f"• 京仓: {total_summary['jd_warehouse']:,.0f}")
        if total_summary['cloud_warehouse'] > 0:
            logger.info(f"• 云仓: {total_summary['cloud_warehouse']:,.0f}")
        if total_summary['tong_warehouse'] > 0:
            logger.info(f"• 统仓: {total_summary['tong_warehouse']:,.0f}")
        if total_summary['jinrong_warehouse'] > 0:
            logger.info(f"• 金融仓: {total_summary['jinrong_warehouse']:,.0f}")
        
        logger.info(f"")
        logger.info(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)
    
    def run(self):
        """主运行函数"""
        logger.info("开始执行库存数据处理")
        
        try:
            # 连接数据库
            if not self.connect_databases():
                return False
            
            # 获取wdt库存数据
            wdt_df = self.get_wdt_stock_data()
            if wdt_df.empty:
                logger.warning("未获取到wdt库存数据")
                return False
            
            # 获取Date数据库store数据
            store_data = self.get_date_store_data()
            
            # 处理库存数据
            result_df = self.process_inventory_data(wdt_df, store_data)
            
            if result_df.empty:
                logger.warning("处理后的库存数据为空")
                return False
            
            # 保存结果到CSV
            self.save_to_csv(result_df)
            
            # 生成摘要信息
            self.generate_summary(result_df)
            
            logger.info("库存数据处理完成")
            return True
            
        except Exception as e:
            logger.error(f"库存数据处理异常: {e}")
            return False
        finally:
            self.close_databases()

def main():
    """主函数"""
    processor = InventoryProcessor()
    processor.run()

if __name__ == "__main__":
    main() 