#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据获取问题
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import sys
import logging
import time

# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_date_format(date_str):
    """简化的日期格式处理"""
    if pd.isna(date_str) or date_str is None:
        return None
    
    date_str = str(date_str).strip()
    if not date_str or date_str == '':
        return None
    
    try:
        # 尝试直接解析
        parsed_date = pd.to_datetime(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return None

def get_fixed_fenxiao_data(start_date, end_date=None):
    """修复版的分销数据获取函数"""
    max_retries = 3
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = pymysql.connect(
                host=DB_HOST, port=DB_PORT, user=DB_USER,
                password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
                connect_timeout=30, read_timeout=30, write_timeout=30
            )
            logging.info(f"✅ 数据库连接成功 (尝试 {attempt+1}/{max_retries})")
            break
        except Exception as e:
            logging.error(f"❌ 数据库连接失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logging.info(f"⏳ 等待5秒后重试...")
                time.sleep(5)
            else:
                logging.error("❌ 数据库连接失败，已达到最大重试次数")
                return pd.DataFrame()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        
        # 获取HT_fenxiao表结构
        cursor.execute("DESCRIBE HT_fenxiao")
        columns = [row[0] for row in cursor.fetchall()]
        logging.info(f"📊 HT_fenxiao表字段: {columns}")
        
        # 查找字段名
        amount_fields = [col for col in columns if '金额' in col or '实付' in col or '支付' in col]
        shop_fields = [col for col in columns if '店铺' in col or '商店' in col]
        status_fields = [col for col in columns if '状态' in col or '订单' in col]
        time_fields = [col for col in columns if '时间' in col or '日期' in col or '创建' in col]
        product_fields = [col for col in columns if '产品' in col or '名称' in col]
        qty_fields = [col for col in columns if '数量' in col or '采购数量' in col]
        
        # 选择字段名
        amount_col = '用户实际支付总额' if '用户实际支付总额' in columns else (amount_fields[0] if amount_fields else '用户实际支付金额')
        shop_col = '分销商店铺名称' if '分销商店铺名称' in columns else (shop_fields[0] if shop_fields else '分销商店铺名称')
        status_col = '订单状态' if '订单状态' in columns else (status_fields[0] if status_fields else '订单状态')
        
        # 修复：使用订单创建时间，但增加备用选项
        if '订单创建时间' in columns:
            time_col = '订单创建时间'
            logging.info("📊 使用订单创建时间作为时间字段")
        else:
            time_col = time_fields[0] if time_fields else '订单创建时间'
            logging.info(f"📊 使用默认时间字段: {time_col}")
            
        product_col = '产品名称' if '产品名称' in columns else (product_fields[0] if product_fields else '产品名称')
        qty_col = '采购数量' if '采购数量' in columns else (qty_fields[0] if qty_fields else '采购数量')
        
        # 修复：简化时间条件，避免复杂的OR条件
        if end_date:
            time_condition = f"{time_col} >= '{start_date}' AND {time_col} <= '{end_date} 23:59:59'"
        else:
            if '至' in start_date:
                start_dt, end_dt = start_date.split('至')
                time_condition = f"{time_col} >= '{start_dt}' AND {time_col} <= '{end_dt} 23:59:59'"
            else:
                time_condition = f"DATE({time_col}) = '{start_date}'"
        
        # 修复：简化SQL查询，减少过滤条件
        sql = f"""
        SELECT 
            {shop_col} as 店铺,
            {status_col} as 订单状态,
            {amount_col} as 分摊后总价,
            {time_col} as 交易时间,
            {product_col} as 规格名称,
            {product_col} as 货品名称,
            {qty_col} as 实发数量,
            '分销' as 数据来源
        FROM HT_fenxiao 
        WHERE {time_condition}
        """
        
        logging.info(f"📊 执行修复版分销数据查询: {sql}")
        
        df_fenxiao = pd.read_sql(sql, conn)
        
        if not df_fenxiao.empty:
            logging.info(f"📊 分销数据获取成功，共{len(df_fenxiao)}行")
            
            # 显示原始日期格式样本
            sample_dates = df_fenxiao['交易时间'].head(5).tolist()
            logging.info(f"📊 原始日期格式样本: {sample_dates}")
            
            # 简化的日期格式处理
            df_fenxiao['交易时间'] = df_fenxiao['交易时间'].apply(normalize_date_format)
            
            # 统计日期处理结果
            valid_dates = df_fenxiao['交易时间'].notna().sum()
            total_dates = len(df_fenxiao)
            logging.info(f"📊 日期格式处理结果: 有效日期 {valid_dates}/{total_dates}")
            
            # 移除无效日期的行
            df_fenxiao = df_fenxiao.dropna(subset=['交易时间'])
            logging.info(f"📊 移除无效日期后分销数据行数: {len(df_fenxiao)}")
            
            if not df_fenxiao.empty:
                # 显示处理后的日期范围
                df_fenxiao['交易时间'] = pd.to_datetime(df_fenxiao['交易时间'])
                min_date = df_fenxiao['交易时间'].min()
                max_date = df_fenxiao['交易时间'].max()
                logging.info(f"📊 分销数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
                
                # 显示订单状态分布
                status_counts = df_fenxiao['订单状态'].value_counts()
                logging.info(f"📊 订单状态分布:")
                for status, count in status_counts.items():
                    logging.info(f"   {status}: {count}条")
            
            return df_fenxiao
        else:
            logging.warning("⚠️ 分销数据查询结果为空")
            return pd.DataFrame()
            
    except Exception as e:
        logging.error(f"❌ 获取分销数据失败: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def test_fixed_data_retrieval():
    """测试修复后的数据获取"""
    print("🔍 开始测试修复后的数据获取...")
    
    # 模拟原脚本的日期计算
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    target_month_start = yesterday.replace(day=1)
    if yesterday.month == 12:
        next_month = yesterday.replace(year=yesterday.year + 1, month=1, day=1)
    else:
        next_month = yesterday.replace(month=yesterday.month + 1, day=1)
    month_end = next_month - timedelta(days=1)
    
    this_month_start_str = target_month_start.strftime('%Y-%m-%d')
    month_end_str = month_end.strftime('%Y-%m-%d')
    
    print(f"📅 测试日期范围: {this_month_start_str} 至 {month_end_str}")
    
    # 测试ERP数据获取
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        
        # 获取ERP数据
        erp_query = f"SELECT * FROM Daysales WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59'"
        print(f"📊 执行ERP数据查询: {erp_query}")
        
        df_erp = pd.read_sql(erp_query, conn)
        print(f"✅ ERP数据获取成功，共{len(df_erp)}行")
        
        # 获取分销数据
        print("📊 正在获取分销数据...")
        df_fenxiao = get_fixed_fenxiao_data(this_month_start_str, month_end_str)
        
        if not df_fenxiao.empty:
            print(f"✅ 分销数据获取成功，共{len(df_fenxiao)}行")
            
            # 合并数据
            print("🔄 合并ERP数据和分销数据...")
            df_combined = pd.concat([df_erp, df_fenxiao], ignore_index=True)
            print(f"📊 合并后总数据量: {len(df_combined)}行")
            
            # 显示数据分布
            print("\n📊 数据来源分布:")
            if '数据来源' in df_combined.columns:
                source_counts = df_combined['数据来源'].value_counts()
                for source, count in source_counts.items():
                    print(f"  {source}: {count}条")
            
            # 显示日期分布
            print("\n📊 日期分布:")
            df_combined['交易时间'] = pd.to_datetime(df_combined['交易时间'])
            daily_counts = df_combined.groupby(df_combined['交易时间'].dt.date).size()
            for date, count in daily_counts.items():
                print(f"  {date}: {count}条")
                
        else:
            print("⚠️ 分销数据获取失败，仅使用ERP数据")
            df_combined = df_erp
        
        conn.close()
        print("\n✅ 修复后的数据获取测试完成")
        
    except Exception as e:
        print(f"❌ 测试修复后的数据获取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_data_retrieval() 