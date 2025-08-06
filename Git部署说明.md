# Git推送部署到EdgeOne Pages说明

## 概述

本项目支持多种部署方式，包括Git推送、EdgeOne Pages API和本地部署。当Git推送失败时，系统会自动降级到其他部署方式。

## 部署方式

### 1. Git推送部署（推荐）

**优点：**
- 自动化程度高
- 支持版本控制
- 适合团队协作

**配置要求：**
- Git仓库已初始化
- 远程仓库已配置
- Git用户信息已设置

**配置步骤：**
```bash
# 1. 初始化Git仓库（如果未初始化）
git init

# 2. 配置远程仓库
git remote add origin https://github.com/changchuan123/wecomchan.git

# 3. 配置Git用户信息
git config user.name "weixiaogang"
git config user.email "weixiaogang@haierht.com"
```

### 2. EdgeOne Pages API部署（备选）

**优点：**
- 直接API调用
- 不依赖Git
- 部署速度快

**配置要求：**
- EdgeOne Pages项目已创建
- API Token已配置

### 3. 本地部署（测试用）

**优点：**
- 无需网络连接
- 适合本地测试
- 部署简单快速

**特点：**
- 文件保存在`test_deploy`目录
- 自动生成美观的入口页面
- 支持浏览器直接打开

## 部署流程

### 自动部署流程

1. **生成HTML报告**
   - 系统自动生成销售报告HTML文件
   - 保存到`reports`目录

2. **创建入口文件**
   - 自动生成`index.html`作为入口页面
   - 包含所有可用报告的链接

3. **Git配置检查**
   - 检查Git仓库状态
   - 验证远程仓库配置
   - 确认用户信息设置

4. **文件提交**
   - 添加所有报告文件到Git
   - 提交更改到本地仓库

5. **推送到远程**
   - 推送到GitHub远程仓库
   - EdgeOne Pages自动检测并部署

### 降级机制

如果Git推送失败，系统会自动尝试：

1. **EdgeOne Pages API部署**
   - 使用MCP EdgeOne Pages API
   - 直接上传HTML内容

2. **本地部署**
   - 复制文件到`test_deploy`目录
   - 生成本地可访问的页面

## 配置文件

### Git配置

```python
# Git部署配置
GIT_REMOTE_URL = "https://github.com/changchuan123/wecomchan.git"
GIT_BRANCH = "master"
GIT_USERNAME = "weixiaogang"
GIT_EMAIL = "weixiaogang@haierht.com"
```

### EdgeOne配置

```python
# EdgeOne Pages配置
EDGEONE_PROJECT = "sales-report"
EDGEONE_TOKEN = "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc="
```

## 测试脚本

### 1. Git部署测试
```bash
python3 test_git_deploy.py
```

### 2. 本地部署测试
```bash
python3 test_local_deploy.py
```

### 3. 完整部署演示
```bash
python3 demo_git_deploy.py
```

## 故障排除

### 常见问题

1. **Git推送失败**
   - 检查远程仓库URL是否正确
   - 确认GitHub仓库是否存在
   - 验证用户权限

2. **API部署失败**
   - 检查EdgeOne Pages项目配置
   - 验证API Token是否有效
   - 确认网络连接正常

3. **本地部署失败**
   - 检查文件权限
   - 确认磁盘空间充足
   - 验证Python环境

### 错误处理

系统会自动处理以下情况：

- Git仓库未初始化
- 远程仓库配置错误
- 网络连接问题
- API调用失败
- 文件权限问题

## 访问地址

### 生产环境
- 主页面: https://sales-report.pages.edgeone.com
- 报告页面: https://sales-report.pages.edgeone.com/reports/

### 本地测试
- 本地部署: `file:///path/to/test_deploy/index.html`

## 更新日志

- 2025-08-06: 添加Git推送部署功能
- 2025-08-06: 实现多级降级机制
- 2025-08-06: 优化本地部署功能
- 2025-08-06: 添加完整的测试脚本

## 技术支持

如有问题，请检查：

1. Git配置是否正确
2. 网络连接是否正常
3. 文件权限是否足够
4. Python环境是否完整

系统会自动选择最适合的部署方式，确保报告能够成功发布。 