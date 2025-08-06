#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断服务器端企业微信配置问题
"""

import requests
import json

def diagnose_server_wecom():
    """诊断服务器端企业微信配置问题"""
    
    print("🔍 诊断服务器端企业微信配置问题...")
    print("="*60)
    
    # 1. 检查服务器状态
    print("1️⃣ 检查服务器状态...")
    try:
        response = requests.get("http://212.64.57.87:5001/status", timeout=10)
        status = response.json()
        print(f"✅ 服务器状态: {status.get('status')}")
        print(f"📋 配置信息: {json.dumps(status.get('config', {}), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 无法获取服务器状态: {e}")
        return
    
    # 2. 测试企业微信配置
    print("\n2️⃣ 测试企业微信配置...")
    test_msg = "🔧 企业微信配置诊断测试\n\n这是一条诊断消息，用于检查企业微信配置问题。"
    
    data = {
        "msg": test_msg,
        "token": "wecomchan_token",
        "to_user": "weicungang"
    }
    
    try:
        response = requests.post("http://212.64.57.87:5001/send", json=data, timeout=30)
        result = response.json()
        
        print(f"📤 服务器响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('errcode') == 0:
            print("✅ 企业微信配置正常！")
        else:
            print(f"❌ 企业微信配置有问题: {result.get('errmsg')}")
            
            # 分析错误信息
            errmsg = result.get('errmsg', '')
            if 'invalid corpid' in errmsg.lower():
                print("\n🔍 问题分析: invalid corpid 错误")
                print("💡 可能的原因:")
                print("   1. 服务器端的企业微信公司ID (corpid) 已过期或无效")
                print("   2. 服务器端使用了错误的企业微信应用配置")
                print("   3. 企业微信应用权限设置有问题")
                print("\n🛠️ 解决方案:")
                print("   1. 检查服务器端的企业微信应用配置")
                print("   2. 更新服务器端的企业微信公司ID和Secret")
                print("   3. 确认企业微信应用权限设置")
                print("   4. 联系服务器管理员更新配置")
                
            elif 'access_token' in errmsg.lower():
                print("\n🔍 问题分析: access_token 获取失败")
                print("💡 可能的原因:")
                print("   1. 企业微信应用Secret无效")
                print("   2. 企业微信应用权限不足")
                print("   3. 网络连接问题")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 3. 提供解决方案
    print("\n3️⃣ 解决方案建议...")
    print("📋 由于服务器端企业微信配置有问题，建议:")
    print("   1. 联系服务器管理员 (212.64.57.87) 检查企业微信配置")
    print("   2. 更新服务器端的企业微信应用配置")
    print("   3. 确认企业微信应用的公司ID、Secret和应用ID是否正确")
    print("   4. 检查企业微信应用的权限设置")
    print("\n🔧 临时解决方案:")
    print("   1. 可以暂时禁用企业微信推送功能")
    print("   2. 使用其他通知方式（如邮件、短信等）")
    print("   3. 等待服务器端配置修复后再启用推送")

if __name__ == "__main__":
    print("🚀 开始诊断服务器端企业微信配置问题...\n")
    diagnose_server_wecom()
    print("\n✅ 诊断完成！") 