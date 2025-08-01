#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表列名
"""

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

try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=10
    )
    
    # 检查表结构
    print("📋 检查Daysales表结构...")
    cursor = conn.cursor()
    cursor.execute("DESCRIBE Daysales")
    columns = cursor.fetchall()
    
    print("📊 Daysales表列名:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")
    
    # 检查最近几天的数据
    print("\n📅 检查最近几天的数据量:")
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        cursor.execute(f"SELECT COUNT(*) FROM Daysales WHERE 交易时间 LIKE '{date_str}%'")
        count = cursor.fetchone()[0]
        print(f"  {date_str}: {count} 条记录")
    
    # 获取一条样本数据
    print("\n📝 获取一条样本数据:")
    cursor.execute("SELECT * FROM Daysales LIMIT 1")
    sample = cursor.fetchone()
    if sample:
        cursor.execute("SELECT * FROM Daysales LIMIT 1")
        sample_df = pd.read_sql("SELECT * FROM Daysales LIMIT 1", conn)
        print("样本数据列名:")
        for col in sample_df.columns:
            print(f"  - {col}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 数据库连接或查询失败: {e}") 