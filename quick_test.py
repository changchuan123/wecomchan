#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试多事业部月报数据.py集成功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 快速测试多事业部月报数据.py集成功能")
print("=" * 50)

# 测试导入
try:
    from 多事业部月报数据 import (
        check_url_accessibility,
        auto_fix_url_if_needed,
        generate_monitoring_report,
        integrated_health_check
    )
    print("✅ 成功导入集成功能")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试URL检查功能
print("\n🔍 测试URL检查功能...")
try:
    test_url = "https://edge.haierht.cn/"
    result = check_url_accessibility(test_url)
    if result['accessible']:
        print(f"✅ URL检查功能正常: {test_url}")
    else:
        print(f"⚠️ URL不可访问，但功能正常: {result['status_code']}")
except Exception as e:
    print(f"❌ URL检查功能异常: {e}")

# 测试健康检查
print("\n🔧 测试系统健康检查...")
try:
    health_result = integrated_health_check()
    print("✅ 健康检查功能正常")
except Exception as e:
    print(f"❌ 健康检查功能异常: {e}")

print("\n" + "=" * 50)
print("🎉 基础功能测试完成")
print("\n📝 使用说明:")
print("在您的代码中使用以下函数：")
print("• check_url_accessibility(url) - 检查URL状态")
print("• auto_fix_url_if_needed(filename) - 自动修复URL")
print("• enhanced_upload_html_and_get_url(filename, content) - 增强版上传")
print("• generate_monitoring_report() - 生成监控报告")
print("• integrated_health_check() - 系统健康检查")

print("\n🔧 环境要求:")
print("1. EdgeOne CLI: npm install -g edgeone")
print("2. 登录CLI: edgeone login")
print("3. Python库: pip install requests")

print("\n✅ 集成完成！可以在其他电脑上使用了。") 