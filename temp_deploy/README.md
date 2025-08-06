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
- Git远程仓库: https://github.com/changchuan123/wecomchan.git
- 分支: master
- 用户名: weixiaogang
- 邮箱: weixiaogang@haierht.com

### 自动部署流程
1. 自动创建.gitignore文件
2. 自动创建README.md文件
3. 配置Git仓库
4. 推送代码到远程仓库
5. 自动部署到EdgeOne Pages

## 使用说明
运行主脚本即可自动完成所有部署流程。

## 会话总结

### 2025-08-06 会话：解决CDN域名和Git部署冲突问题

#### 主要目的
解决用户直接上传项目到EdgeOne Pages后，担心Git推送会覆盖直接上传内容的问题。

#### 完成的主要任务
1. **问题诊断**：分析了DNS解析失败的原因，确认域名 `sales-report.pages.edgeone.com` 未正确配置
2. **本地测试**：创建了本地HTTP服务器测试功能，确保524个HTML文件正常工作
3. **智能部署脚本**：开发了 `deploy_with_preserve.py` 脚本，实现保留式部署
4. **配置优化**：更新了 `edgeone.json` 配置，添加部署策略
5. **Git推送修复**：解决了Git上游分支设置问题，成功推送代码

#### 关键决策和解决方案
- **方案选择**：采用智能部署脚本方案，自动备份和恢复直接上传的内容
- **部署策略**：使用"合并模式"和"保留现有内容"策略
- **备份机制**：每次Git推送前自动备份reports目录，推送后恢复
- **域名问题**：确认新项目域名为 `sales-report-new.pages.edgeone.com`

#### 使用的技术栈
- Python 3.13 (本地服务器和部署脚本)
- Git (版本控制和推送)
- EdgeOne Pages (CDN部署)
- HTTP服务器 (本地测试)

#### 修改的文件
1. `edgeone.json` - 添加部署策略配置
2. `deploy_with_preserve.py` - 新建智能部署脚本
3. `local_server_test.py` - 新建本地测试服务器
4. `部署策略指南.md` - 新建详细部署指南
5. `README.md` - 更新项目文档

#### 解决的核心问题
- ✅ DNS解析失败问题已识别
- ✅ Git推送覆盖问题已解决
- ✅ 直接上传内容保护机制已建立
- ✅ 本地测试功能已实现
- ✅ 部署流程已优化

#### 后续建议
1. 使用 `python3 deploy_with_preserve.py` 进行后续部署
2. 定期检查EdgeOne控制台项目状态
3. 监控域名解析和CDN同步状态
4. 保持Git仓库与直接上传内容的同步
