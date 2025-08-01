#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import glob
import requests
from datetime import datetime, timedelta
import re
import time
import json
import sys

# 文件路径设置
erp_folder = r"E:\电商数据\虹图\ERP订单明细"
zhixiao_file = r"E:\电商数据\虹图\滞销清理.xlsx"

# 固定收件人
always_users = ["haozhu", "weicungang"]  # 统一包含weicungang

# 事业部配置（如需补充请补充）
business_groups = {
    "空调事业部": {"keywords": ["空调"], "users": ["YangNing", "NingWenBo", "LiuYiWei", "ZhangYuHe","yangchao"]},
    "冰冷事业部": {"keywords": ["冰箱","冷柜"], "users": ["HuShengJie", "JiaWenLong", "yangchao", "lining", "muping","ZhangWangWang"]},  # 移除weicungang，避免重复
    "洗护事业部": {"keywords": ["洗衣机"], "users": ["yuaiqin", "WangXiaoLong", "yangchao","lining", "muping","zhaohaoran"]},
    "厨卫事业部": {"keywords": ["热水器", "厨电", "消毒柜", "燃气灶", "油烟机", "净水器", "洗碗机"], "users": ["WangMengMeng", "NianJianHeng", "YangJingBo", "WuXiang"]}
}

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

def to_number(val):
    """将各种格式的数值转换为数字"""
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

# ====== 取消企业微信API自动拉取通讯录和userid替换功能 ======
# 直接使用名单，无需userid映射

def get_target_users(category):
    users = set(always_users)
    for dept, conf in business_groups.items():
        if any(kw in str(category) for kw in conf["keywords"]):
            users.update(conf["users"])
    # weicungang已在always_users中，无需重复添加
    return list(users)

def is_online_shop(shop_name):
    if not isinstance(shop_name, str):
        return False
    online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美']
    return any(kw in shop_name for kw in online_keywords)

try:
    # 1. 找到最新的ERP订单明细文件
    pattern = os.path.join(erp_folder, "订单明细*.xlsx")
    erp_files = glob.glob(pattern)
    # 跳过Excel临时锁定文件
    erp_files = [f for f in erp_files if not os.path.basename(f).startswith('~$')]
    if not erp_files:
        result = f"未找到ERP订单明细文件，路径: {erp_folder}"
        globals()['result'] = result
        exit()
    latest_erp_file = max(erp_files, key=os.path.getmtime)
    df_erp = pd.read_excel(latest_erp_file)
    
    # 检查必需列是否存在
    check_required_columns(df_erp)
    
    # 1. 固定使用客服备注列，剔除包含"抽纸"、"纸巾"或完全等于"不发货"的订单
    remark_col = '客服备注'
    if remark_col in df_erp.columns:
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
    else:
        print(f"⚠️ 未找到客服备注列，跳过刷单剔除")
    
    # 2. 识别订单状态列，剔除"未付款"和"已取消"订单
    order_status_col = None
    for col in df_erp.columns:
        if '订单状态' in str(col) or '状态' in str(col):
            order_status_col = col
            break
    if order_status_col and order_status_col in df_erp.columns:
        df_erp = df_erp[~df_erp[order_status_col].astype(str).str.contains('未付款|已取消', na=False)]
    
    # 使用固定列名，不再自动检测
    shop_col = SHOP_COL
    spec_col = MODEL_COL
    qty_col = QTY_COL
    
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
    # 添加金额列的处理
    df_erp[AMOUNT_COL] = df_erp[AMOUNT_COL].apply(to_number)
    spec_col_clean = spec_col + '_CLEAN'
    df_erp[spec_col_clean] = df_erp[spec_col].astype(str).str.strip().str.upper()
    zhixiao_spec_col_clean = zhixiao_spec_col + '_CLEAN'
    df_zhixiao[zhixiao_spec_col_clean] = df_zhixiao[zhixiao_spec_col].astype(str).str.strip().str.upper()
    
    # 数据统计
    sales_summary = df_erp.groupby([spec_col_clean, shop_col])[qty_col].sum().reset_index()
    total_sales = df_erp.groupby(spec_col_clean)[qty_col].sum().reset_index()
    total_sales.columns = [spec_col_clean, '总销量']
    
    # 结果生成
    latest_date = os.path.basename(latest_erp_file).replace('订单明细','').replace('.xlsx','')
    report_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    report_title = f"\n📦 滞销库存清理日报\n📅 数据日期: {report_date}\n"
    result = report_title
    categories = df_zhixiao[category_col].unique()
    
    # 使用T-1日期
    progress_time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    all_segments = []
    seen_categories = set()
    for idx, category in enumerate(categories):
        if pd.isna(category) or category in seen_categories:
            continue
        seen_categories.add(category)
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
        # 构建分段内容
        segment = f"📋 滞销清理进度（{progress_time}）\n{cat_emoji}\n【{category}】\n合计销售：{total_category_qty}台\n"
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
        segment += "\n"
        all_segments.append(segment)

    def _smart_split_content(content, max_chars=800):
        """智能分割内容，避免在单词中间分割"""
        if len(content) <= max_chars:
            return [content]
        
        segments = []
        current_segment = ""
        
        # 按行分割
        lines = content.split('\n')
        
        for line in lines:
            # 如果当前行加上换行符超过限制
            if len(current_segment) + len(line) + 1 > max_chars:
                if current_segment:
                    segments.append(current_segment.strip())
                    current_segment = ""
                
                # 如果单行就超过限制，需要进一步分割
                if len(line) > max_chars:
                    words = line.split()
                    temp_line = ""
                    for word in words:
                        if len(temp_line) + len(word) + 1 > max_chars:
                            if temp_line:
                                segments.append(temp_line.strip())
                                temp_line = word
                            else:
                                # 单个单词就超过限制，强制分割
                                segments.append(word[:max_chars])
                        else:
                            temp_line += " " + word if temp_line else word
                    if temp_line:
                        current_segment = temp_line
                else:
                    current_segment = line
            else:
                current_segment += "\n" + line if current_segment else line
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments

    def _send_single_message(message, to_user):
        url = "http://212.64.57.87:5001/send"
        token = "wecomchan_token"
        data = {
            "msg": message,
            "token": token,
            "to_user": to_user
        }
        
        max_retries = 5
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data, timeout=30)
                print(f"📤 发送给 {to_user} 结果: {response.text[:100]}...")
                
                if "errcode" in response.text and "0" in response.text:
                    print(f"✅ 发送给 {to_user} 成功 (尝试 {attempt + 1}/{max_retries})")
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
                        print(f"❌ 发送给 {to_user} 失败，已重试{max_retries}次")
                        return False
                else:
                    print(f"⚠️ 发送给 {to_user} 返回异常 (尝试 {attempt + 1}/{max_retries}): {response.text}")
                    if attempt < max_retries - 1:
                        print(f"⏳ {retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                    else:
                        print(f"❌ 发送给 {to_user} 失败，已重试{max_retries}次")
                        return False
            except requests.exceptions.ConnectTimeout:
                print(f"❌ 连接超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 发送给 {to_user} 失败: 连接超时，已重试{max_retries}次")
                    return False
            except requests.exceptions.Timeout:
                print(f"❌ 请求超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 发送给 {to_user} 失败: 请求超时，已重试{max_retries}次")
                    return False
            except Exception as e:
                print(f"❌ 发送给 {to_user} 异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(f"❌ 发送给 {to_user} 失败: {e}，已重试{max_retries}次")
                    return False
        return False

    def send_failure_report_to_admin(script_name, error_details, failed_users_list):
        """发送失败报告给管理员"""
        failure_msg = f"""🚨 发送失败报告

📋 脚本名称: {script_name}
⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ 失败原因: {error_details}
👥 失败用户列表: {', '.join(failed_users_list)}

请检查网络连接和服务器状态。"""
        
        admin_data = {"msg": failure_msg, "token": "wecomchan_token", "to_user": "weicungang"}
        try:
            resp = requests.post("http://212.64.57.87:5001/send", json=admin_data, timeout=30)
            print(f"📤 失败报告发送结果: {resp.text[:100]}...")
        except Exception as e:
            print(f"❌ 失败报告发送异常: {e}")

    def send_wecomchan_segment(result, to_user):
        max_chars = 800
        if len(result) <= max_chars:
            success = _send_single_message(result, to_user)
            return success
        else:
            print(f"⚠️ 内容过长({len(result)}字符)，进行智能分段")
            segments = _smart_split_content(result, max_chars)
            for segment in segments:
                success = _send_single_message(segment, to_user)
                if not success:
                    return False
                time.sleep(2)
            return True

    # 按品类分别发送逻辑
    all_failed_users = set()  # 记录所有发送失败的用户
    sent_categories_per_user = {}  # 记录每个用户已收到的品类
    
    # 为每个品类生成独立报告并发送
    for segment in all_segments:
        if not segment.strip():
            continue
        
        # 提取品类名称
        m = re.search(r"【(.+?)】", segment)
        if not m:
            continue
        category = m.group(1)
        
        # 确定该品类的目标用户
        category_users = get_target_users(category)
        print(f"📋 品类 {category} 的目标用户: {category_users}")
        
        # 为每个用户发送该品类的报告
        for user in category_users:
            # 检查该用户是否已收到该品类报告
            if user not in sent_categories_per_user:
                sent_categories_per_user[user] = set()
            
            if category not in sent_categories_per_user[user]:
                # 生成该品类的完整报告
                category_report = report_title + segment
                print(f"📤 发送 {category} 报告给用户 {user}，报告长度: {len(category_report)} 字符")
                
                success = send_wecomchan_segment(category_report, user)
                if not success:
                    all_failed_users.add(user)
                
                # 标记该用户已收到该品类报告
                sent_categories_per_user[user].add(category)
                print(f"✅ 用户 {user} 已收到 {category} 报告")
                
                time.sleep(1)  # 添加短暂延迟，避免发送过快
            else:
                print(f"⚠️ 用户 {user} 已收到 {category} 报告，跳过")
    
    # 统一发送失败报告给管理员
    if all_failed_users:
        send_failure_report_to_admin("滞销库存清理.py", "微信消息发送失败", list(all_failed_users))

    globals()['result'] = result

except Exception as e:
    result = f"数据处理出错: {e}"
    globals()['result'] = result