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

# 事业部分组配置（按货品名称严格筛选）
BUSINESS_GROUPS = {
    "空调事业部": ["家用空调", "商用空调"],
    "制冷事业部": ["冰箱", "冷柜"],
    "洗护事业部": ["洗衣机", "晾衣机", "干衣机", "烘干机"],
    "水联网事业部": ["热水器", "净水", "采暖", "电热水器", "燃气热水器", "多能源热水器"],
    "厨电洗碗机事业部": ["厨电", "洗碗机"]
}

# 渠道分组配置（按店铺名称严格筛选）
CHANNEL_GROUPS = {
    "卡萨帝渠道": ["卡萨帝", "小红书"],
    "天猫渠道": ["天猫", "淘宝"],
    "京东渠道": ["京东"],
    "拼多多渠道": ["拼多多"],
    "抖音渠道": ["抖音", "快手"]
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
        '交易时间': ['交易时间', '下单时间', '订单时间', '创建时间', '时间', '日期', '交易日期', '订单日期']
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
    try:
        return float(val)
    except:
        return 0

def is_online_shop(shop_name):
    if not isinstance(shop_name, str):
        return False
    online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美']
    return any(kw in shop_name for kw in online_keywords)

def _send_single_message(msg):
    data = {"msg": msg, "token": WECHAT_TOKEN, "to_user": WECHAT_USER}
    try:
        resp = requests.post(WECHAT_API, json=data, timeout=15)
        print(f"📤 发送结果: {resp.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False

def send_wecomchan_segment(content):
    """分段发送，确保链接优先发送"""
    max_chars = 1500  # 修正字符限制为1500
    
    # 检查是否包含链接
    link_pattern = r'🌐 查看完整Web页面: (https://[^\s]+)'
    link_match = re.search(link_pattern, content)
    
    if link_match:
        link = link_match.group(1)
        link_text = f"🌐 查看完整Web页面: {link}"
        content_without_link = content.replace(link_text, "").strip()
        
        # 如果内容长度超过限制，优先保证链接发送
        if len(content) > max_chars:
            print(f"⚠️ 内容过长({len(content)}字符)，优先保证链接发送")
            # 截断内容但保留链接
            available_chars = max_chars - len(link_text) - 10  # 预留一些空间
            if available_chars > 0:
                truncated_content = content_without_link[:available_chars] + "..."
                final_content = truncated_content + "\n" + link_text
            else:
                # 如果连链接都放不下，只发送链接
                final_content = link_text
        else:
            final_content = content
        
        print(f"📤 发送消息，长度: {len(final_content)}字符")
        success = _send_single_message(final_content)
        if not success:
            print("❌ 消息发送失败")
    else:
        # 没有链接的情况，正常分段发送
        if len(content) <= max_chars:
            success = _send_single_message(content)
            if not success:
                print("❌ 消息发送失败")
        else:
            print(f"⚠️ 内容过长({len(content)}字符)，进行智能分段")
            segments = _smart_split_content(content, max_chars)
            for segment in segments:
                success = _send_single_message(segment)
                if not success:
                    print("❌ 消息发送失败")
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

def calculate_ratio(current, previous):
    if previous == 0:
        return "📈 100%" if current > 0 else "0%"
    ratio = ((current - previous) / previous) * 100
    if ratio > 0:
        return f"📈 {ratio:.1f}%"
    elif ratio < 0:
        return f"📉 {ratio:.1f}%"
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
print("\n🚀 多事业部日报数据分析系统启动...")

# 步骤2: 读取ERP销售数据
print("📊 正在从数据库读取ERP订单明细数据...")

# 获取前一天日期作为报告日期
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime('%Y-%m-%d')

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
    
# 后续分析逻辑保持不变，df_erp即为主数据源

# 立即检查和修正列名
df_erp = check_and_fix_column_names(df_erp)
check_required_columns(df_erp)

# 2. 数据清洗
for col in [AMOUNT_COL, QTY_COL]:
    df_erp[col] = df_erp[col].apply(to_number)
df_erp = df_erp[(df_erp[AMOUNT_COL] > 0) & (df_erp[QTY_COL] > 0)]

# 剔除刷单 - 修正逻辑：包含"抽纸"或"纸巾"或等于"不发货"的都剔除
if '客服备注' in df_erp.columns:
    before = len(df_erp)
    df_erp = df_erp[~(df_erp['客服备注'].astype(str).str.contains('抽纸|纸巾') | (df_erp['客服备注'] == '不发货'))]
    print(f"刷单过滤: {before} -> {len(df_erp)}")

# 剔除未付款/已取消/已退款订单 - 添加已退款状态
order_status_col = next((c for c in df_erp.columns if '订单状态' in c or '状态' in c), None)
if order_status_col:
    before = len(df_erp)
    df_erp = df_erp[~df_erp[order_status_col].astype(str).str.contains('未付款|已取消|已退款')]
    print(f"订单状态过滤: {before} -> {len(df_erp)}")

# 只保留线上店铺
before = len(df_erp)
df_erp = df_erp[df_erp[SHOP_COL].apply(is_online_shop)]
print(f"线上店铺过滤: {before} -> {len(df_erp)}")

# 只保留五大渠道店铺
channel_keywords = sum(CHANNEL_GROUPS.values(), [])
def is_five_channel(shop):
    if not isinstance(shop, str):
        return False
    # 卡萨帝优先
    if any(kw in shop for kw in CHANNEL_GROUPS['卡萨帝渠道']):
        return True
    if any(kw in shop for kw in CHANNEL_GROUPS['京东渠道']):
        return True
    if any(kw in shop for kw in CHANNEL_GROUPS['天猫渠道']) and not any(kw in shop for kw in CHANNEL_GROUPS['卡萨帝渠道']):
        return True
    if any(kw in shop for kw in CHANNEL_GROUPS['拼多多渠道']):
        return True
    if any(kw in shop for kw in CHANNEL_GROUPS['抖音渠道']):
        return True
    return False

before = len(df_erp)
df_erp = df_erp[df_erp[SHOP_COL].apply(is_five_channel)]
print(f"五大渠道过滤: {before} -> {len(df_erp)}")

# 过滤前一天的数据
before = len(df_erp)
# 处理日期格式问题
if df_erp[DATE_COL].dtype == 'timedelta64[ns]':
    print("🔄 检测到timedelta格式，转换为日期...")
    # 使用基准日期2024-01-01
    base_date = pd.Timestamp('2024-01-01')
    df_erp[DATE_COL] = base_date + df_erp[DATE_COL]
elif df_erp[DATE_COL].dtype == 'object':
    print("🔄 检测到object格式，转换为datetime...")
    df_erp[DATE_COL] = pd.to_datetime(df_erp[DATE_COL], errors='coerce')

# 过滤前一天的数据
target_date = (datetime.now() - timedelta(days=1)).date()
df_erp = df_erp[df_erp[DATE_COL].dt.date == target_date]
print(f"前一天数据过滤: {before} -> {len(df_erp)}")

# 3. 读取前前一天数据用于环比
prev_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
prev_sql = f"SELECT * FROM Daysales WHERE 交易时间 LIKE '{prev_date}%'"

df_prev = None
try:
    # 尝试直接连接
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=10
    )
    df_prev = pd.read_sql(prev_sql, conn)
    conn.close()
    print(f"📊 前前一天数据读取成功，共{len(df_prev)}行")
    
    # 检查和修正列名
    df_prev = check_and_fix_column_names(df_prev)
    check_required_columns(df_prev)
    
    # 数据清洗
    for col in [AMOUNT_COL, QTY_COL]:
        df_prev[col] = df_prev[col].apply(to_number)
    df_prev = df_prev[(df_prev[AMOUNT_COL] > 0) & (df_prev[QTY_COL] > 0)]
    
    # 剔除刷单 - 与当天数据使用相同的筛选条件
    if '客服备注' in df_prev.columns:
        before = len(df_prev)
        df_prev = df_prev[~(df_prev['客服备注'].astype(str).str.contains('抽纸|纸巾') | (df_prev['客服备注'] == '不发货'))]
        print(f"前一天刷单过滤: {before} -> {len(df_prev)}")
    
    # 剔除未付款/已取消/已退款订单 - 与当天数据使用相同的筛选条件
    order_status_col_prev = next((c for c in df_prev.columns if '订单状态' in c or '状态' in c), None)
    if order_status_col_prev:
        before = len(df_prev)
        df_prev = df_prev[~df_prev[order_status_col_prev].astype(str).str.contains('未付款|已取消|已退款')]
        print(f"前一天订单状态过滤: {before} -> {len(df_prev)}")
    
    df_prev = df_prev[df_prev[SHOP_COL].apply(is_online_shop)]
    df_prev = df_prev[df_prev[SHOP_COL].apply(is_five_channel)]
    
    # 过滤前前一天的数据
    before = len(df_prev)
    # 处理日期格式问题
    if df_prev[DATE_COL].dtype == 'timedelta64[ns]':
        print("🔄 前前一天数据检测到timedelta格式，转换为日期...")
        # 使用基准日期2024-01-01
        base_date = pd.Timestamp('2024-01-01')
        df_prev[DATE_COL] = base_date + df_prev[DATE_COL]
    elif df_prev[DATE_COL].dtype == 'object':
        print("🔄 前前一天数据检测到object格式，转换为datetime...")
        df_prev[DATE_COL] = pd.to_datetime(df_prev[DATE_COL], errors='coerce')
    
    # 过滤前前一天的数据
    target_date_prev = (datetime.now() - timedelta(days=2)).date()
    df_prev = df_prev[df_prev[DATE_COL].dt.date == target_date_prev]
    print(f"前前一天数据过滤: {before} -> {len(df_prev)}")
    
except Exception as e:
    print(f"⚠️ 前前一天数据读取失败: {e}")
    df_prev = None

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
    if any(kw in shop_name for kw in CHANNEL_GROUPS['卡萨帝渠道']):
        return "卡萨帝渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['京东渠道']):
        return "京东渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['天猫渠道']) and not any(kw in shop_name for kw in CHANNEL_GROUPS['卡萨帝渠道']):
        return "天猫渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['拼多多渠道']):
        return "拼多多渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['抖音渠道']):
        return "抖音渠道"
    return "其他"

def generate_group_report(group_name, group_type, keywords, df, df_prev, report_date):
    if group_type == 'business':
        group_df = df[df[CATEGORY_COL].apply(lambda x: any(kw in str(x) for kw in keywords))]
        prev_group_df = df_prev[df_prev[CATEGORY_COL].apply(lambda x: any(kw in str(x) for kw in keywords))] if df_prev is not None else None
    else:
        # 渠道分组，卡萨帝优先
        if group_name == '卡萨帝渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in keywords))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in keywords))] if df_prev is not None else None
        elif group_name == '天猫渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in keywords)) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in keywords)) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']))] if df_prev is not None else None
        else:
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in keywords))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in keywords))] if df_prev is not None else None
    
    # 添加调试信息
    print(f"🔍 {group_name} 匹配数据量: {len(group_df)} 行")
    if len(group_df) > 0:
        print(f"   📋 关键词: {keywords}")
        if group_type == 'business':
            print(f"   🏷️ 匹配的品类: {group_df[CATEGORY_COL].unique()[:5].tolist()}")
        else:
            print(f"   🏪 匹配的店铺: {group_df[SHOP_COL].unique()[:5].tolist()}")
    
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
        print(f"🔧 {group_name} 空数据页面HTML生成调试信息:")
        print(f"   内容长度: {len(html_content)} 字符")
        print(f"   使用统一HTML生成函数: ✅")
        
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
    # 整体数据
    total_amount = int(group_df[AMOUNT_COL].sum())
    total_qty = int(group_df[QTY_COL].sum())
    avg_price = int(total_amount / total_qty) if total_qty else 0
    prev_amount = int(prev_group_df[AMOUNT_COL].sum()) if prev_group_df is not None and not prev_group_df.empty else 0
    prev_qty = int(prev_group_df[QTY_COL].sum()) if prev_group_df is not None and not prev_group_df.empty else 0
    prev_avg_price = int(prev_amount / prev_qty) if prev_qty else 0
    # 品类明细
    category_data = group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    category_data = category_data.sort_values(AMOUNT_COL, ascending=False)
    prev_category_data = None
    if prev_group_df is not None:
        prev_category_data = prev_group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 渠道数据（仅事业部，按五大渠道聚合）
    channel_data = None
    prev_channel_data = None
    if group_type == 'business':
        group_df = group_df.copy()
        group_df['渠道'] = group_df[SHOP_COL].apply(classify_channel)
        channel_data = group_df.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        channel_data = channel_data[channel_data['渠道'].isin(CHANNEL_GROUPS.keys())]
        channel_data = channel_data.sort_values(AMOUNT_COL, ascending=False)
        if prev_group_df is not None:
            prev_group_df = prev_group_df.copy()
            prev_group_df['渠道'] = prev_group_df[SHOP_COL].apply(classify_channel)
            prev_channel_data = prev_group_df.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 店铺数据 - 在group_df被修改之前生成
    shop_data = group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    shop_data = shop_data.sort_values(AMOUNT_COL, ascending=False)
    prev_shop_data = None
    if prev_group_df is not None:
        prev_shop_data = prev_group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    # TOP单品
    product_data = group_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    product_data = product_data[product_data[AMOUNT_COL] > 1000]  # 阈值从5000降到1000
    product_data = product_data.sort_values(AMOUNT_COL, ascending=False)
    
    # ---------- 统一分段版 ----------
    web_content = f"""🏢 {group_name}日报
📅 数据日期: {report_date}

━━━━━━━━━━━━━━━━━━━━━━
📊 整体数据
总销售额: ¥{total_amount:,}（环比:{calculate_ratio(total_amount, prev_amount)}）
总销量: {total_qty}件（环比:{calculate_ratio(total_qty, prev_qty)}）
平均单价: ¥{avg_price:,}（环比:{calculate_ratio(avg_price, prev_avg_price)}）

━━━━━━━━━━━━━━━━━━━━━━
📋 品类明细"""
    for _, row in category_data.iterrows():
        cat = row[CATEGORY_COL]
        amount = int(row[AMOUNT_COL])
        qty = int(row[QTY_COL])
        price = int(amount / qty) if qty else 0
        prev_amount_cat = int(prev_category_data.loc[prev_category_data[CATEGORY_COL] == cat, AMOUNT_COL].sum()) if prev_category_data is not None else 0
        web_content += f"\n• {cat}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_cat)})，{qty}件 | 单价: ¥{price:,}"

    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 渠道数据"
        for _, row in channel_data.iterrows():
            channel = row['渠道']
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            prev_amount_channel = int(prev_channel_data.loc[prev_channel_data['渠道'] == channel, AMOUNT_COL].sum()) if prev_channel_data is not None else 0
            web_content += f"\n• {channel}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_channel)})，{qty}件 | 单价: ¥{price:,}"

    if shop_data is not None and not shop_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 店铺数据"
        for _, row in shop_data.head(10).iterrows():
            shop = row[SHOP_COL]
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            prev_amount_shop = int(prev_shop_data.loc[prev_shop_data[SHOP_COL] == shop, AMOUNT_COL].sum()) if prev_shop_data is not None else 0
            web_content += f"\n• {shop}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_shop)})，{qty}件"

    if product_data is not None and not product_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏆 TOP 单品"
        for _, row in product_data.head(10).iterrows():
            model = row[MODEL_COL]
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            # 计算环比数据
            prev_amount_product = 0
            if df_prev is not None:
                prev_product = df_prev[df_prev[MODEL_COL] == model]
                if not prev_product.empty:
                    prev_amount_product = int(prev_product[AMOUNT_COL].sum())
            ratio_str = f"，前一天 ¥{prev_amount_product:,}，环比 {calculate_ratio(amount, prev_amount_product)}"
            web_content += f"\n• {model}: ¥{amount:,}，{qty}件 | 单价: ¥{price:,}{ratio_str}"

    web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n📋 店铺单品明细"
    if shop_data is not None and not shop_data.empty:
        for _, shop_row in shop_data.head(10).iterrows():
            shop = shop_row[SHOP_COL]
            shop_products = df[df[SHOP_COL] == shop].groupby(MODEL_COL).agg({
                AMOUNT_COL: 'sum', QTY_COL: 'sum'
            }).reset_index()
            shop_products = shop_products[(shop_products[AMOUNT_COL] > 100) & ~shop_products[MODEL_COL].str.contains('运费|赠品')]
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
                    ratio_str = f"，前一天 ¥{prev_amount_product:,}，环比 {calculate_ratio(int(p[AMOUNT_COL]), prev_amount_product)}"
                    web_content += f"\n├─ 🔸 {p[MODEL_COL]}"
                    web_content += f"\n├─ 销售额: ¥{int(p[AMOUNT_COL]):,} | 销量: {int(p[QTY_COL])}件 | 单价: ¥{price:,}{ratio_str}"
    else:
        web_content += "\n  暂无店铺数据"

    # 生成纯文本版本用于微信发送 - 简化内容，移除店铺单品明细，保持原有格式
    content = f"🏢 {group_name}日报\n📅 数据日期: {report_date}\n\n"
    content += f"📊 整体数据\n总销售额: ¥{total_amount:,}（环比:{calculate_ratio(total_amount, prev_amount)}）\n总销量: {total_qty}件（环比:{calculate_ratio(total_qty, prev_qty)}）\n平均单价: ¥{avg_price:,}\n\n"
    
    # 品类明细 - 只显示前3个
    content += "📋 品类明细\n"
    for i, (_, row) in enumerate(category_data.iterrows()):
        if i >= 3:  # 只显示前3个品类
            break
        cat = row[CATEGORY_COL]
        amount = int(row[AMOUNT_COL])
        qty = int(row[QTY_COL])
        price = int(amount / qty) if qty else 0
        prev_amount_cat = 0
        if prev_category_data is not None:
            prev_row = prev_category_data[prev_category_data[CATEGORY_COL] == cat]
            if not prev_row.empty:
                prev_amount_cat = int(prev_row.iloc[0][AMOUNT_COL])
        content += f"• {cat}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_cat)})，{qty}件\n"
    
    # 渠道数据（仅事业部，五大渠道聚合）- 只显示前3个
    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        content += "\n🏪 渠道数据\n"
        for i, (_, row) in enumerate(channel_data.iterrows()):
            if i >= 3:  # 只显示前3个渠道
                break
            channel = row['渠道']
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            prev_amount_channel = 0
            if prev_channel_data is not None:
                prev_row = prev_channel_data[prev_channel_data['渠道'] == channel]
                if not prev_row.empty:
                    prev_amount_channel = int(prev_row.iloc[0][AMOUNT_COL])
            content += f"• {channel}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_channel)})，{qty}件\n"
    
    # 店铺数据 - 移到最后一个部分，只显示前3个
    if shop_data is not None and not shop_data.empty:
        content += "\n🏪 店铺数据\n"
        for i, (_, row) in enumerate(shop_data.iterrows()):
            if i >= 3:  # 只显示前3个店铺
                break
            shop = row[SHOP_COL]
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            prev_amount_shop = 0
            if prev_shop_data is not None:
                prev_row = prev_shop_data[prev_shop_data[SHOP_COL] == shop]
                if not prev_row.empty:
                    prev_amount_shop = int(prev_row.iloc[0][AMOUNT_COL])
            content += f"• {shop}: ¥{amount:,} ({calculate_ratio(amount, prev_amount_shop)})，{qty}件\n"
    
    # TOP单品 - 移到店铺数据后面，只显示前3个
    if product_data is not None and not product_data.empty:
        content += "\n🏆 TOP单品\n"
        for i, (_, row) in enumerate(product_data.iterrows()):
            if i >= 3:  # 只显示前3个单品
                break
            model = row[MODEL_COL]
            amount = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amount / qty) if qty else 0
            # 计算环比数据
            prev_amount_product = 0
            if df_prev is not None:
                prev_product = df_prev[df_prev[MODEL_COL] == model]
                if not prev_product.empty:
                    prev_amount_product = int(prev_product[AMOUNT_COL].sum())
            ratio_str = f"，前一天 ¥{prev_amount_product:,}，环比 {calculate_ratio(amount, prev_amount_product)}"
            content += f"• {model}: ¥{amount:,}，{qty}件 | 单价: ¥{price:,}{ratio_str}\n"
    
    # 中文标题
    title_cn = f"{group_name}日报（{report_date}）"
    
    # 强制格式验证 - 确保每次Web生成都使用正确格式
    print(f"🔧 {group_name} 强制格式验证:")
    print(f"   内容长度: {len(web_content)} 字符")
    
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
    
    print(f"   检测到的内容顺序: {' → '.join(sections_found)}")
    
    # 验证店铺数据在TOP单品前面
    if '店铺数据' in sections_found and 'TOP单品' in sections_found:
        shop_index = sections_found.index('店铺数据')
        top_index = sections_found.index('TOP单品')
        if shop_index < top_index:
            print(f"   ✅ 店铺数据在TOP单品前面: 正确")
    else:
        print(f"   ⚠️ 店铺数据顺序错误，需要修正")
    
    # 验证店铺单品明细是否存在
    if '店铺单品明细' in sections_found:
        print(f"   ✅ 店铺单品明细已添加")
    else:
        print(f"   ⚠️ 店铺单品明细缺失")
    
    # HTML内容 - 强制使用统一格式
    html_content = generate_html_content(title_cn, web_content)
    
    # 添加调试信息
    print(f"🔧 {group_name} HTML生成调试信息:")
    print(f"   内容长度: {len(html_content)} 字符")
    print(f"   内容顺序: 整体数据 → 品类明细 → 渠道数据 → 店铺数据 → TOP单品 → 店铺单品明细")
    print(f"   使用统一HTML生成函数: ✅")
    print(f"   店铺单品明细已添加: ✅")
    print(f"   ⚠️ 强制重新生成HTML文件，确保格式修改生效")
    
    file_prefix = to_pinyin(group_name)
    filename = f"{file_prefix}_{report_date}.html".replace('/', '-')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)
    
    # 强制重新生成HTML文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   ✅ HTML文件已重新生成: {filepath}")
    print(f"   文件大小: {os.path.getsize(filepath)} 字节")
    
    return content, filename

# ========== 主流程 ==========
all_group_links = []
all_group_files = []  # 存储所有生成的文件信息

try:
    # 第一步：生成所有分组的HTML文件到reports目录
    for dept, keywords in BUSINESS_GROUPS.items():
        try:
            print(f"\n🔄 正在处理 {dept}...")
            content, filename = generate_group_report(dept, 'business', keywords, df_erp, df_prev, yesterday_str)
            # 无论是否有数据都要处理，避免跳过
            if content and filename:
                all_group_files.append({
                    'name': dept,
                    'content': content,
                    'filename': filename,
                    'type': 'business'
                })
                print(f"✅ {dept} HTML文件生成完成: {filename}")
            else:
                print(f"⚠️ {dept} 生成失败，跳过")
        except Exception as e:
            print(f"❌ {dept} 处理异常: {e}")
            continue
    
    for channel, keywords in CHANNEL_GROUPS.items():
        try:
            print(f"\n🔄 正在处理 {channel}...")
            content, filename = generate_group_report(channel, 'channel', keywords, df_erp, df_prev, yesterday_str)
            # 无论是否有数据都要处理，避免跳过
            if content and filename:
                all_group_files.append({
                    'name': channel,
                    'content': content,
                    'filename': filename,
                    'type': 'channel'
                })
                print(f"✅ {channel} HTML文件生成完成: {filename}")
            else:
                print(f"⚠️ {channel} 生成失败，跳过")
        except Exception as e:
            print(f"❌ {channel} 处理异常: {e}")
            continue
    
    # 第二步：统一部署整个reports目录（只调用一次）
    if all_group_files:
        print(f"\n🌐 开始统一部署 {len(all_group_files)} 个HTML文件...")
        
        # 确保所有文件都已生成到reports目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, "reports")
        
        # 验证所有文件都已正确生成
        print(f"🔍 验证所有HTML文件:")
        for group_info in all_group_files:
            filepath = os.path.join(reports_dir, group_info['filename'])
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"   ✅ {group_info['filename']}: {file_size} 字节")
            else:
                print(f"   ❌ {group_info['filename']}: 文件不存在")
        
        # 使用EdgeOne CLI部署整个reports目录
        edgeone_path = r"C:\Users\weicu\AppData\Roaming\npm\edgeone.cmd"
        cmd = [
            edgeone_path, "pages", "deploy", "./reports",
            "-n", EDGEONE_PROJECT,
            "-t", EDGEONE_TOKEN
        ]
        
        try:
            print(f"\n🌐 正在通过 edgeone CLI 部署整个 reports 目录...")
            print(f"   部署命令: {' '.join(cmd)}")
            print(f"   ⚠️ 强制重新部署，确保格式修改生效")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print(f"   部署输出: {result.stdout}")
            if result.stderr:
                print(f"   部署错误: {result.stderr}")
            if result.returncode == 0:
                print(f"✅ 统一部署成功，所有 {len(all_group_files)} 个文件已上传")
                print(f"   ⚠️ 请清除浏览器缓存或强制刷新页面查看最新格式")
            else:
                print(f"❌ 部署失败，返回码: {result.returncode}")
        except Exception as e:
            print(f"❌ EdgeOne Pages CLI 部署异常: {e}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 第三步：为每个分组拼接公网链接并发送消息
        for group_info in all_group_files:
            try:
                group_name = group_info['name']
                content = group_info['content']
                filename = group_info['filename']
                
                print(f"\n🔗 处理 {group_name} 的Web链接...")
                print(f"   文件名: {filename}")
                print(f"   内容长度: {len(content)} 字符")
                
                # 拼接公网链接 - 使用正确的URL格式（去掉/reports/前缀）
                public_url = f"https://edge.haierht.cn/{filename}"
                print(f"   最终URL: {public_url}")
                
                # 发送消息 - 确保总是附上web链接，无论是否有数据
                msg = content + f"\n🌐 查看完整Web页面: {public_url}"
                print(f"【{group_name}】Web链接: {public_url}")
                print(f"   消息长度: {len(msg)} 字符")
                print(f"   内容长度: {len(content)} 字符")
                print(f"   链接长度: {len(f'🌐 查看完整Web页面: {public_url}')} 字符")
                send_wecomchan_segment(msg)
                time.sleep(2)
                all_group_links.append(f"{group_name}: {public_url}")
                print(f"✅ {group_name} 发送完成")
            except Exception as e:
                print(f"❌ {group_name} 发送异常: {e}")
                continue
    else:
        print("⚠️ 没有生成任何HTML文件")
    
    print("✅ 多事业部日报全部生成、统一部署并推送完成！")
    if all_group_links:
        print("\n📋 所有链接汇总:")
        for link in all_group_links:
            print(f"  {link}")

except Exception as e:
    print(f"❌ 执行异常: {e}\n{traceback.format_exc()}")
