#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 解决中文编码问题 - 强制UTF-8环境
import os
import sys
import locale
import logging
from datetime import datetime, timedelta

# 强制设置UTF-8环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# 重新配置标准输出编码为UTF-8
try:
    import codecs
    import io
    # 方法1：使用io.TextIOWrapper包装
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception as e:
    print(f"编码设置警告: {e}")

# 设置locale为UTF-8支持的环境
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8') 
    except:
        pass  # 如果都设置失败，继续执行

import pandas as pd
import glob
import requests
from datetime import datetime, timedelta
import traceback
import time
import json
from calendar import monthrange
import subprocess
import pymysql

# ========== 日志配置 ==========
def setup_logging():
    """设置日志记录"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = f"logs/多事业部月报数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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

# 微信配置
token = "wecomchan_token"
to_user = "weicungang"
url = "http://212.64.57.87:5001/send"

# 事业部分组配置
business_groups = {
    "空调事业部": {"keywords": ["家用空调", "商用空调"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "制冷事业部": {"keywords": ["冰箱", "冷柜"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "洗护事业部": {"keywords": ["洗衣机", "晾衣机", "干衣机", "烘干机"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "水联网事业部": {"keywords": ["热水器", "净水", "采暖", "电热水器", "燃气热水器", "多能源热水器"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "厨电洗碗机事业部": {"keywords": ["厨电", "洗碗机"], "users": ["weicungang"]}  # 测试期间统一发送给 weicungang
}

# 渠道分组配置
channel_groups = {
    "卡萨帝渠道": {"keywords": ["卡萨帝", "小红书"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "天猫渠道": {"keywords": ["天猫", "淘宝"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "京东渠道": {"keywords": ["京东"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "拼多多渠道": {"keywords": ["拼多多"], "users": ["weicungang"]},  # 测试期间统一发送给 weicungang
    "抖音渠道": {"keywords": ["抖音", "快手"], "users": ["weicungang"]}  # 测试期间统一发送给 weicungang
}

# 固定收件人（always发送）
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

# 拼音映射
pinyin_map = {
    "空调事业部": "kongtiao",
    "制冷事业部": "zhiling", 
    "洗护事业部": "xihu",
    "水联网事业部": "shuilianwang",
    "厨电洗碗机事业部": "chudianxiwangji",
    "卡萨帝渠道": "kasadi",
    "天猫渠道": "tianmao",
    "京东渠道": "jingdong",
    "拼多多渠道": "pinduoduo",
    "抖音渠道": "douyin"
}

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
        for channel, conf in channel_groups.items():
            if channel == group_name:
                users.update(conf["users"])
                break
    
    # 确保用户列表去重
    target_users = list(set(users))
    return target_users

# ========== 函数定义 ==========
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
            
            # 添加京东渠道前缀
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
    """从ERP数据中识别天猫分销数据（仓库字段包含'菜鸟仓自流转'）"""
    try:
        logger.info("🔍 开始识别天猫分销数据...")
        
        # 检查是否有仓库字段
        warehouse_col = '仓库'
        if warehouse_col not in df.columns:
            logger.warning(f"⚠️ 未找到仓库字段: {warehouse_col}")
            return None
        
        # 显示仓库字段的唯一值，用于调试
        unique_warehouses = df[warehouse_col].dropna().unique()
        logger.info(f"📊 仓库字段唯一值: {unique_warehouses[:10]}")  # 只显示前10个
        
        # 筛选天猫渠道且仓库包含"菜鸟仓自流转"的数据
        tianmao_mask = df[SHOP_COL].astype(str).str.contains('天猫|淘宝', na=False)
        warehouse_mask = df[warehouse_col].astype(str).str.contains('菜鸟仓自流转', na=False)
        
        logger.info(f"📊 天猫渠道数据: {tianmao_mask.sum()}行")
        logger.info(f"📊 菜鸟仓自流转数据: {warehouse_mask.sum()}行")
        
        tianmao_fenxiao = df[tianmao_mask & warehouse_mask].copy()
        
        if not tianmao_fenxiao.empty:
            # 添加分销标识
            tianmao_fenxiao['数据来源'] = '分销'
            # 使用货品名称进行品类匹配
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

def clean_paragraphs(text):
    """清理文本段落，去除多余空行和格式化文本"""
    if not text:
        return ""
    
    # 分割成行
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 去除行首行尾空白
        cleaned_line = line.strip()
        cleaned_lines.append(cleaned_line)
    
    # 合并连续的空行为单个空行
    result_lines = []
    prev_empty = False
    
    for line in cleaned_lines:
        if line == "":
            if not prev_empty:
                result_lines.append(line)
            prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    
    # 去除开头和结尾的空行
    while result_lines and result_lines[0] == "":
        result_lines.pop(0)
    while result_lines and result_lines[-1] == "":
        result_lines.pop()
    
    return '\n'.join(result_lines)

def clean_html_tags(text):
    """清理HTML标签，用于微信推送"""
    import re
    if not text:
        return ""
    
    # 移除HTML标签但保留内容
    text = re.sub(r'<span[^>]*>', '', text)
    text = re.sub(r'', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    return text

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
    if pd.isnull(val):
        return 0
    val = str(val).replace('，', '').replace(',', '').replace(' ', '').replace('\u3000', '')
    try:
        return int(float(val))  # 直接返回整数，避免小数位
    except:
        return 0

def is_online_shop(shop_name):
    """判断是否为线上店铺"""
    if pd.isna(shop_name):
        return False
    
    shop_str = str(shop_name).lower()
    offline_keywords = [
        '线下', '实体店', '专柜', '门店', '卖场', '商场', '超市', 
        '国美', '苏宁', '五星', '大中', '永乐', '迪信通',
        '世纪联华', '华润万家', '沃尔玛', '家乐福', '大润发',
        '红星美凯龙', '居然之家', '欧亚达', '金海马', '月星',
        '工厂店', '库存处理', '清仓', '样机', '展示机'
    ]
    
    return not any(keyword in shop_str for keyword in offline_keywords)

def check_server_availability():
    """检查Web服务器是否可用"""
    try:
        response = requests.get("http://127.0.0.1:5002/", timeout=5)
        return response.status_code == 200
    except:
        return False

def _send_single_message(message, target_user=None):
    """发送单条消息，支持5次重试和失败webhook通知"""
    url = "http://212.64.57.87:5001/send"
    token = "wecomchan_token"
    to_user = target_user if target_user else "weicungang"
    data = {
        "msg": message,
        "token": token,
        "to_user": to_user
    }
    
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 尝试发送消息给用户 {to_user} (第{attempt + 1}/{max_retries}次)")
            response = requests.post(url, json=data, timeout=30)
            logger.info(f"📤 发送结果: {response.text[:100]}...")
            
            if "errcode" in response.text and "0" in response.text:
                logger.info(f"✅ 发送成功 (尝试 {attempt + 1}/{max_retries})")
                return True
            elif "500" in response.text or "error" in response.text.lower():
                logger.warning(f"⚠️ 服务器错误 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    # 尝试缩短内容重试
                    shorter_msg = message[:500]
                    data["msg"] = shorter_msg
                else:
                    logger.error(f"❌ 发送失败，已重试{max_retries}次")
                    # 发送失败通知到webhook
                    send_failure_webhook_notification(to_user, message, f"服务器错误: {response.text}")
                    return False
            else:
                logger.warning(f"⚠️ 发送返回异常 (尝试 {attempt + 1}/{max_retries}): {response.text}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    logger.error(f"❌ 发送失败，已重试{max_retries}次")
                    # 发送失败通知到webhook
                    send_failure_webhook_notification(to_user, message, f"发送异常: {response.text}")
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
                send_failure_webhook_notification(to_user, message, "连接超时")
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
                send_failure_webhook_notification(to_user, message, "请求超时")
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
                send_failure_webhook_notification(to_user, message, f"发送异常: {str(e)}")
                return False
    return False

def send_failure_webhook_notification(target_user, message_content, error_details):
    """发送失败通知到webhook"""
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=02d1441f-aa5b-44cb-aeab-b934fe78f8cb"
    
    failure_msg = f"""🚨 多事业部月报数据发送失败通知

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
        target_users = [to_user]
    
    # 确保用户列表去重
    target_users = list(set(target_users))
    
    logger.info(f"📤 准备发送给 {len(target_users)} 个用户: {', '.join(target_users)}")
    
    # 为每个用户发送消息
    success_count = 0
    for user in target_users:
        logger.info(f"📤 正在发送给用户: {user}")
        
        # 检查是否包含链接
        link_pattern = r'🌐 查看完整Web页面: (https://[^\s]+)'
        import re
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
    import unicodedata
    import re
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

def classify_channel(shop_name):
    """渠道归类函数 - 淘宝合并到天猫渠道"""
    if not isinstance(shop_name, str):
        return "其他"
    
    shop_name_lower = shop_name.lower()
    
    # 卡萨帝优先
    if '卡萨帝' in shop_name_lower or '小红书' in shop_name_lower:
        return "卡萨帝渠道"
    if '京东' in shop_name_lower:
        return "京东渠道"
    if '天猫' in shop_name_lower or '淘宝' in shop_name_lower:  # 淘宝合并到天猫
        return "天猫渠道"
    if '拼多多' in shop_name_lower:
        return "拼多多渠道"
    if '抖音' in shop_name_lower or '快手' in shop_name_lower:
        return "抖音渠道"
    return "其他"


# ========== Web报告保存函数，参考日报逻辑 ==========
def save_report_to_local(content, report_id_prefix):
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{report_id_prefix}_{report_date}.html"
    # 直接保存内容，不再添加额外的HTML包装
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 报表已保存: {filename}")
    return os.path.basename(filename)

def _simple_verify_url(public_url):
    """严格验证URL是否可访问"""
    print(f"🔍 正在验证URL: {public_url}")
    
    # 等待CDN同步，最多重试5次
    for attempt in range(5):
        try:
            time.sleep(3)  # 等待CDN同步
            response = requests.head(public_url, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ URL验证成功，文件可正常访问: {public_url}")
                return public_url
            elif response.status_code == 404:
                print(f"⚠️ 第{attempt+1}次验证失败，文件不存在 (404)，等待CDN同步...")
            else:
                print(f"⚠️ 第{attempt+1}次验证失败，状态码: {response.status_code}")
                
        except Exception as verify_e:
            print(f"⚠️ 第{attempt+1}次验证异常: {verify_e}")
    
    print(f"❌ URL验证失败，经过5次重试仍无法访问，不返回URL")
    return None
