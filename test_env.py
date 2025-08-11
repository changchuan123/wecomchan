#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Python环境
"""

import sys
import os

def main():
    print("🐍 Python环境测试")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
    
    # 测试基本导入
    try:
        import pandas as pd
        print("✅ pandas导入成功")
    except ImportError as e:
        print(f"❌ pandas导入失败: {e}")
    
    try:
        import requests
        print("✅ requests导入成功")
    except ImportError as e:
        print(f"❌ requests导入失败: {e}")
    
    try:
        import pymysql
        print("✅ pymysql导入成功")
    except ImportError as e:
        print(f"❌ pymysql导入失败: {e}")
    
    # 检查主脚本
    main_script = "整体日报数据.py"
    if os.path.exists(main_script):
        print(f"✅ 主脚本存在: {main_script}")
        print(f"📄 文件大小: {os.path.getsize(main_script)} 字节")
    else:
        print(f"❌ 主脚本不存在: {main_script}")
    
    print("✅ 环境测试完成")

if __name__ == "__main__":
    main() 