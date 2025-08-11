#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EdgeOne 项目检查脚本
检查CLI和Web控制台的项目同步状态
"""

import subprocess
import json
import os

def check_edgeone_cli():
    """检查EdgeOne CLI状态"""
    try:
        result = subprocess.run(["edgeone", "--version"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 已安装")
        print(f"版本: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ EdgeOne CLI 不可用: {e}")
        return False

def check_login_status():
    """检查登录状态"""
    try:
        result = subprocess.run(["edgeone", "whoami"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("✅ EdgeOne CLI 已登录")
        print("用户信息:")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ EdgeOne CLI 未登录: {e}")
        return False

def list_projects():
    """列出所有项目"""
    try:
        result = subprocess.run(["edgeone", "pages", "list"], 
                              capture_output=True, text=True, check=True, timeout=10)
        print("📋 项目列表:")
        print(result.stdout)
        return result.stdout
    except Exception as e:
        print(f"❌ 获取项目列表失败: {e}")
        return None

def get_project_info(project_name):
    """获取项目详细信息"""
    try:
        result = subprocess.run(["edgeone", "pages", "info", project_name], 
                              capture_output=True, text=True, check=True, timeout=10)
        print(f"📋 项目 {project_name} 详细信息:")
        print(result.stdout)
        return result.stdout
    except Exception as e:
        print(f"❌ 获取项目 {project_name} 信息失败: {e}")
        return None

def check_project_exists(project_name, projects_output):
    """检查项目是否存在"""
    if projects_output and project_name in projects_output:
        print(f"✅ 项目 {project_name} 在CLI列表中存在")
        return True
    else:
        print(f"⚠️  项目 {project_name} 在CLI列表中不存在")
        return False

def check_local_config():
    """检查本地配置文件"""
    project_config = ".edgeone/project.json"
    if os.path.exists(project_config):
        try:
            with open(project_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("📁 本地项目配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return config
        except Exception as e:
            print(f"❌ 读取本地配置失败: {e}")
            return None
    else:
        print("❌ 本地项目配置文件不存在")
        return None

def try_create_project(project_name):
    """尝试创建项目"""
    try:
        print(f"🔄 尝试创建项目 {project_name}...")
        result = subprocess.run(["edgeone", "pages", "create", project_name], 
                              capture_output=True, text=True, check=True, timeout=60)
        print("✅ 项目创建成功")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 项目创建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    """主函数"""
    project_name = "sales-report-new"
    
    print("=" * 60)
    print("🔍 EdgeOne 项目检查工具")
    print("=" * 60)
    
    # 1. 检查CLI
    if not check_edgeone_cli():
        return
    
    # 2. 检查登录状态
    if not check_login_status():
        return
    
    print("\n" + "=" * 60)
    print("📋 项目状态检查")
    print("=" * 60)
    
    # 3. 检查本地配置
    local_config = check_local_config()
    
    # 4. 列出项目
    projects_output = list_projects()
    
    # 5. 检查项目是否存在
    project_exists = check_project_exists(project_name, projects_output)
    
    # 6. 如果项目存在，获取详细信息
    if project_exists:
        get_project_info(project_name)
    else:
        print(f"\n🔄 项目 {project_name} 在CLI中不存在，但可能在Web控制台存在")
        print("💡 这可能是CLI和Web控制台同步问题")
        
        # 7. 尝试创建项目
        print(f"\n🔄 是否尝试创建项目 {project_name}? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes', '是']:
                try_create_project(project_name)
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
    
    print("\n" + "=" * 60)
    print("📋 检查结果总结")
    print("=" * 60)
    
    if local_config:
        print(f"✅ 本地配置: 项目 {local_config.get('Name', 'N/A')}")
    
    if project_exists:
        print(f"✅ CLI项目: {project_name} 存在")
    else:
        print(f"⚠️  CLI项目: {project_name} 不存在")
        print("💡 建议:")
        print("   1. 检查Web控制台项目状态")
        print("   2. 等待CLI同步（可能需要几分钟）")
        print("   3. 尝试重新登录CLI")
        print("   4. 如果项目确实不存在，可以创建新项目")

if __name__ == "__main__":
    main() 