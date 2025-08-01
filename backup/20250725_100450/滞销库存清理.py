#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import glob
import requests
from datetime import datetime, timedelta
import re
import time
import sys

# 文件路径设置
erp_folder = r"E:\电商数据\虹图\ERP订单明细"
zhixiao_file = r"E:\电商数据\虹图\滞销清理.xlsx"

# 固定收件人
always_users = ["weicungang", "haozhu"]

# 事业部配置（如需补充请补充）
business_groups = {
    "空调事业部": {"keywords": ["空调"], "users": ["YangNing", "NingWenBo", "LiuYiWei", "ZhangYuHe","yangchao"]},
    "冰冷事业部": {"keywords": ["冰箱","冷柜"], "users": ["HuShengJie", "WeiCunGang", "JiaWenLong", "yangchao", "lining", "muping","ZhangWangWang"]},
    "洗护事业部": {"keywords": ["洗衣机"], "users": ["yuaiqin", "WangXiaoLong", "yangchao","lining", "muping","zhaohaoran"]},
    "厨卫事业部": {"keywords": ["热水器", "厨电", "消毒柜", "燃气灶", "油烟机", "净水器", "洗碗机"], "users": ["WangMengMeng", "NianJianHeng", "YangJingBo", "WuXiang"]}
}

def get_target_users(category):
    """根据品类获取目标用户列表"""
    users = set(always_users)
    for dept, conf in business_groups.items():
        if any(kw in str(category) for kw in conf["keywords"]):
            users.update(conf["users"])
    return list(users)

# 替换品类emoji为图片路径
category_image_map = {
    '冰箱': 'haier_fridge.jpg',
    '热水器': 'haier_water_heater.jpg',
    '厨电': 'haier_kitchen.jpg',
    '洗碗机': 'haier_dishwasher.jpg',
    '洗衣机': 'haier_washer.jpg',
    '空调': 'haier_aircon.jpg',
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

def send_wecomchan_segment(result, target_users=None):
    """发送消息给指定用户列表"""
    if target_users is None:
        target_users = always_users
    
    # 确保用户列表去重
    target_users = list(set(target_users))
    
    print(f"📤 准备发送给 {len(target_users)} 个用户: {', '.join(target_users)}")
    
    # 为每个用户单独发送
    success_count = 0
    for user in target_users:
        success = _send_single_message(result, user)
        if success:
            success_count += 1
        else:
            send_failure_report_to_admin("滞销库存清理.py", f"发送给用户 {user} 失败", user)
    
    if success_count == 0:
        send_failure_report_to_admin("滞销库存清理.py", "所有用户发送失败", "所有用户")
    else:
        print(f"✅ 成功发送给 {success_count}/{len(target_users)} 个用户")

def _send_single_message(message, to_user=None):
    """发送单条消息给指定用户"""
    url = "http://212.64.57.87:5001/send"
    token = "wecomchan_token"
    data = {
        "msg": message,
        "token": token,
    }
    
    # 如果指定了用户，添加到请求中
    if to_user:
        data["to_user"] = to_user
        print(f"📤 发送给用户: {to_user}")
    
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

def send_failure_report_to_admin(script_name, error_details, target_user):
    """发送失败报告给管理员"""
    failure_msg = f"""🚨 发送失败报告

📋 脚本名称: {script_name}
👤 目标用户: {target_user}
⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ 失败原因: {error_details}

请检查网络连接和服务器状态。"""
    
    admin_data = {"msg": failure_msg, "token": "wecomchan_token", "to_user": "weicungang"}
    try:
        resp = requests.post("http://212.64.57.87:5001/send", json=admin_data, timeout=30)
        print(f"📤 失败报告发送结果: {resp.text[:100]}...")
    except Exception as e:
        print(f"❌ 失败报告发送异常: {e}")

try:
    # 1. 找到昨天的ERP订单明细文件
    now = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)
    
    # 读取所有ERP文件
    pattern = os.path.join(erp_folder, "订单明细*.xlsx")
    erp_files = glob.glob(pattern)
    # 跳过Excel临时锁定文件
    erp_files = [f for f in erp_files if not os.path.basename(f).startswith('~$')]
    if not erp_files:
        result = f"未找到ERP订单明细文件，路径: {erp_folder}"
        globals()['result'] = result
        exit()
    
    # 读取所有文件并合并
    all_dfs = []
    for file in erp_files:
        try:
            df = pd.read_excel(file)
            all_dfs.append(df)
        except Exception as e:
            print(f"❌ 读取文件失败: {file}, 错误: {e}")
            continue
    
    if not all_dfs:
        result = "❌ 没有成功读取任何ERP文件"
        globals()['result'] = result
        exit()
    
    # 合并所有数据
    df_all = pd.concat(all_dfs, ignore_index=True)
    
    # 筛选昨天的数据（修复：只取昨天一天，不是月累计）
    df_all[DATE_COL] = pd.to_datetime(df_all[DATE_COL], errors='coerce')
    df_erp = df_all[
        (df_all[DATE_COL].dt.date == yesterday.date())
    ].copy()
    
    print(f"📅 数据日期: {yesterday.strftime('%Y-%m-%d')}")
    print(f"📊 筛选后数据行数: {len(df_erp)}")

    # 检查必需列是否存在
    check_required_columns(df_erp)

    # 1. 识别客服备注列，剔除包含"抽纸"、"纸巾"或完全等于"不发货"的订单
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

    # 2. 识别订单状态列，剔除"未付款"和"已取消"订单
    order_status_col = None
    for col in df_erp.columns:
        if '订单状态' in str(col) or '状态' in str(col):
            order_status_col = col
            break
    if order_status_col and order_status_col in df_erp.columns:
        df_erp = df_erp[~df_erp[order_status_col].astype(str).str.contains('未付款|已取消', na=False)]

    # 识别其他必要列
    spec_col = '规格名称'
    shop_col = None
    qty_col = None
    for col in df_erp.columns:
        col_str = str(col).lower()
        if '店铺' in col_str:
            shop_col = col
        elif '实发数量' in col_str or '数量' in col_str:
            qty_col = col
    if not all([shop_col, spec_col, qty_col]):
        result = f"未找到必要的列: 店铺={shop_col}, 规格名称={spec_col}, 实发数量={qty_col}"
        globals()['result'] = result
        exit()

    df_zhixiao = pd.read_excel(zhixiao_file)
    category_col = None
    zhixiao_spec_col = None
    for col in df_zhixiao.columns:
        col_str = str(col).lower()
        if '品类' in col_str:
            category_col = col
        elif '规格名称' in col_str or '规格' in col_str:
            zhixiao_spec_col = col
    if not all([category_col, zhixiao_spec_col]):
        result = f"未找到必要的列: 品类={category_col}, 规格名称={zhixiao_spec_col}"
        globals()['result'] = result
        exit()

    # 数据处理
    df_erp[qty_col] = pd.to_numeric(df_erp[qty_col], errors='coerce').fillna(0)
    spec_col_clean = spec_col + '_CLEAN'
    df_erp[spec_col_clean] = df_erp[spec_col].astype(str).str.strip().str.upper()
    zhixiao_spec_col_clean = zhixiao_spec_col + '_CLEAN'
    df_zhixiao[zhixiao_spec_col_clean] = df_zhixiao[zhixiao_spec_col].astype(str).str.strip().str.upper()

    # 日销量统计
    sales_summary = df_erp.groupby([spec_col_clean, shop_col])[qty_col].sum().reset_index()
    total_sales = df_erp.groupby(spec_col_clean)[qty_col].sum().reset_index()
    total_sales.columns = [spec_col_clean, '总销量']

    # 结果生成
    report_date = yesterday.strftime("%Y-%m-%d")
    report_title = f"\n📦 滞销库存清理日报\n📅 数据日期: {report_date}\n"
    result = report_title
    categories = df_zhixiao[category_col].unique()

    # 恢复按品类分别发送的逻辑
    for idx, category in enumerate(categories):
        if pd.isna(category):
            continue
        
        # 恢复品类emoji逻辑
        if '冰箱' in str(category):
            cat_emoji = '🧊'
        elif '洗衣机' in str(category):
            cat_emoji = '🧺'
        elif '热水器' in str(category):
            cat_emoji = '♨️'
        elif '空调' in str(category):
            cat_emoji = '❄️'
        elif '厨电' in str(category) or '灶' in str(category):
            cat_emoji = '🍽️'
        elif '洗碗机' in str(category):
            cat_emoji = '🍽️'
        else:
            cat_emoji = '📦'
        
        # 统计该品类合计销量
        category_specs = df_zhixiao[df_zhixiao[category_col] == category][[zhixiao_spec_col, zhixiao_spec_col_clean]].values
        total_category_qty = 0
        spec_sales_list = []
        spec_zero_list = []
        for spec, spec_clean in category_specs:
            if pd.isna(spec):
                continue
            spec_total = total_sales[total_sales[spec_col_clean] == spec_clean]['总销量'].sum()
            if spec_total == 0:
                spec_zero_list.append((spec, spec_clean, spec_total))
            else:
                spec_sales_list.append((spec, spec_clean, spec_total))
                total_category_qty += int(spec_total)
        
        # 构建该品类的报告内容
        segment = f"📋 滞销清理进度（{report_date}）\n{cat_emoji}\n【{category}】\n合计销售：{total_category_qty}台\n"
        if spec_sales_list:
            segment += "\n✅ 动销产品：\n"
            spec_sales_list.sort(key=lambda x: -x[2])
            for spec, spec_clean, spec_total in spec_sales_list:
                segment += f"  • {spec}：{int(spec_total)}台\n"
                # 店铺明细
                spec_shops = sales_summary[sales_summary[spec_col_clean] == spec_clean]
                spec_shops = spec_shops[spec_shops[qty_col] > 0]
                spec_shops = spec_shops.sort_values(qty_col, ascending=False)
                shop_details = []
                for _, row in spec_shops.iterrows():
                    shop_name = row[shop_col]
                    if is_online_shop(shop_name):
                        shop_qty = int(row[qty_col])
                        shop_details.append(f"{shop_name}{shop_qty}台")
                if shop_details:
                    segment += f"    └ {'，'.join(shop_details)}\n"
        if spec_zero_list:
            segment += "\n❗️🚨 无动销产品：\n"
            for spec, spec_clean, spec_total in spec_zero_list:
                segment += f"  • {spec}：0台（特别提醒）\n"
        
        # 获取该品类的目标用户
        target_users = get_target_users(category)
        print(f"📤 发送 {category} 品类报告给用户: {', '.join(target_users)}")
        
        # 发送该品类的报告
        send_wecomchan_segment(segment, target_users)
        
        # 添加间隔，避免发送过快
        time.sleep(1)
    
    globals()['result'] = result

except Exception as e:
    result = f"数据处理出错: {e}"
    globals()['result'] = result

