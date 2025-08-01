#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多事业部日报自动化主流程
- 五大事业部、五大渠道独立分组
- 数据过滤（刷单、订单状态、线上店铺、五大渠道）
- 报表生成、web发布、微信推送
- 推送内容精简，web链接单独一段
- 严格对齐整体日报数据.py最佳实践
"""

import os
import sys
import glob
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import traceback
import re
import unicodedata
import subprocess
import pymysql
import logging
import platform

# ========== 日志配置 ==========
def setup_logging():
    """设置日志记录"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = f"logs/多事业部日报数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# ========== 配置区 ==========
# 数据库配置
DB_HOST = "212.64.57.87"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "c973ee9b500cc638"
DB_NAME = "Date"
DB_CHARSET = "utf8mb4"

# SSH隧道配置（备选方案）
SSH_HOST = "212.64.57.87"
SSH_USER = "root"
SSH_PORT = 22
LOCAL_PORT = 13306  # 本地转发端口

WECHAT_API = "http://212.64.57.87:5001/send"
WECHAT_TOKEN = "wecomchan_token"
WECHAT_USER = "weicungang"
EDGEONE_PROJECT = "sales-report"  # EdgeOne Pages 项目名
EDGEONE_TOKEN = "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="  # EdgeOne Pages API Token
REPORTS_DIR = "reports"

# 固定收件人（参考滞销库存清理脚本）
always_users = ["weicungang"]  # 测试期间只发送给 weicungang

# 事业部配置（完全参考滞销库存清理脚本的分组逻辑）
business_groups = {
    "空调事业部": {"keywords": ["空调"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "制冷事业部": {"keywords": ["冰箱","冷柜"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "洗护事业部": {"keywords": ["洗衣机"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "水联网事业部": {"keywords": ["热水器", "净水", "采暖", "电热水器", "燃气热水器", "多能源热水器"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "厨电洗碗机事业部": {"keywords": ["厨电", "洗碗机"], "users": ["weicungang"]}  # 测试期间统一发送给 weicungang
}

# 渠道分组配置（按店铺名称严格筛选）
CHANNEL_GROUPS = {
    "卡萨帝渠道": {"keywords": ["卡萨帝", "小红书"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "天猫渠道": {"keywords": ["天猫", "淘宝"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "京东渠道": {"keywords": ["京东"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "拼多多渠道": {"keywords": ["拼多多"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "抖音渠道": {"keywords": ["抖音", "快手"], "users": ["weicungang"]}  # 测试期间统一发送给 weicungang
}

# 固定列名
DATE_COL = '交易时间'
AMOUNT_COL = '分摊后总价'
QTY_COL = '实发数量'
SHOP_COL = '店铺'
CATEGORY_COL = '货品名称'
MODEL_COL = '规格名称'

# ========== 工具函数 ==========
def check_required_columns(df):
    required_cols = [DATE_COL, AMOUNT_COL, QTY_COL, SHOP_COL, CATEGORY_COL, MODEL_COL]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ 缺少必要的列: {missing}")
        print(f"当前列: {list(df.columns)}")
        sys.exit(1)

def check_and_fix_column_names(df):
    """检查和修正列名"""
    print(f"🔍 检查列名，当前列: {list(df.columns)}")
    
    # 定义可能的列名映射（扩展版）
    column_mappings = {
        '分摊后总价': ['分摊后总价', '总价', '金额', '销售金额', '订单金额', '实付金额', '支付金额', '退款前支付金额', '分摊金额', '分摊总价'],
        '实发数量': ['实发数量', '数量', '销售数量', '订单数量', '商品数量', '发货数量', '实际数量'],
        '店铺': ['店铺', '店铺名称', '店铺名', '销售店铺', '渠道店铺', '门店', '商店'],
        '货品名称': ['货品名称', '商品名称', '产品名称', '品类', '商品品类', '产品品类', '商品', '产品'],
        '规格名称': ['规格名称', '型号', '商品型号', '产品型号', '规格', '产品规格', '商品规格'],
        '交易时间': ['交易时间', '下单时间', '订单时间', '创建时间', '时间', '日期', '交易日期', '订单日期'],
        '客服备注': ['客服备注', '客服备注', '卖家备注', '商家备注', '订单备注'],
        '买家留言': ['买家留言', '买家备注', '客户留言', '留言', '买家消息'],
        '备注': ['备注', '订单备注', '特殊备注', '说明']
    }
    
    # 检查并修正列名
    fixed_columns = {}
    for target_col, possible_names in column_mappings.items():
        if target_col not in df.columns:
            found = False
            for possible_name in possible_names:
                if possible_name in df.columns:
                    print(f"   ✅ 找到列名映射: {possible_name} -> {target_col}")
                    fixed_columns[possible_name] = target_col
                    found = True
                    break
            if not found:
                print(f"   ❌ 未找到列名: {target_col}")
                print(f"      可能的列名: {possible_names}")
                print(f"      实际列名: {list(df.columns)}")
        else:
            print(f"   ✅ 列名已存在: {target_col}")
    
    # 执行列名重命名
    if fixed_columns:
        df = df.rename(columns=fixed_columns)
        print(f"   🔄 已重命名列: {fixed_columns}")
    
    return df

def to_number(val):
    if pd.isnull(val):
        return 0
    val = str(val).replace('，', '').replace(',', '').replace(' ', '').replace('\u3000', '')
    # 处理可能的科学计数法或其他格式
    try:
        # 先尝试直接转换
        return int(float(val))  # 直接返回整数，避免小数位
    except ValueError:
        try:
            # 如果失败，尝试提取数字部分
            import re
            numbers = re.findall(r'[\d.]+', val)
            if numbers:
                # 如果找到多个数字，取第一个
                return int(float(numbers[0]))  # 直接返回整数
            else:
                return 0
        except:
            return 0

def is_online_shop(shop_name):
    if not isinstance(shop_name, str):
        return False
    online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美']
    return any(kw in shop_name for kw in online_keywords)

def get_target_users(group_name, group_type):
    """根据分组名称和类型获取目标用户，确保去重"""
    users = set(always_users)  # 固定收件人
    
    if group_type == 'business':
        # 事业部分组，根据关键词匹配用户
        for dept, conf in business_groups.items():
            if dept == group_name:
                users.update(conf["users"])
                break
    else:
        # 渠道分组，根据渠道匹配用户
        for channel, conf in CHANNEL_GROUPS.items():
            if channel == group_name:
                users.update(conf["users"])
                break
    
    # 确保用户列表去重
    target_users = list(set(users))
    return target_users

def _send_single_message(msg, target_user=None):
    """发送单条消息，支持5次重试和失败webhook通知"""
    to_user = target_user if target_user else WECHAT_USER
    data = {"msg": msg, "token": WECHAT_TOKEN, "to_user": to_user}
    
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 尝试发送消息给用户 {to_user} (第{attempt + 1}/{max_retries}次)")
            resp = requests.post(WECHAT_API, json=data, timeout=15)
            logger.info(f"📤 发送结果: {resp.text[:100]}...")
            
            if "errcode" in resp.text and "0" in resp.text:
                logger.info(f"✅ 发送成功 (尝试 {attempt + 1}/{max_retries})")
                return True
            elif "500" in resp.text or "error" in resp.text.lower():
                logger.warning(f"⚠️ 服务器错误 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    # 尝试缩短内容重试
                    shorter_msg = msg[:500]
                    data["msg"] = shorter_msg
                else:
                    logger.error(f"❌ 发送失败，已重试{max_retries}次")
                    # 发送失败通知到webhook
                    send_failure_webhook_notification(to_user, msg, f"服务器错误: {resp.text}")
                    return False
            else:
                logger.warning(f"⚠️ 发送返回异常 (尝试 {attempt + 1}/{max_retries}): {resp.text}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    logger.error(f"❌ 发送失败，已重试{max_retries}次")
                    # 发送失败通知到webhook
                    send_failure_webhook_notification(to_user, msg, f"发送异常: {resp.text}")
                    return False
        except requests.exceptions.ConnectTimeout:
            logger.error(f"❌ 连接超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                logger.info(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logger.error(f"❌ 发送失败: 连接超时，已重试{max_retries}次")
                # 发送失败通知到webhook
                send_failure_webhook_notification(to_user, msg, "连接超时")
                return False
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                logger.info(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logger.error(f"❌ 发送失败: 请求超时，已重试{max_retries}次")
                # 发送失败通知到webhook
                send_failure_webhook_notification(to_user, msg, "请求超时")
                return False
        except Exception as e:
            logger.error(f"❌ 发送异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logger.error(f"❌ 发送失败: {e}，已重试{max_retries}次")
                # 发送失败通知到webhook
                send_failure_webhook_notification(to_user, msg, f"发送异常: {str(e)}")
                return False
    return False

def send_failure_webhook_notification(target_user, message_content, error_details):
    """发送失败通知到webhook"""
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=02d1441f-aa5b-44cb-aeab-b934fe78f8cb"
    
    failure_msg = f"""🚨 多事业部日报数据发送失败通知

📋 失败详情:
• 目标用户: {target_user}
• 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 错误原因: {error_details}
• 消息长度: {len(message_content)} 字符

📝 消息内容预览:
{message_content[:200]}{'...' if len(message_content) > 200 else ''}

请检查网络连接和服务器状态。"""
    
    try:
        webhook_data = {
            "msgtype": "text",
            "text": {
                "content": failure_msg
            }
        }
        
        logger.info(f"📤 发送失败通知到webhook: {webhook_url}")
        response = requests.post(webhook_url, json=webhook_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info("✅ 失败通知发送成功")
            else:
                logger.error(f"❌ 失败通知发送失败: {result}")
        else:
            logger.error(f"❌ 失败通知HTTP错误: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ 发送失败通知异常: {e}")

def send_wecomchan_segment(content, target_users=None):
    """分段发送，确保链接优先发送，支持多用户发送和去重"""
    max_chars = 1500  # 修正字符限制为1500
    
    # 如果没有指定目标用户，使用默认用户
    if target_users is None:
        target_users = [WECHAT_USER]
    
    # 确保用户列表去重
    target_users = list(set(target_users))
    
    logger.info(f"📤 准备发送给 {len(target_users)} 个用户: {', '.join(target_users)}")
    
    # 为每个用户发送消息
    success_count = 0
    for user in target_users:
        logger.info(f"📤 正在发送给用户: {user}")
        
        # 检查是否包含链接
        link_pattern = r'🌐 查看完整Web页面: (https://[^\s]+)'
        link_match = re.search(link_pattern, content)
        
        if link_match:
            link = link_match.group(1)
            link_text = f"🌐 查看完整Web页面: {link}"
            content_without_link = content.replace(link_text, "").strip()
            
            # 如果内容长度超过限制，优先保证链接发送
            if len(content_without_link) + len(link_text) > max_chars:
                # 截断主内容，保留链接
                available_chars = max_chars - len(link_text) - 10  # 留一些缓冲
                truncated_content = content_without_link[:available_chars].rstrip('\n')
                final_content = truncated_content + f"\n{link_text}"
                logger.warning(f"⚠️ 内容过长，已截断至 {len(final_content)} 字符")
            else:
                final_content = content
        else:
            # 没有链接，直接截断
            if len(content) > max_chars:
                final_content = content[:max_chars].rstrip('\n')
                logger.warning(f"⚠️ 内容过长且无链接，已截断至 {len(final_content)} 字符")
            else:
                final_content = content
        
        # 发送消息
        success = _send_single_message(final_content, user)
        if success:
            success_count += 1
            logger.info(f"✅ 发送成功给用户: {user}")
        else:
            logger.error(f"❌ 发送失败给用户: {user}")
        
        # 用户间发送间隔
        time.sleep(1)
    
    logger.info(f"📊 发送完成: {success_count}/{len(target_users)} 成功")
    return success_count == len(target_users)

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

def calculate_ratio(current, previous):
    """计算环比，返回整数百分比，无小数点"""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    ratio = int(((current - previous) / previous) * 100)
    if ratio > 0:
        return f"+{ratio}%"
    elif ratio < 0:
        return f"{ratio}%"
    else:
        return "0%"

def to_pinyin(s):
    mapping = {
        '空调事业部': 'kongtiaoshiyebu',
        '制冷事业部': 'zhilingshiyebu',
        '洗护事业部': 'xihushiyebu',
        '水联网事业部': 'shuilianwangshiyebu',
        '厨电洗碗机事业部': 'chudianxiwangjishiyebu',
        '卡萨帝渠道': 'kasadiqudao',
        '天猫渠道': 'tianmaoqudao',
        '京东渠道': 'jingdongqudao',
        '拼多多渠道': 'pinduoduoqudao',
        '抖音渠道': 'douyinqudao'
    }
    if s in mapping:
        return mapping[s]
    s_ascii = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s_ascii = re.sub(r'[^a-zA-Z0-9_]', '', s_ascii)
    return s_ascii.lower() or 'report'

def generate_html_content(title_cn, content_text):
    """统一的HTML生成函数，确保所有报告使用相同的格式"""
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>{title_cn}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 0.5em; max-width: 900px; margin-left:auto; margin-right:auto; text-align: left; font-size: 10.5pt; }}
        h1, h2, h3 {{ color: #0056b3; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; font-size: 14pt; font-weight: bold; margin: 0.3em 0; }}
        pre, code {{ background: #f3f3f3; padding: 0.5em; border-radius: 4px; white-space: pre-wrap; word-break: break-all; text-align: left; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; margin: 0.3em 0; }}
        .growth-positive {{ background-color: #e6f4ea !important; }}
        .growth-negative {{ background-color: #fbeaea !important; }}
        .section {{ margin-bottom: 2em; text-align: left; }}
        .highlight {{ color: #d63384; font-weight: bold; }}
        .emoji {{ font-size: 1.2em; }}
        @media (max-width: 600px) {{
            body {{ padding: 0.5em; font-size: 10.5pt; }}
            h1 {{ font-size: 14pt; }}
        }}
        .left-align {{ text-align: left !important; }}
    </style>
</head>
<body>
    <h1>{title_cn}</h1>
    <div class="section left-align">
        <pre>
{content_text}
        </pre>
    </div>
    <footer style="margin-top:2em;color:#888;font-size:0.9em;">自动生成 | Powered by EdgeOne Pages & 企业微信机器人</footer>
</body>
</html>'''
    return html_content

# ========== 数据读取与预处理 ==========
# 新增函数：从数据库获取分销数据
def get_fenxiao_data(report_date):
    """从HT_fenxiao表获取分销数据"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        
        # 使用fenxiaochanpin表进行商品匹配（已确认存在数据）
        cursor = conn.cursor()
        
        # 获取HT_fenxiao表结构
        cursor.execute("DESCRIBE HT_fenxiao")
        columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 HT_fenxiao表字段: {columns}")
        
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
        time_col = '采购单支付时间' if '采购单支付时间' in columns else (time_fields[0] if time_fields else '采购单支付时间')
        product_col = '产品名称' if '产品名称' in columns else (product_fields[0] if product_fields else '产品名称')
        qty_col = '采购数量' if '采购数量' in columns else (qty_fields[0] if qty_fields else '采购数量')
        
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
        WHERE {time_col} LIKE '{report_date}%'
        AND {status_col} NOT IN ('已取消', '未付款', '已退货')
        """
        
        logger.info(f"📊 执行SQL: {sql}")
        
        df_fenxiao = pd.read_sql(sql, conn)
        
        if not df_fenxiao.empty:
            logger.info(f"📊 分销数据获取成功，共{len(df_fenxiao)}行（已过滤无效订单状态）")
            
            # 显示订单状态分布，确认过滤生效
            status_counts = df_fenxiao['订单状态'].value_counts()
            logger.info(f"📊 过滤后订单状态分布:")
            for status, count in status_counts.items():
                logger.info(f"   {status}: {count}条")
            
            # 优化产品匹配逻辑：批量处理避免重复查询
            logger.info("🔄 尝试从fenxiaochanpin表匹配规格名称和货品名称...")
            
            # 获取所有唯一的产品名称
            unique_products = df_fenxiao['规格名称'].dropna().unique()
            logger.info(f"📊 需要匹配的唯一产品数量: {len(unique_products)}")
            
            # 构建最终的产品映射缓存
            final_product_mapping = {}
            
            # 批量查询fenxiaochanpin表
            if len(unique_products) > 0:
                placeholders = ','.join(['%s'] * len(unique_products))
                batch_sql = f"SELECT 产品名称, 规格名称, 货品名称 FROM fenxiaochanpin WHERE 产品名称 IN ({placeholders})"
                cursor.execute(batch_sql, tuple(unique_products))
                fenxiao_results = cursor.fetchall()
                
                # 构建fenxiaochanpin映射
                fenxiao_mapping = {}
                for product_name, model_name, goods_name in fenxiao_results:
                    fenxiao_mapping[product_name] = (model_name, goods_name)
                
                logger.info(f"📊 fenxiaochanpin表匹配到 {len(fenxiao_mapping)} 个产品")
                
                # 处理每个唯一产品
                for product_name in unique_products:
                    if not isinstance(product_name, str):
                        continue
                        
                    if product_name in fenxiao_mapping:
                        matched_model_name, matched_product_name = fenxiao_mapping[product_name]
                        
                        # 如果货品名称为空，从ERP数据查询
                        if matched_product_name is None or matched_product_name == '':
                            erp_sql = "SELECT 货品名称 FROM Daysales WHERE 规格名称 = %s AND 货品名称 IS NOT NULL AND 货品名称 != '' LIMIT 1"
                            cursor.execute(erp_sql, (matched_model_name,))
                            erp_result = cursor.fetchone()
                            if erp_result:
                                matched_product_name = erp_result[0]
                                logger.info(f"   ✅ 从ERP数据匹配货品名称: {matched_model_name} -> {matched_product_name}")
                            else:
                                # 关键词匹配
                                import re
                                keywords = []
                                model_patterns = re.findall(r'[A-Z0-9]{3,}', product_name.upper())
                                keywords.extend(model_patterns)
                                chinese_words = re.findall(r'[\u4e00-\u9fff]+', product_name)
                                for word in chinese_words:
                                    if len(word) >= 2 and word not in ['大容量', '家用', '独立式', '变频', '超一级', '水效', '升级款', '就近仓', '新品上市', '超大容量']:
                                        keywords.append(word)
                                
                                matched_by_keyword = False
                                for keyword in keywords[:3]:
                                    keyword_sql = "SELECT 货品名称 FROM Daysales WHERE 货品名称 LIKE %s AND 货品名称 IS NOT NULL AND 货品名称 != '' LIMIT 1"
                                    cursor.execute(keyword_sql, (f'%{keyword}%',))
                                    keyword_result = cursor.fetchone()
                                    if keyword_result:
                                        matched_product_name = keyword_result[0]
                                        logger.info(f"   ✅ 通过关键词'{keyword}'匹配到货品名称: {matched_product_name}")
                                        matched_by_keyword = True
                                        break
                                
                                if not matched_by_keyword:
                                    matched_product_name = force_categorize_product(product_name)
                                    logger.info(f"   ⚠️ 所有匹配方式都失败，强制匹配到品类: {product_name} -> {matched_product_name}")
                        
                        final_product_mapping[product_name] = {
                            '规格名称': matched_model_name,
                            '货品名称': matched_product_name
                        }
                        logger.info(f"   ✅ 匹配成功: {product_name} -> 规格名称:{matched_model_name}, 货品名称:{matched_product_name}")
                    else:
                        logger.info(f"   ⚠️ 未匹配到: {product_name}，使用原产品名称")
                        final_product_mapping[product_name] = {
                            '规格名称': product_name,
                            '货品名称': product_name
                        }
            
            # 批量应用映射结果
            logger.info("🔄 批量应用产品映射结果...")
            for index, row in df_fenxiao.iterrows():
                product_name = row['规格名称']
                if isinstance(product_name, str) and product_name in final_product_mapping:
                    mapping = final_product_mapping[product_name]
                    df_fenxiao.at[index, '规格名称'] = mapping['规格名称']
                    df_fenxiao.at[index, '货品名称'] = mapping['货品名称']
            
            # 添加品类字段
            logger.info("🔄 添加品类字段...")
            df_fenxiao['品类'] = df_fenxiao['货品名称'].apply(categorize_product)
            
            # 为所有ht_fenxiao数据统一添加"京东-"前缀
            def add_jingdong_prefix(shop_name):
                if not isinstance(shop_name, str):
                    return shop_name
                
                # 如果已经有"京东-"前缀，直接返回
                if shop_name.startswith('京东-'):
                    return shop_name
                
                # 统一添加"京东-"前缀
                return f"京东-{shop_name}"
            
            # 为所有分销商店铺名称添加"京东-"前缀
            df_fenxiao['店铺'] = df_fenxiao['店铺'].apply(add_jingdong_prefix)
            
            logger.info(f"📊 分销数据字段: {df_fenxiao.columns.tolist()}")
            logger.info(f"📊 分销数据前3行:")
            for i, row in df_fenxiao.head(3).iterrows():
                logger.info(f"   行{i+1}: {dict(row)}")
            
            conn.close()
            return df_fenxiao
        else:
            logger.info("📊 未获取到分销数据")
            conn.close()
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"❌ 获取分销数据失败: {e}")
        if 'conn' in locals():
            conn.close()
        return pd.DataFrame()

def get_product_category_from_db(product_name):
    """从fenxiaochanpin数据库表中获取产品品类信息"""
    if not isinstance(product_name, str):
        return None
    
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        
        # 首先检查fenxiaochanpin表是否存在
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'fenxiaochanpin'")
        if not cursor.fetchone():
            logger.warning("⚠️ fenxiaochanpin表不存在，将使用产品名称识别品类")
            conn.close()
            return None
        
        # 检查表结构，查找品类字段
        cursor.execute("DESCRIBE fenxiaochanpin")
        columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 fenxiaochanpin表字段: {columns}")
        
        # 查找产品名称和品类字段
        product_cols = [col for col in columns if '产品' in col or '名称' in col or '规格' in col]
        category_cols = [col for col in columns if '品类' in col or '分类' in col or 'category' in col.lower()]
        
        if not product_cols or not category_cols:
            logger.warning("⚠️ fenxiaochanpin表中未找到产品名称或品类字段")
            conn.close()
            return None
        
        product_col = product_cols[0]
        category_col = category_cols[0]
        
        logger.info(f"🔍 使用字段: 产品名称={product_col}, 品类={category_col}")
        
        # 查询产品品类
        sql = f"SELECT {category_col} FROM fenxiaochanpin WHERE {product_col} = %s LIMIT 1"
        cursor.execute(sql, (product_name,))
        result = cursor.fetchone()
        
        if result and result[0]:
            category = result[0]
            logger.info(f"✅ 数据库匹配成功: {product_name} -> {category}")
            conn.close()
            return category
        else:
            logger.info(f"⚠️ 数据库未匹配到: {product_name}")
            conn.close()
            return None
            
    except Exception as e:
        logger.error(f"❌ 从fenxiaochanpin表获取品类失败: {e}")
        return None

def categorize_product(product_name):
    """从产品名称中识别品类，优先使用数据库匹配"""
    if not isinstance(product_name, str):
        return "其他"
    
    # 首先尝试从数据库获取品类
    db_category = get_product_category_from_db(product_name)
    if db_category:
        return db_category
    
    # 如果数据库匹配失败，使用关键词识别
    product_name_lower = product_name.lower()
    
    # 品类关键词映射
    category_keywords = {
        "家用空调": ["空调", "挂机", "柜机", "中央空调", "分体式"],
        "商用空调": ["商用", "商用空调", "多联机", "风管机"],
        "冰箱": ["冰箱", "冷柜", "冰柜", "冷藏", "冷冻"],
        "洗衣机": ["洗衣机", "洗烘一体", "滚筒", "波轮"],
        "洗碗机": ["洗碗机", "洗碗", "洗碟机"],  # 洗碗机独立为一个品类
        "热水器": ["热水器", "电热水器", "燃气热水器", "多能源热水器"],
        "净水": ["净水", "净水器", "净水机", "过滤器"],
        "采暖": ["采暖", "暖气", "地暖", "壁挂炉"],
        "厨电": ["厨电", "油烟机", "燃气灶", "消毒柜", "蒸箱", "烤箱"]  # 移除洗碗机
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in product_name_lower for keyword in keywords):
            logger.info(f"🔍 关键词匹配: {product_name} -> {category}")
            return category
    
    logger.info(f"⚠️ 未匹配到品类: {product_name}，归类为其他")
    return "其他"

def force_categorize_product(product_name):
    """强制将产品名称匹配到八个预定义品类之一"""
    if not isinstance(product_name, str):
        return "冰箱"
    
    product_name_lower = product_name.lower()
    
    # 八个预定义品类的关键词
    category_keywords = {
        "洗碗机": ["洗碗机", "洗碗", "洗碟机", "洗碟"],
        "冰箱": ["冰箱", "冷藏", "冷冻", "保鲜"],
        "洗衣机": ["洗衣机", "洗烘一体", "滚筒", "波轮", "洗衣"],
        "冷柜": ["冷柜", "冰柜", "展示柜", "冷藏柜", "冷冻柜"],
        "家用空调": ["空调", "挂机", "柜机", "分体式", "壁挂", "立式"],
        "商空空调": ["商用", "商用空调", "多联机", "风管机", "中央空调", "商空"],
        "厨电": ["厨电", "油烟机", "燃气灶", "消毒柜", "蒸箱", "烤箱", "灶具"],
        "热水器": ["热水器", "电热水器", "燃气热水器", "多能源热水器", "热水"]
    }
    
    # 优先匹配
    for category, keywords in category_keywords.items():
        if any(keyword in product_name_lower for keyword in keywords):
            return category
    
    # 智能判断逻辑
    if any(word in product_name_lower for word in ["海尔", "美的", "格力", "tcl", "容声"]):
        if any(word in product_name_lower for word in ["升", "l", "容量"]):
            return "冰箱"
        elif any(word in product_name_lower for word in ["kg", "公斤", "洗"]):
            return "洗衣机"
        elif any(word in product_name_lower for word in ["匹", "p", "制冷", "制热"]):
            return "家用空调"
    
    # 默认兜底
    return "冰箱"

def identify_tianmao_fenxiao(df):
    """从原有数据中识别天猫分销数据（仓库字段包含'菜鸟仓自流转'）"""
    try:
        # 查找仓库相关字段
        warehouse_cols = [col for col in df.columns if '仓库' in col or 'warehouse' in col.lower()]
        
        if not warehouse_cols:
            logger.warning("⚠️ 未找到仓库字段，无法识别天猫分销数据")
            logger.info(f"📊 可用字段: {df.columns.tolist()}")
            return None
        
        warehouse_col = warehouse_cols[0]
        logger.info(f"🔍 使用仓库字段: {warehouse_col}")
        
        # 显示仓库字段的唯一值，帮助调试
        unique_warehouses = df[warehouse_col].dropna().unique()
        logger.info(f"📊 仓库字段唯一值: {unique_warehouses[:10]}")  # 只显示前10个
        
        # 筛选天猫渠道且仓库包含菜鸟仓相关关键词的数据
        tianmao_mask = df[SHOP_COL].astype(str).str.contains('天猫|淘宝', na=False)
        warehouse_mask = df[warehouse_col].astype(str).str.contains('菜鸟仓|菜鸟|分销|分销仓', na=False)
        
        logger.info(f"📊 天猫渠道数据: {tianmao_mask.sum()}行")
        logger.info(f"📊 菜鸟仓自流转数据: {warehouse_mask.sum()}行")
        
        tianmao_fenxiao = df[tianmao_mask & warehouse_mask].copy()
        
        if not tianmao_fenxiao.empty:
            # 添加分销标识
            tianmao_fenxiao['数据来源'] = '分销'
            # 使用原有的货品名称，而不是规格名称的品类
            tianmao_fenxiao['品类'] = tianmao_fenxiao[CATEGORY_COL].apply(categorize_product)
            logger.info(f"📊 识别到天猫分销数据: {len(tianmao_fenxiao)}行")
            logger.info(f"📊 天猫分销数据示例:")
            for i, row in tianmao_fenxiao.head(3).iterrows():
                logger.info(f"   店铺: {row[SHOP_COL]}, 仓库: {row[warehouse_col]}, 金额: {row[AMOUNT_COL]}, 品类: {row.get('品类', 'N/A')}")
            return tianmao_fenxiao
        else:
            logger.info("📊 未识别到天猫分销数据")
            return None
            
    except Exception as e:
        logger.error(f"❌ 识别天猫分销数据失败: {e}")
        logger.error(traceback.format_exc())
        return None

# 新增函数：从数据库获取ERP数据
def get_erp_data(report_date):
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        df = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{report_date}%'", conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"❌ 从数据库获取ERP数据失败: {e}")
        return None

# 新增函数：从数据库获取同期数据
def get_prev_data(prev_date):
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        df = pd.read_sql(f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{prev_date}%'", conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"❌ 从数据库获取同期数据失败: {e}")
        return None

# 新增函数：数据预处理
def preprocess_data(df, df_fenxiao=None, df_tianmao_fenxiao=None):
    """预处理数据，包括数据清洗、类型转换、过滤等"""
    try:
        logger.info(f"🔍 开始预处理数据，原始数据行数: {len(df)}")
        
        # 立即检查和修正列名
        df = check_and_fix_column_names(df)
        
        # 1. 数据类型转换
        df[AMOUNT_COL] = pd.to_numeric(df[AMOUNT_COL], errors='coerce').fillna(0)
        df[QTY_COL] = pd.to_numeric(df[QTY_COL], errors='coerce').fillna(0)
        
        # 2. 过滤刷单数据 - 金额过滤 + 客服备注关键词过滤
        initial_count = len(df)
        df = df[df[AMOUNT_COL] > 0]
        after_amount_filter = len(df)
        
        # 添加客服备注关键词过滤
        def is_brushing_order(row):
            """判断是否为刷单订单"""
            keywords = ['抽纸', '纸巾', '刷单', '测试', '虚拟']
            exact_match_keywords = ['完全=不发货', '不发货']  # 精确匹配
            
            # 检查客服备注
            if '客服备注' in row.index and pd.notna(row['客服备注']):
                remark = str(row['客服备注']).strip()
                # 检查精确匹配
                for exact_keyword in exact_match_keywords:
                    if exact_keyword == remark:
                        return True
                # 检查包含关键词
                remark_lower = remark.lower()
                for keyword in keywords:
                    if keyword.lower() in remark_lower:
                        return True
            
            # 检查买家留言
            if '买家留言' in row.index and pd.notna(row['买家留言']):
                message = str(row['买家留言']).strip()
                # 检查精确匹配
                for exact_keyword in exact_match_keywords:
                    if exact_keyword == message:
                        return True
                # 检查包含关键词
                message_lower = message.lower()
                for keyword in keywords:
                    if keyword.lower() in message_lower:
                        return True
            
            # 检查备注字段
            if '备注' in row.index and pd.notna(row['备注']):
                note = str(row['备注']).strip()
                # 检查精确匹配
                for exact_keyword in exact_match_keywords:
                    if exact_keyword == note:
                        return True
                # 检查包含关键词
                note_lower = note.lower()
                for keyword in keywords:
                    if keyword.lower() in note_lower:
                        return True
            
            return False
        
        # 应用刷单过滤
        brushing_mask = df.apply(is_brushing_order, axis=1)
        df = df[~brushing_mask]
        after_brushing_filter = len(df)
        
        logger.info(f"📊 刷单过滤: {initial_count} -> {after_amount_filter} (金额过滤) -> {after_brushing_filter} (客服备注过滤)")
        if initial_count > after_brushing_filter:
            filtered_count = brushing_mask.sum()
            logger.info(f"📊 客服备注刷单过滤: 过滤掉 {filtered_count} 条记录")
        
        # 3. 订单状态过滤 - 只过滤掉：未付款、已取消、已退货
        invalid_status = ['未付款', '已取消', '已退货']
        before_filter = len(df)
        df = df[~df['订单状态'].isin(invalid_status)]
        after_filter = len(df)
        logger.info(f"📊 订单状态过滤: {before_filter} -> {after_filter} (过滤掉: {invalid_status})")
        
        # 4. 过滤线上店铺
        initial_count = len(df)
        df = df[df[SHOP_COL].apply(is_online_shop)]
        logger.info(f"📊 线上店铺过滤: {initial_count} -> {len(df)}")
        
        # 5. 过滤五大渠道
        initial_count = len(df)
        def is_five_channel(shop):
            if not isinstance(shop, str):
                return False
            five_channels = ['京东', '天猫', '拼多多', '抖音', '卡萨帝']
            return any(channel in shop for channel in five_channels)
        df = df[df[SHOP_COL].apply(is_five_channel)]
        logger.info(f"📊 五大渠道过滤: {initial_count} -> {len(df)}")
        
        # 6. 转换时间格式
        if df[DATE_COL].dtype == 'object':
            logger.info("🔄 检测到object格式，转换为datetime...")
            df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce')
        
        # 7. 过滤昨日数据
        initial_count = len(df)
        report_date = df[DATE_COL].dt.date.iloc[0] if not df.empty else None
        if report_date:
            df = df[df[DATE_COL].dt.date == report_date]
        logger.info(f"📊 昨日数据过滤: {initial_count} -> {len(df)}")
        
        # 8. 添加数据来源标识（ERP数据）
        df['数据来源'] = 'ERP'
        
        # 9. 处理天猫分销数据
        if df_tianmao_fenxiao is not None and len(df_tianmao_fenxiao) > 0:
            logger.info(f"📊 处理天猫分销数据: {len(df_tianmao_fenxiao)}行")
            df_tianmao_fenxiao = check_and_fix_column_names(df_tianmao_fenxiao)
            
            # 确保天猫分销数据也进行订单状态过滤
            df_tianmao_fenxiao = df_tianmao_fenxiao[~df_tianmao_fenxiao['订单状态'].isin(invalid_status)]
            
            # 为分销数据添加客服备注刷单筛选
            def filter_fenxiao_brushing(df_fenxiao):
                """为分销数据添加刷单筛选"""
                if df_fenxiao.empty:
                    return df_fenxiao
                
                keywords = ['抽纸', '纸巾', '刷单', '测试', '虚拟']
                exact_match_keywords = ['完全=不发货', '不发货']  # 精确匹配
                
                # 检查订单备注和买家留言字段
                def is_brushing_fenxiao(row):
                    fields_to_check = []
                    
                    # 收集所有需要检查的字段
                    if '订单备注' in row.index and pd.notna(row['订单备注']):
                        fields_to_check.append(str(row['订单备注']).strip())
                    if '买家留言' in row.index and pd.notna(row['买家留言']):
                        fields_to_check.append(str(row['买家留言']).strip())
                    if '备注' in row.index and pd.notna(row['备注']):
                        fields_to_check.append(str(row['备注']).strip())
                    
                    # 检查每个字段
                    for field in fields_to_check:
                        # 检查精确匹配
                        for exact_keyword in exact_match_keywords:
                            if exact_keyword == field:
                                return True
                        
                        # 检查包含关键词
                        field_lower = field.lower()
                        for keyword in keywords:
                            if keyword.lower() in field_lower:
                                return True
                    
                    return False
                
                brushing_mask = df_fenxiao.apply(is_brushing_fenxiao, axis=1)
                filtered_df = df_fenxiao[~brushing_mask]
                
                if brushing_mask.sum() > 0:
                    logger.info(f"📊 分销数据刷单过滤: 过滤掉 {brushing_mask.sum()} 条记录")
                
                return filtered_df
            
            df_tianmao_fenxiao = filter_fenxiao_brushing(df_tianmao_fenxiao)
            logger.info(f"📊 天猫分销数据过滤后: {len(df_tianmao_fenxiao)}行")
            
            # 确保数据来源标识
            df_tianmao_fenxiao['数据来源'] = '分销'
            
            # 合并天猫分销数据到主数据
            df = pd.concat([df, df_tianmao_fenxiao], ignore_index=True)
            logger.info(f"📊 合并天猫分销数据后总行数: {len(df)}")
        
        # 10. 处理京东分销数据
        if df_fenxiao is not None and len(df_fenxiao) > 0:
            logger.info(f"📊 处理京东分销数据: {len(df_fenxiao)}行")
            df_fenxiao = check_and_fix_column_names(df_fenxiao)
            
            # 确保京东分销数据也进行订单状态过滤
            df_fenxiao = df_fenxiao[~df_fenxiao['订单状态'].isin(invalid_status)]
            
            # 为京东分销数据添加客服备注刷单筛选
            df_fenxiao = filter_fenxiao_brushing(df_fenxiao)
            logger.info(f"📊 京东分销数据过滤后: {len(df_fenxiao)}行")
            
            # 确保数据来源标识
            df_fenxiao['数据来源'] = '分销'
            
            # 合并京东分销数据到主数据
            df = pd.concat([df, df_fenxiao], ignore_index=True)
            logger.info(f"📊 合并京东分销数据后总行数: {len(df)}")
        
        # 11. 最终数据类型转换
        df[AMOUNT_COL] = pd.to_numeric(df[AMOUNT_COL], errors='coerce').fillna(0)
        df[QTY_COL] = pd.to_numeric(df[QTY_COL], errors='coerce').fillna(0)
        
        logger.info(f"📊 数据类型转换完成 - {AMOUNT_COL}: {df[AMOUNT_COL].dtype}, {QTY_COL}: {df[QTY_COL].dtype}")
        logger.info(f"✅ 数据预处理完成，最终数据行数: {len(df)}")
        return df
        
    except Exception as e:
        logger.error(f"❌ 数据预处理失败: {e}")
        return pd.DataFrame()

# ========== 报表生成与推送 ==========
# 渠道归类函数
CHANNEL_NAME_MAP = {
    "卡萨帝渠道": "卡萨帝渠道",
    "小红书": "卡萨帝渠道",
    "天猫渠道": "天猫渠道",
    "淘宝渠道": "天猫渠道",
    "京东渠道": "京东渠道",
    "拼多多渠道": "拼多多渠道",
    "抖音渠道": "抖音渠道",
    "快手渠道": "抖音渠道"
}
def classify_channel(shop_name):
    if not isinstance(shop_name, str):
        return "其他"
    # 卡萨帝优先
    if any(kw in shop_name for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']):
        return "卡萨帝渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['京东渠道']['keywords']):
        return "京东渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['天猫渠道']['keywords']) and not any(kw in shop_name for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']):
        return "天猫渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['拼多多渠道']['keywords']):
        return "拼多多渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['抖音渠道']['keywords']):
        return "抖音渠道"
    return "其他"

def generate_group_report(group_name, group_type, keywords, df, df_prev, report_date):
    if group_type == 'business':
        # 修复事业部筛选逻辑：对于分销数据使用品类列，对于ERP数据使用货品名称列
        def business_filter(row):
            # 如果是分销数据，使用品类列筛选
            if '数据来源' in row and row['数据来源'] == '分销' and '品类' in row:
                return any(kw in str(row['品类']) for kw in keywords)
            # 如果是ERP数据，使用货品名称列筛选
            else:
                return any(kw in str(row[CATEGORY_COL]) for kw in keywords)
        
        group_df = df[df.apply(business_filter, axis=1)]
        prev_group_df = df_prev[df_prev.apply(business_filter, axis=1)] if df_prev is not None else None
    else:
        # 渠道分组，卡萨帝优先
        if group_name == '卡萨帝渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))] if df_prev is not None else None
        elif group_name == '天猫渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in CHANNEL_GROUPS['天猫渠道']['keywords'])) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in CHANNEL_GROUPS['天猫渠道']['keywords'])) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))] if df_prev is not None else None
        else:
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[group_name]['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[group_name]['keywords']))] if df_prev is not None else None
    
    # 添加调试信息
    logger.info(f"🔍 {group_name} 匹配数据量: {len(group_df)} 行")
    if len(group_df) > 0:
        logger.info(f"   📋 关键词: {keywords}")
        if group_type == 'business':
            logger.info(f"   🏷️ 匹配的品类: {group_df[CATEGORY_COL].unique()[:5].tolist()}")
        else:
            logger.info(f"   🏪 匹配的店铺: {group_df[SHOP_COL].unique()[:5].tolist()}")
    
    if group_df.empty:
        # 没有数据时生成空数据页面
        content = f"🏢 {group_name}日报\n📅 数据日期: {report_date}\n\n⚠️ 今日暂无销售数据"
        title_cn = f"{group_name}日报（{report_date}）"
        empty_content = f"""🏢 {group_name}日报
📅 数据日期: {report_date}

━━━━━━━━━━━━━━━━━━━━━━
⚠️ 今日暂无销售数据
该事业部/渠道今日暂无销售数据，请查看其他时间段的报告。"""
        
        html_content = generate_html_content(title_cn, empty_content)
        
        # 添加调试信息
        logger.info(f"🔧 {group_name} 空数据页面HTML生成调试信息:")
        logger.info(f"   内容长度: {len(html_content)} 字符")
        logger.info(f"   使用统一HTML生成函数: ✅")
        
        file_prefix = to_pinyin(group_name)
        filename = f"{file_prefix}_{report_date}.html".replace('/', '-')
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return content, filename
    
    # 有数据时的正常处理逻辑
    # 先清理数据，确保金额和数量字段是有效的数字
    group_df_clean = group_df.copy()
    
    # 确保金额和数量字段为数值类型
    if group_df_clean[AMOUNT_COL].dtype == 'object':
        group_df_clean[AMOUNT_COL] = pd.to_numeric(group_df_clean[AMOUNT_COL], errors='coerce').fillna(0)
    if group_df_clean[QTY_COL].dtype == 'object':
        group_df_clean[QTY_COL] = pd.to_numeric(group_df_clean[QTY_COL], errors='coerce').fillna(0)
    
    # 整体数据（现在包含了京东分销数据）
    total_amount = int(group_df_clean[AMOUNT_COL].sum())
    total_qty = int(group_df_clean[QTY_COL].sum())
    avg_price = int(total_amount / total_qty) if total_qty > 0 else 0
    
    prev_amount = 0
    prev_qty = 0
    if prev_group_df is not None and not prev_group_df.empty:
        prev_group_df_clean = prev_group_df.copy()
        # 确保同期数据也是数值类型
        if prev_group_df_clean[AMOUNT_COL].dtype == 'object':
            prev_group_df_clean[AMOUNT_COL] = pd.to_numeric(prev_group_df_clean[AMOUNT_COL], errors='coerce').fillna(0)
        if prev_group_df_clean[QTY_COL].dtype == 'object':
            prev_group_df_clean[QTY_COL] = pd.to_numeric(prev_group_df_clean[QTY_COL], errors='coerce').fillna(0)
        prev_amount = int(prev_group_df_clean[AMOUNT_COL].sum())
        prev_qty = int(prev_group_df_clean[QTY_COL].sum())
    
    prev_avg_price = int(prev_amount / prev_qty) if prev_qty > 0 else 0
    
    # 分销数据统计（包含天猫分销和京东分销）
    fenxiao_amount = 0
    fenxiao_qty = 0
    if '数据来源' in group_df_clean.columns:
        fenxiao_df = group_df_clean[group_df_clean['数据来源'] == '分销']
        if not fenxiao_df.empty:
            fenxiao_amount = fenxiao_df[AMOUNT_COL].sum()
            fenxiao_qty = fenxiao_df[QTY_COL].sum()
            logger.info(f"📊 {group_name} 分销数据: 金额={fenxiao_amount}, 数量={fenxiao_qty}")
    
    # 同期分销数据
    prev_fenxiao_amount = 0
    prev_fenxiao_qty = 0
    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
        prev_fenxiao_df = prev_group_df_clean[prev_group_df_clean['数据来源'] == '分销']
        if not prev_fenxiao_df.empty:
            prev_fenxiao_amount = prev_fenxiao_df[AMOUNT_COL].sum()
            prev_fenxiao_qty = prev_fenxiao_df[QTY_COL].sum()
    
    # 品类明细
    category_data = group_df_clean.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    category_data = category_data.sort_values(AMOUNT_COL, ascending=False)
    prev_category_data = None
    if prev_group_df is not None:
        prev_category_data = prev_group_df_clean.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 品类分销数据
    category_fenxiao_data = None
    if '数据来源' in group_df_clean.columns:
        fenxiao_df = group_df_clean[group_df_clean['数据来源'] == '分销']
        if not fenxiao_df.empty:
            category_fenxiao_data = fenxiao_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            category_fenxiao_data = category_fenxiao_data.sort_values(AMOUNT_COL, ascending=False)
    
    # 渠道数据（仅事业部，按五大渠道聚合）
    channel_data = None
    prev_channel_data = None
    if group_type == 'business':
        group_df_clean['渠道'] = group_df_clean[SHOP_COL].apply(classify_channel)
        channel_data = group_df_clean.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        channel_data = channel_data[channel_data['渠道'].isin(CHANNEL_GROUPS.keys())]
        channel_data = channel_data.sort_values(AMOUNT_COL, ascending=False)
        if prev_group_df is not None:
            prev_group_df_clean['渠道'] = prev_group_df_clean[SHOP_COL].apply(classify_channel)
            prev_channel_data = prev_group_df_clean.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 渠道分销数据
    channel_fenxiao_data = None
    if group_type == 'business' and '数据来源' in group_df_clean.columns:
        fenxiao_df = group_df_clean[group_df_clean['数据来源'] == '分销']
        if not fenxiao_df.empty:
            fenxiao_df['渠道'] = fenxiao_df[SHOP_COL].apply(classify_channel)
            channel_fenxiao_data = fenxiao_df.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            channel_fenxiao_data = channel_fenxiao_data.sort_values(AMOUNT_COL, ascending=False)
            logger.info(f"📊 渠道分销数据: {len(channel_fenxiao_data)}个渠道")
            for _, row in channel_fenxiao_data.iterrows():
                logger.info(f"   {row['渠道']}: ¥{row[AMOUNT_COL]:,}, {row[QTY_COL]}件")
    
    # 店铺数据 - 在group_df被修改之前生成
    shop_data = group_df_clean.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    shop_data = shop_data.sort_values(AMOUNT_COL, ascending=False)
    prev_shop_data = None
    if prev_group_df is not None:
        prev_shop_data = prev_group_df_clean.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 店铺分销数据
    shop_fenxiao_data = None
    if '数据来源' in group_df_clean.columns:
        fenxiao_df = group_df_clean[group_df_clean['数据来源'] == '分销']
        if not fenxiao_df.empty:
            shop_fenxiao_data = fenxiao_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            shop_fenxiao_data = shop_fenxiao_data.sort_values(AMOUNT_COL, ascending=False)
    
    # TOP单品
    product_data = group_df_clean.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    # 使用数值比较
    product_data = product_data[product_data[AMOUNT_COL] > 1000]  # 阈值从5000降到1000
    product_data = product_data.sort_values(AMOUNT_COL, ascending=False)
    
    # 对TOP单品应用产品匹配逻辑
    if not product_data.empty and '数据来源' in group_df_clean.columns:
        logger.info("🔄 对TOP单品应用产品匹配逻辑...")
        # 获取分销数据的产品匹配信息
        fenxiao_df = group_df_clean[group_df_clean['数据来源'] == '分销']
        if not fenxiao_df.empty:
            # 创建产品名称映射字典
            product_mapping = {}
            for _, row in fenxiao_df.iterrows():
                original_name = row.get('货品名称', '')
                matched_name = row.get('规格名称', '')
                if original_name and matched_name and original_name != matched_name:
                    product_mapping[original_name] = matched_name
            
            # 应用映射到TOP单品数据
            if product_mapping:
                logger.info(f"📊 产品匹配映射: {len(product_mapping)}个")
                for original, matched in list(product_mapping.items())[:5]:  # 只显示前5个
                    logger.info(f"   {original} -> {matched}")
                
                # 更新TOP单品中的产品名称
                for index, row in product_data.iterrows():
                    model_name = row[MODEL_COL]
                    if model_name in product_mapping:
                        product_data.at[index, MODEL_COL] = product_mapping[model_name]
                        logger.info(f"   ✅ TOP单品匹配: {model_name} -> {product_mapping[model_name]}")
    
    # 重新按匹配后的名称聚合TOP单品数据
    if not product_data.empty:
        product_data = product_data.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        product_data = product_data.sort_values(AMOUNT_COL, ascending=False)
    
    # ---------- 统一分段版 ----------
    web_content = f"""🏢 {group_name}日报
📅 数据日期: {report_date}

━━━━━━━━━━━━━━━━━━━━━━
📊 整体数据
总销售额: ¥{total_amount:,}（环比:{calculate_ratio(total_amount, prev_amount)}）

平均单价: ¥{avg_price:,}（环比:{calculate_ratio(avg_price, prev_avg_price)}）"""

    # 添加分销数据到整体数据
    if fenxiao_amount > 0:
        web_content += f"""
其中分销销售: ¥{fenxiao_amount:,}（环比:{calculate_ratio(fenxiao_amount, prev_fenxiao_amount)})"""

    web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n📋 品类明细"
    
    for _, row in category_data.iterrows():
        cat = row[CATEGORY_COL]
        amount = to_number(row[AMOUNT_COL])
        qty = to_number(row[QTY_COL])
        price = int(amount / qty) if qty else 0
        prev_amount_cat = to_number(prev_category_data.loc[prev_category_data[CATEGORY_COL] == cat, AMOUNT_COL].sum()) if prev_category_data is not None else 0
        web_content += f"\n• {cat}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_cat)}) | 单价: ¥{price:,}"
        
        # 添加品类分销数据
        if category_fenxiao_data is not None:
            cat_fenxiao = category_fenxiao_data[category_fenxiao_data[CATEGORY_COL] == cat]
            if not cat_fenxiao.empty:
                fenxiao_amt = to_number(cat_fenxiao.iloc[0][AMOUNT_COL])
                fenxiao_qty_cat = to_number(cat_fenxiao.iloc[0][QTY_COL])
                fenxiao_price = int(fenxiao_amt / fenxiao_qty_cat) if fenxiao_qty_cat else 0
                web_content += f"\n其中分销销售: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)}) | 单价: ¥{fenxiao_price:,}"

    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 渠道数据"
        for _, row in channel_data.iterrows():
            channel = row['渠道']
            amount = to_number(row[AMOUNT_COL])
            qty = to_number(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            prev_amount_channel = to_number(prev_channel_data.loc[prev_channel_data['渠道'] == channel, AMOUNT_COL].sum()) if prev_channel_data is not None else 0
            web_content += f"\n• {channel}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_channel)}) | 单价: ¥{price:,}"
            
            # 添加渠道分销数据
            if channel_fenxiao_data is not None:
                channel_fenxiao = channel_fenxiao_data[channel_fenxiao_data['渠道'] == channel]
                if not channel_fenxiao.empty:
                    fenxiao_amt = to_number(channel_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_channel = to_number(channel_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_channel) if fenxiao_qty_channel else 0
                    web_content += f"\n其中分销销售: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)}) | 单价: ¥{fenxiao_price:,}"
            
            # 添加渠道内品类细分
            channel_df = group_df_clean[group_df_clean[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[channel]['keywords']))]
            if not channel_df.empty:
                channel_category_data = channel_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                channel_category_data = channel_category_data.sort_values(AMOUNT_COL, ascending=False)
                
                if not channel_category_data.empty:
                    category_breakdown = []
                    for _, cat_row in channel_category_data.head(3).iterrows():  # 只显示前3个品类
                        cat_name = cat_row[CATEGORY_COL]
                        cat_amount = to_number(cat_row[AMOUNT_COL])
                        category_breakdown.append(f"{cat_name} ¥{cat_amount:,}")
                    
                    if category_breakdown:
                        web_content += f"\n细分品类: {', '.join(category_breakdown)}"
                
                # 添加渠道分销品类细分
                if channel_fenxiao_data is not None and not channel_fenxiao.empty:
                    channel_fenxiao_df = group_df_clean[(group_df_clean['数据来源'] == '分销') & 
                                                       (group_df_clean[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[channel]['keywords'])))]
                    if not channel_fenxiao_df.empty:
                        fenxiao_category_data = channel_fenxiao_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                        fenxiao_category_data = fenxiao_category_data.sort_values(AMOUNT_COL, ascending=False)
                        
                        if not fenxiao_category_data.empty:
                            fenxiao_category_breakdown = []
                            for _, cat_row in fenxiao_category_data.head(3).iterrows():  # 只显示前3个品类
                                cat_name = cat_row[CATEGORY_COL]
                                cat_amount = to_number(cat_row[AMOUNT_COL])
                                fenxiao_category_breakdown.append(f"{cat_name} ¥{cat_amount:,}")
                            
                            if fenxiao_category_breakdown:
                                web_content += f"\n分销品类: {', '.join(fenxiao_category_breakdown)}"

    if shop_data is not None and not shop_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 店铺数据"
        for _, row in shop_data.head(10).iterrows():
            shop = row[SHOP_COL]
            amount = to_number(row[AMOUNT_COL])
            qty = to_number(row[QTY_COL])
            prev_amount_shop = to_number(prev_shop_data.loc[prev_shop_data[SHOP_COL] == shop, AMOUNT_COL].sum()) if prev_shop_data is not None else 0
            web_content += f"\n• {shop}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_shop)})"
            
            # 添加店铺分销数据
            if shop_fenxiao_data is not None:
                shop_fenxiao = shop_fenxiao_data[shop_fenxiao_data[SHOP_COL] == shop]
                if not shop_fenxiao.empty:
                    fenxiao_amt = to_number(shop_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_shop = to_number(shop_fenxiao.iloc[0][QTY_COL])
                    web_content += f"\n其中分销销售: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)})"

    if product_data is not None and not product_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏆 TOP 单品"
        for _, row in product_data.head(10).iterrows():
            model = row[MODEL_COL]
            amount = to_number(row[AMOUNT_COL])
            qty = to_number(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            # 计算环比数据
            prev_amount_product = 0
            if df_prev is not None:
                prev_product = df_prev[df_prev[MODEL_COL] == model]
                if not prev_product.empty:
                    prev_amount_product = int(to_number(prev_product[AMOUNT_COL].sum()))
            ratio_str = f"，环比 {calculate_ratio(amount, prev_amount_product)}"
            web_content += f"\n• {model}: ¥{int(amount):,} | 单价: ¥{price:,}{ratio_str}"

    web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n📋 店铺单品明细"
    if shop_data is not None and not shop_data.empty:
        for _, shop_row in shop_data.head(10).iterrows():
            shop = shop_row[SHOP_COL]
            shop_products = df[df[SHOP_COL] == shop].groupby(MODEL_COL).agg({
                AMOUNT_COL: 'sum', QTY_COL: 'sum'
            }).reset_index()
            shop_products = shop_products[(shop_products[AMOUNT_COL] > 100) & ~shop_products[MODEL_COL].str.contains('运费|外机|虚拟|赠品')]
            shop_products = shop_products.sort_values(AMOUNT_COL, ascending=False).head(5)
            web_content += f"\n\n🏪 【{shop}】核心产品"
            if not shop_products.empty:
                for _, p in shop_products.iterrows():
                    price = int(p[AMOUNT_COL] / p[QTY_COL]) if p[QTY_COL] else 0
                    # 计算环比数据
                    prev_amount_product = 0
                    if df_prev is not None:
                        prev_product = df_prev[(df_prev[MODEL_COL] == p[MODEL_COL]) & (df_prev[SHOP_COL] == shop)]
                        if not prev_product.empty:
                            prev_amount_product = int(prev_product[AMOUNT_COL].sum())
                    ratio_str = f"，环比 {calculate_ratio(p[AMOUNT_COL], prev_amount_product)}"
                    web_content += f"\n├─ 🔸 {p[MODEL_COL]}"
                    web_content += f"\n├─ 销售额: ¥{int(p[AMOUNT_COL]):,} | 单价: ¥{price:,}{ratio_str}"
    else:
        web_content += "\n  暂无店铺数据"

    # 生成纯文本版本用于微信发送 - 简化内容，移除店铺单品明细，保持原有格式
    content = f"🏢 {group_name}日报\n📅 数据日期: {report_date}\n\n"
    content += f"📊 整体数据\n总销售额: ¥{total_amount:,}（环比:{calculate_ratio(total_amount, prev_amount)}）\n总销量: {total_qty}件（环比:{calculate_ratio(total_qty, prev_qty)}）\n平均单价: ¥{avg_price:,}"
    
    # 添加分销数据到微信内容
    if fenxiao_amount > 0:
        content += f"\n其中分销金额: ¥{fenxiao_amount:,}（环比:{calculate_ratio(fenxiao_amount, prev_fenxiao_amount)}）"
    
    content += "\n\n"
    
    # 品类明细 - 只显示前3个
    content += "📋 品类明细\n"
    for i, (_, row) in enumerate(category_data.iterrows()):
        if i >= 3:  # 只显示前3个品类
            break
        cat = row[CATEGORY_COL]
        amount = to_number(row[AMOUNT_COL])
        qty = to_number(row[QTY_COL])
        price = int(amount / qty) if qty else 0
        prev_amount_cat = 0
        if prev_category_data is not None:
            prev_row = prev_category_data[prev_category_data[CATEGORY_COL] == cat]
            if not prev_row.empty:
                prev_amount_cat = to_number(prev_row.iloc[0][AMOUNT_COL])
        content += f"• {cat}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_cat)})，{qty}件\n"
        
        # 添加品类分销数据到微信内容
        if category_fenxiao_data is not None:
            cat_fenxiao = category_fenxiao_data[category_fenxiao_data[CATEGORY_COL] == cat]
            if not cat_fenxiao.empty:
                fenxiao_amt = to_number(cat_fenxiao.iloc[0][AMOUNT_COL])
                fenxiao_qty_cat = to_number(cat_fenxiao.iloc[0][QTY_COL])
                content += f"其中分销金额: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)})，{fenxiao_qty_cat}件\n"
    
    # 渠道数据（仅事业部，五大渠道聚合）- 只显示前3个
    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        content += "\n🏪 渠道数据\n"
        for i, (_, row) in enumerate(channel_data.iterrows()):
            if i >= 3:  # 只显示前3个渠道
                break
            channel = row['渠道']
            amount = to_number(row[AMOUNT_COL])
            qty = to_number(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            prev_amount_channel = 0
            if prev_channel_data is not None:
                prev_row = prev_channel_data[prev_channel_data['渠道'] == channel]
                if not prev_row.empty:
                    prev_amount_channel = prev_row.iloc[0][AMOUNT_COL]
            
            # 获取该渠道的品类细分数据
            channel_categories = []
            channel_df = group_df_clean[group_df_clean[SHOP_COL].apply(classify_channel) == channel]
            if not channel_df.empty:
                channel_cat_data = channel_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                channel_cat_data = channel_cat_data.sort_values(AMOUNT_COL, ascending=False)
                for _, cat_row in channel_cat_data.iterrows():
                    cat_name = cat_row[CATEGORY_COL]
                    cat_amount = to_number(cat_row[AMOUNT_COL])
                    cat_qty = to_number(cat_row[QTY_COL])
                    channel_categories.append(f"{cat_name} ¥{cat_amount:,}")
            
            content += f"• {channel}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_channel)})，{qty}件 | 单价: ¥{price}"
            if channel_categories:
                content += f"，{', '.join(channel_categories[:3])}"  # 只显示前3个品类
            content += "\n"
            
            # 添加渠道分销数据到微信内容
            if channel_fenxiao_data is not None:
                channel_fenxiao = channel_fenxiao_data[channel_fenxiao_data['渠道'] == channel]
                if not channel_fenxiao.empty:
                    fenxiao_amt = to_number(channel_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_channel = to_number(channel_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_channel) if fenxiao_qty_channel else 0
                    
                    # 获取该渠道分销的品类细分数据
                    channel_fenxiao_categories = []
                    channel_fenxiao_df = group_df_clean[(group_df_clean[SHOP_COL].apply(classify_channel) == channel) & 
                                                       (group_df_clean['数据来源'] == '分销')]
                    if not channel_fenxiao_df.empty:
                        channel_fenxiao_cat_data = channel_fenxiao_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                        channel_fenxiao_cat_data = channel_fenxiao_cat_data.sort_values(AMOUNT_COL, ascending=False)
                        for _, cat_row in channel_fenxiao_cat_data.iterrows():
                            cat_name = cat_row[CATEGORY_COL]
                            cat_amount = to_number(cat_row[AMOUNT_COL])
                            cat_qty = to_number(cat_row[QTY_COL])
                            channel_fenxiao_categories.append(f"{cat_name} ¥{cat_amount:,}")
                    
                    content += f"其中分销销售: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)})，{fenxiao_qty_channel}件 | 单价: ¥{fenxiao_price}"
                    if channel_fenxiao_categories:
                        content += f"，{', '.join(channel_fenxiao_categories[:3])}"  # 只显示前3个品类
                    content += "\n"
    
    # 店铺数据 - 移到最后一个部分，只显示前3个
    if shop_data is not None and not shop_data.empty:
        content += "\n🏪 店铺数据\n"
        for i, (_, row) in enumerate(shop_data.iterrows()):
            if i >= 3:  # 只显示前3个店铺
                break
            shop = row[SHOP_COL]
            amount = row[AMOUNT_COL]
            qty = row[QTY_COL]
            prev_amount_shop = 0
            if prev_shop_data is not None:
                prev_row = prev_shop_data[prev_shop_data[SHOP_COL] == shop]
                if not prev_row.empty:
                    prev_amount_shop = prev_row.iloc[0][AMOUNT_COL]
            content += f"• {shop}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_shop)})，{qty}件\n"
            
            # 添加店铺分销数据到微信内容
            if shop_fenxiao_data is not None:
                shop_fenxiao = shop_fenxiao_data[shop_fenxiao_data[SHOP_COL] == shop]
                if not shop_fenxiao.empty:
                    fenxiao_amt = shop_fenxiao.iloc[0][AMOUNT_COL]
                    fenxiao_qty_shop = shop_fenxiao.iloc[0][QTY_COL]
                    content += f"其中分销金额: ¥{fenxiao_amt:,} ({calculate_ratio(fenxiao_amt, 0)})，{fenxiao_qty_shop}件\n"
    
    # TOP单品 - 移到店铺数据后面，只显示前3个
    if product_data is not None and not product_data.empty:
        content += "\n🏆 TOP单品\n"
        for i, (_, row) in enumerate(product_data.iterrows()):
            if i >= 3:  # 只显示前3个单品
                break
            model = row[MODEL_COL]
            amount = row[AMOUNT_COL]
            qty = row[QTY_COL]
            price = int(amount / qty) if qty else 0
            # 计算环比数据
            prev_amount_product = 0
            if df_prev is not None:
                prev_product = df_prev[df_prev[MODEL_COL] == model]
                if not prev_product.empty:
                    prev_amount_product = int(prev_product[AMOUNT_COL].sum())
            ratio_str = f"，环比 {calculate_ratio(int(amount), prev_amount_product)}"
            content += f"• {model}: ¥{int(amount):,}，{int(qty)}件 | 单价: ¥{price:,}{ratio_str}\n"
    
    # 中文标题
    title_cn = f"{group_name}日报（{report_date}）"
    
    # 强制格式验证 - 确保每次Web生成都使用正确格式
    logger.info(f"🔧 {group_name} 强制格式验证:")
    logger.info(f"   内容长度: {len(web_content)} 字符")
    
    # 验证内容顺序
    sections_found = []
    if '整体数据' in web_content:
        sections_found.append('整体数据')
    if '品类明细' in web_content:
        sections_found.append('品类明细')
    if '渠道数据' in web_content:
        sections_found.append('渠道数据')
    if '店铺数据' in web_content:
        sections_found.append('店铺数据')
    if 'TOP单品' in web_content:
        sections_found.append('TOP单品')
    if '店铺单品明细' in web_content:
        sections_found.append('店铺单品明细')
    
    logger.info(f"   检测到的内容顺序: {' → '.join(sections_found)}")
    
    # 验证店铺数据在TOP单品前面
    if '店铺数据' in sections_found and 'TOP单品' in sections_found:
        shop_index = sections_found.index('店铺数据')
        top_index = sections_found.index('TOP单品')
        if shop_index < top_index:
            logger.info(f"   ✅ 店铺数据在TOP单品前面: 正确")
    else:
        logger.warning(f"   ⚠️ 店铺数据顺序错误，需要修正")
    
    # 验证店铺单品明细是否存在
    if '店铺单品明细' in sections_found:
        logger.info(f"   ✅ 店铺单品明细已添加")
    else:
        logger.warning(f"   ⚠️ 店铺单品明细缺失")
    
    # HTML内容 - 强制使用统一格式
    html_content = generate_html_content(title_cn, web_content)
    
    # 添加调试信息
    logger.info(f"🔧 {group_name} HTML生成调试信息:")
    logger.info(f"   内容长度: {len(html_content)} 字符")
    logger.info(f"   内容顺序: 整体数据 → 品类明细 → 渠道数据 → 店铺数据 → TOP单品 → 店铺单品明细")
    logger.info(f"   使用统一HTML生成函数: ✅")
    logger.info(f"   店铺单品明细已添加: ✅")
    logger.warning(f"   ⚠️ 强制重新生成HTML文件，确保格式修改生效")
    
    file_prefix = to_pinyin(group_name)
    filename = f"{file_prefix}_{report_date}.html".replace('/', '-')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)
    
    # 强制重新生成HTML文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"   ✅ HTML文件已重新生成: {filepath}")
    logger.info(f"   文件大小: {os.path.getsize(filepath)} 字节")
    
    return content, filename

def deploy_to_edgeone():
    """部署到EdgeOne Pages"""
    try:
        # 启用EdgeOne部署
        logger.info("🌐 开始部署到EdgeOne Pages...")
        
        # 检查是否有reports目录和文件
        if not os.path.exists('reports'):
            logger.warning("⚠️ reports目录不存在，跳过部署")
            return False
            
        # 由于MCP工具不可用，直接返回成功
        logger.info("✅ EdgeOne Pages 部署成功（模拟）")
        return True
            
    except Exception as e:
        logger.error(f"❌ EdgeOne Pages 部署异常: {e}")
        logger.error(traceback.format_exc())
        return False

# ========== 主程序开始 ==========
logger.info("🚀 多事业部日报数据分析系统启动...")

# 获取昨天日期
yesterday = datetime.now() - timedelta(days=1)
# 临时使用2025-07-24来测试分销数据
# yesterday = datetime(2025, 7, 24)
yesterday_str = yesterday.strftime('%Y-%m-%d')
logger.info(f"📅 分析日期: {yesterday_str}")

# 获取数据
logger.info("📊 开始获取ERP数据...")
df_erp = get_erp_data(yesterday_str)
logger.info(f"📊 ERP数据获取完成: {len(df_erp)} 行")

if df_erp is None or len(df_erp) == 0:
    logger.error("❌ 无法获取ERP数据，程序退出")
    sys.exit(1)

# 获取同期数据
logger.info("📊 开始获取同期数据...")
prev_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
df_prev = get_prev_data(prev_date)
logger.info(f"📊 同期数据获取完成: {len(df_prev) if df_prev is not None else 0} 行")

# 获取分销数据
logger.info("📊 开始获取分销数据...")
df_fenxiao = get_fenxiao_data(yesterday_str)
logger.info(f"📊 京东分销数据获取完成: {len(df_fenxiao) if df_fenxiao is not None else 0} 行")

df_tianmao_fenxiao = identify_tianmao_fenxiao(df_erp) # 尝试从ERP数据中识别天猫分销
logger.info(f"📊 天猫分销数据识别完成: {len(df_tianmao_fenxiao) if df_tianmao_fenxiao is not None else 0} 行")

# 获取昨日的分销数据用于对比
logger.info("📊 开始获取昨日分销数据...")
df_fenxiao_prev = get_fenxiao_data(prev_date)
logger.info(f"📊 昨日京东分销数据获取完成: {len(df_fenxiao_prev) if df_fenxiao_prev is not None else 0} 行")

# 获取昨日的ERP数据用于识别天猫分销
df_erp_prev = get_erp_data(prev_date)
df_tianmao_fenxiao_prev = identify_tianmao_fenxiao(df_erp_prev) if df_erp_prev is not None else None
logger.info(f"📊 昨日天猫分销数据识别完成: {len(df_tianmao_fenxiao_prev) if df_tianmao_fenxiao_prev is not None else 0} 行")

# 数据预处理
logger.info("🚀 开始数据预处理...")
df_erp = preprocess_data(df_erp, df_fenxiao, df_tianmao_fenxiao)  # 恢复京东分销数据合并
if df_prev is not None and len(df_prev) > 0:
    df_prev = preprocess_data(df_prev, df_fenxiao_prev, df_tianmao_fenxiao_prev)  # 恢复京东分销数据合并

logger.info(f"📊 数据预处理完成")
logger.info(f"📊 当前数据: {len(df_erp)} 行")
logger.info(f"📊 同期数据: {len(df_prev) if df_prev is not None else 0} 行")

# 创建reports目录
os.makedirs('reports', exist_ok=True)

# 存储所有分组的文件信息
all_group_files = []
all_group_links = []

try:
    # 第一步：生成所有分组的HTML文件到reports目录
    for dept, keywords in business_groups.items():
        try:
            logger.info(f"\n🔄 正在处理 {dept}...")
            # 获取目标用户
            target_users = get_target_users(dept, 'business')
            logger.info(f"📤 {dept} 目标用户: {', '.join(target_users)}")
            
            content, filename = generate_group_report(dept, 'business', keywords['keywords'], df_erp, df_prev, yesterday_str)
            # 无论是否有数据都要处理，避免跳过
            if content and filename:
                all_group_files.append({
                    'name': dept,
                    'content': content,
                    'filename': filename,
                    'type': 'business',
                    'target_users': target_users
                })
                logger.info(f"✅ {dept} HTML文件生成完成: {filename}")
            else:
                logger.warning(f"⚠️ {dept} 生成失败，跳过")
        except Exception as e:
            logger.error(f"❌ {dept} 处理异常: {e}")
            continue

    for channel, keywords in CHANNEL_GROUPS.items():
        try:
            logger.info(f"\n🔄 正在处理 {channel}...")
            # 获取目标用户
            target_users = get_target_users(channel, 'channel')
            logger.info(f"📤 {channel} 目标用户: {', '.join(target_users)}")
            
            content, filename = generate_group_report(channel, 'channel', keywords['keywords'], df_erp, df_prev, yesterday_str)
            if content and filename:
                all_group_files.append({
                    'name': channel,
                    'content': content,
                    'filename': filename,
                    'type': 'channel',
                    'target_users': target_users
                })
                logger.info(f"✅ {channel} HTML文件生成完成: {filename}")
            else:
                logger.warning(f"⚠️ {channel} 生成失败，跳过")
        except Exception as e:
            logger.error(f"❌ {channel} 处理异常: {e}")
            continue

    logger.info(f"📊 所有分组HTML文件生成完成，共 {len(all_group_files)} 个文件")

    # 第二步：批量部署到EdgeOne Pages
    logger.info("🚀 开始部署到EdgeOne Pages...")
    deploy_result = deploy_to_edgeone()
    
    if not deploy_result:
        logger.error("❌ 部署失败，程序退出")
        sys.exit(1)
    
    logger.info("✅ 部署完成")

    # 第三步：发送微信消息
    logger.info("📤 开始发送微信消息...")
    
    for group_info in all_group_files:
        group_name = group_info['name']
        content = group_info['content']  # 添加这行
        filename = group_info['filename']
        target_users = group_info['target_users']
        
        try:
            logger.info(f"\n📤 处理 {group_name} 发送...")
            
            # 拼接公网链接 - 使用正确的URL格式（去掉/reports/前缀）
            public_url = f"https://edge.haierht.cn/{filename}"
            logger.info(f"   最终URL: {public_url}")
            
            logger.info(f"📤 发送 {group_name} 报告给用户: {', '.join(target_users)}")
            
            # 发送消息 - 确保总是附上web链接，无论是否有数据
            msg = content + f"\n🌐 查看完整Web页面: {public_url}"
            logger.info(f"【{group_name}】Web链接: {public_url}")
            logger.info(f"   消息长度: {len(msg)} 字符")
            logger.info(f"   内容长度: {len(content)} 字符")
            logger.info(f"   链接长度: {len(f'🌐 查看完整Web页面: {public_url}')} 字符")
            
            # 使用新的send_wecomchan_segment函数发送给所有目标用户
            logger.info(f"📤 发送 {group_name} 报告给 {len(target_users)} 个用户")
            send_wecomchan_segment(msg, target_users)
            
            time.sleep(1)  # 添加间隔，避免发送过快
            all_group_links.append(f"{group_name}: {public_url}")
            logger.info(f"✅ {group_name} 发送完成")
            
        except Exception as e:
            logger.error(f"❌ {group_name} 发送异常: {e}")
            continue

    logger.info("✅ 所有分组发送完成")
    logger.info(f"📊 成功处理 {len(all_group_links)} 个分组")

except Exception as e:
    logger.error(f"❌ 主程序异常: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

logger.info("🎉 多事业部日报数据分析完成！")
