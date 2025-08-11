#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的CLI部署测试脚本
直接测试EdgeOne CLI部署功能
"""

import subprocess
import os
import time

def test_cli_deploy():
    """测试CLI部署"""
    print("🚀 测试EdgeOne CLI部署...")
    
    # 检查CLI
    try:
        result = subprocess.run(["edgeone", "--version"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 可用")
    except Exception as e:
        print(f"❌ EdgeOne CLI 不可用: {e}")
        return False
    
    # 检查登录状态
    try:
        result = subprocess.run(["edgeone", "whoami"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 已登录")
    except Exception as e:
        print(f"❌ EdgeOne CLI 未登录: {e}")
        return False
    
    # 检查reports目录
    reports_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.exists(reports_dir):
        print(f"❌ Reports目录不存在: {reports_dir}")
        return False
    
    html_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
    print(f"📄 发现 {len(html_files)} 个HTML文件")
    
    if not html_files:
        print("❌ Reports目录中没有HTML文件")
        return False
    
    # 尝试部署
    print("📤 尝试部署到 sales-report-new...")
    
    try:
        # 方法1: 直接部署项目根目录
        cmd = ["edgeone", "pages", "deploy", ".", "-n", "sales-report-new"]
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        
        print("✅ 部署成功！")
        print("输出:")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 部署失败: {e}")
        print(f"错误输出: {e.stderr}")
        
        # 尝试方法2: 部署reports目录
        try:
            print("🔄 尝试部署reports目录...")
            cmd = ["edgeone", "pages", "deploy", "reports", "-n", "sales-report-new"]
            print(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            
            print("✅ reports目录部署成功！")
            print("输出:")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e2:
            print(f"❌ reports目录部署也失败: {e2}")
            print(f"错误输出: {e2.stderr}")
            
            # 尝试方法3: 创建项目后部署
            try:
                print("🔄 尝试创建项目后部署...")
                
                # 创建项目
                create_cmd = ["edgeone", "pages", "create", "sales-report-new"]
                print(f"创建项目: {' '.join(create_cmd)}")
                
                subprocess.run(create_cmd, check=True, capture_output=True, text=True, timeout=60)
                print("✅ 项目创建成功")
                
                # 等待一下
                time.sleep(5)
                
                # 部署
                deploy_cmd = ["edgeone", "pages", "deploy", ".", "-n", "sales-report-new"]
                print(f"部署到新项目: {' '.join(deploy_cmd)}")
                
                result = subprocess.run(deploy_cmd, check=True, capture_output=True, text=True, timeout=300)
                
                print("✅ 创建并部署成功！")
                print("输出:")
                print(result.stdout)
                return True
                
            except subprocess.CalledProcessError as e3:
                print(f"❌ 创建项目部署也失败: {e3}")
                print(f"错误输出: {e3.stderr}")
                return False
    
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 EdgeOne CLI 部署测试")
    print("=" * 60)
    
    success = test_cli_deploy()
    
    if success:
        print("\n✅ 部署测试成功！")
        print("🌐 访问地址: https://sales-report-new.pages.edgeone.com")
        print("🌐 自定义域名: https://edge.haierht.cn")
    else:
        print("\n❌ 部署测试失败")
        print("💡 建议:")
        print("   1. 检查EdgeOne CLI是否正确安装")
        print("   2. 确认是否已登录")
        print("   3. 检查项目权限")
        print("   4. 尝试在Web控制台手动创建项目")

if __name__ == "__main__":
    main() 