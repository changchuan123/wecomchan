#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断原脚本问题
"""

import sys
import os

def check_script_issues():
    """检查原脚本的问题"""
    print("🔍 开始诊断原脚本问题...")
    
    # 读取原脚本内容
    try:
        with open('整体月报数据_backup.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ 成功读取原脚本")
        
        # 检查导入语句
        print("\n📋 检查导入语句:")
        lines = content.split('\n')
        import_lines = [line for line in lines if line.strip().startswith('import') or line.strip().startswith('from')]
        for line in import_lines:
            print(f"  {line.strip()}")
        
        # 检查数据库配置
        print("\n📋 检查数据库配置:")
        db_config_lines = []
        for i, line in enumerate(lines):
            if 'DB_HOST' in line or 'DB_USER' in line or 'DB_PASSWORD' in line or 'DB_NAME' in line:
                db_config_lines.append((i+1, line.strip()))
        
        if db_config_lines:
            for line_num, line in db_config_lines:
                print(f"  第{line_num}行: {line}")
        else:
            print("  ❌ 未找到数据库配置")
        
        # 检查数据库连接代码
        print("\n📋 检查数据库连接代码:")
        connection_lines = []
        for i, line in enumerate(lines):
            if 'pymysql.connect' in line or 'connect(' in line:
                connection_lines.append((i+1, line.strip()))
        
        if connection_lines:
            for line_num, line in connection_lines:
                print(f"  第{line_num}行: {line}")
        else:
            print("  ❌ 未找到数据库连接代码")
        
        # 检查数据查询代码
        print("\n📋 检查数据查询代码:")
        query_lines = []
        for i, line in enumerate(lines):
            if 'SELECT' in line and 'FROM' in line:
                query_lines.append((i+1, line.strip()))
        
        if query_lines:
            for line_num, line in query_lines[:5]:  # 只显示前5个查询
                print(f"  第{line_num}行: {line}")
        else:
            print("  ❌ 未找到数据查询代码")
        
        # 检查错误处理
        print("\n📋 检查错误处理:")
        error_lines = []
        for i, line in enumerate(lines):
            if 'except' in line or 'try:' in line or 'error' in line.lower():
                error_lines.append((i+1, line.strip()))
        
        if error_lines:
            for line_num, line in error_lines[:10]:  # 只显示前10个
                print(f"  第{line_num}行: {line}")
        else:
            print("  ❌ 未找到错误处理代码")
        
    except Exception as e:
        print(f"❌ 读取脚本失败: {e}")

def check_data_availability():
    """检查数据可用性"""
    print("\n🔍 检查数据可用性...")
    
    # 模拟原脚本的数据检查逻辑
    try:
        # 这里需要实际的数据库连接
        print("📊 需要实际的数据库连接来检查数据")
        print("📊 请确保数据库服务正在运行")
        print("📊 请检查数据库配置是否正确")
        
    except Exception as e:
        print(f"❌ 数据可用性检查失败: {e}")

if __name__ == "__main__":
    check_script_issues()
    check_data_availability() 