#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进阶销售分析系统演示程序
展示系统功能和使用方法
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from advanced_sales_system import AdvancedSalesSystem

def create_demo_data():
    """创建演示数据"""
    print("📊 创建演示销售数据...")
    
    # 模拟ERP销售数据
    demo_data = [
        # 空调事业部数据
        {"店铺名称": "海尔官方旗舰店", "商品名称": "海尔变频空调1.5匹挂机", "渠道": "天猫", "销售额": 156780, "销售量": 89, "日期": "2024-01-15"},
        {"店铺名称": "海尔空调专营店", "商品名称": "海尔柜式空调3匹立式", "渠道": "京东", "销售额": 234567, "销售量": 45, "日期": "2024-01-15"},
        {"店铺名称": "海尔商用空调店", "商品名称": "海尔中央空调家用套装", "渠道": "天猫", "销售额": 345678, "销售量": 23, "日期": "2024-01-15"},
        
        # 冰冷事业部数据
        {"店铺名称": "海尔冰箱旗舰店", "商品名称": "海尔三开门冰箱516L", "渠道": "天猫", "销售额": 189456, "销售量": 67, "日期": "2024-01-15"},
        {"店铺名称": "海尔电器专营店", "商品名称": "海尔冷柜卧式200L", "渠道": "京东", "销售额": 98765, "销售量": 34, "日期": "2024-01-15"},
        
        # 洗护事业部数据
        {"店铺名称": "海尔洗衣机官店", "商品名称": "海尔滚筒洗衣机10KG", "渠道": "天猫", "销售额": 123456, "销售量": 56, "日期": "2024-01-15"},
        {"店铺名称": "海尔洗护专营店", "商品名称": "海尔波轮洗衣机8KG", "渠道": "京东", "销售额": 87654, "销售量": 78, "日期": "2024-01-15"},
        
        # 厨卫事业部数据
        {"店铺名称": "海尔热水器官店", "商品名称": "海尔燃气热水器16L", "渠道": "天猫", "销售额": 76543, "销售量": 45, "日期": "2024-01-15"},
        {"店铺名称": "海尔厨电专营店", "商品名称": "海尔洗碗机13套", "渠道": "京东", "销售额": 54321, "销售量": 23, "日期": "2024-01-15"},
        
        # 抖音项目数据
        {"店铺名称": "海尔抖音官方店", "商品名称": "海尔空调1匹挂机", "渠道": "抖音", "销售额": 234567, "销售量": 156, "日期": "2024-01-15"},
        {"店铺名称": "海尔快手专营店", "商品名称": "海尔冰箱双开门", "渠道": "快手", "销售额": 178934, "销售量": 89, "日期": "2024-01-15"},
        
        # 卡萨帝项目数据
        {"店铺名称": "卡萨帝旗舰店", "商品名称": "卡萨帝空调变频2匹", "渠道": "天猫", "销售额": 456789, "销售量": 67, "日期": "2024-01-15"},
        {"店铺名称": "CASARTE官方店", "商品名称": "卡萨帝冰箱法式四门", "渠道": "京东", "销售额": 345678, "销售量": 34, "日期": "2024-01-15"},
        
        # 拼多多渠道数据
        {"店铺名称": "海尔拼多多店", "商品名称": "海尔空调1匹定频", "渠道": "拼多多", "销售额": 123456, "销售量": 234, "日期": "2024-01-15"},
        {"店铺名称": "海尔PDD专营店", "商品名称": "海尔洗衣机6KG", "渠道": "拼多多", "销售额": 98765, "销售量": 167, "日期": "2024-01-15"},
    ]
    
    # 创建前一天对比数据
    prev_data = []
    for item in demo_data:
        prev_item = item.copy()
        prev_item["日期"] = "2024-01-14"
        # 随机调整前一天数据（±20%）
        import random
        factor = random.uniform(0.8, 1.2)
        prev_item["销售额"] = int(item["销售额"] * factor)
        prev_item["销售量"] = int(item["销售量"] * factor)
        prev_data.append(prev_item)
    
    # 合并数据
    all_data = demo_data + prev_data
    
    # 创建数据目录
    os.makedirs("data", exist_ok=True)
    
    # 保存为Excel文件
    df = pd.DataFrame(all_data)
    excel_path = "data/演示销售数据.xlsx"
    df.to_excel(excel_path, index=False, encoding='utf-8')
    
    print(f"✅ 演示数据已保存到: {excel_path}")
    print(f"📈 数据条目: {len(all_data)} 条")
    print(f"📅 数据时间范围: 2024-01-14 ~ 2024-01-15")
    
    return excel_path

def demo_data_processing():
    """演示数据处理功能"""
    print("\n" + "="*60)
    print("🔄 演示数据处理功能")
    print("="*60)
    
    try:
        # 初始化系统
        system = AdvancedSalesSystem("sales_config.json")
        
        # 创建演示数据
        data_file = create_demo_data()
        
        # 处理数据
        print("\n📊 处理销售数据...")
        result = system.process_sales_data(data_file)
        
        if result["success"]:
            print("✅ 数据处理成功")
            print(f"📋 业务分组数量: {len(result['business_groups'])}")
            print(f"📋 渠道分组数量: {len(result['channel_groups'])}")
            
            # 显示分组结果
            for group_name, group_data in result["business_groups"].items():
                print(f"  🏢 {group_name}: {len(group_data)} 条数据")
                
            for group_name, group_data in result["channel_groups"].items():
                print(f"  📱 {group_name}: {len(group_data)} 条数据")
        else:
            print(f"❌ 数据处理失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 演示数据处理失败: {str(e)}")

def demo_report_generation():
    """演示报告生成功能"""
    print("\n" + "="*60)
    print("📋 演示报告生成功能")
    print("="*60)
    
    try:
        # 初始化系统
        system = AdvancedSalesSystem("sales_config.json")
        
        # 创建演示数据
        data_file = create_demo_data()
        
        # 处理数据
        result = system.process_sales_data(data_file)
        
        if result["success"]:
            # 生成业务分组报告
            print("\n📊 生成业务分组报告...")
            for group_name, group_data in result["business_groups"].items():
                if len(group_data) > 0:
                    print(f"\n🏢 {group_name} 报告:")
                    report = system.analyzer.report_generator.generate_business_group_report(
                        group_name, group_data, "2024-01-15"
                    )
                    print(report[:500] + "..." if len(report) > 500 else report)
            
            # 生成渠道分组报告
            print("\n📱 生成渠道分组报告...")
            for group_name, group_data in result["channel_groups"].items():
                if len(group_data) > 0:
                    print(f"\n📱 {group_name} 报告:")
                    report = system.analyzer.report_generator.generate_channel_group_report(
                        group_name, group_data, "2024-01-15"
                    )
                    print(report[:500] + "..." if len(report) > 500 else report)
                    
    except Exception as e:
        print(f"❌ 演示报告生成失败: {str(e)}")

def demo_organization_structure():
    """演示组织架构获取功能"""
    print("\n" + "="*60)
    print("🏗️ 演示组织架构获取功能")
    print("="*60)
    
    try:
        # 初始化系统
        system = AdvancedSalesSystem("sales_config.json")
        
        # 获取组织架构
        print("📡 获取企业微信组织架构...")
        org_info = system.analyzer.message_sender.get_organization_structure()
        
        if org_info:
            print("✅ 组织架构获取成功")
            print(f"📋 部门总数: {len(org_info.get('departments', []))}")
            
            # 显示前几个部门信息
            departments = org_info.get('departments', [])[:5]
            for dept in departments:
                print(f"  🏢 部门ID: {dept.get('id')}, 名称: {dept.get('name')}")
                
            # 检查配置的部门ID是否存在
            config_dept_ids = []
            for group_config in system.config_manager.business_groups.values():
                dept_id = group_config.get('department_id')
                if isinstance(dept_id, list):
                    config_dept_ids.extend(dept_id)
                else:
                    config_dept_ids.append(dept_id)
            
            print(f"\n🔍 检查配置的部门ID: {config_dept_ids}")
            existing_ids = [dept.get('id') for dept in org_info.get('departments', [])]
            for dept_id in config_dept_ids:
                if dept_id in existing_ids:
                    print(f"  ✅ 部门ID {dept_id} 存在")
                else:
                    print(f"  ❌ 部门ID {dept_id} 不存在")
        else:
            print("❌ 组织架构获取失败")
            
    except Exception as e:
        print(f"❌ 演示组织架构获取失败: {str(e)}")

def demo_complete_workflow():
    """演示完整工作流程"""
    print("\n" + "="*60)
    print("🚀 演示完整工作流程")
    print("="*60)
    
    try:
        # 初始化系统
        system = AdvancedSalesSystem("sales_config.json")
        
        # 创建演示数据
        data_file = create_demo_data()
        
        # 执行完整分析流程
        print("\n🔄 执行完整销售数据分析...")
        success = system.run_analysis(data_file, target_date="2024-01-15")
        
        if success:
            print("✅ 完整工作流程执行成功")
            print("📊 销售数据已分析完成")
            print("📋 报告已生成")
            print("📱 消息已发送到企业微信")
        else:
            print("❌ 完整工作流程执行失败")
            
    except Exception as e:
        print(f"❌ 演示完整工作流程失败: {str(e)}")

def main():
    """主演示函数"""
    print("🎯 进阶销售分析系统演示程序")
    print("="*60)
    print("本演示将展示系统的主要功能:")
    print("1. 数据处理功能")
    print("2. 报告生成功能")
    print("3. 组织架构获取功能")
    print("4. 完整工作流程")
    print("="*60)
    
    try:
        # 检查配置文件
        if not os.path.exists("sales_config.json"):
            print("❌ 配置文件 sales_config.json 不存在")
            return
        
        # 演示各功能模块
        demo_data_processing()
        demo_report_generation()
        demo_organization_structure()
        demo_complete_workflow()
        
        print("\n" + "="*60)
        print("🎉 演示完成！")
        print("="*60)
        print("💡 提示:")
        print("- 修改 sales_config.json 可调整系统配置")
        print("- 将真实ERP数据文件放入 data/ 目录")
        print("- 运行 advanced_sales_system.py 进行实际分析")
        print("- 查看生成的报告文件在 reports/ 目录")
        
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示执行失败: {str(e)}")

if __name__ == "__main__":
    main() 