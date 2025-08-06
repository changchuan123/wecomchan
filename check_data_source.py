#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接检查数据源脚本
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import sys

# 数据库配置 - 从原脚本复制
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

def check_data_source():
    """检查数据源"""
    print("🔍 开始检查数据源...")
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        
        # 检查Daysales表
        print("\n📊 检查Daysales表:")
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'Daysales'")
        if not cursor.fetchall():
            print("❌ Daysales表不存在")
            return
        
        # 检查表结构
        cursor.execute("DESCRIBE Daysales")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"字段: {columns}")
        
        # 检查数据量
        cursor.execute("SELECT COUNT(*) FROM Daysales")
        total_count = cursor.fetchone()[0]
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("❌ Daysales表为空")
            return
        
        # 检查日期范围
        cursor.execute("SELECT MIN(交易时间), MAX(交易时间) FROM Daysales")
        min_date, max_date = cursor.fetchone()
        print(f"日期范围: {min_date} 至 {max_date}")
        
        # 检查最近30天的数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute(f"SELECT COUNT(*) FROM Daysales WHERE 交易时间 >= '{start_date}' AND 交易时间 <= '{end_date}'")
        recent_count = cursor.fetchone()[0]
        print(f"最近30天数据量: {recent_count}")
        
        # 检查每日数据分布
        cursor.execute(f"""
        SELECT DATE(交易时间) as date, COUNT(*) as count 
        FROM Daysales 
        WHERE 交易时间 >= '{start_date}' AND 交易时间 <= '{end_date}'
        GROUP BY DATE(交易时间)
        ORDER BY date
        """)
        
        daily_data = cursor.fetchall()
        print(f"\n📅 最近30天每日数据分布:")
        if daily_data:
            for date, count in daily_data:
                print(f"  {date}: {count} 条记录")
        else:
            print("  ❌ 最近30天没有数据")
        
        # 检查HT_fenxiao表
        print("\n📊 检查HT_fenxiao表:")
        
        cursor.execute("SHOW TABLES LIKE 'HT_fenxiao'")
        if not cursor.fetchall():
            print("❌ HT_fenxiao表不存在")
            return
        
        cursor.execute("DESCRIBE HT_fenxiao")
        fenxiao_columns = [row[0] for row in cursor.fetchall()]
        print(f"字段: {fenxiao_columns}")
        
        cursor.execute("SELECT COUNT(*) FROM HT_fenxiao")
        fenxiao_count = cursor.fetchone()[0]
        print(f"总记录数: {fenxiao_count}")
        
        if fenxiao_count > 0:
            # 查找日期字段
            date_columns = [col for col in fenxiao_columns if '时间' in col or '日期' in col or '创建' in col]
            if date_columns:
                for date_col in date_columns:
                    print(f"\n🔍 检查日期字段: {date_col}")
                    cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM HT_fenxiao")
                    min_date, max_date = cursor.fetchone()
                    print(f"日期范围: {min_date} 至 {max_date}")
                    
                    cursor.execute(f"SELECT COUNT(*) FROM HT_fenxiao WHERE {date_col} >= '{start_date}' AND {date_col} <= '{end_date}'")
                    recent_count = cursor.fetchone()[0]
                    print(f"最近30天数据量: {recent_count}")
            else:
                print("❌ 未找到合适的日期字段")
        
        conn.close()
        print("\n✅ 数据源检查完成")
        
    except Exception as e:
        print(f"❌ 检查数据源失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data_source() 