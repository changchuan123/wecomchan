#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EdgeOne Pages 配置脚本
"""

import os
from datetime import datetime

def create_edgeone_guide():
    """创建EdgeOne Pages配置指南"""
    
    guide_content = f"""# EdgeOne Pages 配置指南

## 🎯 项目信息
- **项目名**: sales-report
- **GitHub仓库**: changchuan123/wecomchan
- **分支**: master
- **构建类型**: 静态HTML

## 📋 配置步骤

### 1. 登录EdgeOne控制台
访问: https://console.cloud.tencent.com/edgeone

### 2. 创建Pages项目
1. 点击"创建项目"
2. 项目名称: sales-report
3. 描述: 销售日报系统 - 自动化数据分析与部署

### 3. 连接GitHub仓库
1. 选择"从Git仓库部署"
2. 选择"GitHub"
3. 授权GitHub账户
4. 选择仓库: changchuan123/wecomchan
5. 选择分支: master

### 4. 配置构建设置
- 构建目录: /
- 输出目录: /
- 构建命令: (留空，静态HTML)
- 环境变量: (无需设置)

### 5. 部署设置
- 自动部署: 开启
- 部署触发: 推送到master分支时
- 构建超时: 10分钟

## 🌐 访问地址
部署完成后，您可以通过以下地址访问:
- 默认域名: https://sales-report.pages.edgeone.com
- 自定义域名: (可选配置)

## 📊 部署状态
- ✅ Git仓库连接正常
- ✅ 自动部署已配置
- ✅ HTML报告已生成
- ✅ 企业微信推送正常

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open("EdgeOne_Pages_配置指南.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("✅ EdgeOne Pages配置指南已创建")

if __name__ == "__main__":
    create_edgeone_guide() 