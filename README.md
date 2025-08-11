# 销售日报系统

## 项目简介
这是一个自动化的销售日报分析系统，**严格按照EdgeOne CLI部署方式**，禁止其他任何部署方式。

## 功能特性
- 📊 自动分析销售数据
- 📈 生成详细的HTML报告
- 🚀 严格使用CLI部署到EdgeOne Pages
- 📱 企业微信推送通知

## 部署方式
**本项目严格使用EdgeOne CLI部署方式，禁止其他任何部署方式！**

### 项目配置
- **项目名称**: `sales-report-new` (固定，禁止修改)
- **项目ID**: `pages-wq4qohexh64i`
- **自定义域名**: `https://edge.haierht.cn`
- **部署方式**: 仅限CLI部署，禁止其他方式

### CLI部署要求
- EdgeOne CLI: `npm install -g @edgeone/cli`
- 登录状态: `edgeone login`
- 项目权限: 确保对`sales-report-new`项目有部署权限

### 禁止的部署方式
- ❌ Git自动部署 - 禁止Git自动生成新项目
- ❌ 控制台手动上传 - 禁止通过Web控制台上传文件
- ❌ 第三方工具 - 禁止使用非官方CLI工具
- ❌ API直接调用 - 禁止绕过CLI直接调用API

### 允许的部署方式
- ✅ EdgeOne CLI - 使用官方CLI工具
- ✅ Python部署脚本 - 基于CLI的自动化脚本

## 使用说明
运行主脚本即可自动完成所有部署流程，严格遵循CLI部署方式。

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

### 2025-01-27 会话：严格CLI部署方式配置

#### 主要目的
根据用户要求，严格遵循EdgeOne CLI部署方式，禁止其他任何部署方式，确保项目名称为`sales-report-new`。

#### 完成的主要任务
1. **配置文档修正**：更新了`EdgeOne_Pages_自定义域名配置指南.md`，严格遵循CLI部署方式
2. **边缘函数配置修正**：更新了`EdgeOne_边缘函数配置指南.md`，确保与CLI部署方式一致
3. **源代码修改**：修改了`整体日报数据.py`中的`deploy_to_edgeone`函数，严格遵循CLI部署方式
4. **配置文件创建**：创建了`edge_function.js`边缘函数配置文件
5. **项目配置确认**：确认项目名称为`sales-report-new`，项目ID为`pages-wq4qohexh64i`

#### 关键决策和解决方案
- **部署方式限制**：严格禁止Git自动部署、控制台手动上传、第三方工具、API直接调用
- **CLI优先策略**：所有部署操作必须通过官方CLI工具执行
- **项目名称固定**：项目名称固定为`sales-report-new`，禁止修改
- **错误处理优化**：增加了多种CLI部署方式的尝试和验证机制

#### 使用的技术栈
- EdgeOne CLI (官方CLI工具)
- Python 3.13 (部署脚本)
- JavaScript (边缘函数)
- EdgeOne Pages (静态网站托管)
- EdgeOne Edge Functions (边缘函数服务)

#### 修改的文件
1. `EdgeOne_Pages_自定义域名配置指南.md` - 完全重写为CLI部署方式
2. `EdgeOne_边缘函数配置指南.md` - 更新为CLI配置方式
3. `整体日报数据.py` - 修改`deploy_to_edgeone`函数
4. `edge_function.js` - 新建边缘函数配置文件
5. `README.md` - 更新项目文档

#### 解决的核心问题
- ✅ 严格遵循CLI部署方式，禁止其他方式
- ✅ 项目名称固定为`sales-report-new`
- ✅ 禁止Git自动生成新项目
- ✅ 边缘函数配置与CLI方式一致
- ✅ 部署脚本严格使用CLI命令

#### 重要提醒
1. **严格遵循CLI部署方式**，禁止其他任何部署方式
2. **项目名称固定为`sales-report-new`**，禁止修改
3. **禁止Git自动生成新项目**，坚决制止
4. **所有部署操作必须通过官方CLI工具执行**
5. **定期监控部署日志和性能指标**

#### 后续建议
1. 使用 `python3 整体日报数据.py` 进行CLI部署
2. 定期检查EdgeOne CLI登录状态
3. 监控边缘函数执行日志
4. 保持配置文件与CLI部署方式一致

# 项目总结

## 2025-01-11 配置文档修正总结

### 会话的主要目的
根据官方文档修正EdgeOne Pages配置指南，确保URL推送正常，解决项目名称和部署方式问题。

### 完成的主要任务

#### 1. 修正 EdgeOne_Pages_自定义域名配置指南.md
- **CLI安装命令修正**：从 `npm install -g @edgeone/cli` 改为 `npm install -g edgeone`
- **部署命令格式更新**：添加环境参数 `-e production/preview`
- **项目类型说明更新**：明确当前项目为Git类型，不支持直接文件夹部署
- **添加CI/CD部署说明**：详细说明使用API Token的部署方式
- **更新故障排除**：针对Git类型项目的特殊处理

#### 2. 修正 EdgeOne_边缘函数配置指南.md
- **文档重命名**：改为"EdgeOne Pages 静态托管配置指南"
- **解决方案修正**：移除边缘函数代理方案，改为正确的静态文件部署
- **CLI安装命令修正**：使用官方正确的安装命令
- **部署方式更新**：重点说明API Token和Git推送方式
- **移除错误概念**：Pages是静态托管，不需要边缘函数代理

#### 3. 修正 整体日报数据.py
- **URL生成逻辑修正**：使用正确的项目名称 `sales-report-new`
- **域名配置更新**：使用自定义域名 `edge.haierht.cn`
- **URL验证优化**：更新多种URL格式的验证顺序
- **get_web_report_url函数修正**：返回正确的EdgeOne Pages URL

### 关键决策和解决方案

#### 项目类型识别
- **问题**：项目不支持直接文件夹部署
- **原因**：当前项目为Git类型，不是"直接上传"类型
- **解决方案**：使用API Token部署或Git推送触发自动部署

#### URL格式标准化
- **主要URL**：`https://edge.haierht.cn/reports/{filename}`
- **备用URL**：`https://sales-report-new.pages.edgeone.com/reports/{filename}`
- **验证顺序**：优先使用自定义域名，其次使用默认域名

#### 部署方式选择
- **推荐方式**：API Token部署（CI/CD方式）
- **备用方式**：Git推送触发自动部署
- **禁止方式**：直接文件夹部署（项目类型不支持）

### 使用的技术栈
- **EdgeOne CLI**：官方CLI工具
- **Git**：版本控制和自动部署触发
- **Python**：自动化部署脚本
- **API Token**：CI/CD流水线认证

### 修改的文件
1. **EdgeOne_Pages_自定义域名配置指南.md** - 全面修正CLI命令和部署方式
2. **EdgeOne_边缘函数配置指南.md** - 重写为静态托管配置指南
3. **整体日报数据.py** - 修正URL生成和验证逻辑

### 重要提醒
1. **项目名称固定**：`sales-report-new`，禁止修改
2. **部署方式限制**：仅支持API Token或Git推送方式
3. **域名配置**：使用自定义域名 `edge.haierht.cn`
4. **CLI命令**：使用官方命令 `npm install -g edgeone`
5. **静态托管特性**：Pages是静态托管服务，不需要边缘函数代理

### 下一步建议
1. 测试Git推送触发自动部署
2. 验证自定义域名访问
3. 监控部署日志和文件可访问性
4. 定期更新CLI工具和配置
