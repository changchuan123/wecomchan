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
from pymysql.cursors import DictCursor
import warnings
warnings.filterwarnings('ignore')

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
# 完全禁用logging，使用print替代
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler()
#     ]
# )

# 创建一个简单的logging替代函数
class SimpleLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
        return True
    def error(self, msg):
        print(f"ERROR: {msg}")
        return True
    def warning(self, msg):
        print(f"WARNING: {msg}")
        return True

# 替换logging模块
logging = SimpleLogger()

# 开始计时
total_start_time = datetime.now()

print("🚀 影刀RPA - 进阶销售分析系统（直接执行版本）")
print("==================================================")

def normalize_date_format(date_str):
    """
    统一日期格式处理，兼容各种日期格式
    支持格式：
    - YYYY-MM-DD HH:MM:SS
    - YYYY-MM-DD
    - MM-DD
    - 7.2号, 7.2日等特殊格式
    - 时间戳格式
    - 其他常见格式
    """
    if pd.isna(date_str) or date_str is None:
        return None
    
    date_str = str(date_str).strip()
    
    # 处理空字符串
    if not date_str or date_str == '':
        return None
    
    # 处理7.2号格式 (7.2, 7.2号, 7.2日等)
    if re.match(r'^\d+\.\d+[号日]?$', date_str):
        # 提取月份和日期
        parts = date_str.replace('号', '').replace('日', '').split('.')
        if len(parts) == 2:
            month = int(parts[0])
            day = int(parts[1])
            # 假设是当前年份
            current_year = datetime.now().year
            try:
                return datetime(current_year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                # 如果日期无效，返回None
                return None
    
    # 处理时间戳格式
    if re.match(r'^\d{10,13}$', date_str):
        try:
            timestamp = int(date_str)
            # 如果是13位时间戳（毫秒），转换为10位（秒）
            if len(date_str) == 13:
                timestamp = timestamp // 1000
            # 使用UTC时间戳转换
            return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
        except (ValueError, OSError):
            pass
    
    # 处理YYYY-MM-DD HH:MM:SS格式
    if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
        try:
            # 提取日期部分，忽略时间部分
            date_part = date_str.split(' ')[0]
            parsed_date = pd.to_datetime(date_part, format='%Y-%m-%d')
            if pd.notna(parsed_date):
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
    
    # 处理MM-DD格式
    if re.match(r'^\d{2}-\d{2}$', date_str):
        current_year = datetime.now().year
        try:
            month, day = map(int, date_str.split('-'))
            return datetime(current_year, month, day).strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    # 处理DD/MM/YYYY格式
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        try:
            parsed_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            if pd.notna(parsed_date):
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
    
    # 处理YYYY/MM/DD格式
    if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_str):
        try:
            parsed_date = pd.to_datetime(date_str, format='%Y/%m/%d')
            if pd.notna(parsed_date):
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
    
    # 处理MM/DD/YYYY格式
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        try:
            parsed_date = pd.to_datetime(date_str, format='%m/%d/%Y')
            if pd.notna(parsed_date):
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
    
    # 处理YYYYMMDD格式
    if re.match(r'^\d{8}$', date_str):
        try:
            # 检查是否为有效的日期格式
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            # 验证日期有效性
            datetime(year, month, day)
            return f'{year:04d}-{month:02d}-{day:02d}'
        except ValueError:
            # 如果标准格式失败，尝试其他可能的格式
            try:
                # 尝试DDMMYYYY格式
                day = int(date_str[:2])
                month = int(date_str[2:4])
                year = int(date_str[4:8])
                datetime(year, month, day)
                return f'{year:04d}-{month:02d}-{day:02d}'
            except ValueError:
                pass
    
    # 处理MMDD格式（假设当前年份）
    if re.match(r'^\d{4}$', date_str) and len(date_str) == 4:
        current_year = datetime.now().year
        try:
            month = int(date_str[:2])
            day = int(date_str[2:])
            return datetime(current_year, month, day).strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    # 尝试标准格式解析（最后手段）
    try:
        # 使用pandas的灵活解析
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(parsed_date):
            return parsed_date.strftime('%Y-%m-%d')
    except:
        pass
    
    # 如果所有方法都失败，返回None
    return None

# ========== URL验证函数 ==========
def _simple_verify_url(public_url):
    """快速验证URL是否可访问（优化为1秒内完成）"""
    print(f"🔍 正在验证URL: {public_url}")
    
    # 快速验证，最多重试2次
    for attempt in range(2):
        try:
            time.sleep(0.2)  # 减少等待时间
            response = requests.head(public_url, timeout=0.5)  # 减少超时时间
            
            if response.status_code == 200:
                print(f"✅ URL验证成功，文件可正常访问: {public_url}")
                return public_url
            elif response.status_code == 404:
                print(f"⚠️ 第{attempt+1}次验证失败，文件不存在 (404)")
            else:
                print(f"⚠️ 第{attempt+1}次验证失败，状态码: {response.status_code}")
                
        except Exception as verify_e:
            print(f"⚠️ 第{attempt+1}次验证异常: {verify_e}")
    
    print(f"❌ URL验证失败，经过2次重试仍无法访问，直接返回URL")
    return public_url  # 即使验证失败也返回URL，避免阻塞



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

def save_report_to_local(content, report_type="overall_weekly"):
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{report_type}_{report_date.replace('至', '_to_')}.html"
    # 新增：标准HTML头部，确保UTF-8编码，防止Web报告乱码
    html_template = f'''

        <!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>销售月报报告 - {report_date}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 0.5em; max-width: 900px; margin-left:auto; margin-right:auto; text-align: left; font-size: 10.5pt; }}
        h1, h2, h3 {{ color: #0056b3; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; font-size: 14pt; font-weight: bold; }}
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
    return f"http://212.64.57.87:5002/reports/latest_report.html"

def _send_single_message(message):
    """发送单条消息到企业微信"""
    # 服务器列表，只使用远程服务器
    servers = [
        "http://212.64.57.87:5001/send"
    ]
    
    token = "wecomchan_token"
    data = {
        "msg": message,
        "token": token,
        "to_user": "weicungang"
    }
    
    max_retries = 5
    retry_delay = 3
    
    for server_url in servers:
        print(f"🔗 尝试连接服务器: {server_url}")
        
        for attempt in range(max_retries):
            try:
                response = requests.post(server_url, json=data, timeout=0.8)
                print(f"📤 发送结果: {response.text[:100]}...")
                
                if "errcode" in response.text and "0" in response.text:
                    print(f"✅ 发送成功 (服务器: {server_url}, 尝试 {attempt + 1}/{max_retries})")
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
                        print(f"❌ 服务器 {server_url} 发送失败，已重试{max_retries}次")
                        break
                else:
                    print(f"⚠️ 发送返回异常 (尝试 {attempt + 1}/{max_retries}): {response.text}")
                    if attempt < max_retries - 1:
                        print(f"⏳ {retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                    else:
                        print(f"❌ 服务器 {server_url} 发送失败，已重试{max_retries}次")
                        break
            except requests.exceptions.ConnectTimeout:
                print(f"❌ 连接超时 (服务器: {server_url}, 尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 服务器 {server_url} 发送失败: 连接超时，已重试{max_retries}次")
                    break
            except requests.exceptions.Timeout:
                print(f"❌ 请求超时 (服务器: {server_url}, 尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 服务器 {server_url} 发送失败: 请求超时，已重试{max_retries}次")
                    break
            except Exception as e:
                print(f"❌ 发送异常 (服务器: {server_url}, 尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 服务器 {server_url} 发送失败: {e}，已重试{max_retries}次")
                    break
        
        # 如果当前服务器失败，尝试下一个服务器
        if server_url != servers[-1]:
            print(f"🔄 切换到下一个服务器...")
            retry_delay = 3  # 重置重试延迟
    
    print("❌ 所有服务器都无法连接")
    return False

def send_failure_report_to_admin(script_name, error_details):
    """发送失败报告给管理员"""
    failure_msg = f"""🚨 发送失败报告

📋 脚本名称: {script_name}
⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ 失败原因: {error_details}

请检查网络连接和服务器状态。"""
    
    admin_data = {"msg": failure_msg, "token": "wecomchan_token", "to_user": "weicungang"}
    
    # 只使用远程服务器
    servers = [
        "http://212.64.57.87:5001/send"
    ]
    
    for server_url in servers:
        try:
            print(f"🔗 尝试发送失败报告到: {server_url}")
            resp = requests.post(server_url, json=admin_data, timeout=0.8)
            print(f"📤 失败报告发送结果: {resp.text[:100]}...")
            if "errcode" in resp.text and "0" in resp.text:
                print("✅ 失败报告发送成功")
                return True
        except Exception as e:
            print(f"❌ 失败报告发送异常 (服务器: {server_url}): {e}")
    
    print("❌ 所有服务器都无法发送失败报告")
    return False

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
    """生成单个HTML报告并部署到EdgeOne Pages"""
    try:
        print(f"\n🌐 正在生成销售报告: {filename}")
        
        # 使用MCP EdgeOne Pages部署
        try:
            # 直接使用MCP部署HTML内容
            public_url = mcp_edgeone-pages-mcp_deploy_html(html_content)
            if public_url:
                print(f"✅ 报告已成功部署: {public_url}")
                return public_url
            else:
                print("❌ MCP部署失败")
                return None
        except Exception as mcp_error:
            print(f"❌ MCP部署异常: {mcp_error}")
            return None
            
    except Exception as e:
        print(f"❌ 生成HTML报告异常: {e}")
        return None

def deploy_to_edgeone():
    """简化部署逻辑，直接返回True让脚本继续执行"""
    return True

# ========== 数据库配置 ==========
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

# ========== 分销数据获取函数 ==========
def get_fenxiao_data(start_date, end_date=None):
    """从HT_fenxiao表获取分销数据 - 优化为批量查询"""
    max_retries = 3
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
            )
            logging.info(f"✅ 数据库连接成功 (尝试 {attempt+1}/{max_retries})")
            break
        except Exception as e:
            logging.error(f"❌ 数据库连接失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logging.info(f"⏳ 等待5秒后重试...")
                time.sleep(5)
            else:
                logging.error("❌ 数据库连接失败，已达到最大重试次数")
                return pd.DataFrame()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        # 使用fenxiaochanpin表进行商品匹配（已确认存在数据）
        cursor = conn.cursor()
        
        # 获取HT_fenxiao表结构
        cursor.execute("DESCRIBE HT_fenxiao")
        columns = [row[0] for row in cursor.fetchall()]
        logging.info(f"📊 HT_fenxiao表字段: {columns}")
        
        # 查找可能的字段名
        amount_fields = [col for col in columns if '金额' in col or '实付' in col or '支付' in col]
        shop_fields = [col for col in columns if '店铺' in col or '商店' in col]
        status_fields = [col for col in columns if '状态' in col or '订单' in col]
        time_fields = [col for col in columns if '时间' in col or '支付' in col]
        product_fields = [col for col in columns if '产品' in col or '名称' in col]
        qty_fields = [col for col in columns if '数量' in col or '采购数量' in col]
        
        # 选择最合适的字段名
        amount_col = '用户实际支付总额' if '用户实际支付总额' in columns else (amount_fields[0] if amount_fields else '用户实际支付金额')
        shop_col = '分销商店铺名称' if '分销商店铺名称' in columns else (shop_fields[0] if shop_fields else '分销商店铺名称')
        status_col = '订单状态' if '订单状态' in columns else (status_fields[0] if status_fields else '订单状态')
        
        # 使用订单创建时间作为时间字段，因为采购单支付时间字段为空
        if '订单创建时间' in columns:
            time_col = '订单创建时间'
            logging.info("📊 使用订单创建时间作为时间字段")
        else:
            time_col = time_fields[0] if time_fields else '订单创建时间'
            logging.info(f"📊 使用默认时间字段: {time_col}")
            
        product_col = '产品名称' if '产品名称' in columns else (product_fields[0] if product_fields else '产品名称')
        qty_col = '采购数量' if '采购数量' in columns else (qty_fields[0] if qty_fields else '采购数量')
        
        # 构建时间过滤条件 - 支持日期范围批量查询
        if end_date:
            # 日期范围查询 - 增强兼容性
            # 支持多种日期格式的数据库字段
            time_condition = f"({time_col} >= '{start_date}' AND {time_col} < '{end_date} 23:59:59')"
            # 同时支持DATE()函数处理
            time_condition += f" OR (DATE({time_col}) >= '{start_date}' AND DATE({time_col}) <= '{end_date}')"
        else:
            # 兼容原有单日查询
            if '至' in start_date:
                start_dt, end_dt = start_date.split('至')
                time_condition = f"({time_col} >= '{start_dt}' AND {time_col} < '{end_dt} 23:59:59')"
                time_condition += f" OR (DATE({time_col}) >= '{start_dt}' AND DATE({time_col}) <= '{end_dt}')"
            else:
                time_condition = f"DATE({time_col}) = '{start_date}' OR {time_col} LIKE '{start_date}%'"
        
        # 查询分销数据，使用动态字段名，确保订单状态过滤生效
        # 只过滤掉：未付款、已取消、已退货
        sql = f"""
        SELECT 
            {shop_col} as 店铺,
            {status_col} as 订单状态,
            {amount_col} as 分摊后总价,
            {time_col} as 交易时间,
            {product_col} as 规格名称,
            {product_col} as 货品名称,
            {qty_col} as 实发数量,
            '分销' as 数据来源
        FROM HT_fenxiao 
        WHERE ({time_condition})
        AND {status_col} NOT IN ('已取消', '未付款', '已退货')
        """
        
        logging.info(f"📊 执行批量分销数据查询: {sql}")
        
        df_fenxiao = pd.read_sql(sql, conn)
        
        if not df_fenxiao.empty:
            logging.info(f"📊 分销数据获取成功，共{len(df_fenxiao)}行（已过滤无效订单状态）")
            
            # 显示原始日期格式样本
            sample_dates = df_fenxiao['交易时间'].head(5).tolist()
            logging.info(f"📊 原始日期格式样本: {sample_dates}")
            
            # 增强的日期格式处理
            df_fenxiao['交易时间'] = df_fenxiao['交易时间'].apply(normalize_date_format)
            
            # 统计日期处理结果
            valid_dates = df_fenxiao['交易时间'].notna().sum()
            total_dates = len(df_fenxiao)
            logging.info(f"📊 日期格式处理结果: 有效日期 {valid_dates}/{total_dates}")
            
            # 移除无效日期的行
            df_fenxiao = df_fenxiao.dropna(subset=['交易时间'])
            logging.info(f"📊 移除无效日期后分销数据行数: {len(df_fenxiao)}")
            
            if not df_fenxiao.empty:
                # 显示处理后的日期范围
                df_fenxiao['交易时间'] = pd.to_datetime(df_fenxiao['交易时间'])
                min_date = df_fenxiao['交易时间'].min()
                max_date = df_fenxiao['交易时间'].max()
                logging.info(f"📊 分销数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
            
            # 过滤虚拟赠品
            before_filter_count = len(df_fenxiao)
            virtual_gift_keywords = ['虚拟赠品', '虚拟', '赠品', '测试商品', '不发货']
            virtual_mask = df_fenxiao['规格名称'].astype(str).str.contains('|'.join(virtual_gift_keywords), case=False, na=False)
            df_fenxiao = df_fenxiao[~virtual_mask]
            after_filter_count = len(df_fenxiao)
            
            if before_filter_count > after_filter_count:
                logging.info(f"📊 过滤虚拟赠品: 过滤掉 {before_filter_count - after_filter_count} 条记录")
            
            # 显示订单状态分布，确认过滤生效
            status_counts = df_fenxiao['订单状态'].value_counts()
            logging.info(f"📊 过滤后订单状态分布:")
            for status, count in status_counts.items():
                logging.info(f"   {status}: {count}条")
            
            # 尝试从fenxiaochanpin表匹配规格名称和货品名称（使用缓存优化）
            logging.info("🔄 尝试从fenxiaochanpin表匹配规格名称和货品名称...")
            
            # 获取所有唯一的产品名称
            unique_products = df_fenxiao['规格名称'].unique()
            logging.info(f"📊 需要匹配的唯一产品数量: {len(unique_products)}")
            
            # 创建最终的产品映射缓存
            final_product_mapping = {}
            
            # 批量处理所有唯一产品
            for product_name in unique_products:
                if not isinstance(product_name, str):
                    continue
                    
                # 第一步：从fenxiaochanpin表查询
                match_sql = f"SELECT 规格名称, 货品名称 FROM fenxiaochanpin WHERE 产品名称 = %s LIMIT 1"
                cursor.execute(match_sql, (product_name,))
                result = cursor.fetchone()
                
                if result:
                    final_product_mapping[product_name] = {
                        '规格名称': result[0],
                        '货品名称': result[1]
                    }
                else:
                    # 第二步：使用模糊匹配
                    match_sql = f"SELECT 规格名称, 货品名称 FROM fenxiaochanpin WHERE 产品名称 LIKE %s LIMIT 1"
                    cursor.execute(match_sql, (f"%{product_name}%",))
                    result = cursor.fetchone()
                    
                    if result:
                        final_product_mapping[product_name] = {
                            '规格名称': result[0],
                            '货品名称': result[1]
                        }
                    else:
                        # 第三步：使用分类匹配
                        categorized_name = categorize_product_for_fenxiao(product_name)
                        if categorized_name != product_name:
                            match_sql = f"SELECT 规格名称, 货品名称 FROM fenxiaochanpin WHERE 产品名称 = %s LIMIT 1"
                            cursor.execute(match_sql, (categorized_name,))
                            result = cursor.fetchone()
                            
                            if result:
                                final_product_mapping[product_name] = {
                                    '规格名称': result[0],
                                    '货品名称': result[1]
                                }
                            else:
                                # 第四步：强制分类匹配
                                forced_name = force_categorize_product(product_name)
                                if forced_name != product_name:
                                    match_sql = f"SELECT 规格名称, 货品名称 FROM fenxiaochanpin WHERE 产品名称 = %s LIMIT 1"
                                    cursor.execute(match_sql, (forced_name,))
                                    result = cursor.fetchone()
                                    
                                    if result:
                                        final_product_mapping[product_name] = {
                                            '规格名称': result[0],
                                            '货品名称': result[1]
                                        }
                                    else:
                                        # 最后：使用原始名称
                                        final_product_mapping[product_name] = {
                                            '规格名称': product_name,
                                            '货品名称': product_name
                                        }
                                else:
                                    final_product_mapping[product_name] = {
                                        '规格名称': product_name,
                                        '货品名称': product_name
                                    }
                        else:
                            final_product_mapping[product_name] = {
                                '规格名称': product_name,
                                '货品名称': product_name
                            }
            
            # 应用映射
            matched_count = 0
            for idx, row in df_fenxiao.iterrows():
                product_name = row['规格名称']
                if product_name in final_product_mapping:
                    df_fenxiao.at[idx, '规格名称'] = final_product_mapping[product_name]['规格名称']
                    df_fenxiao.at[idx, '货品名称'] = final_product_mapping[product_name]['货品名称']
                    matched_count += 1
            
            logging.info(f"📊 产品名称匹配完成: 成功匹配 {matched_count}/{len(df_fenxiao)} 条记录")
            
            # 识别天猫分销
            df_fenxiao = identify_tianmao_fenxiao(df_fenxiao)
            
            return df_fenxiao
        else:
            logging.warning("⚠️ 分销数据为空")
            return pd.DataFrame()
            
    except Exception as e:
        logging.error(f"❌ 分销数据获取失败: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
        return pd.DataFrame()

def add_jingdong_prefix(shop_name):
                if not isinstance(shop_name, str):
                    return shop_name
                
                # 如果已经有"京东-"前缀，直接返回
                if shop_name.startswith('京东-'):
                    return shop_name
                
                # 统一添加"京东-"前缀
                return f"京东-{shop_name}"
            


def categorize_product_for_fenxiao(product_name):
    """从产品名称中识别品类，用于分销数据"""
    if not isinstance(product_name, str):
        return "其他"
    
    product_name_lower = product_name.lower()
    
    # 品类关键词映射
    category_keywords = {
        "家用空调": ["空调", "挂机", "柜机", "中央空调", "分体式"],
        "商用空调": ["商用", "商用空调", "多联机", "风管机"],
        "冰箱": ["冰箱", "冷柜", "冰柜", "冷藏", "冷冻"],
        "洗衣机": ["洗衣机", "洗烘一体", "滚筒", "波轮"],
        "洗碗机": ["洗碗机"],  # 洗碗机独立为一个品类
        "热水器": ["热水器", "电热水器", "燃气热水器", "多能源热水器"],
        "净水": ["净水", "净水器", "净水机", "过滤器"],
        "采暖": ["采暖", "暖气", "地暖", "壁挂炉"],
        "厨电": ["消毒柜", "燃气灶", "油烟机", "厨电"],  # 移除洗碗机
        "干衣机": ["干衣机", "烘干机"],
        "除湿机": ["除湿机", "抽湿机"],
        "新风": ["新风", "新风机", "新风系统"],
        "其他": []
    }
    
    # 遍历品类关键词进行匹配
    for category, keywords in category_keywords.items():
        if any(keyword in product_name_lower for keyword in keywords):
            return category
    
    return "其他"

def force_categorize_product(product_name):
    """强制通过产品名称关键词匹配到八个预定义品类之一"""
    if not product_name:
        return "冰箱"  # 默认返回冰箱
    
    product_name = str(product_name).lower()
    
    # 洗碗机独立为一个品类
    if any(keyword in product_name for keyword in ['洗碗机']):
        return "洗碗机"
    
    # 冰箱
    if any(keyword in product_name for keyword in ['冰箱', '冰柜', '冷藏', '冷冻']):
        return "冰箱"
    
    # 洗衣机
    if any(keyword in product_name for keyword in ['洗衣机', '洗烘', '干衣机']):
        return "洗衣机"
    
    # 冷柜
    if any(keyword in product_name for keyword in ['冷柜', '展示柜', '商用冷柜']):
        return "冷柜"
    
    # 家用空调
    if any(keyword in product_name for keyword in ['空调', '挂机', '柜机', '变频', '定频']) and not any(keyword in product_name for keyword in ['商用', '中央', '多联']):
        return "家用空调"
    
    # 商空空调
    if any(keyword in product_name for keyword in ['商用空调', '中央空调', '多联机', '风管机', '天花机']):
        return "商空空调"
    
    # 厨电（移除洗碗机，增加蒸箱、烤箱）
    if any(keyword in product_name for keyword in ['消毒柜', '燃气灶', '油烟机', '蒸箱', '烤箱']):
        return "厨电"
    
    # 热水器
    if any(keyword in product_name for keyword in ['热水器', '燃气热水器', '电热水器']):
        return "热水器"
    
    # 如果都不匹配，根据产品名称中的关键词进行智能判断
    # 海尔洗碗机的例子：包含"海尔"、"嵌入式"、"洗"、"消"、"烘干"等关键词
    if any(keyword in product_name for keyword in ['嵌入式', '洗', '消', '烘干', '分区洗', '洗消烘']):
        return "洗碗机"
    
    # 默认返回冰箱（八个品类中的第一个）
    return "冰箱"

def identify_tianmao_fenxiao(df):
    """从原有数据中识别天猫分销数据（仓库字段为'菜鸟仓自流转'）"""
    try:
        # 查找仓库相关字段
        warehouse_cols = [col for col in df.columns if '仓库' in col or 'warehouse' in col.lower()]
        
        if not warehouse_cols:
            logging.warning("⚠️ 未找到仓库字段，无法识别天猫分销数据")
            logging.info(f"📊 可用字段: {df.columns.tolist()}")
            return None
        
        warehouse_col = warehouse_cols[0]
        logging.info(f"🔍 使用仓库字段: {warehouse_col}")
        
        # 显示仓库字段的唯一值，帮助调试
        unique_warehouses = df[warehouse_col].dropna().unique()
        logging.info(f"📊 仓库字段唯一值: {unique_warehouses[:10]}")  # 只显示前10个
        
        # 筛选天猫渠道且仓库为"菜鸟仓自流转"的数据
        tianmao_mask = df[SHOP_COL].astype(str).str.contains('天猫|淘宝', na=False)
        warehouse_mask = df[warehouse_col].astype(str) == '菜鸟仓自流转'
        
        logging.info(f"📊 天猫渠道数据: {tianmao_mask.sum()}行")
        logging.info(f"📊 菜鸟仓自流转数据: {warehouse_mask.sum()}行")
        
        tianmao_fenxiao = df[tianmao_mask & warehouse_mask].copy()
        
        if not tianmao_fenxiao.empty:
            # 添加分销标识
            tianmao_fenxiao['数据来源'] = '分销'
            # 使用原有的货品名称进行品类识别
            tianmao_fenxiao[CATEGORY_COL] = tianmao_fenxiao[CATEGORY_COL].apply(categorize_product_for_fenxiao)
            logging.info(f"📊 识别到天猫分销数据: {len(tianmao_fenxiao)}行")
            logging.info(f"📊 天猫分销数据示例:")
            for i, row in tianmao_fenxiao.head(3).iterrows():
                logging.info(f"   店铺: {row[SHOP_COL]}, 仓库: {row[warehouse_col]}, 金额: {row[AMOUNT_COL]}, 品类: {row.get(CATEGORY_COL, 'N/A')}")
            return tianmao_fenxiao
        else:
            logging.info("📊 未识别到天猫分销数据")
            return None
            
    except Exception as e:
        logging.error(f"❌ 识别天猫分销数据失败: {e}")
        logging.error(traceback.format_exc())
        return None

# 步骤2: 读取ERP销售数据
logging.info("🚀 开始执行销售数据分析...")
logging.info(f"📊 读取数据库Daysales表数据")
print("🔍 DEBUG: 日志输出完成，开始执行后续代码...")
print("🔍 DEBUG: 测试print语句1")
print("🔍 DEBUG: 测试print语句2")
print("🔍 DEBUG: 测试print语句3")

# 修改：基于T-1天（昨天）计算月报数据
print("📅 开始计算日期范围...")
today = datetime.now()
yesterday = today - timedelta(days=1)  # T-1天
print(f"📅 今天日期: {today}")
print(f"📅 T-1天日期: {yesterday}")

# 基于T-1天获取所在月份的整月数据
target_month_start = yesterday.replace(day=1)
# 获取T-1天所在月份的最后一天
if yesterday.month == 12:
    next_month = yesterday.replace(year=yesterday.year + 1, month=1, day=1)
else:
    next_month = yesterday.replace(month=yesterday.month + 1, day=1)
month_end = next_month - timedelta(days=1)

print(f"📅 月度开始日期: {target_month_start}")
print(f"📅 月度结束日期: {month_end}")
this_month_start_str = target_month_start.strftime('%Y-%m-%d')
month_end_str = month_end.strftime('%Y-%m-%d')
report_date = f"{this_month_start_str}至{month_end_str}"
print(f"📅 报告日期范围: {report_date}")

# 获取月份信息用于标题
current_month = target_month_start.month
current_month_name = f"{current_month}月份"
print(f"📅 当前月份: {current_month_name}")
print("✅ 日期计算完成")

# 检查数据库是否有昨天的数据
def check_data_availability(date_str):
    """检查指定日期是否有数据"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        df_check = pd.read_sql(f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 LIKE '{date_str}%'", conn)
        conn.close()
        count = df_check.iloc[0]['count']
        return count > 0, count
    except Exception as e:
        print(f"❌ 检查数据可用性失败: {e}")
        return False, 0

# 检查本月数据是否可用
def check_month_data_availability(start_date, end_date):
    """检查指定月度周期是否有数据"""
    try:
        print(f"🔗 正在连接数据库...")
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=30, read_timeout=30, write_timeout=30
        )
        print(f"✅ 数据库连接成功")
        query = f"SELECT COUNT(*) as count FROM Daysales WHERE 交易时间 >= '{start_date}' AND 交易时间 < '{end_date} 23:59:59'"
        print(f"📊 执行查询: {query}")
        df_check = pd.read_sql(query, conn)
        print(f"✅ 查询执行完成")
        conn.close()
        print(f"🔒 数据库连接已关闭")
        count = df_check.iloc[0]['count']
        print(f"📈 查询结果: {count} 条记录")
        return count > 0, count
    except Exception as e:
        print(f"❌ 检查数据可用性失败: {e}")
        return False, 0

print(f"🔍 开始检查月度数据可用性: {this_month_start_str} 至 {month_end_str}")
has_month_data, month_count = check_month_data_availability(this_month_start_str, month_end_str)
print(f"✅ 月度数据检查完成: has_data={has_month_data}, count={month_count}")

if not has_month_data:
    # 发送提醒到指定webhook
    alert_msg = f"""🚨 数据缺失提醒

📅 月度周期: {this_month_start_str} 至 {month_end_str}
❌ 状态: 数据库中没有找到该月度周期的销售数据
📊 记录数: {month_count}
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
        response = requests.post(webhook_url, json=alert_data, timeout=0.8)
        print(f"📤 数据缺失提醒发送结果: {response.text}")
        
        # 同时发送到原有webhook
        _send_single_message(alert_msg)
        
    except Exception as e:
        print(f"❌ 发送数据缺失提醒失败: {e}")
    
    print(f"❌ 数据库中没有找到 {this_month_start_str} 至 {month_end_str} 的数据，脚本停止执行")
    sys.exit(1)

print(f"✅ 数据库中找到 {this_month_start_str} 至 {month_end_str} 的数据，共 {month_count} 条记录")

try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=30, read_timeout=30, write_timeout=30
    )
    # 统一使用月度完整数据范围
    df_erp = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 >= '{this_month_start_str}' AND 交易时间 < '{month_end_str} 23:59:59'", conn)
    conn.close()
    print(f"📊 ERP数据读取成功，共{len(df_erp)}行")
except Exception as e:
    print(f"❌ 直接连接数据库失败: {e}")
    sys.exit(1)

# 获取本月分销数据 - 优化为批量查询
print("📊 正在获取本月分销数据...")
start_time = datetime.now()
df_fenxiao = get_fenxiao_data(this_month_start_str, month_end_str)
end_time = datetime.now()

# 确保df_fenxiao不为None
if df_fenxiao is None:
    df_fenxiao = pd.DataFrame()
    print("⚠️ 分销数据获取失败，使用空DataFrame")

if not df_fenxiao.empty:
    print(f"📊 分销数据获取成功，共{len(df_fenxiao)}行，耗时{end_time - start_time}")
    # 合并ERP数据和分销数据
    print("🔄 合并ERP数据和分销数据...")
    df_erp = pd.concat([df_erp, df_fenxiao], ignore_index=True)
    print(f"📊 合并后总数据量: {len(df_erp)}行")
else:
    print("⚠️ 未获取到分销数据，仅使用ERP数据")

# 识别天猫分销数据
print("📊 正在识别天猫分销数据...")
df_tianmao_fenxiao = identify_tianmao_fenxiao(df_erp)
if df_tianmao_fenxiao is not None and not df_tianmao_fenxiao.empty:
    print(f"📊 天猫分销数据识别成功，共{len(df_tianmao_fenxiao)}行")
    # 注意：天猫分销数据已经在df_erp中，这里只是标记了数据来源
    # 确保天猫分销数据不重复计入整体数据
    df_erp.loc[df_tianmao_fenxiao.index, '数据来源'] = '分销'
else:
    print("⚠️ 未识别到天猫分销数据")

# 读取上月数据用于环比分析
last_month_start = (target_month_start.replace(day=1) - timedelta(days=1)).replace(day=1)
last_month_end = target_month_start - timedelta(days=1)
last_month_start_str = last_month_start.strftime('%Y-%m-%d')
last_month_end_str = last_month_end.strftime('%Y-%m-%d')

# 获取前一天数据用于"前一天销售"显示
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime('%Y-%m-%d')
print(f"📊 正在获取前一天数据: {yesterday_str}")

# 检查上月数据是否可用
has_prev_data, prev_count = check_month_data_availability(last_month_start_str, last_month_end_str)

if not has_prev_data:
    print(f"⚠️ 数据库中没有找到 {last_month_start_str} 至 {last_month_end_str} 的数据，环比分析将受限")
    df_prev = None
else:
    print(f"✅ 数据库中找到 {last_month_start_str} 至 {last_month_end_str} 的数据，共 {prev_count} 条记录")
    try:

        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=0.8, read_timeout=0.8, write_timeout=0.8
        )
        df_prev = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 >= '{last_month_start_str}' AND 交易时间 < '{last_month_end_str} 23:59:59'", conn)
        conn.close()
        print(f"📊 上月ERP数据读取成功，共{len(df_prev)}行")
        
        # 获取上月的分销数据
        print("📊 正在获取上月分销数据...")
        df_prev_fenxiao_list = []
        current_date = last_month_start
        while current_date <= last_month_end:
            date_str = current_date.strftime('%Y-%m-%d')
            df_day_fenxiao = get_fenxiao_data(date_str)
            if not df_day_fenxiao.empty:
                df_prev_fenxiao_list.append(df_day_fenxiao)
            current_date += timedelta(days=1)
        
        if df_prev_fenxiao_list:
            df_prev_fenxiao = pd.concat(df_prev_fenxiao_list, ignore_index=True)
            print(f"📊 上月分销数据获取成功，共{len(df_prev_fenxiao)}行")
            
            # 合并上月ERP数据和分销数据
            print("🔄 合并上月ERP数据和分销数据...")
            df_prev = pd.concat([df_prev, df_prev_fenxiao], ignore_index=True)
            print(f"📊 上月合并后总数据量: {len(df_prev)}行")
        else:
            print("⚠️ 未获取到上月分销数据，仅使用ERP数据")
            
        # 识别上月天猫分销数据
        print("📊 正在识别上月天猫分销数据...")
        df_prev_tianmao_fenxiao = identify_tianmao_fenxiao(df_prev)
        if df_prev_tianmao_fenxiao is not None and not df_prev_tianmao_fenxiao.empty:
            print(f"📊 上月天猫分销数据识别成功，共{len(df_prev_tianmao_fenxiao)}行")
            # 标记上月天猫分销数据来源
            df_prev.loc[df_prev_tianmao_fenxiao.index, '数据来源'] = '分销'
        else:
            print("⚠️ 未识别到上月天猫分销数据")
            
    except Exception as e:
        print(f"⚠️ 读取上月数据失败: {e}")
        df_prev = None

# 获取前一天数据
df_prev_day = None
try:
    conn = pymysql.connect(
                host=DB_HOST, port=DB_PORT, user=DB_USER,
                password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
                connect_timeout=0.8, read_timeout=0.8, write_timeout=0.8
            )
    df_prev_day = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{yesterday_str}%'", conn)
    conn.close()
    print(f"📊 前一天ERP数据读取成功，共{len(df_prev_day)}行")
    
    # 获取前一天的分销数据
    print("📊 正在获取前一天分销数据...")
    df_prev_day_fenxiao = get_fenxiao_data(yesterday_str)
    if not df_prev_day_fenxiao.empty:
        print(f"📊 前一天分销数据获取成功，共{len(df_prev_day_fenxiao)}行")
        # 合并前一天ERP数据和分销数据
        df_prev_day = pd.concat([df_prev_day, df_prev_day_fenxiao], ignore_index=True)
        print(f"📊 前一天合并后总数据量: {len(df_prev_day)}行")
    else:
        print("⚠️ 未获取到前一天分销数据，仅使用ERP数据")
        
    # 识别前一天天猫分销数据
    print("📊 正在识别前一天天猫分销数据...")
    df_prev_day_tianmao_fenxiao = identify_tianmao_fenxiao(df_prev_day)
    if df_prev_day_tianmao_fenxiao is not None and not df_prev_day_tianmao_fenxiao.empty:
        print(f"📊 前一天天猫分销数据识别成功，共{len(df_prev_day_tianmao_fenxiao)}行")
        # 标记前一天天猫分销数据来源
        df_prev_day.loc[df_prev_day_tianmao_fenxiao.index, '数据来源'] = '分销'
    else:
        print("⚠️ 未识别到前一天天猫分销数据")
        
except Exception as e:
    print(f"⚠️ 读取前一天数据失败: {e}")
    df_prev_day = None

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
    """品类标准化函数，优化热水器品类归类"""
    if pd.isna(name) or name == '':
        return '其他'
    
    name_str = str(name).strip()
    
    # 热水器相关 - 包含采暖、空气能、多能源、电热、燃热等涵盖热水器字样的品类
    if any(keyword in name_str for keyword in ['热水器', '采暖', '空气能', '多能源', '电热', '燃热']):
        return '热水器'
    
    # 其他保持原样
    return name_str

# 2. 在清洗数据后，强制归类
df_erp[CATEGORY_COL] = df_erp[CATEGORY_COL].apply(normalize_category)
if df_prev is not None:
    df_prev[CATEGORY_COL] = df_prev[CATEGORY_COL].apply(normalize_category)

# ========== HTML生成函数 ==========

def generate_category_ranking_html(category_data, df_erp, prev_category_data, amount_col, qty_col, CATEGORY_COL, MODEL_COL, category_icons, df_prev=None, SHOP_COL='店铺'):
    """生成品类销售排行榜HTML，标题后固定两个按钮控制所有品类的店铺/单品排行切换，增加环比数据和底色，屏蔽'其他'品类"""
    html = ''
    
    # 添加全局切换按钮和JavaScript
    html += '''

        
    <div style="margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
        <button onclick="showAllShopRanking()" id="btn_all_shop" style="margin-right: 10px; padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">店铺排行</button>
        <button onclick="showAllProductRanking()" id="btn_all_product" style="padding: 8px 15px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">单品排行</button>

    </div>
    
    <script>
    function showAllShopRanking() {
        // 切换所有品类显示店铺排行
        const shopDivs = document.querySelectorAll('[id^="shop_ranking_"]');
        const productDivs = document.querySelectorAll('[id^="product_ranking_"]');
        
        shopDivs.forEach(div => div.style.display = 'block');
        productDivs.forEach(div => div.style.display = 'none');
        
        // 更新按钮样式
        document.getElementById('btn_all_shop').style.background = '#007bff';
        document.getElementById('btn_all_product').style.background = '#6c757d';
    }
    
    function showAllProductRanking() {
        // 切换所有品类显示单品排行
        const shopDivs = document.querySelectorAll('[id^="shop_ranking_"]');
        const productDivs = document.querySelectorAll('[id^="product_ranking_"]');
        
        shopDivs.forEach(div => div.style.display = 'none');
        productDivs.forEach(div => div.style.display = 'block');
        
        // 更新按钮样式
        document.getElementById('btn_all_shop').style.background = '#6c757d';
        document.getElementById('btn_all_product').style.background = '#007bff';
    }
    </script>
    '''

        
    
    # 过滤掉"其他"品类
    filtered_category_data = category_data[category_data[CATEGORY_COL] != '其他']
    
    for idx, row in enumerate(filtered_category_data.iterrows(), 1):
        _, row_data = row
        cat = row_data[CATEGORY_COL]
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        # 查找昨日该品类数据
        prev_amount = 0
        if prev_category_data is not None:
            prev_cat_data = prev_category_data[prev_category_data[CATEGORY_COL] == cat]
            if not prev_cat_data.empty:
                prev_amount = int(prev_cat_data.iloc[0][amount_col])
        icon = category_icons.get(cat, '📦')
        
        # 生成唯一的ID用于JavaScript切换
        category_id = f"category_{idx}_{cat.replace(' ', '_').replace('/', '_')}"
        
        # 计算该品类的分销数据
        fenxiao_amount = 0
        fenxiao_qty = 0
        if '数据来源' in df_erp.columns:
            fenxiao_data = df_erp[(df_erp[CATEGORY_COL] == cat) & (df_erp['数据来源'] == '分销')]
            if not fenxiao_data.empty:
                fenxiao_amount = int(fenxiao_data[amount_col].sum())
                fenxiao_qty = int(fenxiao_data[qty_col].sum())
        
        # 构建品类标题，包含分销信息
        category_title = f'{icon} {idx}. {cat} ─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) ─ 销量: {qty:,}件 | 单价: ¥{price:,}'
        if fenxiao_amount > 0:
            category_title += f'<br>其中分销: ¥{fenxiao_amount:,}（{fenxiao_qty}件）'
        
        html += f'<details><summary>{category_title}</summary>'
        # 生成店铺排行数据
        shop_summary = df_erp[df_erp[CATEGORY_COL] == cat].groupby(SHOP_COL).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        shop_summary = shop_summary.sort_values(amount_col, ascending=False)
        
        # 生成店铺排行HTML
        shop_html = ''
        if len(shop_summary) > 0:
            shop_html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for shop_idx, (_, shop_row) in enumerate(shop_summary.iterrows(), 1):
                shop = shop_row[SHOP_COL]
                shop_amount = int(shop_row[amount_col])
                shop_qty = int(shop_row[qty_col])
                shop_price = int(shop_amount / shop_qty) if shop_qty else 0
                
                # 查找前一天该店铺在该品类的数据
                prev_shop_amount = 0
                prev_shop_qty = 0
                if df_prev is not None:
                    prev_shop_data = df_prev[(df_prev[SHOP_COL] == shop) & (df_prev[CATEGORY_COL] == cat)]
                    if not prev_shop_data.empty:
                        prev_shop_amount = int(prev_shop_data[amount_col].sum())
                        prev_shop_qty = int(prev_shop_data[qty_col].sum())
                
                # 背景色
                if shop_qty > prev_shop_qty:
                    bg = 'background: #f0fff0;'
                elif shop_qty < prev_shop_qty:
                    bg = 'background: #fff0f0;'
                else:
                    bg = ''
                
                # 计算该店铺的分销数据
                fenxiao_amount = 0
                fenxiao_qty = 0
                prev_fenxiao_amount = 0
                prev_fenxiao_qty = 0
                
                # 本月分销数据
                if '数据来源' in df_erp.columns:
                    fenxiao_data = df_erp[(df_erp[SHOP_COL] == shop) & (df_erp[CATEGORY_COL] == cat) & (df_erp['数据来源'] == '分销')]
                    if not fenxiao_data.empty:
                        fenxiao_amount = int(fenxiao_data[amount_col].sum())
                        fenxiao_qty = int(fenxiao_data[qty_col].sum())
                
                # 上月分销数据
                if df_prev is not None and '数据来源' in df_prev.columns:
                    prev_fenxiao_data = df_prev[(df_prev[SHOP_COL] == shop) & (df_prev[CATEGORY_COL] == cat) & (df_prev['数据来源'] == '分销')]
                    if not prev_fenxiao_data.empty:
                        prev_fenxiao_amount = int(prev_fenxiao_data[amount_col].sum())
                        prev_fenxiao_qty = int(prev_fenxiao_data[qty_col].sum())
                
                shop_html += f'<li style="margin-bottom: 5px; {bg}">🏪 TOP{shop_idx} {shop}<br>本期: ¥{shop_amount:,}（{shop_qty}件），对比期: ¥{prev_shop_amount:,}（{prev_shop_qty}件），环比 {calculate_ratio(shop_qty, prev_shop_qty)}'
                
                # 添加分销数据展示（如果有分销数据）
                if fenxiao_amount > 0 or prev_fenxiao_amount > 0:
                    shop_html += f'<br>其中分销: ¥{fenxiao_amount:,}（{fenxiao_qty}件），对比期 ¥{prev_fenxiao_amount:,}（{prev_fenxiao_qty}件）'
                
                shop_html += '</li>'
            shop_html += '</ul>'
        else:
            shop_html += '<p style="margin-left: 20px; color: #666;">暂无店铺数据</p>'
        
        # 生成单品排行数据（原有逻辑）
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
        
        # 生成单品排行HTML
        product_html = ''
        if all_products:
            product_html += '<ul style="margin-left: 20px; padding-left: 10px;">'
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
                    
                    # 计算该单品的分销数据
                    fenxiao_amount = 0
                    fenxiao_qty = 0
                    prev_fenxiao_amount = 0
                    prev_fenxiao_qty = 0
                    
                    # 当月分销数据
                    if '数据来源' in df_erp.columns:
                        fenxiao_product_data = df_erp[(df_erp[MODEL_COL] == product) & (df_erp['数据来源'] == '分销')]
                        if not fenxiao_product_data.empty:
                            fenxiao_amount = int(fenxiao_product_data[amount_col].sum())
                            fenxiao_qty = int(fenxiao_product_data[qty_col].sum())
                    
                    # 昨日分销数据
                    if df_prev is not None and '数据来源' in df_prev.columns:
                        prev_fenxiao_product_data = df_prev[(df_prev[MODEL_COL] == product) & (df_prev['数据来源'] == '分销')]
                        if not prev_fenxiao_product_data.empty:
                            prev_fenxiao_amount = int(prev_fenxiao_product_data[amount_col].sum())
                            prev_fenxiao_qty = int(prev_fenxiao_product_data[qty_col].sum())
                    
                    # 判断是否100%分销
                    is_100_percent_fenxiao = (fenxiao_amount == cur_amount and cur_amount > 0)
                    
                    # 产品名称显示
                    product_display = f'{product}（分销）' if is_100_percent_fenxiao else product
                    
                    product_html += f'<li style="margin-bottom: 5px; {bg}">🔸 {product_display}<br>本期: ¥{cur_amount:,}（{cur_qty}件），对比期: ¥{prev_amount:,}（{prev_qty}件），环比 {ratio_str}'
                    
                    # 如果不是100%分销但有分销数据，显示分销详情
                    if not is_100_percent_fenxiao and (fenxiao_amount > 0 or prev_fenxiao_amount > 0):
                        product_html += f'<br>其中分销: ¥{fenxiao_amount:,}，对比期 ¥{prev_fenxiao_amount:,}'
                    
                    product_html += '</li>'
            product_html += '</ul>'
        else:
            product_html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        
        # 添加店铺排行和单品排行的容器，默认显示店铺排行
        html += f'''

        
        <div id="shop_ranking_{category_id}" style="display: block;">
            {shop_html}
        </div>
        <div id="product_ranking_{category_id}" style="display: none;">
            {product_html}
        </div>
        '''

        
        
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
        
        # 查找昨日该渠道数据
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
                
                # 查找前一周该店铺数据
                prev_s_amount = 0
                prev_s_qty = 0
                if df_prev is not None:
                    prev_shop_data = df_prev[df_prev[SHOP_COL] == shop]
                    if not prev_shop_data.empty:
                        prev_s_amount = int(prev_shop_data[amount_col].sum())
                        prev_s_qty = int(prev_shop_data[qty_col].sum())
                
                html += f'<li style="margin-bottom: 5px;">🏪 {shop}<br>销售额: ¥{s_amount:,} | 单价: ¥{s_price:,}，环比 {calculate_ratio(s_amount, prev_s_amount)}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无店铺数据</p>'
        
        html += '</details>'
    return html

def generate_shop_ranking_html(shop_summary, df_erp, prev_shop_summary, amount_col, qty_col, MODEL_COL, df_prev=None):
    """生成TOP店铺排行HTML，每个店铺下折叠单品明细，增加环比数据和底色"""
    html = ''
    for idx, row in enumerate(shop_summary.iterrows(), 1):
        _, row_data = row
        shop = row_data['店铺']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        
        # 查找上月该店铺数据
        prev_amount = 0
        if prev_shop_summary is not None:
            prev_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
        
        # 计算该店铺的分销数据
        fenxiao_amount = 0
        fenxiao_qty = 0
        prev_fenxiao_amount = 0
        prev_fenxiao_qty = 0
        
        # 当天分销数据
        if '数据来源' in df_erp.columns:
            fenxiao_data = df_erp[(df_erp['店铺'] == shop) & (df_erp['数据来源'] == '分销')]
            if not fenxiao_data.empty:
                fenxiao_amount = int(fenxiao_data[amount_col].sum())
                fenxiao_qty = int(fenxiao_data[qty_col].sum())
        
        # 昨日分销数据
        if df_prev is not None and '数据来源' in df_prev.columns:
            prev_fenxiao_data = df_prev[(df_prev['店铺'] == shop) & (df_prev['数据来源'] == '分销')]
            if not prev_fenxiao_data.empty:
                prev_fenxiao_amount = int(prev_fenxiao_data[amount_col].sum())
                prev_fenxiao_qty = int(prev_fenxiao_data[qty_col].sum())
        
        # 构建店铺标题，包含分销数据
        shop_title = f'🏪 TOP{idx} {shop} ─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) ─ 销量: {qty:,}件 | 单价: ¥{price:,}'
        if fenxiao_amount > 0:
            shop_title += f'<br>其中分销: ¥{fenxiao_amount:,}（{fenxiao_qty}件）'
        
        html += f'<details><summary>{shop_title}</summary>'
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
        def get_product_amount(product):
            product_data = product_summary[product_summary[MODEL_COL]==product]
            if not product_data.empty:
                return int(product_data[amount_col].values[0])
            return 0
        all_products.sort(key=get_product_amount, reverse=True)
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
                
                # 计算分销数据
                cur_fenxiao_amount = 0
                cur_fenxiao_qty = 0
                prev_fenxiao_amount = 0
                prev_fenxiao_qty = 0
                
                # 本期分销数据
                if '数据来源' in df_erp.columns:
                    cur_fenxiao_data = df_erp[(df_erp['店铺'] == shop) & (df_erp[MODEL_COL] == product) & (df_erp['数据来源'] == '分销')]
                    if not cur_fenxiao_data.empty:
                        cur_fenxiao_amount = int(cur_fenxiao_data[amount_col].sum())
                        cur_fenxiao_qty = int(cur_fenxiao_data[qty_col].sum())
                
                # 对比期分销数据
                if df_prev is not None and '数据来源' in df_prev.columns:
                    prev_fenxiao_data = df_prev[(df_prev['店铺'] == shop) & (df_prev[MODEL_COL] == product) & (df_prev['数据来源'] == '分销')]
                    if not prev_fenxiao_data.empty:
                        prev_fenxiao_amount = int(prev_fenxiao_data[amount_col].sum())
                        prev_fenxiao_qty = int(prev_fenxiao_data[qty_col].sum())
                
                # 获取前一天该商品的销售数据
                prev_day_qty = 0
                prev_day_fenxiao_qty = 0
                if df_prev_day is not None:
                    prev_day_product_data = df_prev_day[(df_prev_day['店铺'] == shop) & (df_prev_day[MODEL_COL] == product)]
                    if not prev_day_product_data.empty:
                        # 总销量（包含分销）
                        prev_day_qty = int(prev_day_product_data[qty_col].sum())
                        # 分销销量
                        if '数据来源' in df_prev_day.columns:
                            prev_day_fenxiao_data = prev_day_product_data[prev_day_product_data['数据来源'] == '分销']
                            if not prev_day_fenxiao_data.empty:
                                prev_day_fenxiao_qty = int(prev_day_fenxiao_data[qty_col].sum())
                
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
                    
                    # 判断是否100%分销
                    is_100_percent_fenxiao = (cur_fenxiao_amount == cur_amount and cur_amount > 0)
                    
                    # 产品名称显示
                    product_display = f'{product}（分销）' if is_100_percent_fenxiao else product
                    
                    html += f'<li style="margin-bottom: 5px; {bg}">🔸 {product_display}<br>'
                    html += f'本期: ¥{cur_amount:,}（{cur_qty}件），对比期: ¥{prev_amount:,}（{prev_qty}件），环比 {ratio_str}'
                    
                    # 如果不是100%分销但有分销数据，显示分销详情
                    if not is_100_percent_fenxiao and cur_fenxiao_amount > 0:
                        fenxiao_ratio_str = calculate_ratio(cur_fenxiao_qty, prev_fenxiao_qty)
                        html += f'<br>其中分销: ¥{cur_fenxiao_amount:,}（{cur_fenxiao_qty}件），对比期: ¥{prev_fenxiao_amount:,}（{prev_fenxiao_qty}件），环比 {fenxiao_ratio_str}'
                    
                    html += '</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        html += '</details>'
    return html

def generate_sales_trend_chart_html_simple(df, amount_col, qty_col, category_col, shop_col, model_col, category_icons):
    """
    生成简化版销售趋势图HTML（移除筛选功能）
    """
    try:
        # 数据预处理
        df_copy = df.copy()
        df_copy[amount_col] = pd.to_numeric(df_copy[amount_col], errors='coerce').fillna(0)
        df_copy[qty_col] = pd.to_numeric(df_copy[qty_col], errors='coerce').fillna(0)
        
        # 确保日期列是datetime类型
        try:
            df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
        except Exception:
            # 如果转换失败，尝试其他方法
            df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], format='%Y-%m-%d', errors='coerce')
        
        # 移除无效日期
        df_copy = df_copy.dropna(subset=['交易时间'])
        
        # 按日期聚合数据
        daily_data = df_copy.groupby('交易时间').agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        
        daily_data = daily_data.sort_values('交易时间')
        
        # 准备JavaScript数据
        dates = daily_data['交易时间'].dt.strftime('%Y-%m-%d').tolist()
        amounts = daily_data[amount_col].round(2).tolist()
        quantities = daily_data[qty_col].tolist()
        
        # 生成HTML
        html = f'''
        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px; color: #333;">📈 本月销售走势</h3>
            <div style="position: relative; height: 400px; margin-bottom: 20px;">
                <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        // 销售趋势图数据
        const trendData = {{
            dates: {dates},
            amounts: {amounts},
            quantities: {quantities}
        }};
        
        // 图表配置
        const trendChartConfig = {{
            type: 'bar',
            data: {{
                labels: trendData.dates,
                datasets: [
                    {{
                        label: '销售额 (¥)',
                        data: trendData.amounts,
                        type: 'bar',
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    }},
                    {{
                        label: '销售数量',
                        data: trendData.quantities,
                        type: 'line',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: '销售趋势分析'
                    }},
                    legend: {{
                        display: true,
                        position: 'top'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                if (context.datasetIndex === 0) {{
                                    return context.dataset.label + ': ¥' + context.parsed.y.toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                                }} else {{
                                    return context.dataset.label + ': ' + context.parsed.y + '件';
                                }}
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        display: true,
                        title: {{
                            display: true,
                            text: '日期'
                        }}
                    }},
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: '销售额 (¥)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return '¥' + value.toLocaleString('zh-CN', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                            }}
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: '销售数量'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
            }}
        }};
        
        // 初始化图表
        let salesTrendChart;
        
        function initTrendChart() {{
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {{
                salesTrendChart = new Chart(trendCtx, trendChartConfig);
            }}
        }}
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(initTrendChart, 100);
        }});
        </script>
        '''
        
        return html
        
    except Exception as e:
        print(f"❌ 生成销售趋势图失败: {e}")
        return f'<div style="color: #d32f2f; text-align: center; padding: 20px;">❌ 趋势图生成失败: {str(e)}</div>'

        
    except Exception as e:
        print(f"❌ 生成销售趋势图失败: {e}")
        import traceback
        traceback.print_exc()
        return f'<div style="color: #666; text-align: center; padding: 20px;">❌ 趋势图生成失败: {str(e)}</div>'

def generate_category_trend_html(category_data, prev_category_data, category_icons, shop_summary, prev_shop_summary, df_erp, df_prev, amount_col, qty_col, MODEL_COL):
    """生成品类变化趋势HTML，增加店铺和单品环比监控"""
    html = ''
    
    # 品类变化趋势 - 按销售额从高到低排序
    html += '<details><summary><h3>📊 品类变化趋势</h3></summary>'
    # 按销售额排序
    category_data_sorted = category_data.sort_values(amount_col, ascending=False)
    
    for _, row in category_data_sorted.iterrows():
        category = row[CATEGORY_COL]
        current_amount = int(row[amount_col])
        current_qty = int(row[qty_col])
        
        # 查找前一月该品类数据
        prev_amount = 0
        prev_qty = 0
        if prev_category_data is not None:
            prev_data = prev_category_data[prev_category_data[CATEGORY_COL] == category]
            if not prev_data.empty:
                prev_amount = int(prev_data.iloc[0][amount_col])
                prev_qty = int(prev_data.iloc[0][qty_col])
        
        # 计算分销数据
        fenxiao_amount = 0
        fenxiao_qty = 0
        prev_fenxiao_amount = 0
        prev_fenxiao_qty = 0
        
        # 当天分销数据
        if '数据来源' in df_erp.columns:
            fenxiao_data = df_erp[(df_erp[CATEGORY_COL] == category) & (df_erp['数据来源'] == '分销')]
            if not fenxiao_data.empty:
                fenxiao_amount = int(fenxiao_data[amount_col].sum())
                fenxiao_qty = int(fenxiao_data[qty_col].sum())
        
        # 前一月分销数据
        if df_prev is not None and '数据来源' in df_prev.columns:
            prev_fenxiao_data = df_prev[(df_prev[CATEGORY_COL] == category) & (df_prev['数据来源'] == '分销')]
            if not prev_fenxiao_data.empty:
                prev_fenxiao_amount = int(prev_fenxiao_data[amount_col].sum())
                prev_fenxiao_qty = int(prev_fenxiao_data[qty_col].sum())
        
        if prev_amount > 0:
            growth_rate = ((current_amount - prev_amount) / prev_amount) * 100
            emoji = category_icons.get(category, '📦')
            if growth_rate > 0:
                html += f'<div style="margin-bottom: 8px; padding: 6px; background: #f0f8ff; border-radius: 4px;">'
                html += f'<strong>{emoji} {category}: 📈 +{growth_rate:.1f}%</strong><br>'
                html += f'销售额变化: ¥{prev_amount:,} → ¥{current_amount:,}<br>'
                # 添加分销数据展示（如果有分销数据）
                if fenxiao_amount > 0:
                    html += f'其中分销: ¥{fenxiao_amount:,}（{fenxiao_qty}件），环比 {calculate_ratio(fenxiao_qty, prev_fenxiao_qty)}'
                html += '</div>'
            else:
                html += f'<div style="margin-bottom: 8px; padding: 6px; background: #fff0f0; border-radius: 4px;">'
                html += f'<strong>{emoji} {category}: 📉 {growth_rate:.1f}%</strong><br>'
                html += f'销售额变化: ¥{prev_amount:,} → ¥{current_amount:,}<br>'
                # 添加分销数据展示（如果有分销数据）
                if fenxiao_amount > 0:
                    html += f'其中分销: ¥{fenxiao_amount:,}（{fenxiao_qty}件），环比 {calculate_ratio(fenxiao_qty, prev_fenxiao_qty)}'
                html += '</div>'
    
    # 店铺环比监控（>20%增长或下滑）
    html += '<h3>⚠️ 店铺环比监控</h3>'
    growth_shops = []
    decline_shops = []
    
    for _, row in shop_summary.iterrows():
        shop = row['店铺']
        current_amount = int(row[amount_col])
        current_qty = int(row[qty_col])
        
        # 查找昨日该店铺数据
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
        cat_products = cat_products[(cat_products[amount_col] > 1000) & ~cat_products[MODEL_COL].str.contains('运费|外机|虚拟|赠品')]
        
        growth_products = []
        decline_products = []
        
        for _, row in cat_products.iterrows():
            product = row[MODEL_COL]
            current_qty = int(row[qty_col])
            
            # 查找上月该单品数据
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
    
    html += '</details>'
    
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
        # 只保留销售额>1000且不含"运费""外机""虚拟""赠品"
        product_summary = product_summary[(product_summary[amount_col] > 1000) & ~product_summary[MODEL_COL].str.contains('运费|外机|虚拟|赠品')]
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
        # 只保留销售额>1000且不含"运费""外机""虚拟""赠品"
        product_summary = product_summary[(product_summary[amount_col] > 1000) & ~product_summary[MODEL_COL].str.contains('运费|外机|虚拟|赠品')]
        product_summary = product_summary.sort_values(amount_col, ascending=False)
        
        if len(product_summary) > 0:
            html += '<ul style="margin-left: 20px; padding-left: 10px;">'
            for _, p_row in product_summary.iterrows():
                product = p_row[MODEL_COL]
                p_amount = int(p_row[amount_col])
                p_qty = int(p_row[qty_col])
                p_price = int(p_amount / p_qty) if p_qty else 0
                html += f'<li style="margin-bottom: 5px;">🔸 {product}<br>销售额: ¥{p_amount:,} | 单价: ¥{p_price:,}</li>'
            html += '</ul>'
        else:
            html += '<p style="margin-left: 20px; color: #666;">暂无单品数据</p>'
        
        html += '</div>'
    return html

# ========== Part 1: 整体销售到品类 ==========
# 计算分销数据（单独统计）
fenxiao_amount = 0
fenxiao_qty = 0
if '数据来源' in df_erp.columns:
    fenxiao_df = df_erp[df_erp['数据来源'] == '分销']
    if not fenxiao_df.empty:
        fenxiao_amount = int(fenxiao_df[amount_col].sum())
        fenxiao_qty = int(fenxiao_df[qty_col].sum())

# 计算整体数据（排除分销数据，避免重复计算）
if '数据来源' in df_erp.columns:
    # 只计算非分销数据作为整体销售
    df_main = df_erp[df_erp['数据来源'] != '分销']
else:
    # 如果没有数据来源字段，使用全部数据
    df_main = df_erp

total_amount = int(df_main[amount_col].sum())
total_qty = int(df_main[qty_col].sum())
total_price = int(total_amount / total_qty) if total_qty else 0

# 计算前一天整体数据（排除分销数据）
prev_total_amount = 0
prev_total_qty = 0
if df_prev is not None:
    if '数据来源' in df_prev.columns:
        # 只计算非分销数据作为整体销售
        df_prev_main = df_prev[df_prev['数据来源'] != '分销']
    else:
        # 如果没有数据来源字段，使用全部数据
        df_prev_main = df_prev
    
    prev_total_amount = int(df_prev_main[amount_col].sum())
    prev_total_qty = int(df_prev_main[qty_col].sum())

# 前一天分销数据
prev_fenxiao_amount = 0
prev_fenxiao_qty = 0
if df_prev is not None and '数据来源' in df_prev.columns:
    prev_fenxiao_df = df_prev[df_prev['数据来源'] == '分销']
    if not prev_fenxiao_df.empty:
        prev_fenxiao_amount = int(prev_fenxiao_df[amount_col].sum())
        prev_fenxiao_qty = int(prev_fenxiao_df[qty_col].sum())

# 品类销售情况（按货品名称分组）- 排除分销数据
if '数据来源' in df_erp.columns:
    # 只计算非分销数据作为品类销售
    df_category = df_erp[df_erp['数据来源'] != '分销']
else:
    # 如果没有数据来源字段，使用全部数据
    df_category = df_erp

category_data = df_category.groupby(CATEGORY_COL).agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()

# 过滤掉"其他"品类
category_data = category_data[category_data[CATEGORY_COL] != '其他']

# 前一天品类数据 - 排除分销数据
prev_category_data = None
if df_prev is not None:
    if '数据来源' in df_prev.columns:
        # 只计算非分销数据作为品类销售
        df_prev_category = df_prev[df_prev['数据来源'] != '分销']
    else:
        # 如果没有数据来源字段，使用全部数据
        df_prev_category = df_prev
        
    prev_category_data = df_prev_category.groupby(CATEGORY_COL).agg({
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
        
        # 查找前一周该渠道数据
        prev_ch_amount = 0
        if prev_category_channel_data is not None:
            prev_ch_data = prev_category_channel_data[prev_category_channel_data['渠道'] == channel]
            if not prev_ch_data.empty:
                prev_ch_amount = int(prev_ch_data.iloc[0][amount_col])
        
        channel_breakdown.append(f"{channel}¥{ch_amount:,}({calculate_ratio(ch_amount, prev_ch_amount)})")
    
    # 添加分销数据显示（如果存在）
    fenxiao_data = category_channel_data[category_channel_data['渠道'] == '分销']
    if not fenxiao_data.empty:
        fenxiao_amount = int(fenxiao_data.iloc[0][amount_col])
        
        # 查找前一周分销数据
        prev_fenxiao_amount = 0
        if prev_category_channel_data is not None:
            prev_fenxiao_data = prev_category_channel_data[prev_category_channel_data['渠道'] == '分销']
            if not prev_fenxiao_data.empty:
                prev_fenxiao_amount = int(prev_fenxiao_data.iloc[0][amount_col])
        
        # 如果分销金额大于0，添加特殊标识
        if fenxiao_amount > 0:
            fenxiao_change = fenxiao_amount - prev_fenxiao_amount
            fenxiao_trend = "📈" if fenxiao_change > 0 else "📉" if fenxiao_change < 0 else "➡️"
            channel_breakdown.append(f"🔥分销¥{fenxiao_amount:,}({calculate_ratio(fenxiao_amount, prev_fenxiao_amount)}){fenxiao_trend}")
    
    channel_text = f" | ".join(channel_breakdown) if channel_breakdown else ""
    icon = category_icons.get(cat, '📦')
    
    part1 += f"""
    ├─ {icon} {idx}. {cat}
    ├─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)})
    ├─ 销量: {qty:,}件 | 单价: ¥{price:,}\n└─ {channel_text}"""

# ========== Part 2: 渠道销售分析 ==========

# 渠道销售情况（按渠道分组）- 排除分销数据
if '数据来源' in df_erp.columns:
    # 只计算非分销数据作为渠道销售
    df_channel = df_erp[df_erp['数据来源'] != '分销']
else:
    # 如果没有数据来源字段，使用全部数据
    df_channel = df_erp

channel_summary = df_channel.groupby('渠道').agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()

# 前一天渠道数据 - 排除分销数据
prev_channel_summary = None
if df_prev is not None:
    if '数据来源' in df_prev.columns:
        # 只计算非分销数据作为渠道销售
        df_prev_channel = df_prev[df_prev['数据来源'] != '分销']
    else:
        # 如果没有数据来源字段，使用全部数据
        df_prev_channel = df_prev
        
    prev_channel_summary = df_prev_channel.groupby('渠道').agg({
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
        
        # 查找前一周该店铺数据
        prev_amount = 0
        if prev_shop_summary is not None:
            prev_shop_data = prev_shop_summary[prev_shop_summary['店铺'] == shop]
            if not prev_shop_data.empty:
                prev_amount = int(prev_shop_data.iloc[0][amount_col])
        
        shop_list += f"├─ 🏪 TOP{idx} {shop}\n├─ 销售额: ¥{amount:,} ({calculate_ratio(amount, prev_amount)})\n├─ 单价: ¥{price:,}\n\n"
    
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
    
    # 查找前一周该渠道数据
    prev_amount = 0
    if prev_channel_summary is not None:
        prev_channel_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
        if not prev_channel_data.empty:
            prev_amount = int(prev_channel_data.iloc[0][amount_col])
    
    part2 += f"🏪 {idx}. {channel}渠道: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) | ¥{price:,}/件\n"

part2 += "\n🏆 【TOP店铺排行】\n"

# 店铺汇总 - 排除分销数据
if '数据来源' in df_erp.columns:
    # 只计算非分销数据作为店铺销售
    df_shop = df_erp[df_erp['数据来源'] != '分销']
else:
    # 如果没有数据来源字段，使用全部数据
    df_shop = df_erp

shop_summary = df_shop.groupby('店铺').agg({
    amount_col: 'sum',
    qty_col: 'sum'
}).reset_index()
# 只保留销售额>0的店铺
shop_summary = shop_summary[shop_summary[amount_col] > 0]
shop_summary = shop_summary.sort_values(amount_col, ascending=False)

# 前一天店铺数据 - 排除分销数据
prev_shop_summary = None
if df_prev is not None:
    if '数据来源' in df_prev.columns:
        # 只计算非分销数据作为店铺销售
        df_prev_shop = df_prev[df_prev['数据来源'] != '分销']
    else:
        # 如果没有数据来源字段，使用全部数据
        df_prev_shop = df_prev
    
    prev_shop_summary = df_prev_shop.groupby('店铺').agg({
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
    # 排除分销数据
    if '数据来源' in df_erp.columns:
        category_df = df_erp[(df_erp[CATEGORY_COL] == category) & (df_erp['数据来源'] != '分销')]
    else:
        category_df = df_erp[df_erp[CATEGORY_COL] == category]
    
    product_summary = category_df.groupby(MODEL_COL).agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()
    # 对比期
    prev_product_summary = None
    if df_prev is not None:
        if '数据来源' in df_prev.columns:
            prev_category_df = df_prev[(df_prev[CATEGORY_COL] == category) & (df_prev['数据来源'] != '分销')]
        else:
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
            part3 += f"🔸 {product}：本期¥{cur_amount:,}，对比期¥{prev_amount:,}\n"

# ========== Part 4: 店铺核心产品销售分析 ==========
part4 = f"""🎯 【店铺核心产品分析】\n"""
for idx, row in enumerate(shop_summary.iterrows(), 1):
    _, row_data = row
    shop = row_data['店铺']
    # 排除分销数据
    if '数据来源' in df_erp.columns:
        shop_df = df_erp[(df_erp['店铺'] == shop) & (df_erp['数据来源'] != '分销')]
    else:
        shop_df = df_erp[df_erp['店铺'] == shop]
    
    product_summary = shop_df.groupby(MODEL_COL).agg({
        amount_col: 'sum',
        qty_col: 'sum'
    }).reset_index()
    # 对比期
    prev_product_summary = None
    if df_prev is not None:
        if '数据来源' in df_prev.columns:
            prev_shop_df = df_prev[(df_prev['店铺'] == shop) & (df_prev['数据来源'] != '分销')]
        else:
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
            part4 += f"🔸 {product}：本期¥{cur_amount:,}，对比期¥{prev_amount:,}\n"

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
    
    # 查找前一周该渠道数据
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
    
    # 查找前一周该店铺数据
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
    
    # 查找前一周该品类数据
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
    web_content = f'''

        <!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>销售月报报告 - {report_date}</title>
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
    <h1>{current_month_name}销售月报报告</h1>
    <div style="margin-bottom: 15px; font-size: 11pt; color: #666;">
        <div>本期{this_month_start_str}至{month_end_str}</div>
        <div>对比期{last_month_start_str}至{last_month_end_str}</div>
    </div>

    <!-- 整体销售概况（置顶） -->
    <div class="overview-box">
        <h2>💰 【整体销售概况】</h2>
        <div style="font-size: 12pt; line-height: 1.6;">
            <div>├─ 总销售额: ¥{total_amount:,}，上月 ¥{prev_total_amount:,}，环比 {calculate_ratio(total_amount, prev_total_amount)}</div>
            <div>├─ 单价: ¥{total_price:,}，上月 ¥{int(prev_total_amount / prev_total_qty) if prev_total_qty else 0:,}，变化 {calculate_ratio(total_price, int(prev_total_amount / prev_total_qty) if prev_total_qty else 0)}</div>
            <div style="margin-top: 10px; color: #ff6b35; font-weight: bold;">🔄 分销数据:</div>
            <div>└─ 分销销售额: ¥{fenxiao_amount:,}，上月 ¥{prev_fenxiao_amount:,}，环比 {calculate_ratio(fenxiao_amount, prev_fenxiao_amount)}</div>
        </div>
    </div>
    

    
    <div class="section left-align">
        <!-- 销售趋势图 -->
        <h2>📈 【销售趋势图】</h2>
        {generate_sales_trend_chart_html_simple(df_erp, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons)}
        
        <!-- 品类变化趋势 -->
        <h2>🔍 【品类变化趋势】</h2>
        {generate_category_trend_html(category_data, prev_category_data, category_icons, shop_summary, prev_shop_summary, df_erp, df_prev, amount_col, qty_col, MODEL_COL)}
        
        <!-- 品类销售排行榜 -->
        <h2>【品类销售排行榜】</h2>
        {generate_category_ranking_html(category_data, df_erp, prev_category_data, amount_col, qty_col, CATEGORY_COL, MODEL_COL, category_icons, df_prev)}
        
        <!-- 渠道销售分析 -->
        <h2>📊 【渠道销售分析】</h2>
        {generate_channel_ranking_html(channel_summary, df_erp, prev_channel_summary, amount_col, qty_col, SHOP_COL)}
        
        <!-- TOP店铺排行 -->
        <h2>【TOP店铺排行】</h2>
        {generate_shop_ranking_html(shop_summary, df_erp, prev_shop_summary, amount_col, qty_col, MODEL_COL, df_prev)}
        
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

        

    filename = save_report_to_local(web_content, report_type="overall_weekly")
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
                resp1 = requests.get(test_url1, timeout=0.5)
                if resp1.status_code == 200:
                    public_url = test_url1
                elif test_url2:
                    resp2 = requests.get(test_url2, timeout=0.5)
                    if resp2.status_code == 200:
                        public_url = test_url2
            except Exception:
                public_url = url1
        else:
            public_url = None

    # 微信推送内容严格只用三段手动拼接，所有推送函数、异常、分段推送等只用 wechat_content
    wechat_content = f"""{current_month}月销售分析报告\n📊 本期{this_month_start_str}至{month_end_str}\n对比期{last_month_start_str}至{last_month_end_str}\n💰 【整体销售概况】\n├─ 总销售额: ¥{total_amount:,}\n├─ 单价: ¥{total_price:,}\n├─ 环比: {calculate_ratio(total_amount, prev_total_amount)}\n🔄 【分销数据】\n└─ 分销销售额: ¥{fenxiao_amount:,} ({calculate_ratio(fenxiao_amount, prev_fenxiao_amount)})\n\n📊 【渠道销售分析】\n"""
    channel_summary = channel_summary.sort_values(amount_col, ascending=False)
    for idx, row in enumerate(channel_summary.iterrows(), 1):
        _, row_data = row
        channel = row_data['渠道']
        amount = int(row_data[amount_col])
        qty = int(row_data[qty_col])
        price = int(amount / qty) if qty else 0
        # 修复：正确获取上月该渠道数据
        prev_amount = 0
        if prev_channel_summary is not None:
            prev_channel_data = prev_channel_summary[prev_channel_summary['渠道'] == channel]
            if not prev_channel_data.empty:
                prev_amount = int(prev_channel_data.iloc[0][amount_col])
        wechat_content += f"🏪 {idx}. {channel}渠道: ¥{amount:,} ({calculate_ratio(amount, prev_amount)}) | ¥{price:,}/件\n"
    wechat_content += "\n🔍 【品类变化趋势】\n"
    # 品类变化趋势排序：按本期销售额从高到低
    category_trend_sorted = sorted(category_changes, key=lambda x: x[3], reverse=True)
    for category, growth_rate, prev_amount, current_amount in category_trend_sorted:
        emoji = category_icons.get(category, '📦')
        
        # 计算该品类的分销数据
        fenxiao_amount_cat = 0
        fenxiao_qty_cat = 0
        prev_fenxiao_amount_cat = 0
        prev_fenxiao_qty_cat = 0
        
        # 本月分销数据
        if '数据来源' in df_erp.columns:
            fenxiao_data_cat = df_erp[(df_erp[CATEGORY_COL] == category) & (df_erp['数据来源'] == '分销')]
            if not fenxiao_data_cat.empty:
                fenxiao_amount_cat = int(fenxiao_data_cat[amount_col].sum())
                fenxiao_qty_cat = int(fenxiao_data_cat[qty_col].sum())
        
        # 上月分销数据
        if df_prev is not None and '数据来源' in df_prev.columns:
            prev_fenxiao_data_cat = df_prev[(df_prev[CATEGORY_COL] == category) & (df_prev['数据来源'] == '分销')]
            if not prev_fenxiao_data_cat.empty:
                prev_fenxiao_amount_cat = int(prev_fenxiao_data_cat[amount_col].sum())
                prev_fenxiao_qty_cat = int(prev_fenxiao_data_cat[qty_col].sum())
        
        # 基本品类变化信息
        if growth_rate > 0:
            wechat_content += f"   {emoji} {category}: 📈 +{growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"
        else:
            wechat_content += f"   {emoji} {category}: 📉 {growth_rate:.1f}% (¥{prev_amount:,}→¥{current_amount:,})\n"
        
        # 添加分销数据（如果有分销数据才显示）
        if fenxiao_amount_cat > 0 or prev_fenxiao_amount_cat > 0:
            wechat_content += f"   其中分销: ¥{fenxiao_amount_cat:,} ({calculate_ratio(fenxiao_amount_cat, prev_fenxiao_amount_cat)})\n"
    # 将URL链接和报告内容聚合到一条消息，如果字数超标则优先展示URL链接
    MAX_MSG_LEN = 1000
    
    if public_url:
        url_part = f"\n🌐 查看完整Web页面: {public_url}"
        
        # 如果内容加上URL超过限制，则截断内容但保留URL
        if len(wechat_content + url_part) > MAX_MSG_LEN:
            # 计算可用于内容的字符数（预留URL部分的空间）
            available_len = MAX_MSG_LEN - len(url_part) - 10  # 预留10个字符作为缓冲
            if available_len > 0:
                # 在合适的位置截断内容
                truncated_content = wechat_content[:available_len]
                # 尝试在换行符处截断，避免截断到单词中间
                last_newline = truncated_content.rfind('\n')
                if last_newline > available_len * 0.8:  # 如果最后一个换行符位置合理
                    truncated_content = truncated_content[:last_newline]
                final_message = truncated_content + "\n..." + url_part
            else:
                # 如果URL太长，只发送URL
                final_message = url_part
        else:
            # 内容和URL都能放下，直接合并
            final_message = wechat_content + url_part
    else:
        # 没有成功获取到URL，只发送内容，不发送假链接
        final_message = wechat_content
    
    # 发送聚合后的单条消息
    _send_single_message(final_message)

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

def get_trend_data_with_filters(df_erp, start_date, end_date, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL):
    """
    获取趋势图数据，包含数据过滤和京东分销数据汇总
    增强版：更好的日期格式兼容性
    """
    try:
        # 数据预处理
        df_copy = df_erp.copy()
        
        # 增强的日期格式处理
        print(f"📊 开始处理日期格式，原始数据行数: {len(df_copy)}")
        
        # 检查交易时间列的原始格式
        sample_dates = df_copy['交易时间'].head(10).tolist()
        print(f"📊 日期格式样本: {sample_dates}")
        
        # 使用增强的日期格式处理函数
        df_copy['交易时间'] = df_copy['交易时间'].apply(normalize_date_format)
        
        # 统计处理结果
        valid_dates = df_copy['交易时间'].notna().sum()
        total_dates = len(df_copy)
        print(f"📊 日期格式处理结果: 有效日期 {valid_dates}/{total_dates}")
        
        # 移除无效日期的行
        df_copy = df_copy.dropna(subset=['交易时间'])
        print(f"📊 移除无效日期后数据行数: {len(df_copy)}")
        
        if df_copy.empty:
            print("❌ 警告：所有日期数据都无效，无法生成趋势图")
            return pd.DataFrame()
        
        # 转换为datetime类型
        df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'])
        
        # 显示日期范围
        min_date = df_copy['交易时间'].min()
        max_date = df_copy['交易时间'].max()
        print(f"📊 数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
        
        # 筛选日期范围
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        print(f"📊 筛选日期范围: {start_datetime.strftime('%Y-%m-%d')} 至 {end_datetime.strftime('%Y-%m-%d')}")
        
        df_filtered = df_copy[(df_copy['交易时间'] >= start_datetime) & (df_copy['交易时间'] <= end_datetime)].copy()
        
        print(f"📊 趋势图数据筛选: {start_date} 至 {end_date}, 共{len(df_filtered)}行")
        
        # 显示筛选后的日期分布
        if not df_filtered.empty:
            filtered_dates = df_filtered['交易时间'].dt.strftime('%Y-%m-%d').value_counts().sort_index()
            print(f"📊 筛选后日期分布 (前10个):")
            for date, count in filtered_dates.head(10).items():
                print(f"   {date}: {count}条记录")
        
        # 京东分销数据汇总处理
        jingdong_data = df_filtered[df_filtered['店铺'].str.contains('京东', na=False)]
        if not jingdong_data.empty:
            print(f"📊 京东分销数据: {len(jingdong_data)}行")
            # 对京东数据进行汇总
            jingdong_summary = jingdong_data.groupby(['交易时间', CATEGORY_COL]).agg({
                amount_col: 'sum',
                qty_col: 'sum'
            }).reset_index()
            jingdong_summary['店铺'] = '京东分销汇总'
            jingdong_summary[SHOP_COL] = '京东分销汇总'
            
            # 将汇总数据添加到原数据中
            df_filtered = pd.concat([df_filtered, jingdong_summary], ignore_index=True)
            print(f"📊 添加京东汇总后总行数: {len(df_filtered)}")
        
        return df_filtered
        
    except Exception as e:
        print(f"❌ 趋势图数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def generate_sales_trend_chart_html(df_erp, amount_col, qty_col, CATEGORY_COL, SHOP_COL, MODEL_COL, category_icons):
    """
    生成销售趋势图HTML - 堆积柱形图版本
    包含堆积柱形图、万为单位显示、多筛选条件联动、智能排序、详细数据表格
    """
    try:
        # 数据预处理
        df_copy = df_erp.copy()
        if df_copy is None or df_copy.empty:
            print("❌ 警告：输入数据为空，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无销售数据</div>'
        
        print(f"📊 开始处理销售趋势图，原始数据行数: {len(df_copy)}")
        
        # 确保日期列是datetime类型
        df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
        df_copy = df_copy.dropna(subset=['交易时间'])
        
        if df_copy.empty:
            print("❌ 警告：所有日期数据都无效，无法生成趋势图")
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无有效的销售数据</div>'
        
        # 显示数据日期范围
        min_date = df_copy['交易时间'].min()
        max_date = df_copy['交易时间'].max()
        print(f"📊 数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
        
        # 获取数据的实际日期范围
        data_start = min_date.replace(day=1)  # 从数据开始月份的第一天开始
        data_end = max_date  # 到数据的最后一天结束
        
        print(f"📊 使用数据实际范围: {data_start.strftime('%Y-%m-%d')} 至 {data_end.strftime('%Y-%m-%d')}")
        
        # 筛选数据范围内的数据
        df_filtered = df_copy[(df_copy['交易时间'] >= data_start) & (df_copy['交易时间'] <= data_end)].copy()
        
        print(f"📊 筛选后数据行数: {len(df_filtered)}")
        
        if df_filtered.empty:
            return '<div style="color: #666; text-align: center; padding: 20px;">📊 暂无销售数据</div>'
        
        # 获取所有日期范围
        date_range = pd.date_range(start=data_start, end=data_end, freq='D')
        all_dates = [d.strftime('%Y-%m-%d') for d in date_range]
        
        print(f"📊 趋势图日期范围: {all_dates[0]} 至 {all_dates[-1]}, 共{len(all_dates)}天")
        
        # 按品类和日期聚合数据，用于堆积图
        df_filtered['日期'] = df_filtered['交易时间'].dt.strftime('%Y-%m-%d')
        
        # 获取品类、店铺、单品列表，按销售额排序
        category_sales = df_filtered.groupby(CATEGORY_COL)[amount_col].sum().sort_values(ascending=False)
        categories = category_sales.index.tolist()
        
        shop_sales = df_filtered.groupby(SHOP_COL)[amount_col].sum().sort_values(ascending=False)
        shops = shop_sales.index.tolist()
        
        product_sales = df_filtered.groupby(MODEL_COL)[amount_col].sum().sort_values(ascending=False)
        products = product_sales.index.tolist()
        
        # 生成HTML选项
        category_options = '\n'.join([f'<option value="{cat}">{category_icons.get(cat, "📦")} {cat}</option>' for cat in categories])
        shop_options = '\n'.join([f'<option value="{shop}">{shop}</option>' for shop in shops])
        product_options = '\n'.join([f'<option value="{product}">{product}</option>' for product in products])
        
        # 准备堆积图数据 - 按品类聚合
        category_daily_data = df_filtered.groupby(['日期', CATEGORY_COL]).agg({
            amount_col: 'sum',
            qty_col: 'sum'
        }).reset_index()
        
        # 确保所有日期和品类组合都有数据
        category_daily_complete = []
        for date in all_dates:
            for category in categories:
                data = category_daily_data[(category_daily_data['日期'] == date) & (category_daily_data[CATEGORY_COL] == category)]
                if not data.empty:
                    category_daily_complete.append({
                        '日期': date,
                        '品类': category,
                        '销售额': float(data.iloc[0][amount_col]),
                        '销售数量': float(data.iloc[0][qty_col])
                    })
                else:
                    category_daily_complete.append({
                        '日期': date,
                        '品类': category,
                        '销售额': 0.0,
                        '销售数量': 0.0
                    })
        
        category_daily_df = pd.DataFrame(category_daily_complete)
        
        # 准备图表数据
        dates = all_dates
        category_datasets = []
        
        # 按销售额排序品类，规模大的在下面
        category_order = category_sales.index.tolist()
        
        # 定义颜色数组
        colors = [
            'rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(255, 205, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)', 'rgba(153, 102, 255, 0.7)', 'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)', 'rgba(83, 102, 255, 0.7)', 'rgba(78, 252, 3, 0.7)',
            'rgba(252, 3, 244, 0.7)', 'rgba(3, 252, 198, 0.7)', 'rgba(252, 186, 3, 0.7)'
        ]
        
        for i, category in enumerate(category_order):
            category_data = category_daily_df[category_daily_df['品类'] == category]
            amounts = [float(x) / 10000 for x in category_data['销售额'].tolist()]  # 转换为万元
            category_datasets.append({
                'label': category,
                'data': amounts,
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)].replace('0.7', '1'),
                'borderWidth': 1,
                'stack': 'stack0'
            })
        
        # 生成完整HTML
        html = f'''
        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px; color: #333;">📈 销售走势（堆积图）</h3>
            
            <!-- 筛选控件 -->
            <div style="margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">品类:</label>
                    <select id="categoryFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部品类</option>
                        {category_options}
                    </select>
                </div>
                
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">店铺:</label>
                    <select id="shopFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部店铺</option>
                        {shop_options}
                    </select>
                </div>
                
                <div style="display: flex; align-items: center; gap: 5px;">
                    <label style="font-weight: bold; color: #555;">单品:</label>
                    <select id="productFilter" style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: white;">
                        <option value="">全部单品</option>
                        {product_options}
                    </select>
                </div>
                
                <button onclick="resetFilters()" style="padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">重置筛选</button>
            </div>
            
            <!-- 图表容器 -->
            <div style="position: relative; height: 400px; margin-bottom: 20px;">
                <canvas id="salesTrendChart" style="width: 100%; height: 100%;"></canvas>
            </div>
            
            <!-- 数据表格 -->
            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px; color: #333;">📊 详细数据（万元）</h4>
                <div id="dataTable" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
                    <table id="trendDataTable" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">日期</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">销售额 (万元)</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">销售数量</th>
                            </tr>
                        </thead>
                        <tbody id="trendDataTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        // 销售趋势图数据
        const trendData = {{
            dates: {dates},
            categoryDatasets: {category_datasets},
            categories: {categories},
            shops: {shops},
            products: {products},
            categorySales: {category_sales.to_dict()},
            shopSales: {shop_sales.to_dict()},
            productSales: {product_sales.to_dict()}
        }};
        
        // 图表配置
        let salesTrendChart;
        
        function initTrendChart() {{
            const trendCtx = document.getElementById('salesTrendChart');
            if (trendCtx) {{
                // 销毁现有图表
                if (salesTrendChart) {{
                    salesTrendChart.destroy();
                }}
                
                // 获取筛选条件
                const selectedCategory = document.getElementById('categoryFilter').value;
                const selectedShop = document.getElementById('shopFilter').value;
                const selectedProduct = document.getElementById('productFilter').value;
                
                // 准备图表数据
                let chartDatasets = trendData.categoryDatasets;
                
                // 如果有筛选条件，重新计算数据
                if (selectedCategory || selectedShop || selectedProduct) {{
                    // 这里可以添加筛选逻辑，暂时使用全部数据
                    console.log('筛选条件:', {{category: selectedCategory, shop: selectedShop, product: selectedProduct}});
                }}
                
                // 更新数据表格
                updateDataTable(trendData.dates, chartDatasets);
                
                // 创建堆积柱形图
                salesTrendChart = new Chart(trendCtx, {{
                    type: 'bar',
                    data: {{
                        labels: trendData.dates,
                        datasets: chartDatasets
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            mode: 'index',
                            intersect: false
                        }},
                        plugins: {{
                            title: {{
                                display: true,
                                text: '销售趋势分析（堆积图）'
                            }},
                            legend: {{
                                display: true,
                                position: 'top'
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '万元';
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: '日期'
                                }}
                            }},
                            y: {{
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {{
                                    display: true,
                                    text: '销售额 (万元)'
                                }},
                                ticks: {{
                                    callback: function(value) {{
                                        return value.toFixed(1) + '万';
                                    }}
                                }},
                                stacked: true
                            }}
                        }}
                    }}
                }});
            }}
        }}
        
        function updateDataTable(dates, datasets) {{
            const tbody = document.getElementById('trendDataTableBody');
            tbody.innerHTML = '';
            
            let totalAmount = 0;
            let totalQty = 0;
            
            for (let i = 0; i < dates.length; i++) {{
                const row = document.createElement('tr');
                
                // 计算当日总销售额
                let dailyAmount = 0;
                let dailyQty = 0;
                for (let j = 0; j < datasets.length; j++) {{
                    dailyAmount += datasets[j].data[i] || 0;
                    // 这里可以添加数量计算逻辑
                }}
                
                totalAmount += dailyAmount;
                totalQty += dailyQty;
                
                row.innerHTML = `
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{dates[i]}}</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{dailyAmount.toFixed(1)}}万</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{dailyQty}}件</td>
                `;
                tbody.appendChild(row);
            }}
            
            // 添加月累汇总行
            const summaryRow = document.createElement('tr');
            summaryRow.style.backgroundColor = '#f8f9fa';
            summaryRow.style.fontWeight = 'bold';
            summaryRow.innerHTML = `
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">月累汇总</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{totalAmount.toFixed(1)}}万</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">${{totalQty}}件</td>
            `;
            tbody.appendChild(summaryRow);
        }}
        
        function resetFilters() {{
            document.getElementById('categoryFilter').value = '';
            document.getElementById('shopFilter').value = '';
            document.getElementById('productFilter').value = '';
            initTrendChart();
        }}
        
        // 智能筛选联动
        function updateShopOptions() {{
            const selectedCategory = document.getElementById('categoryFilter').value;
            const shopFilter = document.getElementById('shopFilter');
            
            if (selectedCategory) {{
                // 根据选中的品类重新排序店铺选项
                // 这里可以添加具体的筛选逻辑
                console.log('更新店铺选项，选中品类:', selectedCategory);
            }}
        }}
        
        function updateProductOptions() {{
            const selectedCategory = document.getElementById('categoryFilter').value;
            const selectedShop = document.getElementById('shopFilter').value;
            const productFilter = document.getElementById('productFilter');
            
            if (selectedCategory || selectedShop) {{
                // 根据选中的品类和店铺重新排序单品选项
                console.log('更新单品选项，选中品类:', selectedCategory, '选中店铺:', selectedShop);
            }}
        }}
        
        // 事件监听器
        document.getElementById('categoryFilter').addEventListener('change', function() {{
            updateShopOptions();
            updateProductOptions();
            initTrendChart();
        }});
        document.getElementById('shopFilter').addEventListener('change', function() {{
            updateProductOptions();
            initTrendChart();
        }});
        document.getElementById('productFilter').addEventListener('change', initTrendChart);
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(initTrendChart, 100);
        }});
        </script>
        '''
        
        return html
        
    except Exception as e:
        print(f"❌ 生成销售趋势图失败: {e}")
        import traceback
        traceback.print_exc()
        return f'<div style="color: #666; text-align: center; padding: 20px;">❌ 趋势图生成失败: {str(e)}</div>'
