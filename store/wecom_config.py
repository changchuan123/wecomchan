#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信配置文件
请在此文件中填写您的企业微信配置信息
"""

# 企业微信配置
# 请从企业微信管理后台获取以下信息
WECOM_CONFIG = {
    'corpid': '',  # 企业ID，在企业微信管理后台 -> 我的企业 -> 企业信息中查看
    'corpsecret': '',  # 应用Secret，在企业微信管理后台 -> 应用管理 -> 自建应用 -> 选择应用 -> 查看Secret
    'agentid': '',  # 应用ID，在企业微信管理后台 -> 应用管理 -> 自建应用 -> 选择应用 -> AgentId
    'touser': 'weicungang'  # 接收消息的用户ID，可以是多个用户，用逗号分隔
}

# 配置说明：
# 1. corpid: 企业微信的企业ID
# 2. corpsecret: 应用的Secret，用于获取access_token
# 3. agentid: 应用的AgentId
# 4. touser: 接收消息的用户ID，可以是多个用户，用逗号分隔

# 获取方式：
# 1. 登录企业微信管理后台：https://work.weixin.qq.com/wework_admin/
# 2. 在"我的企业" -> "企业信息"中查看企业ID
# 3. 在"应用管理" -> "自建应用"中创建或选择应用
# 4. 在应用详情页面查看AgentId和Secret 