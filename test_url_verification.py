#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL验证测试脚本
"""

import requests
import time

def test_url_formats():
    """测试不同的URL格式"""
    filename = "overall_daily_2025-08-05_183534.html"
    
    possible_urls = [
        f"https://sales-report.pages.edgeone.com/{filename}",
        f"https://edge.haierht.cn/{filename}",
        f"https://sales-report.pages.edgeone.com/reports/{filename}",
        f"https://edge.haierht.cn/reports/{filename}"
    ]
    
    print("🧪 测试URL格式...")
    print("="*60)
    
    for i, url in enumerate(possible_urls, 1):
        print(f"\n📡 测试URL {i}/{len(possible_urls)}: {url}")
        
        try:
            response = requests.head(url, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 成功！文件可访问")
                return url
            elif response.status_code == 404:
                print(f"   ❌ 404错误 - 文件不存在")
            else:
                print(f"   ⚠️ 其他错误 - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
    
    print("\n" + "="*60)
    print("❌ 所有URL格式都不可用")
    return None

def test_edgeone_pages_status():
    """测试EdgeOne Pages主页面状态"""
    print("\n🔍 测试EdgeOne Pages主页面...")
    
    main_urls = [
        "https://sales-report.pages.edgeone.com/",
        "https://edge.haierht.cn/",
        "https://sales-report.pages.edgeone.com/reports/",
        "https://edge.haierht.cn/reports/"
    ]
    
    for url in main_urls:
        try:
            response = requests.head(url, timeout=10)
            print(f"📡 {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - 连接失败: {e}")

if __name__ == "__main__":
    print("🚀 URL验证测试开始")
    print("="*60)
    
    # 测试主页面状态
    test_edgeone_pages_status()
    
    # 测试具体文件URL
    working_url = test_url_formats()
    
    if working_url:
        print(f"\n✅ 找到可用URL: {working_url}")
    else:
        print(f"\n❌ 未找到可用URL，可能需要等待CDN同步") 