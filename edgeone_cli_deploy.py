#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EdgeOne CLI 直接部署脚本
直接部署到 sales-report-new 项目，不通过Git
"""

import os
import subprocess
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

class EdgeOneCLIDeployer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.project_name = "sales-report-new"
        
    def check_edgeone_cli(self):
        """检查EdgeOne CLI是否可用"""
        try:
            result = subprocess.run(["edgeone", "--version"], 
                                  capture_output=True, text=True, check=True)
            print("✅ EdgeOne CLI 已安装")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ EdgeOne CLI 未安装或不可用")
            return False
    
    def check_login_status(self):
        """检查登录状态"""
        try:
            result = subprocess.run(["edgeone", "whoami"], 
                                  capture_output=True, text=True, check=True)
            print("✅ EdgeOne CLI 已登录")
            return True
        except subprocess.CalledProcessError:
            print("❌ EdgeOne CLI 未登录，请先运行: edgeone login")
            return False
    
    def create_deployment_package(self):
        """创建部署包"""
        print("📦 创建部署包...")
        
        # 创建临时目录
        temp_dir = self.project_root / "temp_deploy"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        # 复制reports目录
        if self.reports_dir.exists():
            shutil.copytree(self.reports_dir, temp_dir / "reports")
            print(f"✅ 复制了 {len(list(self.reports_dir.glob('*.html')))} 个HTML文件")
        
        # 复制配置文件
        config_files = ["edgeone.json", "README.md"]
        for file in config_files:
            if (self.project_root / file).exists():
                shutil.copy2(self.project_root / file, temp_dir / file)
                print(f"✅ 复制配置文件: {file}")
        
        # 创建ZIP包
        zip_path = self.project_root / "deployment_package.zip"
        if zip_path.exists():
            zip_path.unlink()
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ 创建部署包: {zip_path}")
        return zip_path
    
    def deploy_with_cli(self, zip_path):
        """使用CLI部署"""
        print(f"🚀 使用EdgeOne CLI部署到项目: {self.project_name}")
        
        try:
            # 尝试直接部署ZIP包
            cmd = [
                "edgeone", "pages", "deploy", 
                str(zip_path), 
                "-n", self.project_name
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print("✅ CLI部署成功！")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ CLI部署失败: {e}")
            print(f"错误输出: {e.stderr}")
            
            # 尝试其他部署方式
            return self.try_alternative_deployment()
    
    def try_alternative_deployment(self):
        """尝试替代部署方式"""
        print("🔄 尝试替代部署方式...")
        
        try:
            # 方法1: 使用文件夹部署
            temp_dir = self.project_root / "temp_deploy"
            if temp_dir.exists():
                cmd = [
                    "edgeone", "pages", "deploy", 
                    str(temp_dir), 
                    "-n", self.project_name
                ]
                
                print(f"尝试文件夹部署: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                print("✅ 文件夹部署成功！")
                print(result.stdout)
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 文件夹部署也失败: {e}")
            
            # 方法2: 使用Git推送方式
            return self.try_git_deployment()
    
    def try_git_deployment(self):
        """尝试Git推送部署"""
        print("🔄 尝试Git推送部署...")
        
        try:
            # 确保Git配置正确
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"CLI部署更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
            subprocess.run(["git", "push"], check=True)
            
            print("✅ Git推送部署成功！")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git推送部署失败: {e}")
            return False
    
    def cleanup_deployment_files(self, zip_path):
        """清理部署文件"""
        # 清理ZIP包
        if zip_path.exists():
            zip_path.unlink()
            print("🧹 清理部署包")
        
        # 清理临时目录
        temp_dir = self.project_root / "temp_deploy"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("🧹 清理临时目录")
    
    def get_deployment_url(self):
        """获取部署URL"""
        base_url = f"https://{self.project_name}.pages.edgeone.com"
        return base_url
    
    def show_deployment_info(self):
        """显示部署信息"""
        print("\n📋 部署信息:")
        print(f"   - 项目名称: {self.project_name}")
        print(f"   - 项目根目录: {self.project_root}")
        print(f"   - Reports目录: {self.reports_dir}")
        
        if self.reports_dir.exists():
            html_files = list(self.reports_dir.glob("*.html"))
            print(f"   - HTML文件数量: {len(html_files)}")
            
            if html_files:
                print("   - 最新文件:")
                for file in sorted(html_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"     * {file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    def deploy(self):
        """执行完整部署流程"""
        print("=" * 60)
        print("🚀 EdgeOne CLI 直接部署 - sales-report-new")
        print("=" * 60)
        
        # 1. 检查CLI状态
        if not self.check_edgeone_cli():
            return False
        
        if not self.check_login_status():
            return False
        
        # 2. 显示部署信息
        self.show_deployment_info()
        
        # 3. 创建部署包
        zip_path = self.create_deployment_package()
        
        try:
            # 4. 执行部署
            success = self.deploy_with_cli(zip_path)
            
            if success:
                # 5. 显示部署结果
                deployment_url = self.get_deployment_url()
                print(f"\n🎉 部署完成！")
                print(f"📊 访问地址: {deployment_url}")
                print(f"📋 报告列表: {deployment_url}/reports/")
                print(f"💡 提示: 域名可能需要几分钟时间生效")
                
                # 6. 测试访问
                self.test_deployment_url(deployment_url)
                
                return True
            else:
                print("\n❌ 所有部署方式都失败了")
                return False
                
        finally:
            # 7. 清理文件
            self.cleanup_deployment_files(zip_path)
    
    def test_deployment_url(self, url):
        """测试部署URL是否可访问"""
        print(f"\n🔍 测试部署URL: {url}")
        
        try:
            import requests
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print("✅ 部署URL可访问")
            else:
                print(f"⚠️ 部署URL返回状态码: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 无法访问部署URL: {e}")
            print("💡 提示: 域名可能需要几分钟时间生效")

def main():
    """主函数"""
    deployer = EdgeOneCLIDeployer()
    
    success = deployer.deploy()
    
    if success:
        print("\n✅ EdgeOne CLI 直接部署完成！")
        print("💡 后续操作:")
        print("   - 等待域名生效（通常几分钟）")
        print("   - 在EdgeOne控制台查看部署状态")
        print("   - 使用CLI进行后续更新")
    else:
        print("\n❌ EdgeOne CLI 部署失败")
        print("💡 建议:")
        print("   - 检查EdgeOne CLI配置")
        print("   - 确认项目权限")
        print("   - 尝试手动在控制台部署")

if __name__ == "__main__":
    main() 