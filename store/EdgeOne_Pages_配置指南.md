# EdgeOne Pages CLI 部署配置指南

## 🎯 项目信息
- **项目名**: sales-report-new
- **部署方式**: 仅限 CLI 命令行部署
- **禁止方式**: API、MCP、GIT推送等所有其他部署方式；
直接走CLI部署，不走 CDN 转发


## ⚠️ 重要声明
**本项目严格禁止使用以下部署方式：**
- ❌ API 接口部署
- ❌ MCP 工具部署  
- ❌ GIT 推送自动部署
- ❌ 控制台手动上传
- ❌ 其他任何非CLI方式

**唯一允许的部署方式：**
- ✅ EdgeOne CLI 命令行部署

## 📋 CLI 部署配置步骤

### 1. 安装 EdgeOne CLI
```bash
# 安装 EdgeOne CLI
npm install -g @tencent/edgeone-cli
```

### 2. 登录 EdgeOne CLI
```bash
# 登录到 EdgeOne
edgeone login
```

### 3. 验证 CLI 状态
```bash
# 检查 CLI 版本
edgeone --version

# 检查登录状态
edgeone whoami
```

### 4. 项目配置
- **项目名称**: sales-report-new
- **部署目录**: reports/
- **构建类型**: 静态HTML

### 5. CLI 部署命令
```bash
# 标准部署命令
edgeone pages deploy reports/ -n sales-report-new

# 带超时设置的部署命令
edgeone pages deploy reports/ -n sales-report-new --timeout 300
```

## 🌐 访问地址
部署完成后，您可以通过以下地址访问:
- 自定义域名: https://edge.haierht.cn
- 报告页面: https://edge.haierht.cn/[文件名].html

## 🔧 CLI 部署流程

### 触发条件
1. 手动执行 CLI 部署命令
2. 脚本自动调用 CLI 部署
3. 确保 reports/ 目录包含最新文件

### 部署内容
- reports/ 目录下的所有HTML文件
- 静态资源文件
- 配置文件

## 📈 监控和日志
1. 在命令行查看部署状态
2. 查看 CLI 输出日志
3. 验证部署结果

## 🚨 故障排除

### 常见问题
1. **CLI 未安装**
   - 检查 npm 是否安装
   - 重新安装 EdgeOne CLI
   - 验证环境变量

2. **CLI 未登录**
   - 运行 `edgeone login`
   - 检查登录状态
   - 重新登录

3. **部署失败**
   - 检查项目名称是否正确
   - 确认 reports/ 目录存在
   - 查看错误日志

4. **访问失败**
   - 检查域名配置
   - 确认SSL证书状态
   - 验证DNS解析

### 联系支持
- EdgeOne技术支持: 400-9100-100
- CLI文档: 查看官方CLI文档

## 📝 更新日志
- 2025-08-06: 初始配置完成
- 2025-08-06: CLI部署配置完成
- 2025-08-07: 明确禁止非CLI部署方式
- 2025-08-07: 统一项目名称为sales-report-new
- 2025-08-07: 修复URL访问问题

## 🔧 最新修复记录 (2025-08-07)

### 问题描述
1. **部署方式混乱**: 多个脚本使用不同的部署方式
2. **项目名称不一致**: 不同脚本使用不同的项目名称
3. **部署路径问题**: 部分脚本部署整个项目而不是reports目录
4. **URL访问问题**: 部署后文件无法通过URL访问

### 解决方案

#### 1. 统一部署方式
```bash
# 统一使用CLI部署
edgeone pages deploy reports/ -n sales-report-new
```

#### 2. 统一项目名称
```python
# 所有脚本统一使用
EDGEONE_PROJECT = "sales-report-new"
```

#### 3. 统一部署路径
```python
# 只部署reports目录，不部署整个项目
deploy_path = "reports/"
```

#### 4. 修复URL访问问题
```python
# 使用简化的URL结构
base_url = "https://edge.haierht.cn"
deployed_url = f"{base_url}/{filename}"
```

### 技术要点
1. **CLI优先**: 只使用EdgeOne CLI进行部署
2. **路径优化**: 只部署reports目录而不是整个项目
3. **项目统一**: 所有脚本使用相同的项目名称
4. **错误处理**: 完善的CLI错误处理和重试机制
5. **URL验证**: 部署后验证URL可访问性

### 验证结果
- ✅ CLI部署成功: 项目ID pages-wq4qohexh64i
- ✅ URL可访问: https://edge.haierht.cn/test_deploy.html
- ✅ 企业微信推送正常
- ✅ 跨平台兼容性验证通过
- ✅ URL访问问题已修复

---
生成时间: 2025-08-07 12:38:00
配置状态: ✅ 就绪
部署方式: ✅ 仅限CLI
修复状态: ✅ 完成
URL访问: ✅ 正常 