#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多事业部日报自动化主流程 - 整数数据版本
- 五大事业部、五大渠道独立分组
- 数据过滤（刷单、订单状态、线上店铺、五大渠道）
- 报表生成、web发布、微信推送
- 所有数据保持整数，无小数点
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
    
    log_filename = f"logs/多事业部日报数据_整数版_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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

WECHAT_API = "http://212.64.57.87:5001/send"
WECHAT_TOKEN = "wecomchan_token"
WECHAT_USER = "weicungang"
REPORTS_DIR = "reports"

# 固定收件人
always_users = ["weicungang"]

# 事业部配置
business_groups = {
    "空调事业部": {"keywords": ["空调"], "users": ["weicungang"]},
    "制冷事业部": {"keywords": ["冰箱","冷柜"], "users": ["weicungang"]},
    "洗护事业部": {"keywords": ["洗衣机"], "users": ["weicungang"]},
    "水联网事业部": {"keywords": ["热水器", "净水", "采暖", "电热水器", "燃气热水器", "多能源热水器"], "users": ["weicungang"]},
    "厨电洗碗机事业部": {"keywords": ["厨电", "洗碗机"], "users": ["weicungang"]}
}

# 渠道分组配置
CHANNEL_GROUPS = {
    "卡萨帝渠道": {"keywords": ["卡萨帝", "小红书"], "users": ["weicungang"]},
    "天猫渠道": {"keywords": ["天猫", "淘宝"], "users": ["weicungang"]},
    "京东渠道": {"keywords": ["京东"], "users": ["weicungang"]},
    "拼多多渠道": {"keywords": ["拼多多"], "users": ["weicungang"]},
    "抖音渠道": {"keywords": ["抖音", "快手"], "users": ["weicungang"]}
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

def to_integer(val):
    """确保所有数值转换为整数"""
    if pd.isnull(val):
        return 0
    val = str(val).replace('，', '').replace(',', '').replace(' ', '').replace('\u3000', '')
    try:
        return int(float(val))
    except:
        return 0

def calculate_ratio_int(current, previous):
    """计算环比，返回整数百分比"""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    ratio = int(((current - previous) / previous) * 100)
    if ratio > 0:
        return f"+{ratio}%"
    elif ratio < 0:
        return f"{ratio}%"
    else:
        return "0%"

def is_online_shop(shop_name):
    if not isinstance(shop_name, str):
        return False
    online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美']
    return any(kw in shop_name for kw in online_keywords)

def get_target_users(group_name, group_type):
    """根据分组名称和类型获取目标用户"""
    users = set(always_users)
    
    if group_type == 'business':
        for dept, conf in business_groups.items():
            if dept == group_name:
                users.update(conf["users"])
                break
    else:
        for channel, conf in CHANNEL_GROUPS.items():
            if channel == group_name:
                users.update(conf["users"])
                break
    
    return list(set(users))

def _send_single_message(msg, target_user=None):
    """发送单条消息"""
    to_user = target_user if target_user else WECHAT_USER
    data = {"msg": msg, "token": WECHAT_TOKEN, "to_user": to_user}
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(WECHAT_API, json=data, timeout=15)
            if "errcode" in resp.text and "0" in resp.text:
                return True
            else:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        except:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    return False

def send_wecomchan_segment(content, target_users=None):
    """分段发送消息"""
    max_chars = 1500
    
    if target_users is None:
        target_users = [WECHAT_USER]
    
    target_users = list(set(target_users))
    
    for user in target_users:
        link_pattern = r'🌐 查看完整Web页面: (https://[^\s]+)'
        link_match = re.search(link_pattern, content)
        
        if link_match:
            link = link_match.group(1)
            link_text = f"🌐 查看完整Web页面: {link}"
            content_without_link = content.replace(link_text, "").strip()
            
            if len(content_without_link) + len(link_text) > max_chars:
                available_chars = max_chars - len(link_text) - 10
                truncated_content = content_without_link[:available_chars].rstrip('\n')
                final_content = truncated_content + f"\n{link_text}"
            else:
                final_content = content
        else:
            if len(content) > max_chars:
                final_content = content[:max_chars].rstrip('\n')
            else:
                final_content = content
        
        _send_single_message(final_content, user)
        time.sleep(1)

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
    """统一的HTML生成函数"""
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

# ========== 数据获取 ==========
def get_erp_data(report_date):
    """从数据库获取ERP数据"""
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

def get_prev_data(prev_date):
    """从数据库获取同期数据"""
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

def get_fenxiao_data(report_date):
    """从HT_fenxiao表获取分销数据"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("DESCRIBE HT_fenxiao")
        columns = [row[0] for row in cursor.fetchall()]
        
        amount_fields = [col for col in columns if '金额' in col or '实付' in col or '支付' in col]
        shop_fields = [col for col in columns if '店铺' in col or '商店' in col]
        status_fields = [col for col in columns if '状态' in col or '订单' in col]
        time_fields = [col for col in columns if '时间' in col or '支付' in col]
        product_fields = [col for col in columns if '产品' in col or '名称' in col]
        qty_fields = [col for col in columns if '数量' in col or '采购数量' in col]
        
        amount_col = '用户实际支付总额' if '用户实际支付总额' in columns else (amount_fields[0] if amount_fields else '用户实际支付金额')
        shop_col = '分销商店铺名称' if '分销商店铺名称' in columns else (shop_fields[0] if shop_fields else '分销商店铺名称')
        status_col = '订单状态' if '订单状态' in columns else (status_fields[0] if status_fields else '订单状态')
        time_col = '采购单支付时间' if '采购单支付时间' in columns else (time_fields[0] if time_fields else '采购单支付时间')
        product_col = '产品名称' if '产品名称' in columns else (product_fields[0] if product_fields else '产品名称')
        qty_col = '采购数量' if '采购数量' in columns else (qty_fields[0] if qty_fields else '采购数量')
        
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
        
        df_fenxiao = pd.read_sql(sql, conn)
        
        if not df_fenxiao.empty:
            # 优化产品匹配逻辑：批量处理避免重复查询
            logger.info("🔄 优化产品匹配逻辑...")
            
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
            
            df_fenxiao['品类'] = df_fenxiao['货品名称'].apply(lambda x: "其他" if not isinstance(x, str) else x)
            
            def add_jingdong_prefix(shop_name):
                if not isinstance(shop_name, str):
                    return shop_name
                # 如果已经有"京东-"前缀，直接返回
                if shop_name.startswith('京东-'):
                    return shop_name
                # 统一添加"京东-"前缀
                return f"京东-{shop_name}"
            
            df_fenxiao['店铺'] = df_fenxiao['店铺'].apply(add_jingdong_prefix)
            
        conn.close()
        return df_fenxiao
    except Exception as e:
        logger.error(f"❌ 获取分销数据失败: {e}")
        return pd.DataFrame()

def categorize_product(product_name):
    """从产品名称中识别品类"""
    if not isinstance(product_name, str):
        return "其他"
    
    product_name_lower = product_name.lower()
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
            return category
    
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

# ========== 报表生成 ==========
def classify_channel(shop_name):
    """渠道归类函数"""
    if not isinstance(shop_name, str):
        return "其他"
    
    if any(kw in shop_name for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']):
        return "卡萨帝渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['京东渠道']['keywords']):
        return "京东渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['天猫渠道']['keywords']):
        return "天猫渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['拼多多渠道']['keywords']):
        return "拼多多渠道"
    if any(kw in shop_name for kw in CHANNEL_GROUPS['抖音渠道']['keywords']):
        return "抖音渠道"
    return "其他"

def generate_group_report(group_name, group_type, keywords, df, df_prev, report_date):
    if group_type == 'business':
        def business_filter(row):
            if '数据来源' in row and row['数据来源'] == '分销' and '品类' in row:
                return any(kw in str(row['品类']) for kw in keywords)
            else:
                return any(kw in str(row[CATEGORY_COL]) for kw in keywords)
        
        group_df = df[df.apply(business_filter, axis=1)]
        prev_group_df = df_prev[df_prev.apply(business_filter, axis=1)] if df_prev is not None else None
    else:
        if group_name == '卡萨帝渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))] if df_prev is not None else None
        elif group_name == '天猫渠道':
            group_df = df[df[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in CHANNEL_GROUPS['天猫渠道']['keywords'])) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: (any(kw in str(x) for kw in CHANNEL_GROUPS['天猫渠道']['keywords'])) and not any(kw in str(x) for kw in CHANNEL_GROUPS['卡萨帝渠道']['keywords']))] if df_prev is not None else None
        else:
            group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[group_name]['keywords']))]
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in CHANNEL_GROUPS[group_name]['keywords']))] if df_prev is not None else None
    
    if group_df.empty:
        content = f"🏢 {group_name}日报\n📅 数据日期: {report_date}\n\n⚠️ 今日暂无销售数据"
        title_cn = f"{group_name}日报（{report_date}）"
        empty_content = f"""🏢 {group_name}日报
📅 数据日期: {report_date}

━━━━━━━━━━━━━━━━━━━━━━
⚠️ 今日暂无销售数据
该事业部/渠道今日暂无销售数据，请查看其他时间段的报告。"""
        
        html_content = generate_html_content(title_cn, empty_content)
        file_prefix = to_pinyin(group_name)
        filename = f"{file_prefix}_{report_date}.html".replace('/', '-')
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return content, filename
    
    # 数据类型转换
    group_df[AMOUNT_COL] = group_df[AMOUNT_COL].apply(to_integer)
    group_df[QTY_COL] = group_df[QTY_COL].apply(to_integer)
    
    total_amount = group_df[AMOUNT_COL].sum()
    total_qty = group_df[QTY_COL].sum()
    avg_price = total_amount // total_qty if total_qty > 0 else 0
    
    prev_amount = 0
    prev_qty = 0
    if prev_group_df is not None and not prev_group_df.empty:
        prev_group_df[AMOUNT_COL] = prev_group_df[AMOUNT_COL].apply(to_integer)
        prev_group_df[QTY_COL] = prev_group_df[QTY_COL].apply(to_integer)
        prev_amount = prev_group_df[AMOUNT_COL].sum()
        prev_qty = prev_group_df[QTY_COL].sum()
    
    prev_avg_price = prev_amount // prev_qty if prev_qty > 0 else 0
    
    # 分销数据统计
    fenxiao_amount = 0
    fenxiao_qty = 0
    if '数据来源' in group_df.columns:
        fenxiao_df = group_df[group_df['数据来源'] == '分销']
        if not fenxiao_df.empty:
            fenxiao_amount = fenxiao_df[AMOUNT_COL].sum()
            fenxiao_qty = fenxiao_df[QTY_COL].sum()
    
    # 同期分销数据
    prev_fenxiao_amount = 0
    prev_fenxiao_qty = 0
    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
        prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
        if not prev_fenxiao_df.empty:
            prev_fenxiao_amount = prev_fenxiao_df[AMOUNT_COL].sum()
            prev_fenxiao_qty = prev_fenxiao_df[QTY_COL].sum()
    
    # 品类明细
    category_data = group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    category_data = category_data.sort_values(AMOUNT_COL, ascending=False)
    prev_category_data = None
    if prev_group_df is not None:
        prev_category_data = prev_group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 渠道数据
    channel_data = None
    prev_channel_data = None
    if group_type == 'business':
        group_df['渠道'] = group_df[SHOP_COL].apply(classify_channel)
        channel_data = group_df.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        channel_data = channel_data[channel_data['渠道'].isin(CHANNEL_GROUPS.keys())]
        channel_data = channel_data.sort_values(AMOUNT_COL, ascending=False)
        if prev_group_df is not None:
            prev_group_df['渠道'] = prev_group_df[SHOP_COL].apply(classify_channel)
            prev_channel_data = prev_group_df.groupby('渠道').agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 店铺数据
    shop_data = group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    shop_data = shop_data.sort_values(AMOUNT_COL, ascending=False)
    prev_shop_data = None
    if prev_group_df is not None:
        prev_shop_data = prev_group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # TOP单品
    product_data = group_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    product_data = product_data[product_data[AMOUNT_COL] > 1000]
    product_data = product_data.sort_values(AMOUNT_COL, ascending=False)
    
    # 生成内容
    web_content = f"""🏢 {group_name}日报
📅 数据日期: {report_date}

━━━━━━━━━━━━━━━━━━━━━━
📊 整体数据
总销售额: ¥{total_amount:,}（环比:{calculate_ratio_int(total_amount, prev_amount)}）
总销量: {total_qty}件（环比:{calculate_ratio_int(total_qty, prev_qty)}）
平均单价: ¥{avg_price:,}（环比:{calculate_ratio_int(avg_price, prev_avg_price)}）"""

    if fenxiao_amount > 0:
        web_content += f"""
其中分销销售: ¥{fenxiao_amount:,}（环比:{calculate_ratio_int(fenxiao_amount, prev_fenxiao_amount)}），{fenxiao_qty}件"""

    web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n📋 品类明细"
    
    for _, row in category_data.iterrows():
        cat = row[CATEGORY_COL]
        amount = to_integer(row[AMOUNT_COL])
        qty = to_integer(row[QTY_COL])
        price = amount // qty if qty else 0
        prev_amount_cat = to_integer(prev_category_data.loc[prev_category_data[CATEGORY_COL] == cat, AMOUNT_COL].sum()) if prev_category_data is not None else 0
        web_content += f"\n• {cat}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_cat)}），{qty}件 | 单价: ¥{price:,}"

    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 渠道数据"
        for _, row in channel_data.iterrows():
            channel = row['渠道']
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            price = amount // qty if qty else 0
            prev_amount_channel = to_integer(prev_channel_data.loc[prev_channel_data['渠道'] == channel, AMOUNT_COL].sum()) if prev_channel_data is not None else 0
            web_content += f"\n• {channel}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_channel)}），{qty}件 | 单价: ¥{price:,}"

    if shop_data is not None and not shop_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏪 店铺数据"
        for _, row in shop_data.head(10).iterrows():
            shop = row[SHOP_COL]
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            prev_amount_shop = to_integer(prev_shop_data.loc[prev_shop_data[SHOP_COL] == shop, AMOUNT_COL].sum()) if prev_shop_data is not None else 0
            web_content += f"\n• {shop}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_shop)}），{qty}件"

    if product_data is not None and not product_data.empty:
        web_content += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏆 TOP 单品"
        for _, row in product_data.head(10).iterrows():
            model = row[MODEL_COL]
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            price = amount // qty if qty else 0
            prev_amount_product = 0
            if df_prev is not None:
                prev_product = df_prev[df_prev[MODEL_COL] == model]
                if not prev_product.empty:
                    prev_amount_product = prev_product[AMOUNT_COL].sum()
            web_content += f"\n• {model}: ¥{amount:,}，{qty}件 | 单价: ¥{price:,}"

    # 生成简洁微信内容
    content = f"🏢 {group_name}日报\n📅 数据日期: {report_date}\n\n"
    content += f"📊 整体数据\n总销售额: ¥{total_amount:,}（环比:{calculate_ratio_int(total_amount, prev_amount)}）\n总销量: {total_qty}件（环比:{calculate_ratio_int(total_qty, prev_qty)}）\n平均单价: ¥{avg_price:,}"
    
    if fenxiao_amount > 0:
        content += f"\n其中分销金额: ¥{fenxiao_amount:,}（环比:{calculate_ratio_int(fenxiao_amount, prev_fenxiao_amount)}）"
    
    content += "\n\n📋 品类明细\n"
    for i, (_, row) in enumerate(category_data.iterrows()):
        if i >= 3:
            break
        cat = row[CATEGORY_COL]
        amount = to_integer(row[AMOUNT_COL])
        qty = to_integer(row[QTY_COL])
        prev_amount_cat = to_integer(prev_category_data.loc[prev_category_data[CATEGORY_COL] == cat, AMOUNT_COL].sum()) if prev_category_data is not None else 0
        content += f"• {cat}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_cat)}），{qty}件\n"
    
    if group_type == 'business' and channel_data is not None and not channel_data.empty:
        content += "\n🏪 渠道数据\n"
        for i, (_, row) in enumerate(channel_data.iterrows()):
            if i >= 3:
                break
            channel = row['渠道']
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            prev_amount_channel = to_integer(prev_channel_data.loc[prev_channel_data['渠道'] == channel, AMOUNT_COL].sum()) if prev_channel_data is not None else 0
            content += f"• {channel}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_channel)}），{qty}件\n"
    
    if shop_data is not None and not shop_data.empty:
        content += "\n🏪 店铺数据\n"
        for i, (_, row) in enumerate(shop_data.iterrows()):
            if i >= 3:
                break
            shop = row[SHOP_COL]
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            prev_amount_shop = to_integer(prev_shop_data.loc[prev_shop_data[SHOP_COL] == shop, AMOUNT_COL].sum()) if prev_shop_data is not None else 0
            content += f"• {shop}: ¥{amount:,}（环比:{calculate_ratio_int(amount, prev_amount_shop)}），{qty}件\n"
    
    if product_data is not None and not product_data.empty:
        content += "\n🏆 TOP单品\n"
        for i, (_, row) in enumerate(product_data.iterrows()):
            if i >= 3:
                break
            model = row[MODEL_COL]
            amount = to_integer(row[AMOUNT_COL])
            qty = to_integer(row[QTY_COL])
            content += f"• {model}: ¥{amount:,}，{qty}件\n"
    
    title_cn = f"{group_name}日报（{report_date}）"
    html_content = generate_html_content(title_cn, web_content)
    
    file_prefix = to_pinyin(group_name)
    filename = f"{file_prefix}_{report_date}.html".replace('/', '-')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return content, filename

# ========== 主程序 ==========
logger.info("🚀 多事业部日报数据分析系统启动...")

yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime('%Y-%m-%d')
logger.info(f"📅 分析日期: {yesterday_str}")

logger.info("📊 开始获取ERP数据...")
df_erp = get_erp_data(yesterday_str)
logger.info(f"📊 ERP数据获取完成: {len(df_erp)} 行")

if df_erp is None or len(df_erp) == 0:
    logger.error("❌ 无法获取ERP数据，程序退出")
    sys.exit(1)

logger.info("📊 开始获取同期数据...")
prev_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
df_prev = get_prev_data(prev_date)
logger.info(f"📊 同期数据获取完成: {len(df_prev) if df_prev is not None else 0} 行")

logger.info("📊 开始获取分销数据...")
df_fenxiao = get_fenxiao_data(yesterday_str)
logger.info(f"📊 分销数据获取完成: {len(df_fenxiao) if df_fenxiao is not None else 0} 行")

# 数据预处理
logger.info("🚀 开始数据预处理...")
df_erp[AMOUNT_COL] = df_erp[AMOUNT_COL].apply(to_integer)
df_erp[QTY_COL] = df_erp[QTY_COL].apply(to_integer)
df_erp = df_erp[(df_erp[AMOUNT_COL] > 0) & (df_erp[QTY_COL] > 0)]
df_erp = df_erp[df_erp[SHOP_COL].apply(is_online_shop)]

def is_five_channel(shop):
    if not isinstance(shop, str):
        return False
    five_channels = ['京东', '天猫', '拼多多', '抖音', '卡萨帝']
    return any(channel in shop for channel in five_channels)

df_erp = df_erp[df_erp[SHOP_COL].apply(is_five_channel)]
df_erp['数据来源'] = 'ERP'

if df_fenxiao is not None and len(df_fenxiao) > 0:
    df_fenxiao[AMOUNT_COL] = df_fenxiao[AMOUNT_COL].apply(to_integer)
    df_fenxiao[QTY_COL] = df_fenxiao[QTY_COL].apply(to_integer)
    df_fenxiao = df_fenxiao[(df_fenxiao[AMOUNT_COL] > 0) & (df_fenxiao[QTY_COL] > 0)]
    df_fenxiao['数据来源'] = '分销'
    df_erp = pd.concat([df_erp, df_fenxiao], ignore_index=True)

if df_prev is not None and len(df_prev) > 0:
    df_prev[AMOUNT_COL] = df_prev[AMOUNT_COL].apply(to_integer)
    df_prev[QTY_COL] = df_prev[QTY_COL].apply(to_integer)
    df_prev = df_prev[(df_prev[AMOUNT_COL] > 0) & (df_prev[QTY_COL] > 0)]
    df_prev = df_prev[df_prev[SHOP_COL].apply(is_online_shop)]
    df_prev = df_prev[df_prev[SHOP_COL].apply(is_five_channel)]
    df_prev['数据来源'] = 'ERP'

logger.info(f"📊 数据预处理完成 - 当前数据: {len(df_erp)} 行")
logger.info(f"📊 数据预处理完成 - 同期数据: {len(df_prev) if df_prev is not None else 0} 行")

os.makedirs('reports', exist_ok=True)

all_group_files = []
all_group_links = []

for dept, keywords in business_groups.items():
    try:
        logger.info(f"\n🔄 正在处理 {dept}...")
        target_users = get_target_users(dept, 'business')
        logger.info(f"📤 {dept} 目标用户: {', '.join(target_users)}")
        
        content, filename = generate_group_report(dept, 'business', keywords['keywords'], df_erp, df_prev, yesterday_str)
        if content and filename:
            all_group_files.append({
                'name': dept,
                'content': content,
                'filename': filename,
                'type': 'business',
                'target_users': target_users
            })
            logger.info(f"✅ {dept} 处理完成")
    except Exception as e:
        logger.error(f"❌ {dept} 处理异常: {e}")
        continue

for channel, keywords in CHANNEL_GROUPS.items():
    try:
        logger.info(f"\n🔄 正在处理 {channel}...")
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
            logger.info(f"✅ {channel} 处理完成")
    except Exception as e:
        logger.error(f"❌ {channel} 处理异常: {e}")
        continue

logger.info("📤 开始发送微信消息...")
for group_info in all_group_files:
    group_name = group_info['name']
    content = group_info['content']
    filename = group_info['filename']
    target_users = group_info['target_users']
    
    try:
        public_url = f"https://edge.haierht.cn/{filename}"
        msg = content + f"\n🌐 查看完整Web页面: {public_url}"
        logger.info(f"📤 发送 {group_name} 报告给 {len(target_users)} 个用户")
        send_wecomchan_segment(msg, target_users)
        time.sleep(1)
        all_group_links.append(f"{group_name}: {public_url}")
    except Exception as e:
        logger.error(f"❌ {group_name} 发送异常: {e}")
        continue

logger.info("🎉 多事业部日报数据分析完成！")