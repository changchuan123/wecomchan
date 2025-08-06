#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Git部署测试脚本
"""

import os
import subprocess
import sys

def test_git_deploy():
    """测试Git部署功能"""
    try:
        print("🧪 测试Git部署功能...")
        
        # 导入主脚本的Git函数
        sys.path.append('.')
        from 整体日报数据 import create_gitignore, create_readme, configure_git_repository
        
        print("\n1. 测试create_gitignore函数...")
        result = create_gitignore()
        print(f"✅ create_gitignore: {result}")
        
        print("\n2. 测试create_readme函数...")
        result = create_readme()
        print(f"✅ create_readme: {result}")
        
        print("\n3. 测试configure_git_repository函数...")
        result = configure_git_repository()
        print(f"✅ configure_git_repository: {result}")
        
        print("\n✅ Git部署功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Git部署测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_git_deploy()
    sys.exit(0 if success else 1) 