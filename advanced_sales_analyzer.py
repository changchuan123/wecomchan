#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进阶销售数据分析器
整合数据处理、报告生成、消息发送等功能的主控制器
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from sales_config import SalesConfigManager
from sales_data_processor import SalesDataProcessor
from sales_report_generator import SalesReportGenerator
from wecom_message_sender import WecomMessageSender

class AdvancedSalesAnalyzer:
    """进阶销售数据分析器"""
    
    def __init__(self, config_path=None):
        """初始化分析器"""
        try:
            # 初始化配置管理器
            self.config_manager = SalesConfigManager()
            if config_path and os.path.exists(config_path):
                self.config_manager.load_config_from_file(config_path)
            
            # 初始化各功能模块
            self.data_processor = SalesDataProcessor(self.config_manager)
            self.report_generator = SalesReportGenerator(self.config_manager)
            self.message_sender = WecomMessageSender(self.config_manager)
            
            # 状态信息
            self.last_analysis_time = None
            self.last_data_file = None
            self.analysis_results = {}
            
            print("✅ 进阶销售分析系统初始化成功")
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            raise
    
    def load_sales_data(self, file_path, date_filter=None):
        """加载销售数据"""
        try:
            print(f"📊 加载销售数据: {file_path}")
            
            # 检查文件存在性
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
            # 使用数据处理器加载数据
            data = self.data_processor.load_data_from_file(file_path)
            if data is None or data.empty:
                raise ValueError("数据加载失败或文件为空")
            
            # 应用日期筛选
            if date_filter:
                data = self.data_processor.filter_data_by_date(data, date_filter)
            
            # 数据清洗
            cleaned_data = self.data_processor.clean_sales_data(data)
            
            # 更新状态
            self.last_data_file = file_path
            self.last_analysis_time = datetime.now()
            
            print(f"✅ 数据加载完成，共 {len(cleaned_data)} 条记录")
            return cleaned_data
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            raise
    
    def analyze_sales_data(self, data):
        """分析销售数据"""
        try:
            print("🔍 开始销售数据分析...")
            
            analysis_results = {
                'business_groups': {},
                'channel_groups': {},
                'overall_stats': {},
                'analysis_time': datetime.now().isoformat()
            }
            
            # 业务分组分析
            print("\n📊 分析业务分组数据...")
            for group_name, group_config in self.config_manager.business_groups.items():
                print(f"  正在分析: {group_name}")
                
                # 根据关键词分类数据
                group_data = self.data_processor.classify_data_by_keywords(
                    data, group_config['keywords']
                )
                
                if not group_data.empty:
                    # 数据汇总分析
                    group_analysis = self.data_processor.analyze_group_data(group_data, group_name)
                    analysis_results['business_groups'][group_name] = group_analysis
                    
                    print(f"    ✅ {group_name}: {len(group_data)} 条记录")
                else:
                    print(f"    ⚠️ {group_name}: 无匹配数据")
            
            # 渠道分组分析
            print("\n🎯 分析渠道分组数据...")
            for group_name, group_config in self.config_manager.channel_groups.items():
                print(f"  正在分析: {group_name}")
                
                # 根据关键词分类数据
                group_data = self.data_processor.classify_data_by_keywords(
                    data, group_config['keywords']
                )
                
                if not group_data.empty:
                    # 数据汇总分析
                    group_analysis = self.data_processor.analyze_group_data(group_data, group_name)
                    analysis_results['channel_groups'][group_name] = group_analysis
                    
                    print(f"    ✅ {group_name}: {len(group_data)} 条记录")
                else:
                    print(f"    ⚠️ {group_name}: 无匹配数据")
            
            # 整体统计
            overall_stats = self.data_processor.calculate_overall_stats(data)
            analysis_results['overall_stats'] = overall_stats
            
            # 保存分析结果
            self.analysis_results = analysis_results
            
            print("✅ 销售数据分析完成")
            return analysis_results
            
        except Exception as e:
            print(f"❌ 数据分析失败: {e}")
            raise
    
    def generate_reports(self, analysis_results=None):
        """生成销售报告"""
        try:
            print("📝 开始生成销售报告...")
            
            if analysis_results is None:
                analysis_results = self.analysis_results
            
            if not analysis_results:
                raise ValueError("没有可用的分析结果")
            
            reports = {
                'business_groups': {},
                'channel_groups': {},
                'generation_time': datetime.now().isoformat()
            }
            
            # 生成业务分组报告
            if 'business_groups' in analysis_results:
                print("\n📊 生成业务分组报告...")
                for group_name, group_analysis in analysis_results['business_groups'].items():
                    print(f"  生成报告: {group_name}")
                    
                    report_content = self.report_generator.generate_business_group_report(
                        group_name, group_analysis
                    )
                    reports['business_groups'][group_name] = report_content
                    
                    # 检查报告长度
                    report_length = len(report_content.encode('utf-8'))
                    print(f"    ✅ {group_name}: {report_length} 字节")
            
            # 生成渠道分组报告
            if 'channel_groups' in analysis_results:
                print("\n🎯 生成渠道分组报告...")
                for group_name, group_analysis in analysis_results['channel_groups'].items():
                    print(f"  生成报告: {group_name}")
                    
                    report_content = self.report_generator.generate_channel_group_report(
                        group_name, group_analysis
                    )
                    reports['channel_groups'][group_name] = report_content
                    
                    # 检查报告长度
                    report_length = len(report_content.encode('utf-8'))
                    print(f"    ✅ {group_name}: {report_length} 字节")
            
            print("✅ 销售报告生成完成")
            return reports
            
        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            raise
    
    def send_reports_by_organization(self, reports, test_mode=False, test_user=None):
        """按组织架构发送报告"""
        try:
            print("📤 开始按组织架构发送报告...")
            
            if test_mode and test_user:
                print(f"🧪 测试模式：仅发送给 {test_user}")
                return self._send_test_reports(reports, test_user)
            
            # 测试服务器连接
            if not self.message_sender.test_connection():
                raise Exception("企业微信服务器连接失败")
            
            # 发送所有报告
            success = self.message_sender.send_reports_to_all_groups(reports)
            
            if success:
                print("✅ 报告发送完成")
            else:
                print("❌ 部分报告发送失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 报告发送失败: {e}")
            raise
    
    def _send_test_reports(self, reports, test_user):
        """发送测试报告"""
        try:
            print(f"🧪 向测试用户 {test_user} 发送报告...")
            
            success_count = 0
            total_count = 0
            
            # 发送业务分组报告
            if 'business_groups' in reports:
                for group_name, report_content in reports['business_groups'].items():
                    total_count += 1
                    test_message = f"【测试-{group_name}】\n{report_content}"
                    
                    if self.message_sender.send_message_to_single_user(test_user, test_message):
                        success_count += 1
                        print(f"✅ {group_name} 测试报告发送成功")
                    else:
                        print(f"❌ {group_name} 测试报告发送失败")
            
            # 发送渠道分组报告
            if 'channel_groups' in reports:
                for group_name, report_content in reports['channel_groups'].items():
                    total_count += 1
                    test_message = f"【测试-{group_name}】\n{report_content}"
                    
                    if self.message_sender.send_message_to_single_user(test_user, test_message):
                        success_count += 1
                        print(f"✅ {group_name} 测试报告发送成功")
                    else:
                        print(f"❌ {group_name} 测试报告发送失败")
            
            print(f"📊 测试发送完成: {success_count}/{total_count} 成功")
            return success_count == total_count
            
        except Exception as e:
            print(f"❌ 测试发送失败: {e}")
            return False
    
    def run_full_analysis(self, data_file_path, output_dir=None, test_mode=False, test_user=None):
        """运行完整的分析流程"""
        try:
            print("🚀 开始运行完整销售分析流程...")
            print(f"📂 数据文件: {data_file_path}")
            
            # 1. 加载销售数据
            sales_data = self.load_sales_data(data_file_path)
            
            # 2. 分析销售数据
            analysis_results = self.analyze_sales_data(sales_data)
            
            # 3. 生成销售报告
            reports = self.generate_reports(analysis_results)
            
            # 4. 保存报告（可选）
            if output_dir:
                self._save_reports_to_files(reports, output_dir)
            
            # 5. 按组织架构发送报告
            send_success = self.send_reports_by_organization(reports, test_mode, test_user)
            
            # 6. 生成执行总结
            summary = {
                'execution_time': datetime.now().isoformat(),
                'data_file': data_file_path,
                'total_records': len(sales_data),
                'business_groups_count': len(analysis_results.get('business_groups', {})),
                'channel_groups_count': len(analysis_results.get('channel_groups', {})),
                'reports_generated': len(reports.get('business_groups', {})) + len(reports.get('channel_groups', {})),
                'send_success': send_success,
                'test_mode': test_mode
            }
            
            print("\n📊 执行总结:")
            print(f"  ⏰ 执行时间: {summary['execution_time']}")
            print(f"  📁 数据文件: {summary['data_file']}")
            print(f"  📊 数据记录: {summary['total_records']} 条")
            print(f"  🏢 业务分组: {summary['business_groups_count']} 个")
            print(f"  🎯 渠道分组: {summary['channel_groups_count']} 个")
            print(f"  📝 生成报告: {summary['reports_generated']} 份")
            print(f"  📤 发送状态: {'成功' if send_success else '失败'}")
            print(f"  🧪 测试模式: {'是' if test_mode else '否'}")
            
            print("\n✅ 完整分析流程执行完成")
            return summary
            
        except Exception as e:
            print(f"❌ 分析流程执行失败: {e}")
            raise
    
    def _save_reports_to_files(self, reports, output_dir):
        """保存报告到文件"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存业务分组报告
            if 'business_groups' in reports:
                for group_name, report_content in reports['business_groups'].items():
                    filename = f"business_{group_name}_{timestamp}.txt"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    print(f"💾 保存报告: {filepath}")
            
            # 保存渠道分组报告
            if 'channel_groups' in reports:
                for group_name, report_content in reports['channel_groups'].items():
                    filename = f"channel_{group_name}_{timestamp}.txt"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    print(f"💾 保存报告: {filepath}")
            
        except Exception as e:
            print(f"⚠️ 保存报告文件失败: {e}")
    
    def get_system_status(self):
        """获取系统状态"""
        try:
            status = {
                'system_initialized': True,
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'last_data_file': self.last_data_file,
                'server_connection': self.message_sender.test_connection(),
                'available_business_groups': list(self.config_manager.business_groups.keys()),
                'available_channel_groups': list(self.config_manager.channel_groups.keys()),
                'analysis_results_available': bool(self.analysis_results)
            }
            
            return status
            
        except Exception as e:
            print(f"❌ 获取系统状态失败: {e}")
            return {'system_initialized': False, 'error': str(e)}
    
    def validate_configuration(self):
        """验证系统配置"""
        try:
            print("🔧 验证系统配置...")
            
            issues = []
            
            # 检查业务分组配置
            if not self.config_manager.business_groups:
                issues.append("缺少业务分组配置")
            else:
                for group_name, config in self.config_manager.business_groups.items():
                    if not config.get('keywords'):
                        issues.append(f"业务分组 {group_name} 缺少关键词配置")
                    if not config.get('department_id'):
                        issues.append(f"业务分组 {group_name} 缺少部门ID配置")
            
            # 检查渠道分组配置
            if not self.config_manager.channel_groups:
                issues.append("缺少渠道分组配置")
            else:
                for group_name, config in self.config_manager.channel_groups.items():
                    if not config.get('keywords'):
                        issues.append(f"渠道分组 {group_name} 缺少关键词配置")
                    if not config.get('department_id'):
                        issues.append(f"渠道分组 {group_name} 缺少部门ID配置")
            
            # 检查服务器配置
            server_config = self.config_manager.server_config
            if not server_config.get('base_url'):
                issues.append("缺少服务器URL配置")
            if not server_config.get('token'):
                issues.append("缺少服务器Token配置")
            
            # 测试服务器连接
            if not self.message_sender.test_connection():
                issues.append("服务器连接测试失败")
            
            if issues:
                print("❌ 配置验证发现问题:")
                for issue in issues:
                    print(f"  • {issue}")
                return False
            else:
                print("✅ 配置验证通过")
                return True
                
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            return False

def main():
    """主函数 - 演示系统功能"""
    try:
        print("🎯 进阶销售分析系统演示")
        print("=" * 50)
        
        # 初始化系统
        analyzer = AdvancedSalesAnalyzer()
        
        # 验证配置
        if not analyzer.validate_configuration():
            print("❌ 系统配置验证失败，请检查配置")
            return
        
        # 获取系统状态
        status = analyzer.get_system_status()
        print("\n📊 系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 示例：运行完整分析流程（测试模式）
        print("\n🧪 运行测试分析...")
        
        # 检查是否有示例数据文件
        sample_data_files = [
            "sales_data.xlsx",
            "sales_data.csv", 
            "销售数据.xlsx",
            "销售数据.csv"
        ]
        
        data_file = None
        for filename in sample_data_files:
            if os.path.exists(filename):
                data_file = filename
                break
        
        if data_file:
            print(f"📁 找到数据文件: {data_file}")
            
            # 运行完整分析流程（测试模式）
            summary = analyzer.run_full_analysis(
                data_file_path=data_file,
                test_mode=True,
                test_user="weicungang"  # 测试用户
            )
            
            print("\n✅ 演示完成")
        else:
            print("⚠️ 未找到数据文件，跳过分析演示")
            print("💡 请准备销售数据文件（Excel或CSV格式）")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")

if __name__ == "__main__":
    main() 