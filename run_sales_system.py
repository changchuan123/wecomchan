#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实销售分析系统执行脚本
从ERP系统读取真实数据，按组织架构发送报告
用于影刀RPA执行
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))

from sales_config import ConfigManager
from sales_data_processor import SalesDataProcessor  
from sales_report_generator import SalesReportGenerator
from wecom_message_sender import WeComMessageSender

class RealSalesSystem:
    def __init__(self):
        print("🚀 初始化真实销售分析系统...")
        self.config_manager = ConfigManager()
        self.data_processor = SalesDataProcessor(self.config_manager)
        self.report_generator = SalesReportGenerator(self.config_manager)
        self.message_sender = WeComMessageSender(self.config_manager)
        
        # 业务分组配置
        self.business_groups = {
            "空调事业部": {
                "categories": ["家用空调", "商用空调"],
                "keywords": ["空调", "挂机", "柜机", "中央空调", "多联机"],
                "department_id": 69,  # 空调事业部ID
                "leader": "YangNing"
            },
            "冰冷事业部": {
                "categories": ["冰箱", "冷柜"],
                "keywords": ["冰箱", "冷柜", "保鲜", "冷藏", "冷冻"],
                "department_id": 70,  # 冰冷事业部ID
                "leader": "WeiCunGang"
            },
            "洗护事业部": {
                "categories": ["洗衣机"],
                "keywords": ["洗衣机", "烘干机", "洗烘一体"],
                "department_id": 71,  # 洗护事业部ID  
                "leader": "YingJieBianHua"
            },
            "厨卫事业部": {
                "categories": ["水联网", "厨电洗碗机"],
                "keywords": ["热水器", "洗碗机", "厨电", "净水器", "软水机"],
                "department_id": [72, 78],  # 水联网事业部和厨电洗碗机事业部
                "leader": "WuXiang"
            }
        }
        
        self.channel_groups = {
            "抖音项目": {
                "keywords": ["抖音", "快手"],
                "department_id": 28,  # 抖音项目ID
                "leader": "LuZhiHang"
            },
            "卡萨帝项目": {
                "keywords": ["卡萨帝"],
                "department_id": 3,   # 卡萨帝项目ID
                "leader": "Mao"
            },
            "拼多多渠道": {
                "keywords": ["拼多多"],
                "department_id": 76,  # 拼多多渠道ID
                "leader": "Wen"
            }
        }
        
    def read_erp_data(self, file_path: str = None) -> pd.DataFrame:
        """读取ERP销售数据"""
        try:
            if not file_path:
                # 从配置中获取ERP数据路径
                config = self.config_manager.get_config()
                file_path = config.get("erp_data_path", "销售数据.xlsx")
            
            print(f"📊 读取ERP数据文件: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                print("请确保ERP数据文件路径正确")
                return pd.DataFrame()
            
            # 读取Excel文件
            if file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                data = pd.read_csv(file_path, encoding='utf-8')
            else:
                print(f"❌ 不支持的文件格式: {file_path}")
                return pd.DataFrame()
            
            print(f"✅ 成功读取数据，共 {len(data)} 条记录")
            print(f"📋 数据列名: {list(data.columns)}")
            
            return data
            
        except Exception as e:
            print(f"❌ 读取ERP数据失败: {e}")
            return pd.DataFrame()
    
    def process_business_groups(self, data: pd.DataFrame) -> dict:
        """按业务分组处理数据"""
        group_reports = {}
        
        for group_name, config in self.business_groups.items():
            print(f"\n🏭 处理业务分组: {group_name}")
            
            # 根据关键词筛选数据
            keywords = config["keywords"]
            group_data = self.filter_data_by_keywords(data, keywords)
            
            if not group_data.empty:
                # 生成报告
                report = self.report_generator.generate_business_report(
                    group_data, group_name, config["categories"]
                )
                group_reports[group_name] = {
                    "report": report,
                    "department_id": config["department_id"],
                    "leader": config["leader"]
                }
                print(f"✅ {group_name} 报告生成完成，数据量: {len(group_data)}")
            else:
                print(f"⚠️ {group_name} 无匹配数据")
        
        return group_reports
    
    def process_channel_groups(self, data: pd.DataFrame) -> dict:
        """按渠道分组处理数据"""
        group_reports = {}
        
        for group_name, config in self.channel_groups.items():
            print(f"\n🚀 处理渠道分组: {group_name}")
            
            # 根据关键词筛选数据
            keywords = config["keywords"]
            group_data = self.filter_data_by_keywords(data, keywords)
            
            if not group_data.empty:
                # 生成报告
                report = self.report_generator.generate_channel_report(
                    group_data, group_name
                )
                group_reports[group_name] = {
                    "report": report,
                    "department_id": config["department_id"],
                    "leader": config["leader"]
                }
                print(f"✅ {group_name} 报告生成完成，数据量: {len(group_data)}")
            else:
                print(f"⚠️ {group_name} 无匹配数据")
        
        return group_reports
    
    def filter_data_by_keywords(self, data: pd.DataFrame, keywords: list) -> pd.DataFrame:
        """根据关键词筛选数据"""
        if data.empty:
            return data
        
        # 尝试在商品名称、店铺名称等字段中查找关键词
        possible_columns = ['商品名称', '产品名称', '商品标题', '店铺名称', '店铺', '渠道', '平台']
        search_columns = [col for col in possible_columns if col in data.columns]
        
        if not search_columns:
            print(f"⚠️ 未找到可搜索的列，使用所有数据")
            return data
        
        # 创建筛选条件
        mask = pd.Series([False] * len(data))
        
        for keyword in keywords:
            for col in search_columns:
                column_mask = data[col].astype(str).str.contains(keyword, case=False, na=False)
                mask = mask | column_mask
        
        filtered_data = data[mask]
        print(f"🔍 关键词 {keywords} 筛选结果: {len(filtered_data)} 条记录")
        
        return filtered_data
    
    def get_department_users(self, department_id) -> list:
        """获取部门用户列表"""
        try:
            if isinstance(department_id, list):
                # 如果是多个部门，合并用户列表
                all_users = []
                for dept_id in department_id:
                    users = self.message_sender.get_department_users(dept_id)
                    all_users.extend(users)
                return all_users
            else:
                return self.message_sender.get_department_users(department_id)
        except Exception as e:
            print(f"❌ 获取部门用户失败: {e}")
            return []
    
    def send_reports_to_departments(self, group_reports: dict) -> bool:
        """发送报告给相应部门"""
        success_count = 0
        total_count = 0
        
        for group_name, group_info in group_reports.items():
            print(f"\n📤 发送 {group_name} 报告...")
            
            department_id = group_info["department_id"]
            report = group_info["report"]
            
            # 获取部门用户
            users = self.get_department_users(department_id)
            
            if not users:
                print(f"⚠️ {group_name} 部门无用户，跳过")
                continue
            
            # 发送给部门所有用户
            for user in users:
                user_id = user.get("userid")
                username = user.get("name", user_id)
                
                if user_id:
                    total_count += 1
                    result = self.message_sender.send_message_to_user(
                        user_id=user_id,
                        message=report,
                        username=username
                    )
                    if result:
                        success_count += 1
                        print(f"  ✅ 发送成功: {username}")
                    else:
                        print(f"  ❌ 发送失败: {username}")
        
        print(f"\n📊 发送统计: {success_count}/{total_count} 成功")
        return success_count > 0
    
    def run_full_analysis(self, erp_file_path: str = None):
        """执行完整的销售分析"""
        print("🎯 开始执行完整销售分析...")
        
        # 1. 读取ERP数据
        data = self.read_erp_data(erp_file_path)
        if data.empty:
            print("❌ 无法读取数据，退出")
            return False
        
        # 2. 处理业务分组
        print("\n🏭 处理业务分组数据...")
        business_reports = self.process_business_groups(data)
        
        # 3. 处理渠道分组
        print("\n🚀 处理渠道分组数据...")
        channel_reports = self.process_channel_groups(data)
        
        # 4. 合并所有报告
        all_reports = {**business_reports, **channel_reports}
        
        if not all_reports:
            print("❌ 未生成任何报告")
            return False
        
        print(f"\n📋 总共生成 {len(all_reports)} 个分组报告")
        
        # 5. 发送报告
        print("\n📤 开始发送报告...")
        result = self.send_reports_to_departments(all_reports)
        
        if result:
            print("🎉 销售分析完成！")
        else:
            print("❌ 报告发送失败")
        
        return result

def main():
    """主函数"""
    if len(sys.argv) > 1:
        erp_file = sys.argv[1]
        print(f"📄 使用指定的ERP文件: {erp_file}")
    else:
        erp_file = None
        print("📄 使用配置文件中的默认ERP路径")
    
    # 创建系统实例
    system = RealSalesSystem()
    
    # 执行分析
    success = system.run_full_analysis(erp_file)
    
    if success:
        print("\n✅ 任务执行成功！")
        sys.exit(0)
    else:
        print("\n❌ 任务执行失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 