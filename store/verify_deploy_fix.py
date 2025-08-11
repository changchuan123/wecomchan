#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证部署修复的关键点
"""

import os
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_deploy_fix():
    """验证部署修复的关键点"""
    try:
        logger.info("🔍 验证部署修复的关键点...")
        
        # 1. 检查路径计算
        script_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本目录（store）
        main_project_dir = os.path.dirname(script_dir)  # 主项目目录（wecomchan）
        reports_dir = os.path.join(main_project_dir, "reports")  # 主项目的reports目录
        
        logger.info(f"📁 脚本目录: {script_dir}")
        logger.info(f"📁 主项目目录: {main_project_dir}")
        logger.info(f"📁 reports目录: {reports_dir}")
        
        # 2. 检查reports目录是否存在
        if os.path.exists(reports_dir):
            logger.info("✅ reports目录存在")
        else:
            logger.warning("⚠️ reports目录不存在，将创建")
            os.makedirs(reports_dir, exist_ok=True)
        
        # 3. 检查EdgeOne CLI
        try:
            result = subprocess.run(["edgeone", "--version"], 
                              capture_output=True, text=True, check=True, timeout=10)
            logger.info("✅ EdgeOne CLI 可用")
            logger.info(f"📤 CLI版本: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"❌ EdgeOne CLI 不可用: {e}")
            return False
        
        # 4. 检查登录状态
        try:
            result = subprocess.run(["edgeone", "whoami"], 
                              capture_output=True, text=True, check=True, timeout=10)
            logger.info("✅ EdgeOne CLI 已登录")
            logger.info(f"📤 用户信息: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"❌ EdgeOne CLI 未登录: {e}")
            return False
        
        # 5. 检查项目配置
        project_name = "sales-report-new"
        domain = "edge.haierht.cn"
        
        logger.info(f"📋 项目名称: {project_name}")
        logger.info(f"🌐 域名: {domain}")
        
        # 6. 测试部署命令（不实际执行）
        test_cmd = [
            "edgeone", "pages", "deploy", 
            reports_dir,  # 使用绝对路径
            "-n", project_name
        ]
        
        logger.info(f"📤 测试部署命令: {' '.join(test_cmd)}")
        logger.info(f"📁 工作目录: {main_project_dir}")
        
        # 7. 检查reports目录内容
        if os.path.exists(reports_dir):
            files = os.listdir(reports_dir)
            logger.info(f"📄 reports目录文件: {files}")
        
        logger.info("✅ 部署修复验证完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = verify_deploy_fix()
    if success:
        logger.info("\n🎉 验证完成！部署修复配置正确。")
    else:
        logger.error("\n❌ 验证失败！需要检查配置。") 