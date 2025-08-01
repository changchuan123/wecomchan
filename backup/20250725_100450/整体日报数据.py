#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================
📊 整体日报数据分析系统
==============================================
功能：整体销售日报数据分析和企业微信推送
数据源：ERP订单明细系统
更新时间：每日自动执行
==============================================
"""

"""
影刀RPA执行脚本 - 进阶销售分析系统（直接执行版本）
直接读取ERP数据，按组织架构自动发送销售报告
"""

import requests
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import sys
import glob
import logging
import time
import numpy as np
import re
import traceback
import platform
import io
import subprocess
import pymysql

def to_number(val):
    if pd.isnull(val):
        return 0
    val = str(val).replace('，', '').replace(',', '').replace(' ', '').replace('\u3000', '')
    try:
        return float(val)
    except:
        return 0

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sales_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 开始计时
total_start_time = datetime.now()

print("🚀 影刀RPA - 进阶销售分析系统（直接执行版本）")
print("==================================================")

# 在主流程最前面初始化趋势图变量，防止未定义报错
trend_chart_html = ''

# ========== 配置区 ==========
erp_folder = r"E:\电商数据\虹图\ERP订单明细"  # ERP数据路径
url = "http://212.64.57.87:5001/send"         # WecomChan服务器地址
token = "wecomchan_token"                      # 认证令牌
to_user = "weicungang"                         # 先只发给weicungang

# 企业微信服务器配置
server_base = "http://212.64.57.87:5001"

# Web发布服务器配置
# WEB_DEPLOY_API = "http://212.64.57.87:5002/deploy_html"  # 已废弃
EDGEONE_PROJECT = "sales-report"  # EdgeOne Pages 项目名
EDGEONE_TOKEN = "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="  # EdgeOne Pages API Token

# 离线模式标志（当服务器不可达时自动启用）
offline_mode = False

# 业务分组配置
business_groups = {
    "空调事业部": {
        "department_id": 69,
        "keywords": ["空调", "KFR", "挂机", "柜机", "变频", "定频", "1匹", "1.5匹", "2匹", "3匹"],
        "users": ["YangNing", "NingWenBo", "LiuYiWei", "yangchao","ZhangYuHe"]  # 空调事业部用户
    },
    "冰冷事业部": {
        "department_id": 70,
        "keywords": ["冰箱", "BCD", "冷藏", "冷冻", "保鲜", "对开门", "三门", "双门", "单门", "变频冰箱"],
        "users": ["HuShengJie", "WeiCunGang", "JiaWenLong", "yangchao", "ZhangWangWang"]  # 冰冷事业部用户
    },
    "洗护事业部": {
        "department_id": 71,
        "keywords": ["洗衣机", "XQG", "波轮", "滚筒", "洗烘一体", "干衣机", "护理", "除菌"],
        "users": ["YingJieBianHua", "WangXiaoLong", "yangchao","zhaohaoran"]  # 洗护事业部用户
    },
    "卡萨帝项目": {
        "department_id": 3,
        "keywords": ["卡萨帝", "Casarte", "高端", "艺术家电", "意式", "法式", "小红书", "RED", "红书"],
        "users": ["lining", "LiXinXin", "MuPing"]  # 卡萨帝项目用户
    },
    "厨卫事业部": {
        "department_id": 78,
        "keywords": ["洗碗机", "消毒柜", "燃气灶", "油烟机", "热水器", "净水器", "厨电"],
        "users": ["WangMengMeng", "NianJianHeng", "YangJingBo", "WuXiang"]  # 厨电洗碗机事业部用户
    }
}

# 渠道分组配置
channel_groups = {
    "抖音项目": {
        "department_id": 28,
        "keywords": ["抖音", "快手", "直播", "短视频", "抖音商城"],
        "users": [ "LuZhiHang","WangTianTian"]  # 抖音项目用户
    },
    "拼多多渠道": {
        "department_id": 76,
        "keywords": ["拼多多", "PDD", "拼团", "百亿补贴"],
        "users": ["yangchao", "LiNa", "SongChengZhuo", "LiShiBo"]  # 拼多多渠道用户
    }
}

# use context7
CHANNEL_LOGOS = {
    '京东': 'images/jd_logo.png',    # 图片1
    '天猫': 'images/tmall_logo.png', # 图片2
    '拼多多': 'images/pdd_logo.png',  # 图片3
    '抖音': 'images/douyin_logo.png', # 图片4
    '卡萨帝': 'images/casarte_logo.png', # 图片5
    '其他': 'images/default_logo.png'   # 默认logo（可自定义）
}

# use context7
PLATFORM_LOGO_MAP = {
    "京东": "images/jd_logo.png",      # 图片1
    "天猫": "images/tmall_logo.png",   # 图片2
    "拼多多": "images/pdd_logo.png",   # 图片3
    "抖音": "images/douyin_logo.png",  # 图片4
    "卡萨帝": "images/casarte_logo.png" # 图片5
}

# 恢复品类emoji符号
category_icons = {
    '冰箱': '🧊',
    '热水器': '♨️',
    '厨电': '🍽️',
    '洗碗机': '🍽️',
    '洗衣机': '🧺',
    '空调': '❄️',
    '家用空调': '❄️',
    '商用空调': '❄️',
    '冷柜': '📦',
    '其他': '📦',
}

# ========== 固定列名配置 ==========
DATE_COL = '交易时间'
AMOUNT_COL = '分摊后总价'
QTY_COL = '实发数量'
SHOP_COL = '店铺'
CATEGORY_COL = '货品名称'
MODEL_COL = '规格名称'

def check_required_columns(df):
    """检查必需的列是否存在，如果不存在直接报错退出"""
    required_cols = [DATE_COL, AMOUNT_COL, QTY_COL, SHOP_COL, CATEGORY_COL, MODEL_COL]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        error_msg = f"❌ 缺少必要的列: {', '.join(missing_cols)}"
        print(error_msg)
        print(f"📋 当前文件列名: {list(df.columns)}")
        sys.exit(1)
    
    print(f"✅ 所有必需列存在: {', '.join(required_cols)}")
    return True

def is_online_shop(shop_name):
    if not isinstance(shop_name, str):
        return False
    online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美']
    return any(kw in shop_name for kw in online_keywords)

def save_report_to_local(content, report_type="overall_daily"):
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{report_type}_{report_date}.html"
    # 新增：标准HTML头部，确保UTF-8编码，防止Web报告乱码
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>销售日报报告 - {report_date}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 0.5em; max-width: 900px; margin-left:auto; margin-right:auto; text-align: left; font-size: 10.5pt; }}
        h1, h2, h3 {{ color: #0056b3; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; font-size: 14pt; font-weight: bold; margin: 0.3em 0; }}
        pre, code {{ background: #f3f3f3; padding: 0.5em; border-radius: 4px; white-space: pre-wrap; word-break: break-all; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; margin: 0.3em 0; }}
        .growth-positive {{ background-color: #e6f4ea !important; }}
        .growth-negative {{ background-color: #fbeaea !important; }}
        .left-align {{ text-align: left !important; }}
        @media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}
    </style>
</head>
<body>
    <div class="report-content">
        {content}
    </div>
</body>
</html>'''
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ 报表已保存: {filename}")
    return filename

def get_web_report_url():
    """获取Web报告URL"""
    return f"http://127.0.0.1:5002/reports/latest_report.html"

def _send_single_message(message):
    """发送单条消息"""
    url = "http://212.64.57.87:5001/send"
    token = "wecomchan_token"
    data = {
        "msg": message,
        "token": token,
        "to_user": "weicungang"
    }
    
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, timeout=30)
            print(f"📤 发送结果: {response.text[:100]}...")
            
            if "errcode" in response.text and "0" in response.text:
                print(f"✅ 发送成功 (尝试 {attempt + 1}/{max_retries})")
                return True
            elif "500" in response.text or "error" in response.text.lower():
                print(f"⚠️ 服务器错误 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    # 尝试缩短内容重试
                    shorter_msg = message[:500]
                    data["msg"] = shorter_msg
                else:
                    print(f"❌ 发送失败，已重试{max_retries}次")
                    return False
            else:
                print(f"⚠️ 发送返回异常 (尝试 {attempt + 1}/{max_retries}): {response.text}")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 发送失败，已重试{max_retries}次")
                    return False
        except requests.exceptions.ConnectTimeout:
            print(f"❌ 连接超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                print(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                print(f"❌ 发送失败: 连接超时，已重试{max_retries}次")
                return False
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                print(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                print(f"❌ 发送失败: 请求超时，已重试{max_retries}次")
                return False
        except Exception as e:
            print(f"❌ 发送异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                print(f"❌ 发送失败: {e}，已重试{max_retries}次")
                return False
    return False

def send_failure_report_to_admin(script_name, error_details):
    """发送失败报告给管理员"""
    failure_msg = f"""🚨 发送失败报告

📋 脚本名称: {script_name}
⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ 失败原因: {error_details}

请检查网络连接和服务器状态。"""
    
    admin_data = {"msg": failure_msg, "token": "wecomchan_token", "to_user": "weicungang"}
    try:
        resp = requests.post("http://212.64.57.87:5001/send", json=admin_data, timeout=30)
        print(f"📤 失败报告发送结果: {resp.text[:100]}...")
    except Exception as e:
        print(f"❌ 失败报告发送异常: {e}")

def send_wecomchan_segment(result):
    """分段发送，去除分段编号和截断提示"""
    max_chars = 800
    if len(result) <= max_chars:
        success = _send_single_message(result)
        if not success:
            send_failure_report_to_admin("整体日报数据.py", "微信消息发送失败")
    else:
        print(f"⚠️ 内容过长({len(result)}字符)，进行智能分段")
        segments = _smart_split_content(result, max_chars)
        for segment in segments:
            success = _send_single_message(segment)
            if not success:
                send_failure_report_to_admin("整体日报数据.py", "微信消息发送失败")
                break
            time.sleep(2)

def _smart_split_content(content, max_chars):
    """智能分割内容"""
    # 按照自然分段符分割
    natural_breaks = ['\n\n', '\n━━━', '\n===', '\n---', '\n📊', '\n🔥', '\n💰']
    
    segments = []
    current_segment = ""
    
    lines = content.split('\n')
    for line in lines:
        if len(current_segment + line + '\n') > max_chars:
            if current_segment:
                segments.append(current_segment.strip())
                current_segment = line + '\n'
            else:
                # 单行太长，强制截断
                segments.append(line[:max_chars])
                current_segment = ""
        else:
            current_segment += line + '\n'
    
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    return segments

def upload_html_and_get_url(filename, html_content):
    """自动适配 Windows 和 Mac/Linux 的 edgeone CLI 路径"""
    import subprocess
    import time
    temp_path = os.path.join("reports", filename)
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    # 判断平台
    system = platform.system().lower()
    if system == 'windows':
        edgeone_path = r"C:\Users\weicu\AppData\Roaming\npm\edgeone.cmd"
        cmd = [edgeone_path, "pages", "deploy", "./reports", "-n", EDGEONE_PROJECT, "-t", EDGEONE_TOKEN]
    else:
        # Mac/Linux 默认全局命令
        edgeone_path = "edgeone"
        cmd = [edgeone_path, "pages", "deploy", "./reports", "-n", EDGEONE_PROJECT, "-t", EDGEONE_TOKEN]
    try:
        print(f"\n🌐 正在通过 edgeone CLI 上传 reports 目录: {temp_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(result.stdout)
        public_url = f"https://edge.haierht.cn/reports/{filename}"
        print(f"✅ EdgeOne Pages 公网链接: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ EdgeOne Pages CLI 上传异常: {e}")
        return None

def deploy_to_edgeone():
    try:
        result = subprocess.run([
            "edgeone", "pages", "deploy", ".",
            "-n", "sales-report",
            "-t", "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ EdgeOne Pages 自动部署成功！")
        else:
            print("❌ EdgeOne Pages 部署失败：", result.stderr)
    except Exception as e:
        print("❌ EdgeOne Pages 部署异常：", e)

# ========== 数据库配置 ==========
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

# 步骤2: 读取ERP销售数据
logging.info("🚀 开始执行销售数据分析...")
logging.info(f"📊 读取数据库Daysales表数据")

# 修改：自动获取昨天的数据
today = datetime.now()
yesterday = today - timedelta(days=1)
yesterday_str = yesterday.strftime('%Y-%m-%d')
report_date = yesterday_str

# 检查数据库是否有昨天的数据
def check_data_availability(date_str):
    """检查指定日期是否有数据"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        df_check = pd.read_sql(f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 LIKE '{date_str}%'", conn)
        conn.close()
        count = df_check.iloc[0]['count']
        return count > 0, count
    except Exception as e:
        print(f"❌ 检查数据可用性失败: {e}")
        return False, 0

# 检查昨天数据是否可用
has_yesterday_data, yesterday_count = check_data_availability(yesterday_str)

if not has_yesterday_data:
    # 发送提醒到指定webhook
    alert_msg = f"""🚨 数据缺失提醒

📅 日期: {yesterday_str}
❌ 状态: 数据库中没有找到该日期的销售数据
📊 记录数: {yesterday_count}
⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查：
1. 数据是否已上传到数据库
2. 数据日期格式是否正确
3. 数据库连接是否正常

脚本已停止执行，等待数据补充后重新运行。"""
    
    alert_data = {
        "msg": alert_msg,
        "token": "wecomchan_token",
        "to_user": "weicungang"
    }
    
    try:
        # 发送到指定的webhook
        webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=02d1441f-aa5b-44cb-aeab-b934fe78f8cb"
        response = requests.post(webhook_url, json=alert_data, timeout=30)
        print(f"📤 数据缺失提醒发送结果: {response.text}")
        
        # 同时发送到原有webhook
        _send_single_message(alert_msg)
        
    except Exception as e:
        print(f"❌ 发送数据缺失提醒失败: {e}")
    
    print(f"❌ 数据库中没有找到 {yesterday_str} 的数据，脚本停止执行")
    sys.exit(1)

print(f"✅ 数据库中找到 {yesterday_str} 的数据，共 {yesterday_count} 条记录")

try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=10
    )
    df_erp = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{yesterday_str}%'", conn)
    conn.close()
    print(f"📊 直接连接成功，共{len(df_erp)}行")
except Exception as e:
    print(f"❌ 直接连接数据库失败: {e}")
    sys.exit(1)

# 读取前前一天数据用于环比分析
day_before_yesterday = yesterday - timedelta(days=1)
day_before_yesterday_str = day_before_yesterday.strftime('%Y-%m-%d')

# 检查前前一天数据是否可用
has_prev_data, prev_count = check_data_availability(day_before_yesterday_str)

if not has_prev_data:
    print(f"⚠️ 数据库中没有找到 {day_before_yesterday_str} 的数据，环比分析将受限")
    df_prev = None
else:
    print(f"✅ 数据库中找到 {day_before_yesterday_str} 的数据，共 {prev_count} 条记录")
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        df_prev = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{day_before_yesterday_str}%'", conn)
        conn.close()
        print(f"📊 前前一天数据读取成功，共{len(df_prev)}行")
    except Exception as e:
        print(f"⚠️ 读取前前一天数据失败: {e}")
        df_prev = None

# 后续分析逻辑保持不变，df_erp即为主数据源

# 1. 替换渠道归类函数

def classify_channel(shop_name):
    if not isinstance(shop_name, str):
        return "其他"
    shop_name = shop_name.strip()
    # 优先卡萨帝和小红书
    if "卡萨帝" in shop_name or "小红书" in shop_name:
        return "卡萨帝"
    if shop_name.startswith("京东"):
        return "京东"
    if shop_name.startswith("天猫") or "淘宝" in shop_name:
        return "天猫"
    if shop_name.startswith("拼多多"):
        return "拼多多"
    if shop_name.startswith("抖音"):
        return "抖音"
    return "其他"

# 使用固定列名
amount_col = AMOUNT_COL
qty_col = QTY_COL

# 使用context7推荐的现代数据处理方法
df_erp[amount_col] = pd.to_numeric(df_erp[amount_col], errors='coerce').fillna(0)
df_erp[qty_col] = pd.to_numeric(df_erp[qty_col], errors='coerce').fillna(0)

# 过滤掉金额或数量为0的记录
df_erp = df_erp[(df_erp[amount_col] > 0) & (df_erp[qty_col] > 0)]

# 刷单剔除逻辑（只认"客服备注"列，严格匹配，剔除包含"抽纸""纸巾"或完全等于"不发货"）
remark_col = None
for col in df_erp.columns:
    if col == '客服备注':
        remark_col = col
        break
if remark_col and remark_col in df_erp.columns:
    before_rows = len(df_erp)
    df_erp[remark_col] = df_erp[remark_col].astype(str).fillna('')
    filter_condition = ~(
        df_erp[remark_col].str.contains('抽纸', na=False) |
        df_erp[remark_col].str.contains('纸巾', na=False) |
        (df_erp[remark_col] == '不发货')
    )
    df_erp = df_erp[filter_condition]
    after_rows = len(df_erp)
    print(f"刷单剔除：{before_rows} -> {after_rows}")
# 同期数据也做同样处理
if df_prev is not None and remark_col and remark_col in df_prev.columns:
    before_rows_prev = len(df_prev)
    df_prev[remark_col] = df_prev[remark_col].astype(str).fillna('')
    filter_condition_prev = ~(
        df_prev[remark_col].str.contains('抽纸', na=False) |
        df_prev[remark_col].str.contains('纸巾', na=False) |
        (df_prev[remark_col] == '不发货')
    )
    df_prev = df_prev[filter_condition_prev]
    after_rows_prev = len(df_prev)
    print(f"同期刷单剔除：{before_rows_prev} -> {after_rows_prev}")

# 2. 识别订单状态列，剔除"未付款"和"已取消"订单
order_status_col = None
for col in df_erp.columns:
    if '订单状态' in str(col) or '状态' in str(col):
        order_status_col = col
        break
if order_status_col and order_status_col in df_erp.columns:
    df_erp = df_erp[~df_erp[order_status_col].astype(str).str.contains('未付款|已取消', na=False)]

# 过滤线下店铺
df_erp = df_erp[df_erp[SHOP_COL].apply(is_online_shop)]

# 添加渠道列
df_erp['渠道'] = df_erp[SHOP_COL].apply(classify_channel)

# 清洗前一天数据
if df_prev is not None:
    df_prev[amount_col] = pd.to_numeric(df_prev[amount_col], errors='coerce').fillna(0)
    df_prev[qty_col] = pd.to_numeric(df_prev[qty_col], errors='coerce').fillna(0)
    df_prev = df_prev[(df_prev[amount_col] > 0) & (df_prev[qty_col] > 0)]
    df_prev = df_prev[df_prev[SHOP_COL].apply(is_online_shop)]  # 修复：使用df_prev的店铺列
    df_prev['渠道'] = df_prev[SHOP_COL].apply(classify_channel)
    print(f"📊 前一天数据过滤后行数: {len(df_prev)}")

# 环比计算函数
def calculate_ratio(current, previous):
    """计算增长比例"""
    if previous == 0:
        return "📈 100%" if current > 0 else "0%"
    
    ratio = ((current - previous) / previous) * 100
    if ratio > 0:
        return f"📈 {ratio:.1f}%"
    elif ratio < 0:
        return f"📉 {ratio:.1f}%"
    else:
        return "📊 0%"

# 1. 新增归类函数
def normalize_category(name):
    if '热水器' in str(name):
        return '热水器'
    return name

# 2. 在清洗数据后，强制归类
df_erp[CATEGORY_COL] = df_erp[CATEGORY_COL].apply(normalize_category)
if df_prev is not None:
    df_prev[CATEGORY_COL] = df_prev[CATEGORY_COL].apply(normalize_category)

# ========== HTML生成函数 ==========
def generate_category_ranking_html(category_data, df_erp, prev_category_data, amount_col, qty_col, CATEGORY_COL, MODEL_COL, category_icons):
    """生成品类销售排行榜HTML，每个品类下折叠单品明细，增加环比数据和底色，屏蔽'其他'品类"""
    html = ''
    # 过滤掉"其他"品类
    filtered_category_data = category_data[category_data[CATEGORY_COL] != '其他']
    
    for idx, row in enumerate(filtered_category_data.iterrows(), 1):
        _, row_data = row
        cat = row_data[CATEGORY_COL]
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        # 查找前一天该品类数据
        prev_amount = 0
        if prev_category_data is not None:
            prev_cat_data = prev_category_data[prev_category_data[CATEGORY_COL] == cat]
            if not prev_cat_data.empty:
                prev_amount = int(prev_cat_data.iloc[0][amount_col])
        icon = category_icons.get(cat, '📦')
        html += f'<details><summary>{icon} {idx}. {cat} ─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) ─ 销量: {qty:,}件 | 单价: ¥{price:,}</summary>'
        # 单品明细（折叠内容）- 用并集遍历，按本期销售额排序
        product_summary = df_erp[df_erp[CATEGORY_COL] == cat].groupby(MODEL_COL).agg({
            amount_col: 'sum', 
            qty_col: 'sum'
        }).reset_index()
        prev_product_summary = None
        if prev_category_data is not None and df_prev is not None:
            prev_cat_df = df_prev[df_prev[CATEGORY_COL] == cat]
            if not prev_cat_df.empty:
                prev_product_summary = prev_cat_df.groupby(MODEL_COL).agg({
                    amount_col: 'sum',
                    qty_col: 'sum'
                }).reset_index()
        current_products = set(product_summary[MODEL_COL])
        prev_products = set(prev_product_summary[MODEL_COL]) if prev_product_summary is not None else set()
        all_products = list(current_products | prev_products)
        # 按本期销售额排序
        all_products.sort(key=lambda p: int(product_summary[product_summary[MODEL_COL]==p][amount_col].values[0]) if not product_summary[product_summary[MODEL_COL]==p].empty else 0, reverse=True)
        if all_products:
            html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for product in all_products:
                # 本期
                cur_row = product_summary[product_summary[MODEL_COL] == product]
                cur_amount = int(cur_row[amount_col].values[0]) if not cur_row.empty else 0
                cur_qty = int(cur_row[qty_col].values[0]) if not cur_row.empty else 0
                # 对比期
                prev_amount = 0
                prev_qty = 0
                if prev_product_summary is not None:
                    prev_row = prev_product_summary[prev_product_summary[MODEL_COL] == product]
                    prev_amount = int(prev_row[amount_col].values[0]) if not prev_row.empty else 0
                    prev_qty = int(prev_row[qty_col].values[0]) if not prev_row.empty else 0
                # 只要有一方大于1000就展示
                if cur_amount > 1000 or prev_amount > 1000:
                    ratio_str = calculate_ratio(cur_qty, prev_qty)
                    # 背景色
                    if cur_qty > prev_qty:
                        bg = 'background: #f0fff0;'
                    elif cur_qty < prev_qty:
                        bg = 'background: #fff0f0;'
                    else:
                        bg = ''
                    html += f'<li style="margin-bottom: 5px; {bg}">🔸 {product}<br>本期: ¥{cur_amount:,}（{cur_qty}件），对比期: ¥{prev_amount:,}（{prev_qty}件），前一天销售 {prev_qty} 件，环比 {ratio_str}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        html += '</details>'
    return html

def generate_channel_ranking_html(channel_summary, df_erp, prev_channel_summary, amount_col, qty_col, SHOP_COL):
    """生成渠道销售分析HTML，每个渠道下折叠店铺明细，增加环比数据"""
    html = ''
    for idx, row in enumerate(channel_summary.iterrows(), 1):
        _, row_data = row
        channel = row_data['渠道']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        
        # 查找前一天该渠道数据
        prev_amount = 0
        if prev_channel_summary is not None:
            prev_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
        
        html += f'<details><summary>🏪 {idx}. {channel}渠道: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) | {qty:,}件 | ¥{price:,}/件</summary>'
        
        # 店铺明细（折叠内容）- 增加环比
        shop_summary = df_erp[df_erp['渠道'] == channel].groupby(SHOP_COL).agg({
            amount_col: 'sum', 
            qty_col: 'sum'
        }).reset_index()
        shop_summary = shop_summary.sort_values(amount_col, ascending=False)
        
        if len(shop_summary) > 0:
            html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for _, s_row in shop_summary.iterrows():
                shop = s_row[SHOP_COL]
                s_amount = int(s_row[amount_col])
                s_qty = int(s_row[qty_col])
                s_price = int(s_amount / s_qty) if s_qty else 0
                
                # 查找前一天该店铺数据
                prev_s_amount = 0
                prev_s_qty = 0
                if df_prev is not None:
                    prev_shop_data = df_prev[df_prev[SHOP_COL] == shop]
                    if not prev_shop_data.empty:
                        prev_s_amount = int(prev_shop_data[amount_col].sum())
                        prev_s_qty = int(prev_shop_data[qty_col].sum())
                
                html += f'<li style="margin-bottom: 5px;">🏪 {shop}<br>销售额: ¥{s_amount:,} | 销量: {s_qty:,}件 | 单价: ¥{s_price:,}，前一天销售 {prev_s_qty} 件，环比 {calculate_ratio(s_qty, prev_s_qty)}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无店铺数据</p>'
        
        html += '</details>'
    return html

def generate_shop_ranking_html(shop_summary, df_erp, prev_shop_summary, amount_col, qty_col, MODEL_COL):
    """生成TOP店铺排行HTML，每个店铺下折叠单品明细，增加环比数据和底色"""
    html = ''
    for idx, row in enumerate(shop_summary.iterrows(), 1):
        _, row_data = row
        shop = row_data['店铺']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        # 查找前一天该店铺数据
        prev_amount = 0
        if prev_shop_summary is not None:
            prev_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
        html += f'<details><summary>🏪 TOP{idx} {shop} ─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) ─ 销量: {qty:,}件 | 单价: ¥{price:,}</summary>'
        # 单品明细（折叠内容）- 用并集遍历，按本期销售额排序
        product_summary = df_erp[df_erp['店铺'] == shop].groupby(MODEL_COL).agg({
            amount_col: 'sum', 
            qty_col: 'sum'
        }).reset_index()
        prev_product_summary = None
        if df_prev is not None:
            prev_shop_df = df_prev[df_prev['店铺'] == shop]
            if not prev_shop_df.empty:
                prev_product_summary = prev_shop_df.groupby(MODEL_COL).agg({
                    amount_col: 'sum',
                    qty_col: 'sum'
                }).reset_index()
        current_products = set(product_summary[MODEL_COL])
        prev_products = set(prev_product_summary[MODEL_COL]) if prev_product_summary is not None else set()
        all_products = list(current_products | prev_products)
        # 按本期销售额排序
        all_products.sort(key=lambda p: int(product_summary[product_summary[MODEL_COL]==p][amount_col].values[0]) if not product_summary[product_summary[MODEL_COL]==p].empty else 0, reverse=True)
        if all_products:
            html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for product in all_products:
                # 本期
                cur_row = product_summary[product_summary[MODEL_COL] == product]
                cur_amount = int(cur_row[amount_col].values[0]) if not cur_row.empty else 0
                cur_qty = int(cur_row[qty_col].values[0]) if not cur_row.empty else 0
                # 对比期
                prev_amount = 0
                prev_qty = 0
                if prev_product_summary is not None:
                    prev_row = prev_product_summary[prev_product_summary[MODEL_COL] == product]
                    prev_amount = int(prev_row[amount_col].values[0]) if not prev_row.empty else 0
                    prev_qty = int(prev_row[qty_col].values[0]) if not prev_row.empty else 0
                # 只要有一方大于1000就展示
                if cur_amount > 1000 or prev_amount > 1000:
                    ratio_str = calculate_ratio(cur_qty, prev_qty)
                    # 背景色
                    if cur_qty > prev_qty:
                        bg = 'background: #f0fff0;'
                    elif cur_qty < prev_qty:
                        bg = 'background: #fff0f0;'
                    else:
                        bg = ''
                    html += f'<li style="margin-bottom: 5px; {bg}">🔸 {product}<br>本期: ¥{cur_amount:,}（{cur_qty}件），对比期: ¥{prev_amount:,}（{prev_qty}件），前一天销售 {prev_qty} 件，环比 {ratio_str}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        html += '</details>'
    return html

def generate_category_trend_html(category_data, prev_category_data, category_icons, shop_summary, prev_shop_summary, df_erp, df_prev, amount_col, qty_col, MODEL_COL):
    """生成品类变化趋势HTML，增加店铺和单品环比监控"""
    html = ''
    
    # 品类变化趋势 - 按销售额从高到低排序
    html += '<h3>📊 品类变化趋势</h3>'
    # 按销售额排序
    category_data_sorted = category_data.sort_values(amount_col, ascending=False)
    
    for _, row in category_data_sorted.iterrows():
        category = row[CATEGORY_COL]
        current_amount = int(row[amount_col])
        
        # 查找前一天该品类数据
        prev_amount = 0
        if prev_category_data is not None:
            prev_data = prev_category_data[prev_category_data[CATEGORY_COL] == category]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
        
        if prev_amount > 0:
            growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
            emoji = category_icons.get(category, '📦')
            if growth_rate > 0:
                html += f'<div style="margin-bottom: 8px; padding: 6px; background: #f0f8ff; border-radius: 4px;">'
                html += f'<strong>{emoji} {category}: 📈 +{growth_rate:.1f}%</strong><br>'
                html += f'销售额变化: ¥{prev_amount:,} → ¥{current_amount:,}</div>'
            else:
                html += f'<div style="margin-bottom: 8px; padding: 6px; background: #fff0f0; border-radius: 4px;">'
                html += f'<strong>{emoji} {category}: 📉 {growth_rate:.1f}%</strong><br>'
                html += f'销售额变化: ¥{prev_amount:,} → ¥{current_amount:,}</div>'
    
    # 店铺环比监控（>20%增长或下滑）
    html += '<h3>⚠️ 店铺环比监控</h3>'
    growth_shops = []
    decline_shops = []
    
    for _, row in shop_summary.iterrows():
        shop = row['店铺']
        current_amount = int(row[amount_col])
        current_qty = int(row[qty_col])
        
        # 查找前一天该店铺数据
        prev_amount = 0
        prev_qty = 0
        if prev_shop_summary is not None:
            prev_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
                prev_qty = int(prev_data.iloc[0][qty_col])
        
        if prev_amount > 0:
            growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
            if growth_rate > 20:
                growth_shops.append((shop, growth_rate, prev_amount, current_amount))
            elif growth_rate < -20:
                decline_shops.append((shop, growth_rate, prev_amount, current_amount))
    
    # 显示增长店铺
    if growth_shops:
        html += '<div style="margin-bottom: 10px; padding: 8px; background: #f0fff0; border-radius: 4px;">'
        html += '<strong>📈 高速增长店铺 (>20%)</strong><br>'
        for shop, growth_rate, prev_amount, current_amount in growth_shops[:5]:
            html += f'🏪 {shop}: +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})<br>'
        html += '</div>'
    
    # 显示下滑店铺
    if decline_shops:
        html += '<div style="margin-bottom: 10px; padding: 8px; background: #fff0f0; border-radius: 4px;">'
        html += '<strong>📉 严重下滑店铺 (>20%)</strong><br>'
        for shop, growth_rate, prev_amount, current_amount in decline_shops[:5]:
            html += f'🏪 {shop}: {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})<br>'
        html += '</div>'
    
    # 单品环比监控（>20%增长或下滑）- 按品类分组显示所有满足条件的单品
    html += '<h3>⚠️ 单品环比监控</h3>'
    
    # 按品类分组处理单品
    categories = df_erp[CATEGORY_COL].unique()
    
    for cat in categories:
        if cat == '其他':
            continue
            
        icon = category_icons.get(cat, '📦')
        cat_df = df_erp[df_erp[CATEGORY_COL] == cat]
        
        # 获取该品类所有单品数据
        cat_products = cat_df.groupby(MODEL_COL).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        cat_products = cat_products[(cat_products[amount_col] > 1000) & ~cat_products[MODEL_COL].str.contains('运费|赠品')]
        
        growth_products = []
        decline_products = []
        
        for _, row in cat_products.iterrows():
            product = row[MODEL_COL]
            current_qty = int(row[qty_col])
            
            # 查找前一天该单品数据
            prev_qty = 0
            if df_prev is not None:
                prev_product_data = df_prev[df_prev[MODEL_COL] == product]
                if not prev_product_data.empty:
                    prev_qty = int(prev_product_data[qty_col].sum())
            
            if prev_qty > 0:
                growth_rate = ((current_qty - prev_qty) / prev_qty) * 100
                if growth_rate > 20:
                    growth_products.append((product, growth_rate, prev_qty, current_qty))
                elif growth_rate < -20:
                    decline_products.append((product, growth_rate, prev_qty, current_qty))
        
        # 按件数排序
        growth_products.sort(key=lambda x: x[3], reverse=True)  # 按当前件数排序
        decline_products.sort(key=lambda x: x[3], reverse=True)  # 按当前件数排序
        
        # 显示该品类的增长单品
        if growth_products:
            html += f'<div style="margin-bottom: 10px; padding: 8px; background: #f0fff0; border-radius: 4px;">'
            html += f'<strong>📈 {icon} {cat} - 高速增长单品 (>20%)</strong><br>'
            for product, growth_rate, prev_qty, current_qty in growth_products:
                html += f'🔸 {product}: +{growth_rate:.1f}% ({prev_qty}→{current_qty}件)<br>'
            html += '</div>'
        
        # 显示该品类的下滑单品
        if decline_products:
            html += f'<div style="margin-bottom: 10px; padding: 8px; background: #fff0f0; border-radius: 4px;">'
            html += f'<strong>📉 {icon} {cat} - 严重下滑单品 (>20%)</strong><br>'
            for product, growth_rate, prev_qty, current_qty in decline_products:
                html += f'🔸 {product}: {growth_rate:.1f}% ({prev_qty}→{current_qty}件)<br>'
            html += '</div>'
    
    return html

def generate_top_product_html(df_erp, amount_col, qty_col, MODEL_COL, CATEGORY_COL, category_icons, top_n=5):
    """分品类展示TOP单品，每个品类下展示TOP N"""
    html = ''
    # 获取所有品类
    categories = df_erp[CATEGORY_COL].unique()
    for cat in categories:
        if cat == '其他':
            continue
        icon = category_icons.get(cat, '📦')
        cat_df = df_erp[df_erp[CATEGORY_COL] == cat]
        product_summary = cat_df.groupby(MODEL_COL).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        # 只保留销售额>1000且不含"运费""赠品"
        product_summary = product_summary[(product_summary[amount_col] > 1000) & ~product_summary[MODEL_COL].str.contains('运费|赠品')]
        product_summary = product_summary.sort_values(amount_col, ascending=False)
        if len(product_summary) > 0:
            html += f'<div style="margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px;">'
            html += f'<strong>{icon} {cat} TOP单品</strong><br>'
            for idx, row in enumerate(product_summary.iterrows(), 1):
                if idx > top_n:
                    break
                _, p_row = row
                product = p_row[MODEL_COL]
                p_amount = int(p_row[amount_col])
                p_qty = int(p_row[qty_col])
                p_price = int(p_amount / p_qty) if p_qty else 0
                html += f'🔸 TOP{idx} {product}<br>销售额: ¥{p_amount:,} | 销量: {p_qty:,}件 | 单价: ¥{p_price:,}<br>'
            html += '</div>'
    return html

def generate_shop_product_html(shop_summary, df_erp, amount_col, qty_col, MODEL_COL):
    """生成店铺单品数据HTML，直接展示，无折叠"""
    html = ''
    for _, row in shop_summary.iterrows():
        shop = row['店铺']
        html += f'<div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">'
        html += f'<h4 style="margin-top: 0; color: #0056b3;">🏪 {shop}</h4>'
        
        # 获取该店铺的单品数据
        shop_df = df_erp[df_erp['店铺'] == shop]
        product_summary = shop_df.groupby(MODEL_COL).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        # 只保留销售额>1000且不含"运费""赠品"
        product_summary = product_summary[(product_summary[amount_col] > 1000) & ~product_summary[MODEL_COL].str.contains('运费|赠品')]
        product_summary = product_summary.sort_values(amount_col, ascending=False)
        
        if len(product_summary) > 0:
            html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for _, p_row in product_summary.iterrows():
                product = p_row[MODEL_COL]
                p_amount = int(p_row[amount_col])
                p_qty = int(p_row[qty_col])
                p_price = int(p_amount / p_qty) if p_qty else 0
                html += f'<li style="margin-bottom: 5px;">🔸 {product}<br>销售额: ¥{p_amount:,} | 销量: {p_qty:,}件 | 单价: ¥{p_price:,}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        
        html += '</div>'
    return html

# ========== Part 1: 整体销售到品类 ==========
total_amount = int(df_erp[amount_col].sum())
total_qty = int(df_erp[qty_col].sum())
total_price = int(total_amount / total_qty) if total_qty else 0

# 计算前一天整体数据
prev_total_amount = 0
prev_total_qty = 0
if df_prev is not None:
    prev_total_amount = int(df_prev[amount_col].sum())
    prev_total_qty = int(df_prev[qty_col].sum())

# 品类销售情况（按货品名称分组）
category_data = df_erp.groupby(CATEGORY_COL).agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()

# 过滤掉"其他"品类
category_data = category_data[category_data[CATEGORY_COL] != '其他']

# 前一天品类数据
prev_category_data = None
if df_prev is not None:
    prev_category_data = df_prev.groupby(CATEGORY_COL).agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()
    prev_category_data = prev_category_data[prev_category_data[CATEGORY_COL] != '其他']

# 按销售金额排序
category_data = category_data.sort_values(amount_col, ascending=False)

part1 = f"""💰 【整体销售概况】\n├─ 总销售额: ¥{total_amount:,}\n├─ 总销量: {total_qty:,}件  \n├─ 单价: ¥{total_price:,}\n└─ 环比: {calculate_ratio(total_amount, prev_total_amount)}\n\n🏆 【品类销售排行榜】"""

for idx, row in enumerate(category_data.iterrows(), 1):
    _, row_data = row
    cat = row_data[CATEGORY_COL]
    amount = int(row_data[amount_col])
    qty = int(row_data[qty_col])
    price = int(amount / qty) if qty else 0
    
    # 查找前一天该品类数据
    prev_amount = 0
    if prev_category_data is not None:
        prev_cat_data = prev_category_data[prev_category_data[CATEGORY_COL] == cat]
        if not prev_cat_data.empty:
            prev_amount = int(prev_cat_data.iloc[0][amount_col])
    
    # 获取该品类的渠道分解
    category_channel_data = df_erp[df_erp[CATEGORY_COL] == cat].groupby('渠道').agg({
        amount_col: 'sum'
    }).reset_index().sort_values(amount_col, ascending=False)
    
    # 获取前一天该品类的渠道分解
    prev_category_channel_data = None
    if df_prev is not None:
        prev_category_channel_data = df_prev[df_prev[CATEGORY_COL] == cat].groupby('渠道').agg({
            amount_col: 'sum'
        }).reset_index()
    
    # 构建渠道分解字符串
    channel_breakdown = []
    for _, ch_row in category_channel_data.iterrows():
        channel = ch_row['渠道']
        ch_amount = int(ch_row[amount_col])
        
        # 查找前一天该渠道数据
        prev_ch_amount = 0
        if prev_category_channel_data is not None:
            prev_ch_data = prev_category_channel_data[prev_category_channel_data['渠道'] == channel]
            if not prev_ch_data.empty:
                prev_ch_amount = int(prev_ch_data.iloc[0][amount_col])
        
        channel_breakdown.append(f"{channel}¥{ch_amount:,}({calculate_ratio(ch_amount, prev_ch_amount)})")
    
    channel_text = f" | ".join(channel_breakdown) if channel_breakdown else ""
    icon = category_icons.get(cat, '📦')
    
    part1 += f"""
    ├─ {icon} {idx}. {cat}
    ├─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)})
    ├─ 销量: {qty:,}件 | 单价: ¥{price:,}\n└─ {channel_text}"""

# ========== Part 2: 渠道销售分析 ==========

# 渠道销售情况（按渠道分组）
channel_summary = df_erp.groupby('渠道').agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()

# 前一天渠道数据
prev_channel_summary = None
if df_prev is not None:
    prev_channel_summary = df_prev.groupby('渠道').agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()

# 为Web版本生成完整店铺列表
def generate_shop_ranking(shop_summary, prev_shop_summary, for_web=False):
    shop_list = ""
    limit = None if for_web else 10  # Web版本无限制，微信版本限制10个
    
    for idx, row in enumerate(shop_summary.iterrows(), 1):
        if not for_web and idx > 10:  # 微信版本只显示前10个
            break
            
        _, row_data = row
        shop = row_data['店铺']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        
        # 查找前一天该店铺数据
        prev_amount = 0
        if prev_shop_summary is not None:
            prev_shop_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
            if not prev_shop_data.empty:
                prev_amount = int(prev_shop_data.iloc[0][amount_col])
        
        shop_list += f"├─ 🏪 TOP{idx} {shop}\n├─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)})\n├─ 销量: {qty:,}件 | 单价: ¥{price:,}\n\n"
    
    return shop_list

part2 = f"""📊 【渠道销售分析】
"""

channel_summary = channel_summary.sort_values(amount_col, ascending=False)
for idx, row in enumerate(channel_summary.iterrows(), 1):
    _, row_data = row
    channel = row_data['渠道']
    amount = int(row_data[amount_col])
    qty = int(row_data[qty_col])
    price = int(amount / qty) if qty else 0
    
    # 查找前一天该渠道数据
    prev_amount = 0
    if prev_channel_summary is not None:
        prev_channel_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
        if not prev_channel_data.empty:
            prev_amount = int(prev_channel_data.iloc[0][amount_col])
    
    part2 += f"🏪 {idx}. {channel}渠道: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) | {qty:,}件 | ¥{price:,}/件\n"

part2 += "\n🏆 【TOP店铺排行】\n"

# 店铺汇总
shop_summary = df_erp.groupby('店铺').agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()
# 只保留销售额>0的店铺
shop_summary = shop_summary[shop_summary[amount_col] > 0]
shop_summary = shop_summary.sort_values(amount_col, ascending=False)

prev_shop_summary = None
if df_prev is not None:
    prev_shop_summary = df_prev.groupby('店铺').agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()

# 微信版本的Part2（只显示前10个店铺）
part2_wechat = part2 + generate_shop_ranking(shop_summary, prev_shop_summary, for_web=False)

# Web版本的Part2（显示所有店铺）  
part2_web = part2 + generate_shop_ranking(shop_summary, prev_shop_summary, for_web=True)

# ========== Part 3: 单品销售分析（按品类分类） ==========
part3 = f"""💎 【单品销售分析】\n"""
for idx, row in enumerate(category_data.iterrows(), 1):
    _, row_data = row
    category = row_data[CATEGORY_COL]
    if category == '其他':
        continue
    category_df = df_erp[df_erp[CATEGORY_COL] == category]
    product_summary = category_df.groupby(MODEL_COL).agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()
    # 对比期
    prev_product_summary = None
    if df_prev is not None:
        prev_category_df = df_prev[df_prev[CATEGORY_COL] == category]
        if not prev_category_df.empty:
            prev_product_summary = prev_category_df.groupby(MODEL_COL).agg({
                amount_col: 'sum',
                qty_col: 'sum'
            }).reset_index()
    # 获取所有单品全集
    current_products = set(product_summary[MODEL_COL])
    prev_products = set()
    if prev_product_summary is not None:
        prev_products = set(prev_product_summary[MODEL_COL])
    all_products = current_products | prev_products
    icon = category_icons.get(category, '📦')
    part3 += f"\n{icon} 【{category}】单品对比\n"
    for product in all_products:
        # 本期数据
        cur_row = product_summary[product_summary[MODEL_COL] == product]
        cur_amount = int(cur_row[amount_col].values[0]) if not cur_row.empty else 0
        cur_qty = int(cur_row[qty_col].values[0]) if not cur_row.empty else 0
        # 对比期数据
        prev_amount = 0
        prev_qty = 0
        if prev_product_summary is not None:
            prev_row = prev_product_summary[prev_product_summary[MODEL_COL] == product]
            prev_amount = int(prev_row[amount_col].values[0]) if not prev_row.empty else 0
            prev_qty = int(prev_row[qty_col].values[0]) if not prev_row.empty else 0
        # 只要有一方大于1000就展示
        if cur_amount > 1000 or prev_amount > 1000:
            part3 += f"🔸 {product}：本期¥{cur_amount:,}（{cur_qty}件），对比期¥{prev_amount:,}（{prev_qty}件）\n"

# ========== Part 4: 店铺核心产品销售分析 ==========
part4 = f"""🎯 【店铺核心产品分析】\n"""
for idx, row in enumerate(shop_summary.iterrows(), 1):
    _, row_data = row
    shop = row_data['店铺']
    shop_df = df_erp[df_erp['店铺'] == shop]
    product_summary = shop_df.groupby(MODEL_COL).agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()
    # 对比期
    prev_product_summary = None
    if df_prev is not None:
        prev_shop_df = df_prev[df_prev['店铺'] == shop]
        if not prev_shop_df.empty:
            prev_product_summary = prev_shop_df.groupby(MODEL_COL).agg({
                amount_col: 'sum',
                qty_col: 'sum'
            }).reset_index()
    # 获取所有单品全集
    current_products = set(product_summary[MODEL_COL])
    prev_products = set()
    if prev_product_summary is not None:
        prev_products = set(prev_product_summary[MODEL_COL])
    all_products = current_products | prev_products
    part4 += f"\n🏪 【{shop}】单品对比\n"
    for product in all_products:
        # 本期数据
        cur_row = product_summary[product_summary[MODEL_COL] == product]
        cur_amount = int(cur_row[amount_col].values[0]) if not cur_row.empty else 0
        cur_qty = int(cur_row[qty_col].values[0]) if not cur_row.empty else 0
        # 对比期数据
        prev_amount = 0
        prev_qty = 0
        if prev_product_summary is not None:
            prev_row = prev_product_summary[prev_product_summary[MODEL_COL] == product]
            prev_amount = int(prev_row[amount_col].values[0]) if not prev_row.empty else 0
            prev_qty = int(prev_row[qty_col].values[0]) if not prev_row.empty else 0
        # 只要有一方大于1000就展示
        if cur_amount > 1000 or prev_amount > 1000:
            part4 += f"🔸 {product}：本期¥{cur_amount:,}（{cur_qty}件），对比期¥{prev_amount:,}（{prev_qty}件）\n"

# ========== Part 5: 重点关注分析 ==========
part5 = f"""⚠️ 【重点关注：同比增长与下滑分析】
        
📈 【高速增长表现】
🌟 渠道增长排行：
"""

# 计算渠道增长率
growth_channels = []
decline_channels = []

for _, row in channel_summary.iterrows():
    channel = row['渠道']
    current_amount = int(row[amount_col])
    
    # 查找前一天该渠道数据
    prev_amount = 0
    if prev_channel_summary is not None:
        prev_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
        if not prev_data.empty:
            prev_amount = int(prev_data.iloc[0][amount_col])
    
    if prev_amount > 0:
        growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
        if growth_rate > 0:
            growth_channels.append((channel, growth_rate, prev_amount, current_amount))
        elif growth_rate < -10:  # 下滑超过10%才显示
            decline_channels.append((channel, growth_rate, prev_amount, current_amount))

# 按增长率排序
growth_channels.sort(key=lambda x: x[1], reverse=True)
decline_channels.sort(key=lambda x: x[1])

# 显示增长渠道
for channel, growth_rate, prev_amount, current_amount in growth_channels[:5]:
    if '卡萨帝' in channel:
        emoji = '✨'
    elif '天猫' in channel:
        emoji = '🐱'
    elif '京东' in channel:
        emoji = '🛍️'
    elif '抖音' in channel:
        emoji = '🎵'
    else:
        emoji = '🏪'
    part5 += f"   {emoji} {channel}: +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"

part5 += f"""
🏆 店铺增长排行：
"""

# 计算店铺增长率
growth_shops = []
decline_shops = []

for _, row in shop_summary.iterrows():
    shop = row['店铺']
    current_amount = int(row[amount_col])
    
    # 查找前一天该店铺数据
    prev_amount = 0
    if prev_shop_summary is not None:
        prev_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
        if not prev_data.empty:
            prev_amount = int(prev_data.iloc[0][amount_col])
    
    if prev_amount > 0:
        growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
        if growth_rate > 50:  # 增长超过50%才显示
            growth_shops.append((shop, growth_rate, prev_amount, current_amount))
        elif growth_rate < -30:  # 下滑超过30%才显示
            decline_shops.append((shop, growth_rate, prev_amount, current_amount))

# 按增长率排序
growth_shops.sort(key=lambda x: x[1], reverse=True)
decline_shops.sort(key=lambda x: x[1])

# 显示增长店铺
for shop, growth_rate, prev_amount, current_amount in growth_shops[:5]:
    part5 += f"   🏪 {shop}\n      增长率: +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"

part5 += f"""
📉 【需要关注的下滑情况】
⚠️ 渠道下滑警报：
"""

# 显示下滑渠道
for channel, growth_rate, prev_amount, current_amount in decline_channels[:3]:
    if '抖音' in channel:
        emoji = '🎵'
    elif '天猫' in channel:
        emoji = '🐱'
    elif '京东' in channel:
        emoji = '🛍️'
    else:
        emoji = '🏪'
    part5 += f"   {emoji} {channel}: {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"

part5 += f"""
🔻 店铺下滑预警：
"""

# 显示下滑店铺
for shop, growth_rate, prev_amount, current_amount in decline_shops[:3]:
    part5 += f"   📉 {shop}\n      下滑率: {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"

part5 += f"""
🔍 【品类变化趋势】
"""

# 计算品类变化
category_changes = []
for _, row in category_data.iterrows():
    category = row[CATEGORY_COL]
    current_amount = int(row[amount_col])
    
    # 查找前一天该品类数据
    prev_amount = 0
    if prev_category_data is not None:
        prev_data = prev_category_data[prev_category_data[CATEGORY_COL] == category]
        if not prev_data.empty:
            prev_amount = int(prev_data.iloc[0][amount_col])
    
    if prev_amount > 0:
        growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
        category_changes.append((category, growth_rate, prev_amount, current_amount))

# 按增长率排序
category_changes.sort(key=lambda x: x[1], reverse=True)

# 显示品类变化
for category, growth_rate, prev_amount, current_amount in category_changes:
    if '冰箱' in category:
        emoji = '🧊'
    elif '空调' in category:
        emoji = '❄️'
    elif '洗衣机' in category:
        emoji = '🧺'
    elif '洗碗机' in category or '厨电' in category:
        emoji = '🍽️'
    elif '冷柜' in category:
        emoji = '📦'
    else:
        emoji = '📦'
    
    if growth_rate > 0:
        part5 += f"   {emoji} {category}: 📈 +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"
    else:
        part5 += f"   {emoji} {category}: 📉 {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"

# ============ 微信推送与Web发布分离，优化推送逻辑 ============

try:
    # 首先发布到Web (完整版本显示所有店铺)
    web_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>销售日报报告 - {report_date}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 2em; max-width: 900px; margin-left:auto; margin-right:auto; text-align: left; font-size: 10.5pt; }}
        h1, h2, h3 {{ color: #0056b3; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; font-size: 14pt; font-weight: bold; }}
        pre, code {{ background: #f3f3f3; padding: 0.5em; border-radius: 4px; white-space: pre-wrap; word-break: break-all; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; }}
        .section {{ margin-bottom: 2em; text-align: left; }}
        .highlight {{ color: #d63384; font-weight: bold; }}
        .emoji {{ font-size: 1.2em; }}
        details {{ margin-bottom: 1em; }}
        summary {{ cursor: pointer; font-weight: bold; }}
        @media (max-width: 600px) {{ body {{ padding: 0.5em; font-size: 10.5pt; }} h1 {{ font-size: 14pt; }} }}
        .left-align {{ text-align: left !important; }}
        .overview-box {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196f3; }}
    </style>
</head>
<body>
    <h1>销售日报报告（{report_date}）</h1>
    
    <!-- 整体销售概况（置顶） -->
    <div class="overview-box">
        <h2>💰 【整体销售概况】</h2>
        <div style="font-size: 12pt; line-height: 1.6;">
            <div>├─ 总销售额: ¥{total_amount:,}，前一天 ¥{prev_total_amount:,}，环比 {calculate_ratio(total_amount, prev_total_amount)}</div>
            <div>├─ 总销量: {total_qty:,}件，前一天 {prev_total_qty:,}件，环比 {calculate_ratio(total_qty, prev_total_qty)}</div>
            <div>├─ 单价: ¥{total_price:,}，前一天 ¥{int(prev_total_amount / prev_total_qty) if prev_total_qty else 0:,}，变化 {calculate_ratio(total_price, int(prev_total_amount / prev_total_qty) if prev_total_qty else 0)}</div>
        </div>
    </div>
    
    <div class="section left-align">
        <!-- 品类变化趋势 -->
        <h2>🔍 【品类变化趋势】</h2>
        {generate_category_trend_html(category_data, prev_category_data, category_icons, shop_summary, prev_shop_summary, df_erp, df_prev, amount_col, qty_col, MODEL_COL)}
        
        <!-- 品类销售排行榜 -->
        <h2>【品类销售排行榜】</h2>
        {generate_category_ranking_html(category_data, df_erp, prev_category_data, amount_col, qty_col, CATEGORY_COL, MODEL_COL, category_icons)}
        
        <!-- 渠道销售分析 -->
        <h2>📊 【渠道销售分析】</h2>
        {generate_channel_ranking_html(channel_summary, df_erp, prev_channel_summary, amount_col, qty_col, SHOP_COL)}
        
        <!-- TOP店铺排行 -->
        <h2>【TOP店铺排行】</h2>
        {generate_shop_ranking_html(shop_summary, df_erp, prev_shop_summary, amount_col, qty_col, MODEL_COL)}
        
        <!-- TOP单品数据 -->
        <h2>【TOP单品数据】</h2>
        {generate_top_product_html(df_erp, amount_col, qty_col, MODEL_COL, CATEGORY_COL, category_icons, top_n=5)}
        
        <!-- 店铺单品数据 -->
        <h2>【店铺单品数据】</h2>
        {generate_shop_product_html(shop_summary, df_erp, amount_col, qty_col, MODEL_COL)}
    </div>
    <footer style="margin-top:2em;color:#888;font-size:0.9em;">自动生成 | Powered by EdgeOne Pages & 企业微信机器人</footer>
</body>
</html>'''

    filename = save_report_to_local(web_content, report_type="overall_daily")
    public_url = None
    if filename:
        with open(filename, 'r', encoding='utf-8') as f:
            html_content = f.read()
        url1 = upload_html_and_get_url(os.path.basename(filename), html_content)
        url2 = None
        if url1:
            import requests
            test_url1 = url1
            test_url2 = url1.replace('/reports/', '/') if '/reports/' in url1 else None
            try:
                resp1 = requests.get(test_url1, timeout=5)
                if resp1.status_code == 200:
                    public_url = test_url1
                elif test_url2:
                    resp2 = requests.get(test_url2, timeout=5)
                    if resp2.status_code == 200:
                        public_url = test_url2
            except Exception:
                public_url = url1
        else:
            public_url = None

    # 微信推送内容严格只用三段手动拼接，所有推送函数、异常、分段推送等只用 wechat_content
    wechat_content = f"""📊 {yesterday_str} 每日销售分析报告\n💰 【整体销售概况】\n├─ 总销售额: ¥{total_amount:,}\n├─ 总销量: {total_qty:,}件  \n├─ 单价: ¥{total_price:,}\n└─ 环比: {calculate_ratio(total_amount, prev_total_amount)}\n\n📊 【渠道销售分析】\n"""
    channel_summary = channel_summary.sort_values(amount_col, ascending=False)
    for idx, row in enumerate(channel_summary.iterrows(), 1):
        _, row_data = row
        channel = row_data['渠道']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        # 修复：正确获取前一天该渠道数据
        prev_amount = 0
        if prev_channel_summary is not None:
            prev_channel_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
            if not prev_channel_data.empty:
                prev_amount = int(prev_channel_data.iloc[0][amount_col])
        wechat_content += f"🏪 {idx}. {channel}渠道: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) | {qty:,}件 | ¥{price:,}/件\n"
    wechat_content += "\n�� 【品类变化趋势】\n"
    # 品类变化趋势排序：按本期销售额从高到低
    category_trend_sorted = sorted(category_changes, key=lambda x: x[3], reverse=True)
    for category, growth_rate, prev_amount, current_amount in category_trend_sorted:
        emoji = category_icons.get(category, '📦')
        if growth_rate > 0:
            wechat_content += f"   {emoji} {category}: 📈 +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"
        else:
            wechat_content += f"   {emoji} {category}: 📉 {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"
    # 拼接Web链接，无论检测是否成功都强制拼接
    if not public_url:
        public_url = f"https://edge.haierht.cn/reports/overall_daily_{yesterday_str}.html"
    wechat_content += f"\n🌐 查看完整Web页面: {public_url}"
    # 所有推送、异常、分段推送等只用 wechat_content
    # 微信推送内容分段发送，Web链接单独一段
    MAX_MSG_LEN = 1000
    segments = []
    content = wechat_content.strip()
    while len(content) > MAX_MSG_LEN:
        split_pos = content.rfind('\n', 0, MAX_MSG_LEN)
        if split_pos == -1:
            split_pos = MAX_MSG_LEN
        segments.append(content[:split_pos].strip())
        content = content[split_pos:].strip()
    if content:
        segments.append(content)
    # 最后一段强制只发 Web 链接
    if segments and '🌐 查看完整Web页面:' not in segments[-1]:
        segments.append(f"🌐 查看完整Web页面: {public_url}")
    for seg in segments:
        _send_single_message(seg)
        time.sleep(1)

    if public_url:
        print(f"✅ Web报告已发布: {public_url}")
    else:
        print("⚠️ Web报告未能成功发布")
    print("✅ 微信版本发送完成（精简版）！")
    print("🌐 Web完整版本已发布！")

except Exception as e:
    error_msg = f"""❌ 执行过程中发生错误: {str(e)}
    {traceback.format_exc()}"""
    print(error_msg)
    send_wecomchan_segment(error_msg)

finally:
    # 计算总耗时
    total_time = datetime.now() - total_start_time
    print(f"\n⏱️ 总执行时间: {total_time}")
    logging.info(f"脚本执行完成，耗时: {total_time}")

