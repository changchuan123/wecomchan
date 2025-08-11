#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL检查和修复脚本
用于检查EdgeOne Pages部署的文件是否可以正常访问，如果不可访问则重新部署
"""

import os
import time
import requests
import subprocess
import sys

# EdgeOne Pages配置
EDGEONE_PROJECT = "sales-report-new"
EDGEONE_TOKEN = "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="

def check_url_accessibility(url, max_retries=3):
    """检查URL是否可访问"""
    print(f"🔍 检查URL: {url}")
    
    for attempt in range(max_retries):
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ URL可正常访问: {url}")
                return True
            else:
                print(f"⚠️ URL不可访问 (状态码: {response.status_code}): {url}")
        except Exception as e:
            print(f"❌ URL检查失败 (尝试 {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"⏳ 等待5秒后重试...")
            time.sleep(5)
    
    return False

def deploy_to_edgeone():
    """部署到EdgeOne Pages"""
    try:
        print("🚀 开始重新部署到EdgeOne Pages...")
        
        # 获取当前脚本目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, "reports")
        
        if not os.path.exists(reports_dir):
            print(f"❌ reports目录不存在: {reports_dir}")
            return False
        
        # 执行部署命令
        result = subprocess.run([
            "edgeone", "pages", "deploy", reports_dir,
            "-n", EDGEONE_PROJECT, "-t", EDGEONE_TOKEN
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ EdgeOne Pages 重新部署成功！")
            return True
        else:
            print("❌ EdgeOne Pages 部署失败：", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python check_and_fix_url.py <文件名>")
        print("例如: python check_and_fix_url.py overall_weekly_2025-07-28_to_2025-08-03.html")
        return
    
    filename = sys.argv[1]
    url = f"https://edge.haierht.cn/{filename}"
    
    print(f"🔍 检查文件: {filename}")
    print(f"🌐 目标URL: {url}")
    
    # 检查URL是否可访问
    if check_url_accessibility(url):
        print("✅ 文件可以正常访问，无需修复")
        return
    
    print("❌ 文件无法访问，开始重新部署...")
    
    # 重新部署
    if deploy_to_edgeone():
        print("⏳ 等待CDN同步...")
        time.sleep(15)
        
        # 再次检查URL
        if check_url_accessibility(url):
            print("✅ 重新部署成功，文件现在可以正常访问")
        else:
            print("⚠️ 重新部署后文件仍无法访问，可能需要更长时间同步")
    else:
        print("❌ 重新部署失败")

if __name__ == "__main__":
    main() 