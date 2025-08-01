#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销售数据分析系统配置管理
用于管理业务分组规则、渠道分类、部门映射等配置信息
"""

import os
import json
from pathlib import Path

# ========== 基础配置 ==========
class BaseConfig:
    # 服务器配置
    WECOMCHAN_SERVER_URL = "http://212.64.57.87:5001"
    TOKEN = "wecomchan_token"
    
    # 数据文件路径
    ERP_FOLDER = r"E:\电商数据\虹图\ERP订单明细"
    
    # 消息发送配置
    MAX_MESSAGE_BYTES = 2048
    REQUEST_TIMEOUT = 10
    
    # 报告配置
    MAX_TOP_SHOPS = 5
    MAX_TOP_PRODUCTS = 10
    MAX_SHOP_PRODUCTS = 5

# ========== 业务分组配置 ==========
BUSINESS_GROUPS = {
    "空调事业部": {
        "department_keywords": ["空调", "家用空调", "商用空调"],
        "product_keywords": ["空调", "挂机", "柜机", "中央空调", "多联机", "风管机"],
        "categories": ["家用空调", "商用空调"],
        "description": "包含家用空调和商用空调品类",
        "priority": 1
    },
    "冰冷事业部": {
        "department_keywords": ["冰冷", "冰箱", "冷柜"],
        "product_keywords": ["冰箱", "冷柜", "冷藏", "冷冻", "酒柜"],
        "categories": ["冰箱", "冷柜"],
        "description": "包含冰箱、冷柜品类",
        "priority": 2
    },
    "洗护事业部": {
        "department_keywords": ["洗护", "洗衣机"],
        "product_keywords": ["洗衣机", "干衣机", "洗烘", "波轮", "滚筒"],
        "categories": ["洗衣机"],
        "description": "包含洗衣机品类",
        "priority": 3
    },
    "厨卫事业部": {
        "department_keywords": ["水联网", "热水器", "厨电", "洗碗机"],
        "product_keywords": ["热水器", "燃气", "电热", "厨电", "洗碗机", "消毒柜", "烟机", "灶具", "集成灶"],
        "categories": ["热水器", "厨电", "洗碗机"],
        "description": "包含水联网事业部和厨电洗碗机事业部",
        "priority": 4
    }
}

# ========== 渠道分组配置 ==========
CHANNEL_GROUPS = {
    "抖音项目": {
        "department_keywords": ["抖音", "快手"],
        "shop_keywords": ["抖音", "快手", "douyin", "kuaishou"],
        "channels": ["抖音", "快手"],
        "description": "包含抖音和快手渠道店铺",
        "priority": 1
    },
    "卡萨帝项目": {
        "department_keywords": ["卡萨帝"],
        "shop_keywords": ["卡萨帝", "casarte"],
        "channels": ["卡萨帝"],
        "description": "所有带卡萨帝字样的店铺",
        "priority": 2
    },
    "拼多多渠道": {
        "department_keywords": ["拼多多"],
        "shop_keywords": ["拼多多", "pdd", "pinduoduo"],
        "channels": ["拼多多"],
        "description": "拼多多渠道所有店铺",
        "priority": 3
    }
}

# ========== 数据清洗配置 ==========
DATA_CLEANING_CONFIG = {
    # 列名映射规则
    "column_mapping": {
        "amount_keywords": ["退款前支付金额", "金额", "支付金额", "销售额"],
        "quantity_keywords": ["实发数量", "数量", "销售数量"],
        "shop_keywords": ["店铺", "店铺名称"],
        "remark_keywords": ["客服备注", "备注", "说明"]
    },
    
    # 过滤规则
    "filter_rules": {
        "exclude_remarks": ["抽纸", "不发货", "测试", "样品"],
        "min_amount": 0,
        "min_quantity": 0
    },
    
    # 必需列
    "required_columns": ["货品名称", "规格名称"]
}

# ========== 报告模板配置 ==========
REPORT_TEMPLATES = {
    "business_group": {
        "header": "{date} {group_name}销售分析：",
        "summary": "整体销售 {total_amount}，前一天 {prev_total_amount}，环比 {ratio}，销售数量 {total_qty}，单价 {avg_price}",
        "shop_section": "TOP 店铺数据：",
        "category_header": "\n{category}",
        "shop_line": "{shop}，销售 {amount}，前一天 {prev_amount}，环比 {ratio}，销售数量 {qty}，单价 {price}",
        "product_line": "单品 TOP{rank} {product}，销售 {amount}，销售数量 {qty}，前一天 {prev_qty}，环比 {ratio}",
        "overall_products": "\n核心单品销售明细（累计整体单品 top）",
        "overall_product_line": "TOP{rank} {product}，销售 {amount}，销售数量 {qty}，前一天 {prev_qty}，环比 {ratio}"
    },
    
    "channel_group": {
        "header": "{date} {group_name}销售分析：",
        "summary": "整体销售 {total_amount}，前一天 {prev_total_amount}，环比 {ratio}，销售数量 {total_qty}，单价 {avg_price}",
        "shop_section": "\n店铺数据：",
        "shop_line": "店铺 {rank} {shop}，销售 {amount}，前一天 {prev_amount}，环比 {ratio}，销售数量 {qty}，单价 {price}",
        "product_section": "\n单品数据：",
        "product_line": "TOP{rank} 单品 {product}，销售 {amount}，前一天 {prev_qty}，环比 {ratio}，销售数量 {qty}，单价 {price}"
    }
}

# ========== 配置管理类 ==========
class SalesConfigManager:
    """销售分析系统配置管理器"""
    
    def __init__(self):
        # 服务器配置
        self.server_config = {
            "base_url": "http://212.64.57.87:5001",
            "token": "wecomchan_token",
            "timeout": 30
        }
        
        # 4个品类组配置
        self.business_groups = {
            "空调事业部": {
                "keywords": ["空调", "家用空调", "商用空调", "中央空调", "挂机", "柜机"],
                "department_id": 69,  # 根据实际组织架构调整
                "leader": "YangNing",
                "description": "家用+商用空调"
            },
            "冰冷事业部": {
                "keywords": ["冰箱", "冷柜", "冰柜", "保鲜", "冷冻", "双开门", "三开门"],
                "department_id": 70,
                "leader": "WeiCunGang", 
                "description": "冰箱+冷柜"
            },
            "洗护事业部": {
                "keywords": ["洗衣机", "干衣机", "洗烘一体", "波轮", "滚筒"],
                "department_id": 71,
                "leader": "YingJieBianHua",
                "description": "洗衣机"
            },
            "厨卫事业部": {
                "keywords": ["热水器", "净水器", "洗碗机", "厨电", "水联网", "燃气灶", "油烟机"],
                "department_id": [72, 78],  # 水联网+厨电洗碗机合并
                "leader": "WuXiang",
                "description": "水联网+厨电洗碗机合并"
            }
        }
        
        # 3个渠道组配置
        self.channel_groups = {
            "抖音项目": {
                "keywords": ["抖音", "快手", "短视频", "直播"],
                "department_id": 28,
                "leader": "LuZhiHang",
                "description": "抖音+快手"
            },
            "卡萨帝项目": {
                "keywords": ["卡萨帝", "Casarte", "高端"],
                "department_id": 3,
                "leader": "Mao",
                "description": "带卡萨帝字样店铺"
            },
            "拼多多渠道": {
                "keywords": ["拼多多", "PDD", "百亿补贴"],
                "department_id": 76,
                "leader": "Wen", 
                "description": "拼多多渠道"
            }
        }
        
        # 报告配置
        self.report_config = {
            "max_message_length": 4000,  # 企业微信消息最大长度
            "top_stores_count": 10,      # TOP店铺数量
            "top_products_count": 15,    # 核心单品数量
            "decimal_places": 2          # 小数位数
        }
        
        # 数据字段映射
        self.field_mapping = {
            "product_name": ["商品名称", "产品名称", "商品", "产品"],
            "store_name": ["店铺名称", "店铺", "门店"],
            "channel": ["渠道", "平台", "来源"],
            "sales_amount": ["销售额", "金额", "营收"],
            "sales_quantity": ["销售量", "数量", "件数"],
            "date": ["日期", "时间", "统计日期"]
        }
    
    def get_business_group_by_keywords(self, product_name, store_name=""):
        """根据关键词识别产品所属的事业部"""
        text = f"{product_name} {store_name}".lower()
        
        for group_name, config in self.business_groups.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    return group_name
        return None
    
    def get_channel_group_by_keywords(self, channel_name, store_name=""):
        """根据关键词识别渠道所属的项目组"""
        text = f"{channel_name} {store_name}".lower()
        
        for group_name, config in self.channel_groups.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    return group_name
        return None
    
    def get_department_mapping(self):
        """获取所有部门映射关系"""
        mapping = {}
        
        # 添加业务分组
        for group_name, config in self.business_groups.items():
            dept_ids = config["department_id"]
            if isinstance(dept_ids, list):
                for dept_id in dept_ids:
                    mapping[dept_id] = {
                        "group_name": group_name,
                        "group_type": "business",
                        "leader": config["leader"]
                    }
            else:
                mapping[dept_ids] = {
                    "group_name": group_name,
                    "group_type": "business", 
                    "leader": config["leader"]
                }
        
        # 添加渠道分组
        for group_name, config in self.channel_groups.items():
            dept_id = config["department_id"]
            mapping[dept_id] = {
                "group_name": group_name,
                "group_type": "channel",
                "leader": config["leader"]
            }
        
        return mapping
    
    def get_server_config(self):
        """获取服务器配置"""
        return self.server_config
    
    def get_report_config(self):
        """获取报告配置"""
        return self.report_config
    
    def get_all_groups(self):
        """获取所有分组配置"""
        return {
            "business_groups": self.business_groups,
            "channel_groups": self.channel_groups
        }

# ========== 配置工具函数 ==========
def create_default_config_file():
    """创建默认配置文件"""
    config_manager = SalesConfigManager()
    if config_manager.save_config():
        print("✅ 已创建默认配置文件: sales_config.json")
    else:
        print("❌ 创建配置文件失败")

def main():
    """主函数 - 配置管理工具"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python sales_config.py list          # 列出所有分组")
        print("  python sales_config.py create        # 创建默认配置文件")
        print("  python sales_config.py validate      # 验证配置")
        return
    
    action = sys.argv[1]
    config_manager = SalesConfigManager()
    
    if action == "list":
        config_manager.list_groups()
    elif action == "create":
        create_default_config_file()
    elif action == "validate":
        errors = config_manager.validate_config()
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ 配置验证通过")
    else:
        print(f"❌ 未知操作: {action}")

if __name__ == "__main__":
    main() 