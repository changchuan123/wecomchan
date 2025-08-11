#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的CLI测试脚本
测试基本的EdgeOne CLI命令
"""

import subprocess
import os

def test_basic_commands():
    """测试基本CLI命令"""
    print("🧪 测试基本CLI命令...")
    
    # 测试版本
    try:
        result = subprocess.run(["edgeone", "--version"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ 版本命令正常")
    except Exception as e:
        print(f"❌ 版本命令失败: {e}")
        return False
    
    # 测试登录状态
    try:
        result = subprocess.run(["edgeone", "whoami"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ 登录状态正常")
    except Exception as e:
        print(f"❌ 登录状态失败: {e}")
        return False
    
    # 测试项目列表
    try:
        result = subprocess.run(["edgeone", "pages", "list"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ 项目列表命令正常")
        print("项目列表输出:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ 项目列表失败: {e}")
        return False
    
    return True

def test_project_info():
    """测试项目信息命令"""
    print("\n🔍 测试项目信息命令...")
    
    try:
        result = subprocess.run(["edgeone", "pages", "info", "sales-report-new"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ 项目信息获取成功")
        print("项目信息:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 项目信息获取失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 项目信息异常: {e}")
        return False

def test_simple_deploy():
    """测试简单部署"""
    print("\n📤 测试简单部署...")
    
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
    
    # 尝试项目根目录部署（手工创建的项目支持）
    try:
        cmd = ["edgeone", "pages", "deploy", ".", "-n", "sales-report-new"]
        print(f"执行命令: {' '.join(cmd)}")
        
        # 使用较长的超时时间（因为文件较多）
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        
        print("✅ 项目根目录部署成功！")
        print("输出:")
        print(result.stdout)
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ 部署超时（300秒）")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 项目根目录部署失败: {e}")
        print(f"错误输出: {e.stderr}")
        
        # 尝试reports目录部署
        try:
            print("🔄 尝试reports目录部署...")
            cmd = ["edgeone", "pages", "deploy", "reports", "-n", "sales-report-new"]
            print(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
            
            print("✅ reports目录部署成功！")
            print("输出:")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e2:
            print(f"❌ reports目录部署也失败: {e2}")
            print(f"错误输出: {e2.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            print("❌ reports目录部署超时")
            return False
        
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 简单CLI测试")
    print("=" * 60)
    
    # 测试基本命令
    if not test_basic_commands():
        print("❌ 基本命令测试失败")
        return
    
    # 测试项目信息
    test_project_info()
    
    # 测试简单部署
    success = test_simple_deploy()
    
    if success:
        print("\n✅ 所有测试通过！")
        print("🌐 访问地址: https://sales-report-new.pages.edgeone.com")
        print("🌐 自定义域名: https://edge.haierht.cn")
    else:
        print("\n❌ 部署测试失败")
        print("💡 建议:")
        print("   1. 检查网络连接")
        print("   2. 尝试重新登录CLI")
        print("   3. 检查项目权限")

if __name__ == "__main__":
    main() 