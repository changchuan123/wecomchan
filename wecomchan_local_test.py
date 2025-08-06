#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地企业微信测试服务器
使用正确的企业微信配置进行测试
"""

import json
import requests
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 使用正确的企业微信配置
SENDKEY = 'set_a_sendkey'
WECOM_CID = 'ww5396d87e63595849'
WECOM_SECRET = 'HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II'
WECOM_AID = '1000011'
WECOM_TOUID = '@all'

def send_to_wecom(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    """发送文本消息到企业微信"""
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    
    try:
        print(f"🔗 正在获取access_token...")
        response = requests.get(get_token_url)
        token_data = response.json()
        
        if token_data.get('errcode') != 0:
            return {"errcode": -1, "errmsg": f"获取access_token失败: {token_data}"}
        
        access_token = token_data.get('access_token')
        print(f"✅ access_token获取成功")
        
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "text",
            "text": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        
        print(f"📤 正在发送消息...")
        response = requests.post(send_msg_url, data=json.dumps(data))
        result = response.json()
        print(f"📤 发送结果: {result}")
        return result
        
    except Exception as e:
        return {"errcode": -1, "errmsg": f"发送失败: {str(e)}"}

def handle_wecom_request():
    """处理推送请求的通用函数"""
    if request.method == 'GET':
        sendkey = request.args.get('sendkey')
        msg = request.args.get('msg')
    else:
        sendkey = request.form.get('sendkey')
        msg = request.form.get('msg')
    
    print(f"📥 收到请求: sendkey={sendkey}, msg={msg[:50]}...")
    
    # 验证参数
    if not sendkey or not msg:
        return jsonify({"errcode": -1, "errmsg": "缺少必要参数 sendkey 或 msg"}), 400
    
    if sendkey != SENDKEY:
        return jsonify({"errcode": -1, "errmsg": "sendkey 验证失败"}), 401
    
    # 发送消息
    result = send_to_wecom(msg, WECOM_CID, WECOM_AID, WECOM_SECRET, WECOM_TOUID)
    return jsonify(result)

@app.route('/', methods=['GET', 'POST'])
def wecomchan():
    """处理推送请求 - 根路径"""
    return handle_wecom_request()

@app.route('/send', methods=['GET', 'POST'])
def wecomchan_send():
    """处理推送请求 - /send路径"""
    return handle_wecom_request()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "本地企业微信测试服务运行正常"})

if __name__ == '__main__':
    print("🚀 启动本地企业微信测试服务器...")
    print(f"📍 配置信息:")
    print(f"   SENDKEY: {SENDKEY}")
    print(f"   WECOM_CID: {WECOM_CID}")
    print(f"   WECOM_AID: {WECOM_AID}")
    print(f"   WECOM_TOUID: {WECOM_TOUID}")
    print("📝 使用方法:")
    print("   GET:  http://localhost:5002/?sendkey=set_a_sendkey&msg=消息内容")
    print("   POST: http://localhost:5002/ (form-data: sendkey, msg)")
    print("   POST: http://localhost:5002/send (form-data: sendkey, msg)")
    print("🔧 健康检查: http://localhost:5002/health")

    app.run(host='0.0.0.0', port=5002, debug=False) 