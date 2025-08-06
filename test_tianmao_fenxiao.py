#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试天猫分销数据识别功能
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

def test_tianmao_fenxiao_identification():
    """测试天猫分销数据识别功能"""
    print("🔍 开始测试天猫分销数据识别功能...")
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print("✅ 数据库连接成功")
        
        # 获取最近的数据进行测试
        query = """
        SELECT 店铺, 仓库, 订单编号, 交易时间, 订单支付金额, 货品名称
        FROM Daysales 
        WHERE 交易时间 >= '2025-04-19' 
        AND (店铺 LIKE '%天猫%' OR 店铺 LIKE '%淘宝%')
        AND 仓库 = '菜鸟仓自流转'
        LIMIT 10
        """
        
        df = pd.read_sql(query, conn)
        
        print(f"\n📊 查询结果: {len(df)}条记录")
        print("="*80)
        
        if not df.empty:
            print("📋 天猫分销数据样本:")
            for i, row in df.iterrows():
                print(f"  记录{i+1}:")
                print(f"    店铺: {row['店铺']}")
                print(f"    仓库: {row['仓库']}")
                print(f"    订单号: {row['订单编号']}")
                print(f"    交易时间: {row['交易时间']}")
                print(f"    订单金额: {row['订单支付金额']}")
                print(f"    货品名称: {row['货品名称']}")
                print()
        
        # 测试筛选逻辑
        print("🔍 测试筛选逻辑:")
        
        # 1. 天猫渠道筛选
        tianmao_mask = df['店铺'].astype(str).str.contains('天猫|淘宝', na=False)
        print(f"  天猫渠道数据: {tianmao_mask.sum()}行")
        
        # 2. 仓库筛选
        warehouse_mask = df['仓库'].astype(str) == '菜鸟仓自流转'
        print(f"  菜鸟仓自流转数据: {warehouse_mask.sum()}行")
        
        # 3. 组合筛选
        combined_mask = tianmao_mask & warehouse_mask
        print(f"  组合筛选结果: {combined_mask.sum()}行")
        
        # 4. 验证结果
        if combined_mask.sum() > 0:
            print("  ✅ 成功识别到天猫分销数据")
            result_df = df[combined_mask]
            print(f"  📊 识别到的分销数据: {len(result_df)}条")
            
            # 显示识别到的数据
            print("\n📋 识别到的天猫分销数据:")
            for i, row in result_df.iterrows():
                print(f"    {row['店铺']} | {row['仓库']} | {row['订单编号']} | {row['订单支付金额']}")
        else:
            print("  ❌ 未识别到天猫分销数据")
        
        conn.close()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_tianmao_fenxiao_identification() 