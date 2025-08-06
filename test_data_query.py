#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据查询逻辑
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import sys

# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

def test_data_query():
    """测试数据查询逻辑"""
    print("🔍 开始测试数据查询逻辑...")
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        
        # 模拟原脚本的日期计算逻辑
        today = datetime.now()
        yesterday = today - timedelta(days=1)  # T-1天
        
        print(f"📅 今天: {today}")
        print(f"📅 昨天: {yesterday}")
        
        # 基于T-1天获取所在月份的整月数据
        target_month_start = yesterday.replace(day=1)
        # 获取T-1天所在月份的最后一天
        if yesterday.month == 12:
            next_month = yesterday.replace(year=yesterday.year + 1, month=1, day=1)
        else:
            next_month = yesterday.replace(month=yesterday.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
        
        print(f"📅 月度开始日期: {target_month_start}")
        print(f"📅 月度结束日期: {month_end}")
        
        this_month_start_str = target_month_start.strftime('%Y-%m-%d')
        month_end_str = month_end.strftime('%Y-%m-%d')
        
        print(f"📅 查询开始日期: {this_month_start_str}")
        print(f"📅 查询结束日期: {month_end_str}")
        
        # 执行原脚本的查询
        query = f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59'"
        print(f"📊 执行查询: {query}")
        
        df_check = pd.read_sql(query, conn)
        count = df_check.iloc[0]['count']
        print(f"📈 查询结果: {count} 条记录")
        
        if count > 0:
            print("✅ 数据查询成功，有数据")
            
            # 获取实际数据样本
            sample_query = f"SELECT 交易时间, 店铺, 货品名称, 成交价, 实发数量 FROM Daysales WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59' LIMIT 10"
            print(f"📊 获取样本数据: {sample_query}")
            
            df_sample = pd.read_sql(sample_query, conn)
            print(f"📋 样本数据:")
            for _, row in df_sample.iterrows():
                print(f"  {row['交易时间']}: {row['店铺']} - {row['货品名称']} - ¥{row['成交价']} x {row['实发数量']}")
            
            # 检查每日数据分布
            daily_query = f"""
            SELECT DATE(交易时间) as date, COUNT(*) as count 
            FROM Daysales 
            WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59'
            GROUP BY DATE(交易时间)
            ORDER BY date
            """
            
            df_daily = pd.read_sql(daily_query, conn)
            print(f"\n📅 月度每日数据分布:")
            for _, row in df_daily.iterrows():
                print(f"  {row['date']}: {row['count']} 条记录")
                
        else:
            print("❌ 数据查询失败，没有数据")
            
            # 检查数据库中的实际日期范围
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(交易时间), MAX(交易时间) FROM Daysales")
            min_date, max_date = cursor.fetchone()
            print(f"📅 数据库中实际日期范围: {min_date} 至 {max_date}")
            
            # 检查查询日期范围是否有问题
            print(f"🔍 检查查询日期范围: {this_month_start_str} 至 {month_end_str}")
            
            # 尝试不同的日期范围
            test_dates = [
                (this_month_start_str, month_end_str),
                (f"{this_month_start_str} 00:00:00", f"{month_end_str} 23:59:59"),
                (this_month_start_str, month_end_str),
            ]
            
            for start_date, end_date in test_dates:
                test_query = f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 >= '{start_date}' AND 交易时间 <= '{end_date}'"
                print(f"📊 测试查询: {test_query}")
                
                try:
                    df_test = pd.read_sql(test_query, conn)
                    test_count = df_test.iloc[0]['count']
                    print(f"📈 测试结果: {test_count} 条记录")
                except Exception as e:
                    print(f"❌ 测试查询失败: {e}")
        
        conn.close()
        print("\n✅ 数据查询测试完成")
        
    except Exception as e:
        print(f"❌ 测试数据查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_query() 