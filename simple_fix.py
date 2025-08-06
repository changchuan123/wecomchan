#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单修复测试脚本
"""

import os
import sys

def test_function_order():
    """测试函数定义顺序"""
    try:
        print("🧪 测试函数定义顺序...")
        
        # 导入主脚本
        sys.path.append('.')
        
        # 测试函数导入
        try:
            from 整体日报数据 import (
                create_gitignore,
                create_readme,
                create_index_html,
                configure_git_repository,
                deploy_to_edgeone
            )
            print("✅ 所有函数导入成功")
            
            # 测试函数调用
            print("\n测试函数调用...")
            
            # 测试create_gitignore
            try:
                result = create_gitignore()
                print(f"✅ create_gitignore: {result}")
            except Exception as e:
                print(f"❌ create_gitignore失败: {e}")
            
            # 测试create_readme
            try:
                result = create_readme()
                print(f"✅ create_readme: {result}")
            except Exception as e:
                print(f"❌ create_readme失败: {e}")
            
            # 测试configure_git_repository
            try:
                result = configure_git_repository()
                print(f"✅ configure_git_repository: {result}")
            except Exception as e:
                print(f"❌ configure_git_repository失败: {e}")
            
            print("\n✅ 函数定义顺序测试完成")
            return True
            
        except ImportError as e:
            print(f"❌ 函数导入失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_function_order()
    sys.exit(0 if success else 1) 