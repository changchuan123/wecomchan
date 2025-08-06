#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化数据检查脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入原脚本的配置
try:
    # 尝试导入原脚本的配置
    exec(open('整体月报数据_backup.py').read())
except Exception as e:
    print(f"❌ 导入原脚本失败: {e}")
    sys.exit(1)

def check_data_source():
    """检查数据源"""
    print("🔍 开始检查数据源...")
    
    # 检查数据库连接
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        
        # 检查Daysales表
        print("\n📊 检查Daysales表:")
        cursor = conn.cursor()
        cursor.execute("DESCRIBE Daysales")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"字段: {columns}")
        
        # 检查数据量
        cursor.execute("SELECT COUNT(*) FROM Daysales")
        total_count = cursor.fetchone()[0]
        print(f"总记录数: {total_count}")
        
        # 检查日期范围
        cursor.execute("SELECT MIN(交易时间), MAX(交易时间) FROM Daysales")
        min_date, max_date = cursor.fetchone()
        print(f"日期范围: {min_date} 至 {max_date}")
        
        # 检查最近30天的数据
        from datetime import datetime, timedelta
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
        for date, count in daily_data:
            print(f"  {date}: {count} 条记录")
        
        # 检查HT_fenxiao表
        print("\n📊 检查HT_fenxiao表:")
        cursor.execute("DESCRIBE HT_fenxiao")
        fenxiao_columns = [row[0] for row in cursor.fetchall()]
        print(f"字段: {fenxiao_columns}")
        
        cursor.execute("SELECT COUNT(*) FROM HT_fenxiao")
        fenxiao_count = cursor.fetchone()[0]
        print(f"总记录数: {fenxiao_count}")
        
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
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据源失败: {e}")

if __name__ == "__main__":
    check_data_source() 