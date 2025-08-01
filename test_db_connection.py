#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import sys

# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

print("🔍 测试数据库连接...")
print(f"主机: {DB_HOST}:{DB_PORT}")
print(f"数据库: {DB_NAME}")
print(f"用户: {DB_USER}")

try:
    print("\n⏳ 正在连接数据库...")
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset=DB_CHARSET,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30
    )
    print("✅ 数据库连接成功！")
    
    # 测试简单查询
    print("\n⏳ 测试查询...")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM Daysales LIMIT 1")
    result = cursor.fetchone()
    print(f"✅ 查询成功！Daysales表记录数: {result[0]}")
    
    # 测试日期范围查询
    print("\n⏳ 测试日期范围查询...")
    cursor.execute("SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 >= '2025-07-01' AND 交易时间 < '2025-07-31 23:59:59'")
    result = cursor.fetchone()
    print(f"✅ 日期范围查询成功！7月份记录数: {result[0]}")
    
    cursor.close()
    conn.close()
    print("\n🎉 所有测试通过！")
    
except Exception as e:
    print(f"\n❌ 数据库连接失败: {e}")
    print(f"错误类型: {type(e).__name__}")
    import traceback
    print(f"详细错误信息:\n{traceback.format_exc()}")
    sys.exit(1)