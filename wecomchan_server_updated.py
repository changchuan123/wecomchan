#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wecomchan Web服务器 - 更新版
基于Flask的HTTP API服务，用于接收推送请求并发送到企业微信
"""

import json
import requests
import logging
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wecomchan.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 从环境变量获取配置
SENDKEY = os.environ.get('SENDKEY', 'wecomchan_token')  # 更新为正确的token
WECOM_CID = os.environ.get('WECOM_CID', 'ww5396d87e63595849')  # 正确的企业微信公司ID
WECOM_SECRET = os.environ.get('WECOM_SECRET', 'HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II')  # 正确的企业微信应用Secret
WECOM_AID = os.environ.get('WECOM_AID', '1000011')  # 正确的企业微信应用ID
WECOM_TOUID = os.environ.get('WECOM_TOUID', '@all')

def send_to_wecom(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    """发送文本消息到企业微信"""
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    
    try:
        logger.info(f"正在获取access_token...")
        response = requests.get(get_token_url, timeout=10)
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            error_msg = f"获取access_token失败: {token_data}"
            logger.error(error_msg)
            return {"errcode": -1, "errmsg": error_msg}
        
        logger.info("access_token获取成功，正在发送消息...")
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
        
        response = requests.post(send_msg_url, data=json.dumps(data), timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("消息发送成功")
        else:
            logger.error(f"消息发送失败: {result}")
            
        return result
        
    except requests.exceptions.Timeout:
        error_msg = "请求超时"
        logger.error(error_msg)
        return {"errcode": -1, "errmsg": error_msg}
    except Exception as e:
        error_msg = f"发送失败: {str(e)}"
        logger.error(error_msg)
        return {"errcode": -1, "errmsg": error_msg}

def handle_wecom_request():
    """处理推送请求的通用函数"""
    try:
        if request.method == 'GET':
            sendkey = request.args.get('sendkey')
            msg = request.args.get('msg')
            to_user = request.args.get('to_user', '@all')
        else:
            # 支持多种数据格式
            if request.is_json:
                # JSON格式
                json_data = request.get_json()
                sendkey = json_data.get('token') or json_data.get('sendkey')  # 兼容token和sendkey字段
                msg = json_data.get('msg')
                to_user = json_data.get('to_user', '@all')
            else:
                # Form-data格式
                sendkey = request.form.get('token') or request.form.get('sendkey')  # 兼容token和sendkey字段
                msg = request.form.get('msg')
                to_user = request.form.get('to_user', '@all')
        
        # 记录请求信息
        logger.info(f"收到请求 - 方法: {request.method}, IP: {request.remote_addr}")
        
        # 验证参数
        if not sendkey or not msg:
            logger.warning("缺少必要参数 sendkey/token 或 msg")
            return jsonify({"errcode": -1, "errmsg": "缺少必要参数 sendkey 或 msg"}), 400
        
        if sendkey != SENDKEY:
            logger.warning(f"sendkey验证失败: {sendkey}")
            return jsonify({"errcode": -1, "errmsg": "sendkey 验证失败"}), 401
        
        # 发送消息
        logger.info(f"准备发送消息: {msg[:50]}...")
        result = send_to_wecom(msg, WECOM_CID, WECOM_AID, WECOM_SECRET, to_user)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return jsonify({"errcode": -1, "errmsg": f"服务器内部错误: {str(e)}"}), 500

@app.route('/', methods=['GET', 'POST'])
def wecomchan():
    """处理推送请求 - 根路径"""
    return handle_wecom_request()

@app.route('/send', methods=['GET', 'POST'])
def wecomchan_send():
    """处理推送请求 - /send路径（兼容现有脚本）"""
    return handle_wecom_request()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok", 
        "message": "Wecomchan服务运行正常",
        "timestamp": datetime.now().isoformat(),
        "version": "updated"
    })

@app.route('/status', methods=['GET'])
def status():
    """状态检查接口"""
    return jsonify({
        "service": "wecomchan_server_updated",
        "status": "running",
        "port": 5001,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "sendkey_configured": True,  # 使用默认值，所以是已配置
            "wecom_cid_configured": True,  # 使用默认值，所以是已配置
            "wecom_aid_configured": True   # 使用默认值，所以是已配置
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"errcode": -1, "errmsg": "接口不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"errcode": -1, "errmsg": "服务器内部错误"}), 500

if __name__ == '__main__':
    print("🚀 启动 Wecomchan Web服务器 (更新版)...")
    print(f"📍 配置信息:")
    print(f"   SENDKEY: {SENDKEY}")
    print(f"   WECOM_CID: {WECOM_CID}")
    print(f"   WECOM_AID: {WECOM_AID}")
    print(f"   WECOM_TOUID: {WECOM_TOUID}")
    print("📝 使用方法:")
    print("   GET:  http://localhost:5001/?sendkey=你的key&msg=消息内容")
    print("   POST: http://localhost:5001/ (form-data: sendkey, msg)")
    print("   POST: http://localhost:5001/send (form-data: sendkey, msg)")
    print("🔧 健康检查: http://localhost:5001/health")
    print("📊 状态检查: http://localhost:5001/status")
    print("⏰ 启动时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        sys.exit(1) 