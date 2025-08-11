#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多事业部月报数据.py中集成的监控和修复功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入多事业部月报数据.py中的集成功能
try:
    from 多事业部月报数据 import (
        check_url_accessibility,
        auto_fix_url_if_needed,
        enhanced_upload_html_and_get_url,
        generate_monitoring_report,
        integrated_health_check,
        main_with_integrated_monitoring
    )
    print("✅ 成功导入集成功能")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保多事业部月报数据.py文件存在且包含集成功能")
    sys.exit(1)

def test_url_check():
    """测试URL检查功能"""
    print("\n🔍 测试URL检查功能...")
    
    # 测试一个已知的URL
    test_url = "https://edge.haierht.cn/"
    result = check_url_accessibility(test_url)
    
    print(f"URL: {result['url']}")
    print(f"状态码: {result['status_code']}")
    print(f"可访问: {result['accessible']}")
    if result['error']:
        print(f"错误: {result['error']}")
    
    return result['accessible']

def test_health_check():
    """测试系统健康检查"""
    print("\n🔧 测试系统健康检查...")
    return integrated_health_check()

def test_monitoring_report():
    """测试监控报告生成"""
    print("\n📊 测试监控报告生成...")
    return generate_monitoring_report()

def test_html_upload():
    """测试HTML上传功能"""
    print("\n🌐 测试HTML上传功能...")
    
    # 创建测试HTML内容
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>集成功能测试</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>🧪 集成功能测试页面</h1>
        <p>这是一个测试页面，用于验证集成的URL监控和修复功能。</p>
        <p>生成时间: {datetime}</p>
        <div style="background: #f0f0f0; padding: 20px; margin: 20px 0;">
            <h2>功能列表:</h2>
            <ul>
                <li>✅ 自动URL检查和修复</li>
                <li>✅ 增强版HTML上传</li>
                <li>✅ URL监控报告</li>
                <li>✅ 系统健康检查</li>
                <li>✅ 集成主函数</li>
            </ul>
        </div>
        <p>如果您能看到这个页面，说明集成功能正常工作！</p>
    </body>
    </html>
    """.format(datetime=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 生成测试文件名
    import time
    filename = f"integration_test_{int(time.time())}.html"
    
    try:
        # 使用集成的上传函数
        url = enhanced_upload_html_and_get_url(filename, test_html)
        
        if url:
            print(f"✅ 测试页面已生成: {url}")
            
            # 验证URL可访问性
            print("🔍 验证URL可访问性...")
            check_result = check_url_accessibility(url)
            if check_result['accessible']:
                print("✅ URL验证成功，集成功能正常工作！")
            else:
                print(f"❌ URL验证失败: {check_result['error']}")
        else:
            print("❌ HTML上传失败")
        
        return url
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("🧪 开始测试多事业部月报数据.py集成功能")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 测试URL检查
    try:
        test_results['url_check'] = test_url_check()
    except Exception as e:
        print(f"❌ URL检查测试失败: {e}")
        test_results['url_check'] = False
    
    # 2. 测试健康检查
    try:
        health_result = test_health_check()
        test_results['health_check'] = health_result is not None
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
        test_results['health_check'] = False
    
    # 3. 测试监控报告
    try:
        monitoring_result = test_monitoring_report()
        test_results['monitoring_report'] = monitoring_result is not None
    except Exception as e:
        print(f"❌ 监控报告测试失败: {e}")
        test_results['monitoring_report'] = False
    
    # 4. 测试HTML上传（可选，需要EdgeOne CLI配置）
    print("\n❓ 是否测试HTML上传功能？(需要EdgeOne CLI已配置)")
    print("输入 'y' 或 'yes' 进行测试，其他键跳过:")
    user_input = input().strip().lower()
    
    if user_input in ['y', 'yes']:
        try:
            test_url = test_html_upload()
            test_results['html_upload'] = test_url is not None
        except Exception as e:
            print(f"❌ HTML上传测试失败: {e}")
            test_results['html_upload'] = False
    else:
        print("⏩ 跳过HTML上传测试")
        test_results['html_upload'] = None
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果报告")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⏩ 跳过"
        
        test_display_name = {
            'url_check': 'URL检查功能',
            'health_check': '系统健康检查',
            'monitoring_report': '监控报告生成',
            'html_upload': 'HTML上传功能'
        }.get(test_name, test_name)
        
        print(f"{test_display_name}: {status}")
    
    # 总结
    passed_tests = sum(1 for result in test_results.values() if result is True)
    total_tests = sum(1 for result in test_results.values() if result is not None)
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 测试通过率: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    else:
        print(f"\n⚠️ 没有执行任何测试")
    
    if passed_tests == total_tests and total_tests > 0:
        print("\n🎉 所有测试通过！集成功能正常工作。")
        print("💡 您可以在其他电脑上使用 多事业部月报数据.py 脚本了。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和环境。")
    
    print("\n🔧 环境要求提醒:")
    print("1. Python 3.6+")
    print("2. requests库: pip install requests")
    print("3. EdgeOne CLI: npm install -g edgeone")
    print("4. EdgeOne CLI登录: edgeone login")
    
    print("\n📖 使用方法:")
    print("在您的代码中替换:")
    print("  url = upload_html_and_get_url(filename, html_content)")
    print("为:")
    print("  url = enhanced_upload_html_and_get_url(filename, html_content)")

if __name__ == "__main__":
    main() 