#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查EdgeOne Pages的配置和URL有效期
"""

import subprocess
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# EdgeOne配置
EDGEONE_CONFIG = {
    'cli_path': "/Users/weixiaogang/.npm-global/bin/edgeone",
    'token': "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=",
    'project_name': "sales-report",
    'domain': "edge.haierht.cn"
}

def check_edgeone_config():
    """检查EdgeOne Pages配置"""
    try:
        logger.info("🔧 检查EdgeOne Pages配置...")
        
        # 检查CLI是否存在
        cli_path = EDGEONE_CONFIG['cli_path']
        if subprocess.run(['which', cli_path], capture_output=True).returncode == 0:
            logger.info(f"✅ EdgeOne CLI存在: {cli_path}")
        else:
            logger.warning(f"❌ EdgeOne CLI不存在: {cli_path}")
            # 尝试使用环境变量
            cli_path = "edgeone"
            logger.info(f"🔧 尝试使用环境变量: {cli_path}")
        
        # 检查项目状态
        project_name = EDGEONE_CONFIG['project_name']
        token = EDGEONE_CONFIG['token']
        
        cmd = [
            cli_path,
            "pages",
            "list",
            "-t", token
        ]
        
        logger.info(f"📋 执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✅ EdgeOne CLI连接成功")
            logger.info(f"📤 输出: {result.stdout}")
        else:
            logger.error(f"❌ EdgeOne CLI连接失败: {result.stderr}")
            return
        
        # 检查特定项目
        cmd_describe = [
            cli_path,
            "pages",
            "describe",
            "-n", project_name,
            "-t", token
        ]
        
        logger.info(f"📋 检查项目: {' '.join(cmd_describe)}")
        
        result_describe = subprocess.run(
            cmd_describe,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result_describe.returncode == 0:
            logger.info("✅ 项目信息获取成功")
            logger.info(f"📤 项目信息: {result_describe.stdout}")
        else:
            logger.error(f"❌ 项目信息获取失败: {result_describe.stderr}")
        
        # 检查域名配置
        domain = EDGEONE_CONFIG['domain']
        logger.info(f"🌐 检查域名: {domain}")
        
        # 测试域名访问
        import requests
        try:
            response = requests.get(f"https://{domain}", timeout=10)
            logger.info(f"✅ 域名可访问: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 域名访问失败: {e}")
        
        logger.info("✅ EdgeOne Pages配置检查完成")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")

def check_url_permanence():
    """检查URL永久性"""
    try:
        logger.info("🔗 检查URL永久性...")
        
        # 测试几个不同的报告URL
        test_urls = [
            "https://edge.haierht.cn/inventory_analysis_20250806_132805.html",
            "https://edge.haierht.cn/inventory_analysis_20250806_110142.html",
            "https://edge.haierht.cn/inventory_analysis_20250806_102940.html"
        ]
        
        import requests
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {url} - 可访问")
                    # 检查内容长度
                    content_length = len(response.content)
                    logger.info(f"   📄 内容大小: {content_length:,} 字节")
                else:
                    logger.warning(f"⚠️ {url} - 状态码: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ {url} - 访问失败: {e}")
        
        logger.info("✅ URL永久性检查完成")
        
    except Exception as e:
        logger.error(f"❌ URL检查失败: {e}")

if __name__ == "__main__":
    check_edgeone_config()
    check_url_permanence() 