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
    text = re.sub(r'</span>', '', text)
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

def upload_html_and_get_url(filename, html_content):
    api = 'http://212.64.57.87:5002/deploy_html'
    files = {'file': (filename, html_content.encode('utf-8'))}
    try:
        resp = requests.post(api, files=files, timeout=60)
        try:
            res = resp.json()
            print("API返回：", res)
            if res.get('success') and res.get('url'):
                # 只返回根目录链接
                url = res.get('url')
                if url.startswith('http') and '/reports/' in url:
                    url = url.replace('/reports/', '/')
                return url
            else:
                print(f"❌ 服务器 Web 发布失败: {res}")
                return None
        except Exception as e:
            print(f"❌ 上传或发布异常: {e}, 原始返回: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 上传或发布异常: {e}")
        return None

def deploy_to_edgeone():
    try:
        result = subprocess.run([
            "edgeone", "pages", "deploy", "./reports",
            "-n", "sales-report",
            "-t", "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ EdgeOne Pages 自动部署成功！")
        else:
            print("❌ EdgeOne Pages 部署失败：", result.stderr)
    except Exception as e:
        print("❌ EdgeOne Pages 部署异常：", e)


# ========== 分组拼音映射 ==========
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



# ========== 事业部/渠道月报统一分析函数 ==========
def generate_monthly_report_for_group(group_name, group_config, df, df_prev, report_date, date_title, is_web, pinyin_map):
    # 1. 数据筛选
    if group_name in business_groups:
        # 修复事业部筛选逻辑：对于分销数据使用品类列，对于ERP数据使用货品名称列
        def business_filter(row):
            # 如果是分销数据，使用品类列筛选
            if '数据来源' in row and row['数据来源'] == '分销' and '品类' in row:
                return any(kw in str(row['品类']) for kw in group_config["keywords"])
            # 如果是ERP数据，使用货品名称列筛选
            else:
                return any(kw in str(row[CATEGORY_COL]) for kw in group_config["keywords"])
        
        group_df = df[df.apply(business_filter, axis=1)]
        prev_group_df = None
        if df_prev is not None:
            prev_group_df = df_prev[df_prev.apply(business_filter, axis=1)]
    else:
        group_df = df[df[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in group_config["keywords"]))]
        prev_group_df = None
        if df_prev is not None:
            prev_group_df = df_prev[df_prev[SHOP_COL].apply(lambda x: any(kw in str(x) for kw in group_config["keywords"]))]
    
    if group_df.empty:
        print(f"⚠️ {group_name} 无数据")
        # 生成无数据页面
        main_segment = f"🏢 {group_name}月报\n📅 数据月份: {date_title}\n📅 本期时间：2025.7.1-2025.7.22\n📅 对比期时间：2025.6.1-2025.6.22\n\n⚠️ 本月无有效数据，未生成明细。"
        web_content = f'''<!DOCTYPE html>
<html lang="zh-CN"
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>{group_name}月报 - {report_date}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background: #f8f9fa; color: #222; margin: 0; padding: 2em; max-width: 900px; margin-left:auto; margin-right:auto; text-align: left; }}</style>
</head>
<body>
    <h1>{group_name}月报（{report_date}）</h1>
    <div class="section left-align"><pre>⚠️ 本月无有效数据，未生成明细。</pre></div>
    <footer style="margin-top:2em;color:#888;font-size:0.9em;">自动生成 | Powered by EdgeOne Pages & 企业微信机器人</footer>
</body>
</html>'''
        report_id_prefix = pinyin_map.get(group_name, ''.join([c for c in group_name if c.isalnum() or c == '_']).lower())
        filename = save_report_to_local(web_content, report_id_prefix)
        public_url = f"https://edge.haierht.cn/{filename}" if filename else ""
        # 推送无数据提示
        wechat_content = main_segment
        if public_url:
            wechat_content += f"\n🌐 查看完整Web页面: {public_url}"
        
        # 返回发送内容和链接，不在这里直接发送
        if public_url:
            return f"{group_name}: {public_url}", filename, wechat_content
        else:
            return None, None, wechat_content
    
    # 2. 整体数据
    # 确保金额和数量字段为数值类型
    if group_df[AMOUNT_COL].dtype == 'object':
        group_df[AMOUNT_COL] = pd.to_numeric(group_df[AMOUNT_COL], errors='coerce').fillna(0)
    if group_df[QTY_COL].dtype == 'object':
        group_df[QTY_COL] = pd.to_numeric(group_df[QTY_COL], errors='coerce').fillna(0)
    
    total_amount = group_df[AMOUNT_COL].sum()
    total_qty = group_df[QTY_COL].sum()
    avg_price = int(total_amount / total_qty) if total_qty > 0 else 0
    
    prev_amount = 0
    prev_qty = 0
    if prev_group_df is not None and not prev_group_df.empty:
        # 确保同期数据也是数值类型
        if prev_group_df[AMOUNT_COL].dtype == 'object':
            prev_group_df[AMOUNT_COL] = pd.to_numeric(prev_group_df[AMOUNT_COL], errors='coerce').fillna(0)
        if prev_group_df[QTY_COL].dtype == 'object':
            prev_group_df[QTY_COL] = pd.to_numeric(prev_group_df[QTY_COL], errors='coerce').fillna(0)
        prev_amount = prev_group_df[AMOUNT_COL].sum()
        prev_qty = prev_group_df[QTY_COL].sum()
    prev_avg_price = int(prev_amount / prev_qty) if prev_qty > 0 else 0
    
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
    
    def calc_ratio(cur, prev):
        if prev == 0:
            return "+100%" if cur > 0 else "0%"
        ratio = int(((cur - prev) / prev) * 100)
        if ratio > 0:
            return f"+{ratio}%"
        elif ratio < 0:
            return f"{ratio}%"
        else:
            return "0%"
    
    main_segment = f"🏢 {group_name}月报\n📅 数据月份: {date_title}\n📅 本期时间：{current_start.strftime('%Y.%m.%d')}-{current_end.strftime('%Y.%m.%d')}\n📅 对比期时间：{prev_start.strftime('%Y.%m.%d')}-{prev_end.strftime('%Y.%m.%d')}\n\n"
    main_segment += f"📊 整体数据\n总销售额: ¥{total_amount:,}（对比:¥{prev_amount:,}，环比:{calc_ratio(total_amount, prev_amount)}）\n总销量: {total_qty:,}件（对比:{prev_qty:,}件，环比:{calc_ratio(total_qty, prev_qty)}）\n平均单价: ¥{avg_price:,}（对比:¥{prev_avg_price:,}，环比:{calc_ratio(avg_price, prev_avg_price)}）"
    
    # 添加分销数据到整体数据
    if fenxiao_amount > 0:
        main_segment += f"\n其中分销金额： ¥{fenxiao_amount:,}（对比:¥{prev_fenxiao_amount:,}，环比:{calc_ratio(fenxiao_amount, prev_fenxiao_amount)}）"
        main_segment += f"\n其中分销数量： {fenxiao_qty:,}件（对比:{prev_fenxiao_qty:,}件，环比:{calc_ratio(fenxiao_qty, prev_fenxiao_qty)}）"
    
    main_segment += "\n\n"
    
    # 3. 品类明细
    cat_summary = group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    # 过滤掉"其他"品类
    cat_summary = cat_summary[cat_summary[CATEGORY_COL] != '其他']
    cat_summary = cat_summary.sort_values(AMOUNT_COL, ascending=False)
    prev_cat_summary = None
    if prev_group_df is not None and not prev_group_df.empty:
        prev_cat_summary = prev_group_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        # 过滤掉"其他"品类
        prev_cat_summary = prev_cat_summary[prev_cat_summary[CATEGORY_COL] != '其他']
    
    # 品类分销数据
    cat_fenxiao_summary = None
    if '数据来源' in group_df.columns and not fenxiao_df.empty:
        cat_fenxiao_summary = fenxiao_df.groupby(CATEGORY_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        cat_fenxiao_summary = cat_fenxiao_summary[cat_fenxiao_summary[CATEGORY_COL] != '其他']
        cat_fenxiao_summary = cat_fenxiao_summary.sort_values(AMOUNT_COL, ascending=False)
    
    filtered_cat_summary = cat_summary
    
    if not filtered_cat_summary.empty:
        main_segment += "📋 品类明细\n"
        for _, row in filtered_cat_summary.iterrows():
            cat = row[CATEGORY_COL]
            amt = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amt / qty) if qty else 0
            prev_amt = 0
            if prev_cat_summary is not None:
                prev_row = prev_cat_summary[prev_cat_summary[CATEGORY_COL] == cat]
                if not prev_row.empty:
                    prev_amt = int(prev_row.iloc[0][AMOUNT_COL])
            
            # 计算环比并设置底色
            ratio_val = 0
            if prev_amt != 0:
                ratio_val = (amt - prev_amt) / abs(prev_amt)
            
            ratio_str = f" (" + calc_ratio(amt, prev_amt) + ")" if prev_cat_summary is not None else ""
            
            # 根据环比情况设置底色
            if ratio_val > 0:
                color_style = 'style="background-color: #e6f4ea; padding: 2px;"'
            elif ratio_val < 0:
                color_style = 'style="background-color: #fbeaea; padding: 2px;"'
            else:
                color_style = ''
            
            main_segment += f"<span {color_style}>• {cat}: ¥{amt:,} | {qty:,}件 | ¥{price:,}/件{ratio_str}</span>\n"
            
            # 添加品类分销数据
            if cat_fenxiao_summary is not None:
                cat_fenxiao = cat_fenxiao_summary[cat_fenxiao_summary[CATEGORY_COL] == cat]
                if not cat_fenxiao.empty:
                    fenxiao_amt = int(cat_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_cat = int(cat_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_cat) if fenxiao_qty_cat else 0
                    # 计算同期分销数据
                    prev_fenxiao_amt = 0
                    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                        prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                        if not prev_fenxiao_df.empty:
                            prev_cat_fenxiao = prev_fenxiao_df[prev_fenxiao_df[CATEGORY_COL] == cat]
                            if not prev_cat_fenxiao.empty:
                                prev_fenxiao_amt = int(prev_cat_fenxiao[AMOUNT_COL].sum())
                    main_segment += f"其中分销 ¥{fenxiao_amt:,} | {fenxiao_qty_cat:,}件 | ¥{fenxiao_price:,}/件（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）\n"
        
        main_segment += "\n"
    
    # 4. 店铺数据
    shop_summary = group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index().sort_values(AMOUNT_COL, ascending=False)
    prev_shop_summary = None
    if prev_group_df is not None and not prev_group_df.empty:
        prev_shop_summary = prev_group_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
    
    # 店铺分销数据
    shop_fenxiao_summary = None
    if '数据来源' in group_df.columns and not fenxiao_df.empty:
        shop_fenxiao_summary = fenxiao_df.groupby(SHOP_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
        shop_fenxiao_summary = shop_fenxiao_summary.sort_values(AMOUNT_COL, ascending=False)
    
    if not shop_summary.empty:
        main_segment += "🏪 渠道到店铺数据\n"
        for _, row in shop_summary.iterrows():
            shop = row[SHOP_COL]
            amt = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amt / qty) if qty else 0
            prev_amt = 0
            if prev_shop_summary is not None:
                prev_row = prev_shop_summary[prev_shop_summary[SHOP_COL] == shop]
                if not prev_row.empty:
                    prev_amt = int(prev_row.iloc[0][AMOUNT_COL])
            
            # 计算环比并设置底色
            ratio_val = 0
            if prev_amt != 0:
                ratio_val = (amt - prev_amt) / abs(prev_amt)
            
            ratio_str = f" (" + calc_ratio(amt, prev_amt) + ")" if prev_shop_summary is not None else ""
            
            # 根据环比情况设置底色
            if ratio_val > 0:
                color_style = 'style="background-color: #e6f4ea; padding: 2px;"'
            elif ratio_val < 0:
                color_style = 'style="background-color: #fbeaea; padding: 2px;"'
            else:
                color_style = ''
            
            main_segment += f"<span {color_style}>• {shop}: ¥{amt:,}，{qty:,}件，单价¥{price:,}{ratio_str}</span>\n"
            
            # 添加店铺分销数据
            if shop_fenxiao_summary is not None:
                shop_fenxiao = shop_fenxiao_summary[shop_fenxiao_summary[SHOP_COL] == shop]
                if not shop_fenxiao.empty:
                    fenxiao_amt = int(shop_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_shop = int(shop_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_shop) if fenxiao_qty_shop else 0
                    # 计算同期分销数据
                    prev_fenxiao_amt = 0
                    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                        prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                        if not prev_fenxiao_df.empty:
                            prev_shop_fenxiao = prev_fenxiao_df[prev_fenxiao_df[SHOP_COL] == shop]
                            if not prev_shop_fenxiao.empty:
                                prev_fenxiao_amt = int(prev_shop_fenxiao[AMOUNT_COL].sum())
                    main_segment += f"其中分销 ¥{fenxiao_amt:,}，{fenxiao_qty_shop:,}件，单价¥{fenxiao_price:,}（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）\n"
        
        main_segment += "\n"
    
    # 删除重复的图3部分，因为单品和店铺排行在后面的详细部分已经包含
    
    # 5. Web页面额外内容（单品明细）- 清空这部分内容
    web_extra_content = ""  # 直接设置为空字符串，不再生成详细内容
    if is_web and MODEL_COL:
        # 先对品类按销售额降序排序，过滤掉"其他"品类
        filtered_group_df = group_df[group_df[CATEGORY_COL] != '其他']
        cat_sales = filtered_group_df.groupby(CATEGORY_COL)[AMOUNT_COL].sum().sort_values(ascending=False)
        web_extra_content += "\n📦 所有单品明细\n"
        for cat in cat_sales.index:
            cat_df = filtered_group_df[filtered_group_df[CATEGORY_COL] == cat]
            cat_products = cat_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            cat_products = cat_products.sort_values(AMOUNT_COL, ascending=False)
            filtered = cat_products[~cat_products[MODEL_COL].apply(lambda x: any(y in str(x) for y in ["运费","外机","赠品"]))]
            if not filtered.empty:
                web_extra_content += f"📋 {cat}\n"
                for _, row in filtered.iterrows():
                    spec_name = row[MODEL_COL]
                    amt = int(row[AMOUNT_COL])
                    qty = int(row[QTY_COL])
                    price = int(amt / qty) if qty else 0
                    prev_amt = 0
                    if prev_group_df is not None and not prev_group_df.empty:
                        prev_product = prev_group_df[(prev_group_df[MODEL_COL] == spec_name) & (prev_group_df[CATEGORY_COL] == cat)]
                        if not prev_product.empty:
                            prev_amt = int(prev_product[AMOUNT_COL].sum())
                    # 环比span加色，正数绿，负数淡红
                    ratio_val = 0
                    if prev_amt != 0:
                        ratio_val = (amt - prev_amt) / abs(prev_amt)
                    ratio_str = ""
                    if prev_group_df is not None:
                        color = "#e6f4ea" if ratio_val > 0 else ("#fbeaea" if ratio_val < 0 else "")
                        fontcolor = "#1a7f37" if ratio_val > 0 else ("#d93025" if ratio_val < 0 else "")
                        ratio_html = f'<span style="background:{color};color:{fontcolor};padding:0 2px;border-radius:2px;">{calc_ratio(amt, prev_amt)}</span>' if color else calc_ratio(amt, prev_amt)
                        ratio_str = f'，对比期 ¥{prev_amt:,}，环比 {ratio_html}'
                    # 根据环比情况设置底色
                    if ratio_val > 0:
                        color_style = 'style="background-color: #e6f4ea; padding: 2px;"'
                    elif ratio_val < 0:
                        color_style = 'style="background-color: #fbeaea; padding: 2px;"'
                    else:
                        color_style = ''
                    
                    web_extra_content += f"  <span {color_style}>• {spec_name}: ¥{amt:,} | 单价: ¥{price:,}{ratio_str}</span>\n"
                web_extra_content += "\n"  # 品类之间加空行
        web_extra_content = clean_paragraphs(web_extra_content)
        # 店铺单品明细 - 店铺、品类都按销售额降序，分段加空行
        web_extra_content += "\n🏪 店铺单品信息\n"
        shop_total = group_df.groupby(SHOP_COL)[AMOUNT_COL].sum().sort_values(ascending=False)
        for shop in shop_total.index:
            shop_df = group_df[group_df[SHOP_COL] == shop]
            web_extra_content += f"【{shop}】\n"
            filtered_shop_df = shop_df[shop_df[CATEGORY_COL] != '其他']
            shop_cat_total = filtered_shop_df.groupby(CATEGORY_COL)[AMOUNT_COL].sum().sort_values(ascending=False)
            for cat in shop_cat_total.index:
                cat_df = filtered_shop_df[filtered_shop_df[CATEGORY_COL] == cat]
                web_extra_content += f"  📋 {cat}:\n"
                cat_products = cat_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                cat_products = cat_products.sort_values(AMOUNT_COL, ascending=False)
                filtered = cat_products[~cat_products[MODEL_COL].apply(lambda x: any(y in str(x) for y in ["运费","外机","赠品"]))]
                for _, row in filtered.iterrows():
                    spec_name = row[MODEL_COL]
                    amt = int(row[AMOUNT_COL])
                    qty = int(row[QTY_COL])
                    price = int(amt / qty) if qty else 0
                    if amt > 0:
                        prev_amt = 0
                        if prev_group_df is not None and not prev_group_df.empty:
                            prev_product = prev_group_df[(prev_group_df[MODEL_COL] == spec_name) & (prev_group_df[SHOP_COL] == shop) & (prev_group_df[CATEGORY_COL] == cat)]
                            if not prev_product.empty:
                                prev_amt = int(prev_product[AMOUNT_COL].sum())
                        ratio_val = 0
                        if prev_amt != 0:
                            ratio_val = (amt - prev_amt) / abs(prev_amt)
                        ratio_str = ""
                        if prev_group_df is not None:
                            color = "#e6f4ea" if ratio_val > 0 else ("#fbeaea" if ratio_val < 0 else "")
                            fontcolor = "#1a7f37" if ratio_val > 0 else ("#d93025" if ratio_val < 0 else "")
                            ratio_html = f'<span style="background:{color};color:{fontcolor};padding:0 2px;border-radius:2px;">{calc_ratio(amt, prev_amt)}</span>' if color else calc_ratio(amt, prev_amt)
                            ratio_str = f'，对比期 ¥{prev_amt:,}，环比 {ratio_html}'
                        # 根据环比情况设置底色
                        ratio_val_shop = 0
                        if prev_amt != 0:
                            ratio_val_shop = (amt - prev_amt) / abs(prev_amt)
                        
                        if ratio_val_shop > 0:
                            color_style_shop = 'style="background-color: #e6f4ea; padding: 2px;"'
                        elif ratio_val_shop < 0:
                            color_style_shop = 'style="background-color: #fbeaea; padding: 2px;"'
                        else:
                            color_style_shop = ''
                        
                        web_extra_content += f"    <span {color_style_shop}>{spec_name}: ¥{amt:,}，{qty}件，单价¥{price:,}{ratio_str}</span>\n"
                web_extra_content += "\n"  # 品类之间加空行
            web_extra_content += "\n"  # 店铺之间加空行
        web_extra_content = clean_paragraphs(web_extra_content)
    # 6. 生成Web页面
    web_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>{group_name}月报 - {report_date}</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333; 
            margin: 0; 
            padding: 20px; 
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #0056b3 0%, #007bff 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .content {{
            padding: 30px;
            line-height: 1.6;
        }}
        .section {{
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        }}
        .section h2 {{
            color: #0056b3;
            margin: 0 0 15px 0;
            font-size: 18px;
            font-weight: bold;
            display: flex;
            align-items: center;
        }}
        .section h2::before {{
            content: "📊";
            margin-right: 10px;
            font-size: 20px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: 500;
            color: #495057;
        }}
        .metric-value {{
            font-weight: bold;
            color: #0056b3;
        }}
        .metric-change {{
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        }}
        .change-positive {{
            background: #d4edda;
            color: #155724;
        }}
        .change-negative {{
            background: #f8d7da;
            color: #721c24;
        }}
        .change-neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}
        .category-item {{
            background: white;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .category-name {{
            font-weight: bold;
            color: #495057;
        }}
        .category-stats {{
            font-size: 14px;
            color: #6c757d;
        }}
        .shop-list {{
            margin-left: 20px;
            padding-left: 15px;
            border-left: 2px solid #e9ecef;
        }}
        .shop-item {{
            margin: 8px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #e9ecef;
        }}
        .tab-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .tab-button {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            background: #e9ecef;
            color: #495057;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        .tab-button.active {{
            background: #007bff;
            color: white;
        }}
        .tab-button:hover {{
            background: #0056b3;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .product-item {{
            background: white;
            margin: 8px 0;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #28a745;
        }}
        .product-name {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }}
        .product-stats {{
            font-size: 13px;
            color: #6c757d;
        }}
        .fenxiao-info {{
            background: #fff3cd;
            border-left: 3px solid #ffc107;
            padding: 8px;
            margin-top: 8px;
            border-radius: 4px;
            font-size: 12px;
            color: #856404;
        }}
        @media (max-width: 600px) {{
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            .header {{
                padding: 20px;
            }}
            .content {{
                padding: 20px;
            }}
            .tab-buttons {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{group_name}月报</h1>
            <p>数据月份: {date_title}</p>
            <p>本期时间：{current_start.strftime('%Y.%m.%d')}-{current_end.strftime('%Y.%m.%d')}</p>
            <p>对比期时间：{prev_start.strftime('%Y.%m.%d')}-{prev_end.strftime('%Y.%m.%d')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>整体数据</h2>
                <div class="metric">
                    <span class="metric-label">总销售额</span>
                    <span class="metric-value">¥{total_amount:,}</span>
                    <span class="metric-change {'change-positive' if total_amount > prev_amount else 'change-negative' if total_amount < prev_amount else 'change-neutral'}">{calc_ratio(total_amount, prev_amount)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">总销量</span>
                    <span class="metric-value">{total_qty:,}件</span>
                    <span class="metric-change {'change-positive' if total_qty > prev_qty else 'change-negative' if total_qty < prev_qty else 'change-neutral'}">{calc_ratio(total_qty, prev_qty)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">平均单价</span>
                    <span class="metric-value">¥{avg_price:,}</span>
                    <span class="metric-change {'change-positive' if avg_price > prev_avg_price else 'change-negative' if avg_price < prev_avg_price else 'change-neutral'}">{calc_ratio(avg_price, prev_avg_price)}</span>
                </div>'''
    
    # 添加分销数据到整体数据
    if fenxiao_amount > 0:
        web_content += f'''
                <div class="metric">
                    <span class="metric-label">分销金额</span>
                    <span class="metric-value">¥{fenxiao_amount:,}</span>
                    <span class="metric-change {'change-positive' if fenxiao_amount > prev_fenxiao_amount else 'change-negative' if fenxiao_amount < prev_fenxiao_amount else 'change-neutral'}">{calc_ratio(fenxiao_amount, prev_fenxiao_amount)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">分销数量</span>
                    <span class="metric-value">{fenxiao_qty:,}件</span>
                    <span class="metric-change {'change-positive' if fenxiao_qty > prev_fenxiao_qty else 'change-negative' if fenxiao_qty < prev_fenxiao_qty else 'change-neutral'}">{calc_ratio(fenxiao_qty, prev_fenxiao_qty)}</span>
                </div>'''
    
    web_content += '''
            </div>
            
            <div class="section">
                <h2>品类明细</h2>
                <div class="tab-buttons">
                    <button class="tab-button active" onclick="switchTab('shop')">店铺排行</button>
                    <button class="tab-button" onclick="switchTab('product')">单品排行</button>
                </div>
                
                <div id="shop-tab" class="tab-content active">'''
    
    # 添加店铺排行内容
    if not shop_summary.empty:
        for _, row in shop_summary.iterrows():
            shop = row[SHOP_COL]
            amt = int(row[AMOUNT_COL])
            qty = int(row[QTY_COL])
            price = int(amt / qty) if qty else 0
            prev_amt = 0
            if prev_shop_summary is not None:
                prev_row = prev_shop_summary[prev_shop_summary[SHOP_COL] == shop]
                if not prev_row.empty:
                    prev_amt = int(prev_row.iloc[0][AMOUNT_COL])
            
            web_content += f'''
                    <div class="shop-item">
                        <div class="product-name">{shop}</div>
                        <div class="product-stats">¥{amt:,} | {qty:,}件 | ¥{price:,}/件</div>'''
            
            # 添加店铺分销数据
            if shop_fenxiao_summary is not None:
                shop_fenxiao = shop_fenxiao_summary[shop_fenxiao_summary[SHOP_COL] == shop]
                if not shop_fenxiao.empty:
                    fenxiao_amt = int(shop_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_shop = int(shop_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_shop) if fenxiao_qty_shop else 0
                    prev_fenxiao_amt = 0
                    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                        prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                        if not prev_fenxiao_df.empty:
                            prev_shop_fenxiao = prev_fenxiao_df[prev_fenxiao_df[SHOP_COL] == shop]
                            if not prev_shop_fenxiao.empty:
                                prev_fenxiao_amt = int(prev_shop_fenxiao[AMOUNT_COL].sum())
                    web_content += f'''
                        <div class="fenxiao-info">其中分销: ¥{fenxiao_amt:,} | {fenxiao_qty_shop:,}件 | ¥{fenxiao_price:,}/件（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）</div>'''
            
            web_content += '''
                    </div>'''
    
    web_content += '''
                </div>
                
                <div id="product-tab" class="tab-content">'''
    
    # 添加单品排行内容
    if MODEL_COL and not filtered_cat_summary.empty:
        for _, row in filtered_cat_summary.iterrows():
            cat = row[CATEGORY_COL]
            cat_df = group_df[group_df[CATEGORY_COL] == cat]
            cat_products = cat_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            cat_products = cat_products.sort_values(AMOUNT_COL, ascending=False)
            filtered = cat_products[~cat_products[MODEL_COL].apply(lambda x: any(y in str(x) for y in ["运费","外机","赠品"])]
            
            if not filtered.empty:
                web_content += f'''
                    <div class="category-item">
                        <div class="category-header">
                            <span class="category-name">{cat}</span>
                            <span class="category-stats">¥{int(row[AMOUNT_COL]):,} | {int(row[QTY_COL]):,}件</span>
                        </div>'''
                
                # 添加品类分销数据
                if cat_fenxiao_summary is not None:
                    cat_fenxiao = cat_fenxiao_summary[cat_fenxiao_summary[CATEGORY_COL] == cat]
                    if not cat_fenxiao.empty:
                        fenxiao_amt = int(cat_fenxiao.iloc[0][AMOUNT_COL])
                        fenxiao_qty_cat = int(cat_fenxiao.iloc[0][QTY_COL])
                        fenxiao_price = int(fenxiao_amt / fenxiao_qty_cat) if fenxiao_qty_cat else 0
                        prev_fenxiao_amt = 0
                        if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                            prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                            if not prev_fenxiao_df.empty:
                                prev_cat_fenxiao = prev_fenxiao_df[prev_fenxiao_df[CATEGORY_COL] == cat]
                                if not prev_cat_fenxiao.empty:
                                    prev_fenxiao_amt = int(prev_cat_fenxiao[AMOUNT_COL].sum())
                        web_content += f'''
                        <div class="fenxiao-info">其中分销: ¥{fenxiao_amt:,} | {fenxiao_qty_cat:,}件 | ¥{fenxiao_price:,}/件（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）</div>'''
                
                for _, product_row in filtered.iterrows():
                    spec_name = product_row[MODEL_COL]
                    amt = int(product_row[AMOUNT_COL])
                    qty = int(product_row[QTY_COL])
                    price = int(amt / qty) if qty else 0
                    prev_amt = 0
                    if prev_group_df is not None and not prev_group_df.empty:
                        prev_product = prev_group_df[(prev_group_df[MODEL_COL] == spec_name) & (prev_group_df[CATEGORY_COL] == cat)]
                        if not prev_product.empty:
                            prev_amt = int(prev_product[AMOUNT_COL].sum())
                    
                    web_content += f'''
                        <div class="product-item">
                            <div class="product-name">{spec_name}</div>
                            <div class="product-stats">¥{amt:,} | {qty:,}件 | ¥{price:,}/件（对比:¥{prev_amt:,}，环比:{calc_ratio(amt, prev_amt)}）</div>
                        </div>'''
                
                web_content += '''
                    </div>'''
    
    web_content += '''
                </div>
            </div>
            
            <div class="section">
                <h2>单品数据</h2>'''
    
    # 添加单品数据部分
    if MODEL_COL and not filtered_cat_summary.empty:
        for _, row in filtered_cat_summary.iterrows():
            cat = row[CATEGORY_COL]
            cat_df = group_df[group_df[CATEGORY_COL] == cat]
            cat_products = cat_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
            cat_products = cat_products.sort_values(AMOUNT_COL, ascending=False)
            filtered = cat_products[~cat_products[MODEL_COL].apply(lambda x: any(y in str(x) for y in ["运费","外机","赠品"])]
            
            if not filtered.empty:
                web_content += f'''
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-name">{cat}</span>
                        <span class="category-stats">¥{int(row[AMOUNT_COL]):,} | {int(row[QTY_COL]):,}件</span>
                    </div>'''
                
                # 添加品类分销数据
                if cat_fenxiao_summary is not None:
                    cat_fenxiao = cat_fenxiao_summary[cat_fenxiao_summary[CATEGORY_COL] == cat]
                    if not cat_fenxiao.empty:
                        fenxiao_amt = int(cat_fenxiao.iloc[0][AMOUNT_COL])
                        fenxiao_qty_cat = int(cat_fenxiao.iloc[0][QTY_COL])
                        fenxiao_price = int(fenxiao_amt / fenxiao_qty_cat) if fenxiao_qty_cat else 0
                        prev_fenxiao_amt = 0
                        if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                            prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                            if not prev_fenxiao_df.empty:
                                prev_cat_fenxiao = prev_fenxiao_df[prev_fenxiao_df[CATEGORY_COL] == cat]
                                if not prev_cat_fenxiao.empty:
                                    prev_fenxiao_amt = int(prev_cat_fenxiao[AMOUNT_COL].sum())
                        web_content += f'''
                    <div class="fenxiao-info">其中分销: ¥{fenxiao_amt:,} | {fenxiao_qty_cat:,}件 | ¥{fenxiao_price:,}/件（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）</div>'''
                
                for _, product_row in filtered.iterrows():
                    spec_name = product_row[MODEL_COL]
                    amt = int(product_row[AMOUNT_COL])
                    qty = int(product_row[QTY_COL])
                    price = int(amt / qty) if qty else 0
                    prev_amt = 0
                    if prev_group_df is not None and not prev_group_df.empty:
                        prev_product = prev_group_df[(prev_group_df[MODEL_COL] == spec_name) & (prev_group_df[CATEGORY_COL] == cat)]
                        if not prev_product.empty:
                            prev_amt = int(prev_product[AMOUNT_COL].sum())
                    
                    web_content += f'''
                    <div class="product-item">
                        <div class="product-name">{spec_name}</div>
                        <div class="product-stats">¥{amt:,} | {qty:,}件 | ¥{price:,}/件（对比:¥{prev_amt:,}，环比:{calc_ratio(amt, prev_amt)}）</div>
                    </div>'''
                
                web_content += '''
                </div>'''
    
    web_content += '''
            </div>
            
            <div class="section">
                <h2>店铺单品数据</h2>'''
    
    # 添加店铺单品数据部分
    if MODEL_COL and not shop_summary.empty:
        for _, row in shop_summary.iterrows():
            shop = row[SHOP_COL]
            shop_df = group_df[group_df[SHOP_COL] == shop]
            filtered_shop_df = shop_df[shop_df[CATEGORY_COL] != '其他']
            shop_cat_total = filtered_shop_df.groupby(CATEGORY_COL)[AMOUNT_COL].sum().sort_values(ascending=False)
            
            web_content += f'''
            <div class="category-item">
                <div class="category-header">
                    <span class="category-name">{shop}</span>
                    <span class="category-stats">¥{int(row[AMOUNT_COL]):,} | {int(row[QTY_COL]):,}件</span>
                </div>'''
            
            # 添加店铺分销数据
            if shop_fenxiao_summary is not None:
                shop_fenxiao = shop_fenxiao_summary[shop_fenxiao_summary[SHOP_COL] == shop]
                if not shop_fenxiao.empty:
                    fenxiao_amt = int(shop_fenxiao.iloc[0][AMOUNT_COL])
                    fenxiao_qty_shop = int(shop_fenxiao.iloc[0][QTY_COL])
                    fenxiao_price = int(fenxiao_amt / fenxiao_qty_shop) if fenxiao_qty_shop else 0
                    prev_fenxiao_amt = 0
                    if prev_group_df is not None and '数据来源' in prev_group_df.columns:
                        prev_fenxiao_df = prev_group_df[prev_group_df['数据来源'] == '分销']
                        if not prev_fenxiao_df.empty:
                            prev_shop_fenxiao = prev_fenxiao_df[prev_fenxiao_df[SHOP_COL] == shop]
                            if not prev_shop_fenxiao.empty:
                                prev_fenxiao_amt = int(prev_shop_fenxiao[AMOUNT_COL].sum())
                    web_content += f'''
                <div class="fenxiao-info">其中分销: ¥{fenxiao_amt:,} | {fenxiao_qty_shop:,}件 | ¥{fenxiao_price:,}/件（对比:¥{prev_fenxiao_amt:,}，环比:{calc_ratio(fenxiao_amt, prev_fenxiao_amt)}）</div>'''
            
            for cat in shop_cat_total.index:
                cat_df = filtered_shop_df[filtered_shop_df[CATEGORY_COL] == cat]
                web_content += f'''
                <div class="shop-item">
                    <div class="product-name">{cat}</div>'''
                
                cat_products = cat_df.groupby(MODEL_COL).agg({AMOUNT_COL: 'sum', QTY_COL: 'sum'}).reset_index()
                cat_products = cat_products.sort_values(AMOUNT_COL, ascending=False)
                filtered = cat_products[~cat_products[MODEL_COL].apply(lambda x: any(y in str(x) for y in ["运费","外机","赠品"])]
                
                for _, product_row in filtered.iterrows():
                    spec_name = product_row[MODEL_COL]
                    amt = int(product_row[AMOUNT_COL])
                    qty = int(product_row[QTY_COL])
                    price = int(amt / qty) if qty else 0
                    prev_amt = 0
                    if prev_group_df is not None and not prev_group_df.empty:
                        prev_product = prev_group_df[(prev_group_df[MODEL_COL] == spec_name) & (prev_group_df[SHOP_COL] == shop) & (prev_group_df[CATEGORY_COL] == cat)]
                        if not prev_product.empty:
                            prev_amt = int(prev_product[AMOUNT_COL].sum())
                    
                    web_content += f'''
                    <div class="product-stats">{spec_name}: ¥{amt:,} | {qty:,}件 | ¥{price:,}/件（对比:¥{prev_amt:,}，环比:{calc_ratio(amt, prev_amt)}）</div>'''
                
                web_content += '''
                </div>'''
            
            web_content += '''
            </div>'''
    
    web_content += '''
            </div>
        </div>
        
        <div class="footer">
            自动生成 | Powered by EdgeOne Pages & 企业微信机器人
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {{
            // 隐藏所有标签内容
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {{
                content.classList.remove('active');
            }});
            
            // 移除所有按钮的active类
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {{
                button.classList.remove('active');
            }});
            
            // 显示选中的标签内容
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // 添加active类到选中的按钮
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''
    
    report_id_prefix = pinyin_map.get(group_name, ''.join([c for c in group_name if c.isalnum() or c == '_']).lower())
    filename = save_report_to_local(web_content, report_id_prefix)
    public_url = f"https://edge.haierht.cn/{filename}" if filename else ""
    
    # 7. 微信推送 - 主内容尽量保留，超长时截断主内容，最后一行拼Web链接
    import re
    main_msg = re.sub(r'\n*🏢 查看完整Web页面:.*', '', main_segment)
    main_msg = re.sub(r'\n*🌐 查看完整Web页面:.*', '', main_msg)
    main_msg = main_msg.replace('前一天', '对比期')
    # 清理HTML标签用于微信推送
    main_msg = clean_html_tags(main_msg)
    main_msg = clean_paragraphs(main_msg.strip())
    max_chars = 750
    if public_url:
        link_line = f"\n🌐 查看完整Web页面: {public_url}"
        link_len = len(link_line)
        if len(main_msg) + link_len > max_chars:
            main_msg = main_msg[:max_chars-link_len].rstrip('\n')
        wechat_content = main_msg + link_line
    else:
        wechat_content = main_msg[:max_chars]
    
    # 返回发送内容和链接，不在这里直接发送
    if public_url:
        return f"{group_name}: {public_url}", filename, wechat_content
    else:
        return None, None, wechat_content

# ========== 主程序开始 ==========
logger.info("🚀 多事业部月报数据分析系统启动...")

# 获取当前月份和上月同期数据
now = datetime.now()
current_month = now.month
current_year = now.year
current_day = now.day

# 计算上月同期日期
if current_month == 1:
    prev_month = 12
    prev_year = current_year - 1
else:
    prev_month = current_month - 1
    prev_year = current_year

# 获取上月的天数
prev_month_days = monthrange(prev_year, prev_month)[1]
# 如果当前日期超过上月天数，则取上月最后一天
prev_day = min(current_day, prev_month_days)

# 本月累计日期范围
current_start = datetime(current_year, current_month, 1)
current_end = datetime(current_year, current_month, 28)  # 固定到28号

# 上月同期日期范围 - 严格按照天数对比
prev_start = datetime(prev_year, prev_month, 1)
prev_end = datetime(prev_year, prev_month, 28)  # 固定到28号，确保天数一致

logger.info(f"📅 本月累计: {current_start.strftime('%Y-%m-%d')} 至 {current_end.strftime('%Y-%m-%d')}")
logger.info(f"📅 上月同期: {prev_start.strftime('%Y-%m-%d')} 至 {prev_end.strftime('%Y-%m-%d')}")

# 从数据库读取数据
logger.info("📊 正在从数据库读取ERP订单明细数据...")

try:
    # 连接数据库
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASSWORD, database=DB_NAME, charset=DB_CHARSET,
        connect_timeout=10
    )
    
    # 读取当前月份数据
    current_sql = f"SELECT * FROM Daysales WHERE 交易时间 >= '{current_start.strftime('%Y-%m-%d')}' AND 交易时间 <= '{current_end.strftime('%Y-%m-%d 23:59:59')}'"
    df = pd.read_sql(current_sql, conn)
    logger.info(f"📊 当前月份数据读取成功，共{len(df)}行")
    
    # 读取上月同期数据
    prev_sql = f"SELECT * FROM Daysales WHERE 交易时间 >= '{prev_start.strftime('%Y-%m-%d')}' AND 交易时间 <= '{prev_end.strftime('%Y-%m-%d 23:59:59')}'"
    df_prev = pd.read_sql(prev_sql, conn)
    logger.info(f"📊 上月同期数据读取成功，共{len(df_prev)}行")
    
    conn.close()
    
except Exception as e:
    logger.error(f"❌ 数据库连接失败: {e}")
    sys.exit(1)

# 获取分销数据
logger.info("📊 开始获取分销数据...")
df_fenxiao_current = get_fenxiao_data(current_start.strftime('%Y-%m-%d'))
logger.info(f"📊 当前月份分销数据获取完成: {len(df_fenxiao_current) if df_fenxiao_current is not None else 0} 行")

df_fenxiao_prev = get_fenxiao_data(prev_start.strftime('%Y-%m-%d'))
logger.info(f"📊 上月同期分销数据获取完成: {len(df_fenxiao_prev) if df_fenxiao_prev is not None else 0} 行")

# 识别天猫分销数据
df_tianmao_fenxiao_current = identify_tianmao_fenxiao(df)
logger.info(f"📊 当前月份天猫分销数据识别完成: {len(df_tianmao_fenxiao_current) if df_tianmao_fenxiao_current is not None else 0} 行")

df_tianmao_fenxiao_prev = identify_tianmao_fenxiao(df_prev) if df_prev is not None else None
logger.info(f"📊 上月同期天猫分销数据识别完成: {len(df_tianmao_fenxiao_prev) if df_tianmao_fenxiao_prev is not None else 0} 行")

# 检查必需列
check_required_columns(df)
if df_prev is not None and len(df_prev) > 0:
    check_required_columns(df_prev)

# 数据预处理
logger.info("🚀 开始数据预处理...")

# 批量数据类型转换
df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce')
df[AMOUNT_COL] = df[AMOUNT_COL].apply(to_number)
df[QTY_COL] = df[QTY_COL].apply(to_number)

if df_prev is not None and len(df_prev) > 0:
    df_prev[DATE_COL] = pd.to_datetime(df_prev[DATE_COL], errors='coerce')
    df_prev[AMOUNT_COL] = df_prev[AMOUNT_COL].apply(to_number)
    df_prev[QTY_COL] = df_prev[QTY_COL].apply(to_number)

# 处理分销数据
if df_fenxiao_current is not None and not df_fenxiao_current.empty:
    logger.info("🔄 处理当前月份分销数据...")
    # 数据清洗
    for col in [AMOUNT_COL, QTY_COL]:
        if col in df_fenxiao_current.columns:
            df_fenxiao_current[col] = df_fenxiao_current[col].apply(to_number)
    
    # 添加品类信息
    df_fenxiao_current[CATEGORY_COL] = df_fenxiao_current['货品名称'].apply(categorize_product)
    
    # 过滤有效数据
    df_fenxiao_current = df_fenxiao_current[(df_fenxiao_current[AMOUNT_COL] > 0) & (df_fenxiao_current[QTY_COL] > 0)]
    
    # 处理日期
    if df_fenxiao_current[DATE_COL].dtype == 'object':
        df_fenxiao_current[DATE_COL] = pd.to_datetime(df_fenxiao_current[DATE_COL], errors='coerce')
    
    # 分销数据的货品名称字段已经正确设置为产品名称，不需要重新赋值
    
    logger.info(f"📊 当前月份分销数据处理完成: {len(df_fenxiao_current)}行")
    
    # 合并分销数据到主数据
    df = pd.concat([df, df_fenxiao_current], ignore_index=True)
    logger.info(f"📊 合并分销数据后总行数: {len(df)}")

if df_tianmao_fenxiao_current is not None and not df_tianmao_fenxiao_current.empty:
    logger.info("🔄 处理当前月份天猫分销数据...")
    # 数据清洗
    for col in [AMOUNT_COL, QTY_COL]:
        if col in df_tianmao_fenxiao_current.columns:
            df_tianmao_fenxiao_current[col] = df_tianmao_fenxiao_current[col].apply(to_number)
    
    # 过滤有效数据
    df_tianmao_fenxiao_current = df_tianmao_fenxiao_current[(df_tianmao_fenxiao_current[AMOUNT_COL] > 0) & (df_tianmao_fenxiao_current[QTY_COL] > 0)]
    
    # 处理日期
    if df_tianmao_fenxiao_current[DATE_COL].dtype == 'object':
        df_tianmao_fenxiao_current[DATE_COL] = pd.to_datetime(df_tianmao_fenxiao_current[DATE_COL], errors='coerce')
    
    logger.info(f"📊 当前月份天猫分销数据处理完成: {len(df_tianmao_fenxiao_current)}行")
    
    # 合并分销数据到主数据
    df = pd.concat([df, df_tianmao_fenxiao_current], ignore_index=True)
    logger.info(f"📊 合并天猫分销数据后总行数: {len(df)}")

# 处理同期分销数据
if df_fenxiao_prev is not None and not df_fenxiao_prev.empty:
    logger.info("🔄 处理上月同期分销数据...")
    # 数据清洗
    for col in [AMOUNT_COL, QTY_COL]:
        if col in df_fenxiao_prev.columns:
            df_fenxiao_prev[col] = df_fenxiao_prev[col].apply(to_number)
    
    # 添加品类信息
    df_fenxiao_prev[CATEGORY_COL] = df_fenxiao_prev['货品名称'].apply(categorize_product)
    
    # 过滤有效数据
    df_fenxiao_prev = df_fenxiao_prev[(df_fenxiao_prev[AMOUNT_COL] > 0) & (df_fenxiao_prev[QTY_COL] > 0)]
    
    # 处理日期
    if df_fenxiao_prev[DATE_COL].dtype == 'object':
        df_fenxiao_prev[DATE_COL] = pd.to_datetime(df_fenxiao_prev[DATE_COL], errors='coerce')
    
    logger.info(f"📊 上月同期分销数据处理完成: {len(df_fenxiao_prev)}行")
    
    # 合并分销数据到主数据
    df_prev = pd.concat([df_prev, df_fenxiao_prev], ignore_index=True)
    logger.info(f"📊 合并同期分销数据后总行数: {len(df_prev)}")

if df_tianmao_fenxiao_prev is not None and not df_tianmao_fenxiao_prev.empty:
    logger.info("🔄 处理上月同期天猫分销数据...")
    # 数据清洗
    for col in [AMOUNT_COL, QTY_COL]:
        if col in df_tianmao_fenxiao_prev.columns:
            df_tianmao_fenxiao_prev[col] = df_tianmao_fenxiao_prev[col].apply(to_number)
    
    # 过滤有效数据
    df_tianmao_fenxiao_prev = df_tianmao_fenxiao_prev[(df_tianmao_fenxiao_prev[AMOUNT_COL] > 0) & (df_tianmao_fenxiao_prev[QTY_COL] > 0)]
    
    # 处理日期
    if df_tianmao_fenxiao_prev[DATE_COL].dtype == 'object':
        df_tianmao_fenxiao_prev[DATE_COL] = pd.to_datetime(df_tianmao_fenxiao_prev[DATE_COL], errors='coerce')
    
    logger.info(f"📊 上月同期天猫分销数据处理完成: {len(df_tianmao_fenxiao_prev)}行")
    
    # 合并分销数据到主数据
    df_prev = pd.concat([df_prev, df_tianmao_fenxiao_prev], ignore_index=True)
    logger.info(f"📊 合并同期天猫分销数据后总行数: {len(df_prev)}")

# 一次性过滤所有无效数据
valid_mask = (
    df[DATE_COL].notna() & 
    (df[AMOUNT_COL] > 0) & 
    (df[QTY_COL] > 0) &
    df[SHOP_COL].astype(str).str.contains('京东|天猫|拼多多|抖音|卡萨帝|小红书|淘宝|苏宁|国美', na=False)
)
df = df[valid_mask].copy()

if df_prev is not None and len(df_prev) > 0:
    valid_mask_prev = (
        df_prev[DATE_COL].notna() & 
        (df_prev[AMOUNT_COL] > 0) & 
        (df_prev[QTY_COL] > 0) &
        df_prev[SHOP_COL].astype(str).str.contains('京东|天猫|拼多多|抖音|卡萨帝|小红书|淘宝|苏宁|国美', na=False)
    )
    df_prev = df_prev[valid_mask_prev].copy()

# 添加预计算的列
logger.info("🚀 添加预计算列...")
df['渠道'] = df[SHOP_COL].str.extract(r'(京东|天猫|拼多多|抖音|卡萨帝|小红书)', expand=False).fillna('其他')
df['渠道'] = df['渠道'].replace({'小红书': '卡萨帝'})

if df_prev is not None and len(df_prev) > 0:
    df_prev['渠道'] = df_prev[SHOP_COL].str.extract(r'(京东|天猫|拼多多|抖音|卡萨帝|小红书)', expand=False).fillna('其他')
    df_prev['渠道'] = df_prev['渠道'].replace({'小红书': '卡萨帝'})

# 刷单剔除逻辑
remark_col = None
for col in df.columns:
    if col == '客服备注':
        remark_col = col
        break

if remark_col and remark_col in df.columns:
    before_rows = len(df)
    df[remark_col] = df[remark_col].astype(str).fillna('')
    filter_condition = ~(
        df[remark_col].str.contains('抽纸', na=False) |
        df[remark_col].str.contains('纸巾', na=False) |
        (df[remark_col] == '不发货')
    )
    df = df[filter_condition]
    after_rows = len(df)
    logger.info(f"刷单剔除：{before_rows} -> {after_rows}")

# 同期数据刷单剔除处理
if df_prev is not None and len(df_prev) > 0 and remark_col and remark_col in df_prev.columns:
    before_rows_prev = len(df_prev)
    df_prev[remark_col] = df_prev[remark_col].astype(str).fillna('')
    filter_condition_prev = ~(
        df_prev[remark_col].str.contains('抽纸', na=False) |
        df_prev[remark_col].str.contains('纸巾', na=False) |
        (df_prev[remark_col] == '不发货')
    )
    df_prev = df_prev[filter_condition_prev]
    after_rows_prev = len(df_prev)
    logger.info(f"同期刷单剔除：{before_rows_prev} -> {after_rows_prev}")

if df_prev is not None and len(df_prev) > 0:
    logger.info(f"📊 上月同期数据过滤后行数: {len(df_prev)}")
else:
    df_prev = None

logger.info(f"🚀 本月累计数据: {len(df)}行")
logger.info(f"📊 上月同期数据: {len(df_prev) if df_prev is not None else 0}行")

if df_prev is None or len(df_prev) == 0:
    logger.warning("⚠️ 上月同期数据为空，环比数据将显示为空")

# 在主程序中删除趋势图生成代码
# 设置报告日期和Web模式
report_date = f"{current_year}-{current_month:02d}"
is_web = True

# 删除这行：
# trend_chart_html = generate_trend_chart_html(df, DATE_COL, CATEGORY_COL, SHOP_COL, MODEL_COL, AMOUNT_COL, QTY_COL)

# ========== 主程序分组循环 ==========
# ========== 独立发送每个分组消息 ==========
for dept_name, dept_config in business_groups.items():
    logger.info(f"\n🔄 正在处理 {dept_name}...")
    # 获取目标用户
    target_users = get_target_users(dept_name, 'business')
    logger.info(f"📤 {dept_name} 目标用户: {', '.join(target_users)}")
    
    link, filename, wechat_content = generate_monthly_report_for_group(dept_name, dept_config, df, df_prev, report_date, report_date, is_web, pinyin_map)
    
    # 如果有生成的内容，发送给目标用户
    if wechat_content and target_users:
        logger.info(f"📤 发送 {dept_name} 报告给 {len(target_users)} 个用户")
        send_wecomchan_segment(wechat_content, target_users)
    
    time.sleep(2)

for channel_name, channel_config in channel_groups.items():
    logger.info(f"\n🔄 正在处理 {channel_name}...")
    # 获取目标用户
    target_users = get_target_users(channel_name, 'channel')
    logger.info(f"📤 {channel_name} 目标用户: {', '.join(target_users)}")
    
    link, filename, wechat_content = generate_monthly_report_for_group(channel_name, channel_config, df, df_prev, report_date, report_date, is_web, pinyin_map)
    
    # 如果有生成的内容，发送给目标用户
    if wechat_content and target_users:
        logger.info(f"📤 发送 {channel_name} 报告给 {len(target_users)} 个用户")
        send_wecomchan_segment(wechat_content, target_users)
    
    time.sleep(2)

logger.info("✅ 多事业部月报分析完成！")

# 主流程最后自动调用部署
if __name__ == "__main__":
    deploy_to_edgeone()
    logger.info("🎉 脚本全部执行完毕！")
