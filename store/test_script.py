#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("测试脚本开始运行")

try:
    import pymysql
    print("pymysql 导入成功")
except ImportError as e:
    print(f"pymysql 导入失败: {e}")

try:
    import pandas as pd
    print("pandas 导入成功")
except ImportError as e:
    print(f"pandas 导入失败: {e}")

try:
    import numpy as np
    print("numpy 导入成功")
except ImportError as e:
    print(f"numpy 导入失败: {e}")

print("测试脚本运行完成") 