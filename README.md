# 销售日报系统

## 项目简介
这是一个自动化的销售日报分析系统，通过Git推送方式部署到EdgeOne Pages。

## 功能特性
- 📊 自动分析销售数据
- 📈 生成详细的HTML报告
- 🚀 自动部署到EdgeOne Pages
- 📱 企业微信推送通知

## 部署方式
本项目使用Git推送方式自动部署到EdgeOne Pages。

### 配置要求
- Git远程仓库: https://github.com/weixiaogang/wecomchan.git
- 分支: main
- 用户名: weixiaogang
- 邮箱: weixiaogang@haierht.com

### 自动部署流程
1. 生成HTML报告文件
2. 创建index.html入口文件
3. 配置Git仓库
4. 提交更改到Git
5. 推送到远程仓库
6. EdgeOne Pages自动部署

## 访问地址
- 主页面: https://edge.haierht.cn
- 报告页面: https://edge.haierht.cn/reports/

## 更新日志

### 2025-08-06 - Git部署功能完成
- ✅ 添加Git推送部署功能
- ✅ 实现多级降级机制（Git → API → 本地部署）
- ✅ 优化本地部署功能
- ✅ 添加完整的测试脚本
- ✅ 修复函数定义顺序问题
- ✅ 创建详细的部署说明文档

### 部署功能特性
1. **Git推送部署** - 自动化程度高，支持版本控制
2. **EdgeOne Pages API部署** - 直接API调用，部署速度快
3. **本地部署** - 无需网络，适合本地测试

### 测试脚本
- `test_git_deploy.py` - Git部署功能测试
- `test_local_deploy.py` - 本地部署测试
- `demo_git_deploy.py` - 完整部署演示
- `test_deploy_fix.py` - 部署功能修复测试
- `simple_fix.py` - 简单修复测试

### 文档
- `Git部署说明.md` - 详细部署说明文档
- `deploy_status_report.md` - 部署状态报告

## 使用说明

### 快速开始
1. 运行主脚本生成报告：`python3 整体日报数据.py`
2. 测试本地部署：`python3 test_local_deploy.py`
3. 测试Git部署：`python3 test_git_deploy.py`

### 部署方式选择
- **推荐**: Git推送部署（自动化程度高）
- **备选**: EdgeOne Pages API部署（速度快）
- **测试**: 本地部署（无需网络）

### 故障排除
- 如果Git推送失败，系统会自动降级到API部署
- 如果API部署失败，系统会自动降级到本地部署
- 所有部署方式都失败时，会返回错误信息

## 技术栈
- Python 3.x
- Git版本控制
- EdgeOne Pages API
- HTML/CSS/JavaScript
- MCP工具集成

## 项目状态
✅ **Git部署功能已完成并测试通过**
✅ **多级降级机制已实现**
✅ **本地部署功能已优化**
✅ **所有测试脚本已创建**

---
最后更新: 2025-08-06 18:00:00
