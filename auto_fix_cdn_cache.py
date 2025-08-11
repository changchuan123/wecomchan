#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键修复CDN缓存问题脚本
解决"第一时间可以打开，过几分钟就打不开"的问题

使用方法:
1. 简单修复: python3 auto_fix_cdn_cache.py
2. 指定URL: python3 auto_fix_cdn_cache.py https://edge.haierht.cn/your-file.html
"""

import os
import sys
import subprocess
import requests
import time
from datetime import datetime

# EdgeOne配置
EDGEONE_PROJECT = "sales-report-new"
EDGEONE_DOMAIN = "edge.haierht.cn"

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🛠️  EdgeOne Pages CDN缓存一键修复工具")
    print("🎯  解决报告页面404错误和缓存过期问题")
    print("⚡  支持自动检测问题并重新部署")
    print("=" * 60)

def check_url(url):
    """检查URL是否可访问"""
    try:
        print(f"🔍 检查URL: {url}")
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ URL可正常访问: {url}")
            return True
        else:
            print(f"❌ URL不可访问 (状态码: {response.status_code}): {url}")
            return False
    except Exception as e:
        print(f"❌ URL检查失败: {e}")
        return False

def deploy_fix():
    """执行修复部署"""
    try:
        print("🚀 开始修复部署...")
        print("📁 部署reports目录到EdgeOne Pages...")
        
        # 执行部署命令
        result = subprocess.run(
            f"edgeone pages deploy reports/ -n {EDGEONE_PROJECT}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ 部署成功！")
            print("⏳ 等待CDN同步...")
            time.sleep(15)  # 等待CDN同步
            return True
        else:
            print(f"❌ 部署失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

def auto_fix_latest_reports():
    """自动修复最新的报告文件"""
    print("🔍 搜索最新的报告文件...")
    
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        print(f"❌ {reports_dir} 目录不存在")
        return False
    
    # 获取最新的HTML文件
    html_files = []
    for file in os.listdir(reports_dir):
        if file.endswith('.html'):
            html_files.append(file)
    
    if not html_files:
        print("❌ 没有找到HTML文件")
        return False
    
    # 按文件名排序，获取最新的几个文件
    html_files.sort(reverse=True)
    latest_files = html_files[:5]  # 检查最新的5个文件
    
    print(f"📊 找到 {len(latest_files)} 个最新报告文件:")
    for i, file in enumerate(latest_files, 1):
        print(f"   {i}. {file}")
    
    # 检查这些文件是否可访问
    failed_files = []
    for file in latest_files:
        url = f"https://{EDGEONE_DOMAIN}/{file}"
        if not check_url(url):
            failed_files.append(file)
    
    if failed_files:
        print(f"\n🚨 发现 {len(failed_files)} 个不可访问的文件:")
        for file in failed_files:
            print(f"   • {file}")
        
        print("\n🛠️ 开始自动修复...")
        if deploy_fix():
            print("\n🔄 重新验证修复结果...")
            all_fixed = True
            for file in failed_files:
                url = f"https://{EDGEONE_DOMAIN}/{file}"
                if check_url(url):
                    print(f"✅ 修复成功: {file}")
                else:
                    print(f"❌ 修复失败: {file}")
                    all_fixed = False
            
            if all_fixed:
                print("\n🎉 所有文件修复成功！")
                return True
            else:
                print("\n⚠️ 部分文件修复失败，请检查配置")
                return False
        else:
            print("\n❌ 修复部署失败")
            return False
    else:
        print("\n✅ 所有文件都可正常访问，无需修复")
        return True

def fix_specific_url(url):
    """修复特定的URL"""
    print(f"🎯 修复特定URL: {url}")
    
    # 检查URL状态
    if check_url(url):
        print("✅ URL已经可以正常访问")
        return True
    
    print("🛠️ URL不可访问，开始修复...")
    if deploy_fix():
        print("🔄 重新验证...")
        if check_url(url):
            print("🎉 修复成功！")
            return True
        else:
            print("❌ 修复后仍无法访问，请检查文件是否存在")
            return False
    else:
        print("❌ 修复失败")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查EdgeOne CLI
    try:
        result = subprocess.run("edgeone --version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ EdgeOne CLI未安装或未登录")
            print("📝 请先安装并登录EdgeOne CLI:")
            print("   npm install -g @tencent/edgeone-cli")
            print("   edgeone login")
            return
    except:
        print("❌ EdgeOne CLI检查失败")
        return
    
    if len(sys.argv) > 1:
        # 修复特定URL
        url = sys.argv[1]
        fix_specific_url(url)
    else:
        # 自动修复最新报告
        auto_fix_latest_reports()
    
    print("\n" + "=" * 60)
    print("🔗 EdgeOne Pages控制台: https://console.cloud.tencent.com/edgeone/pages")
    print("📊 监控工具: python3 url_monitor.py report")
    print("🚀 手动部署: python3 url_monitor.py deploy")
    print("=" * 60)

if __name__ == "__main__":
    main() 