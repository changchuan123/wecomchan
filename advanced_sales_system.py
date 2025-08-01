#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进阶销售分析系统主控制器
整合配置管理、数据处理、报告生成、消息发送等所有功能模块
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from sales_config import SalesConfigManager
from sales_data_processor import SalesDataProcessor
from sales_report_generator import SalesReportGenerator
from wecom_message_sender import WecomMessageSender
from advanced_sales_analyzer import AdvancedSalesAnalyzer

class AdvancedSalesSystem:
    """进阶销售分析系统主控制器"""
    
    def __init__(self, config_file=None):
        """初始化系统"""
        try:
            print("🚀 初始化进阶销售分析系统...")
            
            # 初始化核心分析器
            self.analyzer = AdvancedSalesAnalyzer(config_file)
            
            # 系统信息
            self.version = "1.0.0"
            self.startup_time = datetime.now()
            
            print(f"✅ 系统初始化完成 (版本: {self.version})")
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            raise
    
    def display_system_info(self):
        """显示系统信息"""
        print("\n" + "="*60)
        print("🎯 进阶销售数据分析系统")
        print("="*60)
        print(f"版本: {self.version}")
        print(f"启动时间: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"企业微信服务器: {self.analyzer.config_manager.server_config['base_url']}")
        
        # 显示业务分组配置
        print("\n📊 业务分组配置:")
        for group_name, config in self.analyzer.config_manager.business_groups.items():
            print(f"  • {group_name}: 部门ID {config['department_id']}, 负责人 {config['leader']}")
        
        # 显示渠道分组配置
        print("\n🎯 渠道分组配置:")
        for group_name, config in self.analyzer.config_manager.channel_groups.items():
            print(f"  • {group_name}: 部门ID {config['department_id']}, 负责人 {config['leader']}")
        
        print("="*60)
    
    def interactive_mode(self):
        """交互模式"""
        try:
            self.display_system_info()
            
            while True:
                print("\n🔧 操作选项:")
                print("1. 运行完整分析流程")
                print("2. 测试模式分析（发送给指定用户）")
                print("3. 验证系统配置")
                print("4. 查看系统状态")
                print("5. 测试服务器连接")
                print("0. 退出系统")
                
                choice = input("\n请选择操作 (0-5): ").strip()
                
                if choice == "1":
                    self._run_full_analysis_interactive()
                elif choice == "2":
                    self._run_test_analysis_interactive()
                elif choice == "3":
                    self._validate_configuration()
                elif choice == "4":
                    self._show_system_status()
                elif choice == "5":
                    self._test_server_connection()
                elif choice == "0":
                    print("👋 退出系统")
                    break
                else:
                    print("❌ 无效选择，请重新输入")
                    
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出系统")
        except Exception as e:
            print(f"❌ 交互模式运行错误: {e}")
    
    def _run_full_analysis_interactive(self):
        """交互式运行完整分析"""
        try:
            print("\n📊 运行完整分析流程")
            
            # 输入数据文件路径
            data_file = input("请输入销售数据文件路径: ").strip()
            if not data_file:
                print("❌ 文件路径不能为空")
                return
            
            if not os.path.exists(data_file):
                print(f"❌ 文件不存在: {data_file}")
                return
            
            # 询问是否保存报告文件
            save_reports = input("是否保存报告文件到本地? (y/n): ").strip().lower()
            output_dir = None
            if save_reports == 'y':
                output_dir = input("请输入报告保存目录 (默认: ./reports): ").strip()
                if not output_dir:
                    output_dir = "./reports"
            
            # 运行分析
            print("\n🚀 开始运行分析流程...")
            summary = self.analyzer.run_full_analysis(
                data_file_path=data_file,
                output_dir=output_dir,
                test_mode=False
            )
            
            print("\n✅ 分析流程完成")
            
        except Exception as e:
            print(f"❌ 分析流程失败: {e}")
    
    def _run_test_analysis_interactive(self):
        """交互式运行测试分析"""
        try:
            print("\n🧪 运行测试分析流程")
            
            # 输入数据文件路径
            data_file = input("请输入销售数据文件路径: ").strip()
            if not data_file:
                print("❌ 文件路径不能为空")
                return
            
            if not os.path.exists(data_file):
                print(f"❌ 文件不存在: {data_file}")
                return
            
            # 输入测试用户
            test_user = input("请输入测试用户ID (默认: weicungang): ").strip()
            if not test_user:
                test_user = "weicungang"
            
            # 运行测试分析
            print(f"\n🚀 开始运行测试分析流程 (测试用户: {test_user})...")
            summary = self.analyzer.run_full_analysis(
                data_file_path=data_file,
                test_mode=True,
                test_user=test_user
            )
            
            print("\n✅ 测试分析流程完成")
            
        except Exception as e:
            print(f"❌ 测试分析流程失败: {e}")
    
    def _validate_configuration(self):
        """验证配置"""
        try:
            print("\n🔧 验证系统配置...")
            success = self.analyzer.validate_configuration()
            
            if success:
                print("✅ 系统配置验证通过")
            else:
                print("❌ 系统配置验证失败，请检查配置文件")
                
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
    
    def _show_system_status(self):
        """显示系统状态"""
        try:
            print("\n📊 系统状态信息...")
            status = self.analyzer.get_system_status()
            
            print("系统状态:")
            for key, value in status.items():
                status_icon = "✅" if value else "❌" if isinstance(value, bool) else "ℹ️"
                print(f"  {status_icon} {key}: {value}")
                
        except Exception as e:
            print(f"❌ 获取系统状态失败: {e}")
    
    def _test_server_connection(self):
        """测试服务器连接"""
        try:
            print("\n🔗 测试企业微信服务器连接...")
            
            success = self.analyzer.message_sender.test_connection()
            
            if success:
                print("✅ 服务器连接正常")
                
                # 获取组织架构信息
                org_data = self.analyzer.message_sender.get_organization_structure()
                if org_data:
                    departments = org_data.get('departments', [])
                    print(f"📊 获取到 {len(departments)} 个部门信息")
                    
                    # 显示前5个部门作为示例
                    print("部门示例:")
                    for dept in departments[:5]:
                        dept_name = dept.get('name', '未知部门')
                        dept_id = dept.get('id', '未知ID')
                        print(f"  • {dept_name} (ID: {dept_id})")
                    
                    if len(departments) > 5:
                        print(f"  ... 还有 {len(departments) - 5} 个部门")
                else:
                    print("⚠️ 无法获取组织架构信息")
            else:
                print("❌ 服务器连接失败")
                
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
    
    def run_batch_mode(self, data_file, test_mode=False, test_user=None, output_dir=None):
        """批处理模式"""
        try:
            print("🤖 批处理模式运行")
            
            # 显示系统信息
            self.display_system_info()
            
            # 验证配置
            print("\n🔧 验证系统配置...")
            if not self.analyzer.validate_configuration():
                print("❌ 系统配置验证失败，终止运行")
                return False
            
            # 运行分析
            summary = self.analyzer.run_full_analysis(
                data_file_path=data_file,
                output_dir=output_dir,
                test_mode=test_mode,
                test_user=test_user
            )
            
            return summary is not None
            
        except Exception as e:
            print(f"❌ 批处理模式运行失败: {e}")
            return False

def create_sample_config():
    """创建示例配置文件"""
    try:
        config_manager = SalesConfigManager()
        config_data = config_manager.get_full_config()
        
        with open("sales_config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 示例配置文件已创建: sales_config.json")
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="进阶销售数据分析系统")
    parser.add_argument("--data-file", help="销售数据文件路径")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--test-mode", action="store_true", help="测试模式")
    parser.add_argument("--test-user", default="weicungang", help="测试用户ID")
    parser.add_argument("--output-dir", help="报告输出目录")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--create-config", action="store_true", help="创建示例配置文件")
    
    args = parser.parse_args()
    
    try:
        # 创建配置文件
        if args.create_config:
            create_sample_config()
            return
        
        # 初始化系统
        system = AdvancedSalesSystem(args.config)
        
        # 交互模式
        if args.interactive:
            system.interactive_mode()
            return
        
        # 批处理模式
        if args.data_file:
            success = system.run_batch_mode(
                data_file=args.data_file,
                test_mode=args.test_mode,
                test_user=args.test_user,
                output_dir=args.output_dir
            )
            
            if success:
                print("✅ 批处理运行成功")
            else:
                print("❌ 批处理运行失败")
                sys.exit(1)
        else:
            # 默认进入交互模式
            system.interactive_mode()
            
    except Exception as e:
        print(f"❌ 系统运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 