# 销售数据分析系统

## 项目概述
这是一个基于Python的销售数据分析系统，支持自动生成销售报告并通过EdgeOne Pages部署到云端。

## 主要功能
- 📊 销售数据分析
- 📈 HTML报告生成
- 🌐 EdgeOne Pages云端部署
- 📱 企业微信推送
- 🔄 Git自动化部署

## 部署配置

### Git配置
- **远程仓库**: https://github.com/changchuan123/wecomchan.git
- **分支**: master
- **用户**: weixiaogang / weixiaogang@haierht.com

### EdgeOne Pages配置
- **项目名**: sales-report
- **访问地址**: https://sales-report.pages.edgeone.com
- **报告页面**: https://sales-report.pages.edgeone.com/reports/

## 部署流程
1. 生成HTML销售报告
2. 自动提交到Git仓库
3. EdgeOne Pages自动检测并部署
4. 企业微信推送通知

## 文件结构
```
wecomchan/
├── reports/           # HTML报告文件
├── data/             # 数据文件
├── logs/             # 日志文件
├── test_deploy/      # 本地测试部署
└── 整体日报数据.py    # 主要分析脚本
```

## 配置文档
- [Git部署说明.md](Git部署说明.md) - Git推送部署详细说明
- [EdgeOne_Pages_配置指南.md](EdgeOne_Pages_配置指南.md) - EdgeOne Pages配置指南

## 更新日志

### 2025-08-06 配置修复
- ✅ 修复了`_simple_verify_url`函数未定义的问题
- ✅ 统一了Git配置信息（仓库URL、分支名称）
- ✅ 更新了访问地址配置
- ✅ 优化了部署流程和错误处理
- ✅ 完善了配置文档的一致性

### 技术栈
- Python 3.x
- pandas (数据分析)
- pymysql (数据库连接)
- requests (HTTP请求)
- Git (版本控制)
- EdgeOne Pages (云端部署)

### 修改的文件
- `整体日报数据.py` - 添加了`_simple_verify_url`函数
- `Git部署说明.md` - 更新了配置信息
- `EdgeOne_Pages_配置指南.md` - 更新了部署状态
- `README.md` - 添加了本次修复总结

## 使用说明
1. 确保Git仓库已正确配置
2. 运行`python3 整体日报数据.py`生成报告
3. 系统会自动部署到EdgeOne Pages
4. 通过企业微信接收推送通知

## 故障排除
- 检查Git配置是否正确
- 确认EdgeOne Pages项目状态
- 查看日志文件获取详细错误信息
