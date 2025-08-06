#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '212.64.57.87'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'c973ee9b500cc638'),
    'database': os.getenv('DB_NAME', 'wdt'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# Date数据库配置
DATE_DB_CONFIG = {
    'host': os.getenv('DB_HOST', '212.64.57.87'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'c973ee9b500cc638'),
    'database': 'Date',
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# 企业微信配置
WECOM_CONFIG = {
    'corpid': os.getenv('WECOM_CID', 'ww5396d87e63595849'),
    'corpsecret': os.getenv('WECOM_SECRET', 'HakXD1he7FuOdgTUQonX562Xy7T1tRdB4-sdZ8F57II'),
    'agentid': os.getenv('WECOM_AID', '1000011'),
    'touser': os.getenv('WECOM_TOUID', '@all')
}

# EdgeOne Pages配置
EDGEONE_CONFIG = {
    'zone_id': os.getenv('EDGEONE_ZONE_ID', ''),
    'token': os.getenv('EDGEONE_TOKEN', ''),
    'project_name': 'inventory-report'
}

# 仓库分类配置
WAREHOUSE_CONFIG = {
    'regular_warehouses': ['常规仓'],
    'sf_warehouses': ['能良顺丰东莞仓', '能良顺丰武汉仓', '能良顺丰武汉金融仓', '能良顺丰金华仓']
}