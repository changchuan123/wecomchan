# EdgeOne Pages CLI 部署配置指南

## 概述

本指南严格按照EdgeOne Pages CLI部署方式，禁止使用其他任何部署方式。项目名称固定为`sales-report-new`，禁止Git自动生成新项目。

禁止通过 GIT上传新的项目到EdgeOne pages！！！

## 当前项目配置状态

### 现有配置
- **项目名称**: `sales-report-new` (固定，禁止修改)
- **项目ID**: `pages-wq4qohexh64i`
- **当前自定义域名**: `https://edge.haierht.cn`
- **部署方式**: 仅限CLI部署，禁止其他方式

### 项目结构
```
/Users/weixiaogang/AI/wecomchan/
├── .edgeone/
│   └── project.json              # EdgeOne项目配置文件
├── edgeone.json                  # EdgeOne Pages配置
├── edgeone_cli_deploy.py         # CLI部署脚本
├── reports/                      # 报告文件目录
└── .gitignore                    # 包含.edgeone配置
```

## CLI部署配置方法

### 1. 安装EdgeOne CLI
```bash
# 安装EdgeOne CLI (修正：使用官方命令)
npm install -g edgeone

# 验证安装
edgeone -v
```

### 2. 登录EdgeOne
```bash
# 登录EdgeOne账户
edgeone login

# 验证登录状态
edgeone whoami
```

### 3. 项目配置
项目已预配置，配置文件位于`.edgeone/project.json`：
```json
{
  "Name": "sales-report-new",
  "ProjectId": "pages-wq4qohexh64i"
}
```

### 4. CLI部署命令
**重要：仅使用以下CLI命令进行部署，禁止其他方式！**

#### 4.1 本地部署命令
```bash
# 方法1: 先链接项目，再部署（推荐）
edgeone pages link sales-report-new
edgeone pages deploy reports -n sales-report-new -e production

# 方法2: 直接部署reports目录
edgeone pages deploy reports -n sales-report-new -e production

# 方法3: 使用Python脚本部署
python3 整体日报数据.py
```

#### 4.2 CI/CD部署命令（使用API Token）
```bash
# 生产环境部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production

# 预览环境部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e preview
```

### 4.3 项目链接（必需步骤）
由于项目类型限制，必须先链接项目：
```bash
# 链接到现有项目
edgeone pages link sales-report-new

# 验证链接状态
ls -la .edgeone/project.json
```

### 4.4 项目类型说明（重要更新）
**重要说明**：当前项目 `sales-report-new` 是通过Git创建的，不支持直接文件夹部署：
- ❌ 不支持项目根目录部署：`edgeone pages deploy . -n sales-report-new`
- ❌ 不支持reports目录直接部署：`edgeone pages deploy reports -n sales-report-new`
- ✅ 支持Git推送触发自动部署
- ✅ 支持使用API Token的CI/CD部署

### 4.5 强制CLI部署
如果遇到"项目类型不支持直接部署"错误，使用以下方法：
```bash
# 方法1: 使用API Token强制部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production

# 方法2: 使用环境变量强制部署
EDGEONE_FORCE_DEPLOY=1 edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=
```

### 5. 自定义域名配置（仅通过CLI）

#### 5.1 添加自定义域名
```bash
# 添加自定义域名
edgeone pages domain add edge.haierht.cn --project sales-report-new
```

#### 5.2 验证域名配置
```bash
# 查看项目域名列表
edgeone pages domain list --project sales-report-new

# 验证域名状态
edgeone pages domain verify edge.haierht.cn --project sales-report-new
```

#### 5.3 配置DNS解析
在域名服务商处添加CNAME记录：
```
记录类型: CNAME
主机记录: edge
记录值: [EdgeOne提供的CNAME值]
TTL: 600
```

## 禁止的部署方式

### ❌ 禁止使用以下方式：
1. **Git自动部署** - 禁止Git自动生成新项目
2. **控制台手动上传** - 禁止通过Web控制台上传文件
3. **第三方工具** - 禁止使用非官方CLI工具
4. **API直接调用** - 禁止绕过CLI直接调用API

### ✅ 仅允许的部署方式：
1. **EdgeOne CLI** - 使用官方CLI工具
2. **Python部署脚本** - 基于CLI的自动化脚本
3. **API Token部署** - 用于CI/CD流水线

## 配置文件说明

### edgeone.json 配置
```json
{
  "static": {
    "directory": "reports"
  },
  "redirects": [
    {
      "source": "/",
      "destination": "/reports/",
      "permanent": false
    }
  ],
  "headers": [
    {
      "source": "/**/*.html",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ],
  "trailingSlash": true,
  "cleanUrls": true
}
```

### .edgeone/project.json 配置
```json
{
  "Name": "sales-report-new",
  "ProjectId": "pages-wq4qohexh64i"
}
```

## 部署流程

### 1. 准备部署
```bash
# 确保在项目根目录
cd /Users/weixiaogang/AI/wecomchan

# 检查项目状态
ls -la .edgeone/
ls -la reports/
```

### 2. 执行CLI部署
```bash
# 使用Python脚本部署（推荐）
python3 整体日报数据.py

# 或直接使用CLI命令（使用API Token）
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production
```

### 3. 验证部署
```bash
# 检查部署状态
edgeone pages list

# 查看项目详情
edgeone pages info sales-report-new
```

## 故障排除

### 1. CLI登录问题
```bash
# 重新登录
edgeone logout
edgeone login

# 检查登录状态
edgeone whoami
```

### 2. 项目权限问题
```bash
# 检查项目权限
edgeone pages list

# 如果项目不存在，联系管理员
```

### 3. 部署失败
```bash
# 检查错误日志
edgeone pages logs sales-report-new

# 重新部署（使用API Token）
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production
```

### 4. 域名配置问题
```bash
# 检查域名状态
edgeone pages domain list --project sales-report-new

# 重新配置域名
edgeone pages domain remove edge.haierht.cn --project sales-report-new
edgeone pages domain add edge.haierht.cn --project sales-report-new
```

## 最佳实践

### 1. 部署前检查
- 确保所有文件在`reports/`目录中
- 验证`edgeone.json`配置正确
- 检查CLI登录状态或API Token有效性

### 2. 部署后验证
- 访问部署URL确认文件可访问
- 检查自定义域名是否生效
- 验证SSL证书状态

### 3. 定期维护
- 定期更新CLI工具
- 监控部署日志
- 备份重要配置文件

## 安全注意事项

### 1. 访问控制
- 仅授权人员使用CLI部署
- 定期轮换访问凭证
- 监控异常部署活动

### 2. 文件安全
- 确保`reports/`目录中的文件安全
- 不要上传敏感信息
- 定期清理临时文件

## 技术支持

### 官方资源
- [EdgeOne CLI 官方文档](https://edgeone.cloud.tencent.com/pages/document/162936923278893056)
- [EdgeOne Pages 使用指南](https://edgeone.cloud.tencent.com/pages/document/173731777508691968)

### 联系支持
- 腾讯云技术支持
- EdgeOne官方社区

---

**重要提醒**：
1. 严格遵循CLI部署方式，禁止其他任何部署方式
2. 项目名称固定为`sales-report-new`，禁止修改
3. 禁止Git自动生成新项目
4. 所有部署操作必须通过官方CLI工具执行
5. 当前项目为Git类型，不支持直接文件夹部署，请使用API Token方式