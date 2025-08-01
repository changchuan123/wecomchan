#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
from datetime import datetime, timedelta

print("开始测试datetime模块...")

try:
    print("测试1: 获取当前时间")
    today = datetime.now()
    print(f"当前时间: {today}")
    
    print("测试2: 计算weekday")
    days_since_monday = today.weekday()
    print(f"距离周一天数: {days_since_monday}")
    
    print("测试3: 计算timedelta")
    this_monday = today - timedelta(days=days_since_monday)
    print(f"本周一日期: {this_monday}")
    
    print("✅ datetime模块测试完成")
    
except Exception as e:
    print(f"❌ datetime模块测试失败: {e}")
    import traceback
    traceback.print_exc()

print("脚本执行完成")