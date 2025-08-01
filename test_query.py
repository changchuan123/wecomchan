#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import pandas as pd
from datetime import datetime, timedelta

# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

# 计算日期范围（和主程序一样的逻辑）
today = datetime.now()
days_since_monday = today.weekday()
this_monday = today - timedelta(days=days_since_monday)

if days_since_monday == 0:
    this_monday = this_monday - timedelta(days=7)
    week_end = this_monday + timedelta(days=6)
else:
    month_end = today - timedelta(days=1)
    this_month_start = today.replace(day=1)

this_month_start_str = this_month_start.strftime('%Y-%m-%d')
month_end_str = month_end.strftime('%Y-%m-%d')

print(f"测试日期范围: {this_month_start_str} 至 {month_end_str}")

def test_query():
    """测试导致卡顿的查询"""
    try:
        print("正在连接数据库...")
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("数据库连接成功")
        
        # 测试导致卡顿的查询
        query = f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59'"
        print(f"执行查询: {query}")
        
        start_time = datetime.now()
        df_check = pd.read_sql(query, conn)
        end_time = datetime.now()
        
        count = df_check.iloc[0]['count']
        print(f"查询完成，耗时: {end_time - start_time}")
        print(f"找到记录数: {count}")
        
        conn.close()
        return count > 0, count
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False, 0

if __name__ == "__main__":
    print("开始测试查询...")
    has_data, count = test_query()
    print(f"结果: has_data={has_data}, count={count}")