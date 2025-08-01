#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器状态测试脚本
测试本地和远程的企业微信服务器(5001端口)和Web部署服务器(5002端口)
"""

import requests
import json
from datetime import datetime

def test_server(name, base_url, server_type="wecom"):
    """
    测试服务器状态
    server_type: 'wecom' 或 'web_deploy'
    """
    print(f"\n=== 测试 {name} ({base_url}) ===")
    
    # 1. 健康检查
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print(f"✅ 健康检查通过: {health_response.status_code}")
            try:
                health_data = health_response.json()
                print(f"   服务状态: {health_data.get('status', 'unknown')}")
            except:
                print(f"   响应: {health_response.text[:100]}")
        else:
            print(f"❌ 健康检查失败: {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 2. 功能测试
    try:
        if server_type == "wecom":
            # 测试企业微信消息发送接口
            test_data = {
                "sendkey": "test_key",
                "msg": f"测试消息 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            response = requests.post(f"{base_url}/", data=test_data, timeout=5)
        else:
            # 测试Web部署服务器的HTML部署接口
            test_data = {
                "html_content": "<html><body><h1>测试报告</h1><p>测试时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "</p></body></html>",
                "filename": "test_report.html"
            }
            response = requests.post(f"{base_url}/deploy_html", json=test_data, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ 功能测试通过: {response.status_code}")
            try:
                result_data = response.json()
                if server_type == "wecom":
                    print(f"   消息发送结果: {result_data}")
                else:
                    print(f"   HTML部署结果: {result_data.get('message', 'success')}")
            except:
                print(f"   响应: {response.text[:100]}")
        else:
            print(f"❌ 功能测试失败: {response.status_code} - {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 功能测试连接失败: {e}")
        return False
    
    return True

def main():
    print("🚀 开始测试所有服务器状态...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    servers = [
        ("本地企业微信服务器", "http://127.0.0.1:5001", "wecom"),
        ("远程企业微信服务器", "http://212.64.57.87:5001", "wecom"),
        ("本地Web部署服务器", "http://127.0.0.1:5002", "web_deploy"),
        ("远程Web部署服务器", "http://212.64.57.87:5002", "web_deploy")
    ]
    
    results = []
    for name, url, server_type in servers:
        success = test_server(name, url, server_type)
        results.append((name, success))
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    for name, success in results:
        status = "✅ 正常" if success else "❌ 异常"
        print(f"   {name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n总计: {success_count}/{len(results)} 个服务器正常运行")

if __name__ == "__main__":
    main()