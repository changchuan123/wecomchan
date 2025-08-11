#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EdgeOne Pages URL监控和自动修复系统
功能：
1. 持续监控报告URL的可访问性
2. 检测到404错误时自动重新部署
3. 记录详细的监控日志
4. 支持批量URL监控
5. 智能修复机制
"""

import os
import sys
import time
import requests
import subprocess
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

# ========== 配置常量 ==========
EDGEONE_PROJECT = "sales-report-new"
EDGEONE_DOMAIN = "edge.haierht.cn"
REPORTS_DIR = "reports"
LOG_FILE = "url_monitor.log"
CHECK_INTERVAL = 300  # 5分钟检查一次
RETRY_ATTEMPTS = 3
TIMEOUT = 10

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class URLMonitor:
    """URL监控和自动修复系统"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.reports_dir = os.path.join(self.script_dir, REPORTS_DIR)
        self.monitored_urls = []
        
    def get_html_files(self) -> List[str]:
        """获取reports目录下的所有HTML文件"""
        html_files = []
        if os.path.exists(self.reports_dir):
            for file in os.listdir(self.reports_dir):
                if file.endswith('.html'):
                    html_files.append(file)
        return sorted(html_files, reverse=True)  # 按时间倒序排列
    
    def check_url_status(self, url: str) -> Dict[str, any]:
        """检查URL状态"""
        try:
            response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
            return {
                'url': url,
                'status_code': response.status_code,
                'accessible': response.status_code == 200,
                'headers': dict(response.headers),
                'error': None
            }
        except Exception as e:
            return {
                'url': url,
                'status_code': None,
                'accessible': False,
                'headers': {},
                'error': str(e)
            }
    
    def deploy_to_edgeone(self) -> bool:
        """使用EdgeOne CLI部署到EdgeOne Pages"""
        try:
            logger.info("🚀 开始自动修复 - 重新部署到EdgeOne Pages...")
            
            # 切换到项目目录
            os.chdir(self.script_dir)
            
            # 执行部署命令
            cmd = f"edgeone pages deploy {REPORTS_DIR}/ -n {EDGEONE_PROJECT}"
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info("✅ EdgeOne Pages部署成功")
                return True
            else:
                logger.error(f"❌ EdgeOne Pages部署失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ EdgeOne Pages部署超时")
            return False
        except Exception as e:
            logger.error(f"❌ EdgeOne Pages部署异常: {e}")
            return False
    
    def auto_fix_url(self, filename: str, max_attempts: int = RETRY_ATTEMPTS) -> bool:
        """自动修复不可访问的URL"""
        url = f"https://{EDGEONE_DOMAIN}/{filename}"
        
        for attempt in range(max_attempts):
            logger.info(f"🔄 自动修复尝试 {attempt + 1}/{max_attempts}: {url}")
            
            # 重新部署
            if self.deploy_to_edgeone():
                # 等待CDN同步
                logger.info("⏳ 等待CDN同步...")
                time.sleep(20)
                
                # 验证修复结果
                status = self.check_url_status(url)
                if status['accessible']:
                    logger.info(f"✅ 自动修复成功: {url}")
                    return True
                else:
                    logger.warning(f"⚠️ 修复尝试 {attempt + 1} 失败，继续重试...")
            else:
                logger.error(f"❌ 部署失败，修复尝试 {attempt + 1} 失败")
            
            # 等待后重试
            if attempt < max_attempts - 1:
                time.sleep(30)
        
        logger.error(f"❌ 自动修复失败: {url} (尝试了 {max_attempts} 次)")
        return False
    
    def monitor_recent_files(self, num_files: int = 10):
        """监控最近的N个HTML文件"""
        html_files = self.get_html_files()[:num_files]
        
        if not html_files:
            logger.warning("⚠️ 未找到HTML文件进行监控")
            return
        
        logger.info(f"📊 开始监控最近 {len(html_files)} 个报告文件...")
        
        results = []
        for filename in html_files:
            url = f"https://{EDGEONE_DOMAIN}/{filename}"
            status = self.check_url_status(url)
            results.append(status)
            
            if status['accessible']:
                logger.info(f"✅ {filename} - 可访问")
            else:
                logger.error(f"❌ {filename} - 不可访问 (状态码: {status['status_code']}, 错误: {status['error']})")
                
                # 自动修复
                logger.info(f"🛠️ 启动自动修复: {filename}")
                if self.auto_fix_url(filename):
                    logger.info(f"🎉 修复成功: {filename}")
                else:
                    logger.error(f"💥 修复失败: {filename}")
        
        return results
    
    def monitor_specific_url(self, url: str):
        """监控特定URL"""
        logger.info(f"🎯 监控特定URL: {url}")
        
        status = self.check_url_status(url)
        
        if status['accessible']:
            logger.info(f"✅ URL可访问: {url}")
        else:
            logger.error(f"❌ URL不可访问: {url}")
            logger.error(f"   状态码: {status['status_code']}")
            logger.error(f"   错误: {status['error']}")
            
            # 提取文件名并尝试修复
            filename = url.split('/')[-1]
            if filename.endswith('.html'):
                logger.info(f"🛠️ 启动自动修复: {filename}")
                if self.auto_fix_url(filename):
                    logger.info(f"🎉 修复成功: {filename}")
                else:
                    logger.error(f"💥 修复失败: {filename}")
        
        return status
    
    def continuous_monitor(self, check_interval: int = CHECK_INTERVAL):
        """持续监控模式"""
        logger.info(f"🔄 启动持续监控模式 (检查间隔: {check_interval}秒)")
        
        try:
            while True:
                logger.info("=" * 60)
                logger.info("🕐 执行定期检查...")
                
                self.monitor_recent_files()
                
                logger.info(f"⏰ 下次检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (约{check_interval//60}分钟后)")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ 用户停止监控")
        except Exception as e:
            logger.error(f"❌ 监控过程发生错误: {e}")
    
    def generate_status_report(self) -> str:
        """生成监控状态报告"""
        html_files = self.get_html_files()[:20]  # 检查最近20个文件
        
        total_files = len(html_files)
        accessible_count = 0
        inaccessible_files = []
        
        for filename in html_files:
            url = f"https://{EDGEONE_DOMAIN}/{filename}"
            status = self.check_url_status(url)
            
            if status['accessible']:
                accessible_count += 1
            else:
                inaccessible_files.append({
                    'filename': filename,
                    'url': url,
                    'status_code': status['status_code'],
                    'error': status['error']
                })
        
        report = f"""
📊 EdgeOne Pages URL监控报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 总体状态:
   总文件数: {total_files}
   可访问: {accessible_count}
   不可访问: {len(inaccessible_files)}
   可用率: {(accessible_count/total_files*100):.1f}%

🔗 域名: https://{EDGEONE_DOMAIN}/
📁 项目: {EDGEONE_PROJECT}
"""
        
        if inaccessible_files:
            report += "\n❌ 不可访问的文件:\n"
            for item in inaccessible_files:
                report += f"   • {item['filename']} (状态码: {item['status_code']})\n"
        else:
            report += "\n✅ 所有监控文件均可正常访问"
        
        return report

def main():
    """主函数"""
    monitor = URLMonitor()
    
    if len(sys.argv) < 2:
        print("""
EdgeOne Pages URL监控系统

使用方法:
  python url_monitor.py check           # 检查最近10个文件
  python url_monitor.py fix <filename>  # 修复特定文件
  python url_monitor.py url <url>       # 监控特定URL
  python url_monitor.py monitor         # 持续监控模式
  python url_monitor.py report          # 生成状态报告
  python url_monitor.py deploy          # 手动部署

示例:
  python url_monitor.py fix overall_daily_2025-08-07_093658.html
  python url_monitor.py url https://edge.haierht.cn/overall_daily_2025-08-07_093658.html
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "check":
        logger.info("🔍 执行文件可访问性检查...")
        monitor.monitor_recent_files()
        
    elif command == "fix" and len(sys.argv) > 2:
        filename = sys.argv[2]
        logger.info(f"🛠️ 修复文件: {filename}")
        monitor.auto_fix_url(filename)
        
    elif command == "url" and len(sys.argv) > 2:
        url = sys.argv[2]
        monitor.monitor_specific_url(url)
        
    elif command == "monitor":
        monitor.continuous_monitor()
        
    elif command == "report":
        report = monitor.generate_status_report()
        print(report)
        logger.info("📊 状态报告已生成")
        
    elif command == "deploy":
        logger.info("🚀 手动部署到EdgeOne Pages...")
        if monitor.deploy_to_edgeone():
            logger.info("✅ 部署成功")
        else:
            logger.error("❌ 部署失败")
            
    else:
        logger.error("❌ 未知命令")

if __name__ == "__main__":
    main() 