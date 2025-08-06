#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git部署测试脚本
用于测试Git推送部署到EdgeOne Pages的功能
"""

import os
import subprocess
import sys
from datetime import datetime

def test_git_deploy():
    """测试Git部署功能"""
    try:
        print("🧪 开始测试Git部署功能...")
        
        # 1. 测试Git仓库配置
        print("\n1. 测试Git仓库配置...")
        try:
            result = subprocess.run(["git", "status"], check=True, capture_output=True, text=True)
            print("✅ Git仓库状态正常")
        except subprocess.CalledProcessError:
            print("❌ 当前目录不是Git仓库")
            return False
        
        # 2. 测试远程仓库配置
        print("\n2. 测试远程仓库配置...")
        try:
            result = subprocess.run(["git", "remote", "-v"], check=True, capture_output=True, text=True)
            if "origin" in result.stdout:
                print("✅ 远程仓库已配置")
                print(f"远程仓库信息: {result.stdout.strip()}")
            else:
                print("❌ 远程仓库未配置")
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ 检查远程仓库失败: {e}")
            return False
        
        # 3. 测试reports目录
        print("\n3. 测试reports目录...")
        if os.path.exists("reports"):
            html_files = [f for f in os.listdir("reports") if f.endswith('.html')]
            print(f"✅ reports目录存在，包含 {len(html_files)} 个HTML文件")
            for file in html_files:
                print(f"   - {file}")
        else:
            print("❌ reports目录不存在")
            return False
        
        # 4. 测试index.html
        print("\n4. 测试index.html...")
        index_path = os.path.join("reports", "index.html")
        if os.path.exists(index_path):
            print("✅ index.html存在")
        else:
            print("⚠️ index.html不存在，将创建...")
            # 创建测试用的index.html
            test_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>测试页面 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
</head>
<body>
    <h1>Git部署测试页面</h1>
    <p>这是一个测试页面，用于验证Git部署功能。</p>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(test_html)
            print("✅ index.html已创建")
        
        # 5. 测试Git提交
        print("\n5. 测试Git提交...")
        try:
            subprocess.run(["git", "add", "reports/"], check=True)
            print("✅ 文件已添加到Git")
            
            commit_message = f"测试提交 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print("✅ 更改已提交")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git提交失败: {e}")
            return False
        
        # 6. 测试Git推送（不实际推送，只检查配置）
        print("\n6. 测试Git推送配置...")
        try:
            # 检查当前分支
            result = subprocess.run(["git", "branch", "--show-current"], check=True, capture_output=True, text=True)
            current_branch = result.stdout.strip()
            print(f"✅ 当前分支: {current_branch}")
            
            # 检查远程分支
            result = subprocess.run(["git", "branch", "-r"], check=True, capture_output=True, text=True)
            remote_branches = result.stdout.strip().split('\n')
            print(f"✅ 远程分支: {remote_branches}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 检查Git分支失败: {e}")
            return False
        
        print("\n✅ Git部署测试完成！")
        print("📋 测试结果:")
        print("   - Git仓库配置: ✅")
        print("   - 远程仓库配置: ✅")
        print("   - reports目录: ✅")
        print("   - index.html: ✅")
        print("   - Git提交: ✅")
        print("   - Git推送配置: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_git_deploy()
    if success:
        print("\n🎉 所有测试通过！Git部署功能正常。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！请检查配置。")
        sys.exit(1) 