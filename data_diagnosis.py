#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据诊断脚本 - 检查数据库源数据情况
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 数据库配置
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'wecomchan'
DB_CHARSET = 'utf8mb4'

def check_database_connection():
    """检查数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_table_structure(conn, table_name):
    """检查表结构"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        print(f"📊 {table_name}表结构:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        return [col[0] for col in columns]
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return []

def check_data_range(conn, table_name, date_column):
    """检查数据日期范围"""
    try:
        # 检查最早和最晚的日期
        query_min = f"SELECT MIN({date_column}) as min_date FROM {table_name}"
        query_max = f"SELECT MAX({date_column}) as max_date FROM {table_name}"
        
        df_min = pd.read_sql(query_min, conn)
        df_max = pd.read_sql(query_max, conn)
        
        min_date = df_min.iloc[0]['min_date']
        max_date = df_max.iloc[0]['max_date']
        
        print(f"📅 {table_name}表数据日期范围:")
        print(f"  最早日期: {min_date}")
        print(f"  最晚日期: {max_date}")
        
        return min_date, max_date
    except Exception as e:
        print(f"❌ 检查数据范围失败: {e}")
        return None, None

def check_daily_data_count(conn, table_name, date_column, start_date, end_date):
    """检查每日数据量"""
    try:
        query = f"""
        SELECT DATE({date_column}) as date, COUNT(*) as count 
        FROM {table_name} 
        WHERE {date_column} >= '{start_date}' AND {date_column} <= '{end_date}'
        GROUP BY DATE({date_column})
        ORDER BY date
        """
        
        df = pd.read_sql(query, conn)
        print(f"📊 {table_name}表每日数据量 ({start_date} 至 {end_date}):")
        if not df.empty:
            for _, row in df.iterrows():
                print(f"  {row['date']}: {row['count']} 条记录")
        else:
            print("  ❌ 该时间段内没有数据")
        
        return df
    except Exception as e:
        print(f"❌ 检查每日数据量失败: {e}")
        return pd.DataFrame()

def check_sample_data(conn, table_name, date_column, limit=5):
    """检查样本数据"""
    try:
        query = f"SELECT * FROM {table_name} ORDER BY {date_column} DESC LIMIT {limit}"
        df = pd.read_sql(query, conn)
        print(f"📋 {table_name}表最新{limit}条数据样本:")
        for _, row in df.iterrows():
            print(f"  {row[date_column]}: {row}")
        return df
    except Exception as e:
        print(f"❌ 检查样本数据失败: {e}")
        return pd.DataFrame()

def main():
    """主诊断函数"""
    print("🔍 开始数据库源数据诊断...")
    
    # 检查数据库连接
    conn = check_database_connection()
    if not conn:
        return
    
    # 检查Daysales表
    print("\n" + "="*50)
    print("📊 检查Daysales表")
    print("="*50)
    
    daysales_columns = check_table_structure(conn, 'Daysales')
    if daysales_columns:
        min_date, max_date = check_data_range(conn, 'Daysales', '交易时间')
        if min_date and max_date:
            # 检查最近30天的数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            check_daily_data_count(conn, 'Daysales', '交易时间', start_date, end_date)
            check_sample_data(conn, 'Daysales', '交易时间')
    
    # 检查HT_fenxiao表
    print("\n" + "="*50)
    print("📊 检查HT_fenxiao表")
    print("="*50)
    
    fenxiao_columns = check_table_structure(conn, 'HT_fenxiao')
    if fenxiao_columns:
        # 尝试不同的日期字段
        date_columns = [col for col in fenxiao_columns if '时间' in col or '日期' in col or '创建' in col]
        if date_columns:
            for date_col in date_columns:
                print(f"\n🔍 检查字段: {date_col}")
                min_date, max_date = check_data_range(conn, 'HT_fenxiao', date_col)
                if min_date and max_date:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    check_daily_data_count(conn, 'HT_fenxiao', date_col, start_date, end_date)
                    check_sample_data(conn, 'HT_fenxiao', date_col)
        else:
            print("❌ 未找到合适的日期字段")
    
    # 检查其他相关表
    print("\n" + "="*50)
    print("📊 检查其他相关表")
    print("="*50)
    
    # 获取所有表名
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 数据库中的所有表: {tables}")
        
        for table in tables:
            if table not in ['Daysales', 'HT_fenxiao']:
                print(f"\n🔍 检查表: {table}")
                columns = check_table_structure(conn, table)
                if columns:
                    # 查找日期字段
                    date_columns = [col for col in columns if '时间' in col or '日期' in col or '创建' in col]
                    if date_columns:
                        for date_col in date_columns:
                            print(f"  📅 检查日期字段: {date_col}")
                            min_date, max_date = check_data_range(conn, table, date_col)
                            if min_date and max_date:
                                end_date = datetime.now().strftime('%Y-%m-%d')
                                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                                check_daily_data_count(conn, table, date_col, start_date, end_date)
    except Exception as e:
        print(f"❌ 检查其他表失败: {e}")
    
    conn.close()
    print("\n✅ 数据诊断完成")

if __name__ == "__main__":
    main() 