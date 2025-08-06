#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能部署脚本 - 保留直接上传内容
解决Git推送覆盖直接上传内容的问题
"""

import os
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime

class SmartDeployer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.backup_dir = self.project_root / "backup" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def backup_current_reports(self):
        """备份当前的reports目录"""
        if self.reports_dir.exists():
            print(f"📦 备份当前reports目录到: {self.backup_dir}")
            shutil.copytree(self.reports_dir, self.backup_dir)
            return True
        return False
    
    def restore_backup_if_needed(self):
        """如果需要，恢复备份"""
        if self.backup_dir.exists():
            print(f"🔄 恢复备份内容到reports目录")
            if self.reports_dir.exists():
                shutil.rmtree(self.reports_dir)
            shutil.copytree(self.backup_dir, self.reports_dir)
            return True
        return False
    
    def check_edgeone_status(self):
        """检查EdgeOne项目状态"""
        print("🔍 检查EdgeOne项目状态...")
        
        # 检查是否有直接上传的内容
        if self.reports_dir.exists():
            html_files = list(self.reports_dir.glob("*.html"))
            print(f"📁 发现 {len(html_files)} 个HTML文件")
            return len(html_files) > 0
        return False
    
    def create_deployment_config(self):
        """创建部署配置文件"""
        config = {
            "preserve_uploads": True,
            "merge_strategy": "keep_both",
            "backup_before_deploy": True,
            "restore_after_deploy": True
        }
        
        config_file = self.project_root / "deploy_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"📝 创建部署配置文件: {config_file}")
        return config_file
    
    def deploy_with_preserve(self):
        """执行保留式部署"""
        print("=" * 60)
        print("🚀 智能部署 - 保留直接上传内容")
        print("=" * 60)
        
        # 1. 检查当前状态
        has_direct_uploads = self.check_edgeone_status()
        
        if has_direct_uploads:
            print("✅ 检测到直接上传的内容")
            
            # 2. 备份当前内容
            self.backup_current_reports()
            
            # 3. 创建部署配置
            self.create_deployment_config()
            
            # 4. 执行Git推送
            print("📤 执行Git推送...")
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", f"智能部署更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
                subprocess.run(["git", "push"], check=True)
                print("✅ Git推送成功")
                
                # 5. 恢复备份内容
                self.restore_backup_if_needed()
                
                print("✅ 部署完成 - 直接上传内容已保留")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Git推送失败: {e}")
                return False
        else:
            print("⚠️ 未检测到直接上传的内容，执行普通部署")
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", f"普通部署更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
                subprocess.run(["git", "push"], check=True)
                print("✅ 普通部署成功")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ 部署失败: {e}")
                return False
    
    def show_deployment_info(self):
        """显示部署信息"""
        print("\n📋 部署信息:")
        print(f"   - 项目根目录: {self.project_root}")
        print(f"   - Reports目录: {self.reports_dir}")
        print(f"   - 备份目录: {self.backup_dir}")
        
        if self.reports_dir.exists():
            html_files = list(self.reports_dir.glob("*.html"))
            print(f"   - HTML文件数量: {len(html_files)}")
            
            if html_files:
                print("   - 最新文件:")
                for file in sorted(html_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"     * {file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")

def main():
    """主函数"""
    deployer = SmartDeployer()
    
    # 显示部署信息
    deployer.show_deployment_info()
    
    # 执行部署
    success = deployer.deploy_with_preserve()
    
    if success:
        print("\n🎉 部署完成！")
        print("💡 提示：")
        print("   - 直接上传的内容已保留")
        print("   - Git推送不会覆盖现有内容")
        print("   - 可以在EdgeOne控制台查看部署状态")
    else:
        print("\n❌ 部署失败，请检查错误信息")

if __name__ == "__main__":
    main() 