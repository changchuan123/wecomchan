#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报URL一键修复脚本
解决周报URL打不开的问题
"""

import os
import sys
import time
import subprocess
import requests

def check_edgeone_cli():
    """检查EdgeOne CLI是否可用"""
    try:
        result = subprocess.run(["edgeone", "--version"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 已安装")
        return True
    except Exception as e:
        print(f"❌ EdgeOne CLI 不可用: {e}")
        return False

def check_edgeone_login():
    """检查EdgeOne CLI登录状态"""
    try:
        result = subprocess.run(["edgeone", "whoami"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 已登录")
        return True
    except Exception as e:
        print(f"❌ EdgeOne CLI 未登录: {e}")
        return False

def deploy_to_edgeone():
    """部署到EdgeOne Pages"""
    try:
        print("🚀 开始部署到EdgeOne Pages...")
        cmd = ["edgeone", "pages", "deploy", "reports/", "-n", "sales-report-new"]
        print(f"📤 执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        print("✅ 部署成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 部署失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

def test_url_accessibility(url, timeout=10):
    """测试URL可访问性"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception:
        return False

def verify_weekly_url(filename):
    """验证周报URL"""
    print(f"\n🔍 验证周报URL: {filename}")
    
    # 等待CDN同步
    print("⏳ 等待CDN同步...")
    time.sleep(10)
    
    # 测试主URL
    primary_url = f"https://edge.haierht.cn/{filename}"
    print(f"🔗 测试主URL: {primary_url}")
    
    if test_url_accessibility(primary_url):
        print("✅ 主URL可访问")
        return primary_url
    
    # 等待更长时间后再次测试
    print("⏳ 再次等待CDN同步...")
    time.sleep(15)
    
    if test_url_accessibility(primary_url):
        print("✅ 主URL可访问（延迟验证）")
        return primary_url
    
    print("❌ URL验证失败")
    return None

def main():
    """主函数"""
    print("🔧 周报URL一键修复脚本")
    print("=" * 50)
    
    # 1. 检查环境
    print("\n📋 检查环境...")
    if not check_edgeone_cli():
        print("❌ 请先安装EdgeOne CLI: npm install -g edgeone")
        return
    
    if not check_edgeone_login():
        print("❌ 请先登录EdgeOne CLI: edgeone login")
        return
    
    # 2. 检查reports目录
    print("\n📁 检查reports目录...")
    if not os.path.exists("reports"):
        print("❌ reports目录不存在")
        return
    
    # 查找最新的周报文件
    weekly_files = [f for f in os.listdir("reports") if f.startswith("overall_weekly_")]
    if not weekly_files:
        print("❌ 未找到周报文件")
        return
    
    latest_weekly = sorted(weekly_files)[-1]
    print(f"📄 找到最新周报文件: {latest_weekly}")
    
    # 3. 部署文件
    print("\n🚀 部署文件...")
    if not deploy_to_edgeone():
        print("❌ 部署失败")
        return
    
    # 4. 验证URL
    print("\n🔍 验证URL...")
    final_url = verify_weekly_url(latest_weekly)
    
    if final_url:
        print(f"\n🎉 修复成功！")
        print(f"🌐 周报URL: {final_url}")
        print("💡 文件已成功部署并可正常访问")
    else:
        print(f"\n⚠️ 修复部分成功")
        print(f"🔗 请手动验证URL: https://edge.haierht.cn/{latest_weekly}")
        print("💡 CDN同步可能需要更多时间")
    
    print("\n" + "=" * 50)
    print("🔧 修复完成")

if __name__ == "__main__":
    main() 