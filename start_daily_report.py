#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 整体日报数据分析系统
"""

import subprocess
import sys
import os

def main():
    print("🚀 启动整体日报数据分析系统...")
    
    # 检查虚拟环境
    venv_path = "/Users/weixiaogang/AI/wecomchan/venv/bin/python"
    if os.path.exists(venv_path):
        print(f"✅ 找到虚拟环境: {venv_path}")
        python_cmd = venv_path
    else:
        print("⚠️ 虚拟环境不存在，使用系统Python")
        python_cmd = "python3"
    
    # 检查主脚本
    main_script = "整体日报数据.py"
    if not os.path.exists(main_script):
        print(f"❌ 主脚本不存在: {main_script}")
        return 1
    
    print(f"📁 当前目录: {os.getcwd()}")
    print(f"🐍 Python命令: {python_cmd}")
    print(f"📄 主脚本: {main_script}")
    
    try:
        # 启动主脚本
        print("🚀 正在启动主脚本...")
        result = subprocess.run([python_cmd, main_script], 
                              capture_output=False, 
                              text=True, 
                              encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 脚本执行成功")
            return 0
        else:
            print(f"❌ 脚本执行失败，返回码: {result.returncode}")
            return result.returncode
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 