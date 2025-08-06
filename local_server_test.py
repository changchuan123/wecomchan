#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地服务器测试 - 销售报告系统
用于在CDN域名未生效时进行本地测试
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def end_headers(self):
        """添加CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def start_local_server(port=8000, directory="."):
    """启动本地HTTP服务器"""
    
    # 确保reports目录存在
    reports_dir = Path(directory) / "reports"
    if not reports_dir.exists():
        print(f"❌ 错误：reports目录不存在: {reports_dir}")
        return False
    
    # 检查是否有HTML文件
    html_files = list(reports_dir.glob("*.html"))
    if not html_files:
        print(f"❌ 错误：reports目录中没有HTML文件")
        return False
    
    print(f"📁 找到 {len(html_files)} 个HTML文件")
    
    # 切换到reports目录
    os.chdir(reports_dir)
    
    # 创建服务器
    handler = CustomHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 本地服务器已启动")
        print(f"📊 访问地址: http://localhost:{port}")
        print(f"📋 可用报告:")
        for html_file in html_files[:10]:  # 显示前10个文件
            print(f"   - http://localhost:{port}/{html_file.name}")
        if len(html_files) > 10:
            print(f"   ... 还有 {len(html_files) - 10} 个文件")
        print(f"\n💡 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 服务器已停止")
            return True
    
    return False

def main():
    """主函数"""
    print("=" * 60)
    print("🏠 销售报告系统 - 本地服务器测试")
    print("=" * 60)
    
    # 检查命令行参数
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ 错误：端口号必须是数字")
            return
    
    print(f"🔧 配置信息:")
    print(f"   - 端口: {port}")
    print(f"   - 工作目录: {os.getcwd()}")
    print()
    
    # 启动服务器
    success = start_local_server(port)
    
    if success:
        print("✅ 本地服务器测试完成")
    else:
        print("❌ 本地服务器启动失败")

if __name__ == "__main__":
    main() 