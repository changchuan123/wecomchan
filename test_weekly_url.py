#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报URL测试脚本
用于验证周报脚本的URL处理功能
"""

import os
import sys
import time
import requests

def test_url_accessibility(url, timeout=10):
    """测试URL可访问性"""
    try:
        print(f"🔍 测试URL: {url}")
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        print(f"✅ 状态码: {response.status_code}")
        print(f"📋 响应头:")
        for key, value in response.headers.items():
            if key.lower() in ['cache-control', 'content-type', 'content-length', 'last-modified']:
                print(f"   {key}: {value}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 访问失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 周报URL测试开始...")
    
    # 测试最新的周报文件
    test_files = [
        "overall_weekly_2025-08-04_to_2025-08-10_20250811_113322_3960.html",
        "overall_daily_2025-08-10_112630.html"  # 对比日报文件
    ]
    
    for filename in test_files:
        print(f"\n{'='*60}")
        print(f"📄 测试文件: {filename}")
        print(f"{'='*60}")
        
        # 测试主URL
        primary_url = f"https://edge.haierht.cn/{filename}"
        print(f"\n🔗 主URL测试:")
        success1 = test_url_accessibility(primary_url)
        
        # 测试备用URL
        backup_url = f"https://edge.haierht.cn/reports/{filename}"
        print(f"\n🔗 备用URL测试:")
        success2 = test_url_accessibility(backup_url)
        
        if success1 or success2:
            print(f"\n✅ 文件可访问: {filename}")
            if success1:
                print(f"   🌐 主URL: {primary_url}")
            if success2:
                print(f"   🌐 备用URL: {backup_url}")
        else:
            print(f"\n❌ 文件不可访问: {filename}")
    
    print(f"\n{'='*60}")
    print("🧪 测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 