#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地wecomchan服务器
"""

import requests
import json

def test_local_server():
    """测试本地服务器功能"""
    
    print("🔍 测试本地wecomchan服务器...")
    print("="*50)
    
    # 1. 测试健康检查
    print("1️⃣ 测试健康检查...")
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return
    
    # 2. 测试发送消息
    print("\n2️⃣ 测试发送消息...")
    test_data = {
        "sendkey": "set_a_sendkey",
        "msg": "🔧 本地服务器测试消息\n\n这是一条测试消息，用于验证本地服务器功能。\n\n✅ 服务器运行正常！"
    }
    
    try:
        response = requests.post("http://localhost:5001/send", data=test_data, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print("✅ 消息发送成功")
            else:
                print(f"⚠️ 消息发送失败: {result.get('errmsg', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")
    
    # 3. 测试GET方式
    print("\n3️⃣ 测试GET方式发送...")
    try:
        params = {
            "sendkey": "set_a_sendkey",
            "msg": "GET方式测试消息"
        }
        response = requests.get("http://localhost:5001/", params=params, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ GET方式测试异常: {e}")
    
    print("\n" + "="*50)
    print("🎉 测试完成！")

if __name__ == "__main__":
    test_local_server() 