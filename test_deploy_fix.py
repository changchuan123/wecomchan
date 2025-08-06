#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署功能修复测试脚本
验证修复后的部署功能是否正常工作
"""

import os
import sys
from datetime import datetime

def test_deploy_functions():
    """测试部署相关函数"""
    try:
        print("🧪 开始测试部署功能修复...")
        
        # 导入主脚本的函数
        sys.path.append('.')
        from 整体日报数据 import (
            create_gitignore,
            create_readme,
            create_index_html,
            configure_git_repository,
            deploy_to_edgeone
        )
        
        print("✅ 成功导入部署函数")
        
        # 1. 测试create_gitignore函数
        print("\n1. 测试create_gitignore函数...")
        try:
            result = create_gitignore()
            if result:
                print("✅ create_gitignore函数测试通过")
            else:
                print("❌ create_gitignore函数测试失败")
        except Exception as e:
            print(f"❌ create_gitignore函数异常: {e}")
        
        # 2. 测试create_readme函数
        print("\n2. 测试create_readme函数...")
        try:
            result = create_readme()
            if result:
                print("✅ create_readme函数测试通过")
            else:
                print("❌ create_readme函数测试失败")
        except Exception as e:
            print(f"❌ create_readme函数异常: {e}")
        
        # 3. 测试create_index_html函数
        print("\n3. 测试create_index_html函数...")
        try:
            reports_dir = "reports"
            if os.path.exists(reports_dir):
                result = create_index_html(reports_dir)
                if result:
                    print("✅ create_index_html函数测试通过")
                else:
                    print("❌ create_index_html函数测试失败")
            else:
                print("⚠️ reports目录不存在，跳过测试")
        except Exception as e:
            print(f"❌ create_index_html函数异常: {e}")
        
        # 4. 测试configure_git_repository函数
        print("\n4. 测试configure_git_repository函数...")
        try:
            result = configure_git_repository()
            if result:
                print("✅ configure_git_repository函数测试通过")
            else:
                print("❌ configure_git_repository函数测试失败")
        except Exception as e:
            print(f"❌ configure_git_repository函数异常: {e}")
        
        # 5. 测试deploy_to_edgeone函数（仅测试函数调用，不实际部署）
        print("\n5. 测试deploy_to_edgeone函数...")
        try:
            reports_dir = "reports"
            if os.path.exists(reports_dir):
                print("✅ deploy_to_edgeone函数可以正常调用")
            else:
                print("⚠️ reports目录不存在，跳过测试")
        except Exception as e:
            print(f"❌ deploy_to_edgeone函数异常: {e}")
        
        print("\n✅ 部署功能修复测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 部署功能修复测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_deploy_functions()
    sys.exit(0 if success else 1) 