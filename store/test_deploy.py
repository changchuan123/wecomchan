#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试EdgeOne Pages部署
"""

import subprocess
import os
import time
import requests

def test_edgeone_deploy():
    """测试EdgeOne Pages部署"""
    print("🚀 开始测试EdgeOne Pages部署...")
    
    # 获取当前目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    
    # 创建测试HTML文件
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试页面</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>✅ EdgeOne Pages 部署测试成功</h1>
        <p>时间: """ + time.strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p>如果您能看到这个页面，说明部署配置正确！</p>
    </body>
    </html>
    """
    
    # 保存测试文件
    test_filename = "test_deploy.html"
    test_file_path = os.path.join(reports_dir, test_filename)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"📄 已创建测试文件: {test_file_path}")
    
    # 执行部署
    cmd = [
        "edgeone",
        "pages",
        "deploy",
        reports_dir,
        "-n", "sales-report-new"
    ]
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=script_dir
        )
        
        if result.returncode == 0:
            print("✅ 部署成功！")
            print(f"📤 部署输出: {result.stdout}")
            
            # 测试URL访问
            test_url = f"https://edge.haierht.cn/{test_filename}"
            print(f"🌐 测试URL: {test_url}")
            
            # 等待CDN同步
            print("⏳ 等待CDN同步...")
            time.sleep(10)
            
            # 验证URL
            try:
                response = requests.head(test_url, timeout=15)
                if response.status_code == 200:
                    print("✅ URL验证成功！")
                    print(f"📄 响应状态: {response.status_code}")
                    return True
                else:
                    print(f"⚠️ URL验证失败，状态码: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ URL验证异常: {e}")
                return False
        else:
            print("❌ 部署失败：")
            print(f"错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 部署异常: {e}")
        return False

if __name__ == "__main__":
    success = test_edgeone_deploy()
    if success:
        print("\n🎉 测试完成！部署配置正常。")
    else:
        print("\n❌ 测试失败！需要检查配置。") 