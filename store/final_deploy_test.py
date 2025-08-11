#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终部署测试 - 验证修复后的部署功能完全正常
"""

import os
import time
import requests
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# EdgeOne Pages 配置
EDGEONE_PROJECT = "sales-report-new"
EDGEONE_DOMAIN = "edge.haierht.cn"
EDGEONE_CLI_PATH = "edgeone"
EDGEONE_CLI_PATH_ALT = "edgeone"

def final_deploy_test():
    """最终部署测试"""
    try:
        logger.info("🚀 开始最终部署测试...")
        
        # 获取主项目的reports目录路径
        script_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本目录（store）
        main_project_dir = os.path.dirname(script_dir)  # 主项目目录（wecomchan）
        reports_dir = os.path.join(main_project_dir, "reports")  # 主项目的reports目录
        
        # 确保reports目录存在
        os.makedirs(reports_dir, exist_ok=True)
        logger.info(f"📁 确保reports目录存在: {reports_dir}")
        
        # 创建最终测试HTML文件
        test_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>最终部署测试 - 修复成功</title>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif; 
                    margin: 40px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                .success {{ 
                    color: #4CAF50; 
                    font-weight: bold; 
                    font-size: 24px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .info {{ 
                    color: #2196F3; 
                    font-size: 16px;
                    margin: 10px 0;
                }}
                .fix-item {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    border-left: 4px solid #4CAF50;
                }}
                .timestamp {{
                    text-align: center;
                    font-style: italic;
                    margin-top: 30px;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">🎉 EdgeOne Pages 部署修复成功！</h1>
                <p class="info">如果您能看到这个页面，说明部署问题已彻底解决！</p>
                
                <h2>✅ 修复内容：</h2>
                <div class="fix-item">
                    <strong>1. 路径问题修复</strong><br>
                    使用绝对路径部署，确保在正确的工作目录下执行CLI命令
                </div>
                <div class="fix-item">
                    <strong>2. 项目名称统一</strong><br>
                    统一使用项目名称：sales-report-new
                </div>
                <div class="fix-item">
                    <strong>3. 跨平台兼容</strong><br>
                    支持Mac和Windows系统，自动检测操作系统
                </div>
                <div class="fix-item">
                    <strong>4. 错误处理改进</strong><br>
                    完善的错误处理和重试机制
                </div>
                <div class="fix-item">
                    <strong>5. URL验证优化</strong><br>
                    智能URL验证，支持CDN同步等待
                </div>
                
                <h2>🔧 技术细节：</h2>
                <ul>
                    <li>脚本目录: {script_dir}</li>
                    <li>主项目目录: {main_project_dir}</li>
                    <li>reports目录: {reports_dir}</li>
                    <li>项目名称: {EDGEONE_PROJECT}</li>
                    <li>域名: {EDGEONE_DOMAIN}</li>
                </ul>
                
                <div class="timestamp">
                    📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # 保存测试文件
        test_filename = "final_deploy_test.html"
        test_file_path = os.path.join(reports_dir, test_filename)
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_html)
        
        logger.info(f"📄 已创建测试文件: {test_file_path}")
        
        # 检测操作系统
        import platform
        is_windows = platform.system() == "Windows"
        
        # 根据操作系统确定EdgeOne CLI路径
        if is_windows:
            edgeone_cmd = EDGEONE_CLI_PATH
            edgeone_cmd_alt = EDGEONE_CLI_PATH_ALT
        else:
            edgeone_cmd = EDGEONE_CLI_PATH
            edgeone_cmd_alt = EDGEONE_CLI_PATH_ALT
        
        # 检查EdgeOne CLI是否可用
        def check_edgeone_cli():
            try:
                # 尝试主路径
                try:
                    result = subprocess.run([edgeone_cmd, "--version"], 
                                      capture_output=True, text=True, check=True, timeout=10)
                    logger.info(f"✅ EdgeOne CLI 已安装: {edgeone_cmd}")
                    return edgeone_cmd
                except:
                    # 尝试备用路径
                    try:
                        result = subprocess.run([edgeone_cmd_alt, "--version"], 
                                          capture_output=True, text=True, check=True, timeout=10)
                        logger.info(f"✅ EdgeOne CLI 已安装 (备用路径): {edgeone_cmd_alt}")
                        return edgeone_cmd_alt
                    except:
                        pass
                
                logger.error("❌ EdgeOne CLI 不可用")
                return None
            except Exception as e:
                logger.error(f"❌ EdgeOne CLI 检查失败: {e}")
                return None
        
        # 检查登录状态
        def check_edgeone_login(edgeone_path):
            try:
                result = subprocess.run([edgeone_path, "whoami"], 
                                  capture_output=True, text=True, check=True, timeout=10)
                logger.info("✅ EdgeOne CLI 已登录")
                return True
            except Exception as e:
                logger.error(f"❌ EdgeOne CLI 未登录: {e}")
                return False
        
        # 执行CLI部署 - 使用修复后的逻辑
        def execute_cli_deploy(edgeone_path):
            try:
                # 使用绝对路径，在主项目目录下执行
                cmd = [
                    edgeone_path, "pages", "deploy", 
                    reports_dir,  # 使用绝对路径
                    "-n", EDGEONE_PROJECT
                ]
                
                logger.info(f"📤 执行CLI部署命令: {' '.join(cmd)}")
                logger.info(f"📁 工作目录: {main_project_dir}")
                
                # 在主项目目录下执行部署命令
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300,
                    cwd=main_project_dir  # 确保在正确的工作目录下执行
                )
                
                logger.info("✅ EdgeOne CLI 部署成功！")
                logger.info(f"📤 部署输出: {result.stdout}")
                
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ EdgeOne CLI 部署失败: {e}")
                logger.error(f"错误输出: {e.stderr}")
                return False
            except Exception as e:
                logger.error(f"❌ EdgeOne CLI 部署异常: {e}")
                return False
        
        # 主部署流程
        logger.info("🔍 检查EdgeOne CLI...")
        edgeone_path = check_edgeone_cli()
        
        if not edgeone_path:
            logger.error("❌ EdgeOne CLI 不可用，请先安装")
            return False
        
        logger.info("🔍 检查登录状态...")
        if not check_edgeone_login(edgeone_path):
            logger.error("❌ EdgeOne CLI 未登录，请先运行登录命令")
            logger.info(f"💡 登录命令: {edgeone_path} login")
            return False
        
        logger.info("🚀 开始CLI部署...")
        if execute_cli_deploy(edgeone_path):
            logger.info("✅ EdgeOne CLI 部署完成！")
            
            # 等待CDN同步
            logger.info("⏳ 等待CDN同步...")
            time.sleep(15)  # 等待15秒让CDN同步
            
            # 测试URL访问
            test_url = f"https://{EDGEONE_DOMAIN}/{test_filename}"
            logger.info(f"🌐 测试URL: {test_url}")
            
            # 验证URL
            try:
                response = requests.head(test_url, timeout=15)
                if response.status_code == 200:
                    logger.info("✅ URL验证成功！")
                    logger.info(f"📄 响应状态: {response.status_code}")
                    logger.info(f"🌐 访问地址: {test_url}")
                    return True
                else:
                    logger.warning(f"⚠️ URL验证失败，状态码: {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"❌ URL验证异常: {e}")
                return False
        else:
            logger.error("❌ EdgeOne CLI 部署失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = final_deploy_test()
    if success:
        logger.info("\n🎉 最终测试完成！部署修复完全成功。")
        logger.info("✅ 所有问题已彻底解决！")
    else:
        logger.error("\n❌ 最终测试失败！需要进一步检查配置。") 