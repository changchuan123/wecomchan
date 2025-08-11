# EdgeOne Pages 静态托管配置指南

## 问题描述
当前 EdgeOne Pages 部署后访问报告文件时返回 404 错误，这是因为静态文件没有正确部署到 Pages 平台。

## 解决方案
确保静态文件正确部署到 EdgeOne Pages，使用正确的 CLI 命令和配置。**严格按照CLI方式配置，禁止其他方式。**

## 配置步骤

### 1. 安装并登录 EdgeOne CLI
```bash
# 安装EdgeOne CLI (修正：使用官方命令)
npm install -g edgeone

# 登录EdgeOne
edgeone login

# 验证登录状态
edgeone whoami
```

### 2. 项目配置和部署

#### 2.1 项目链接
```bash
# 链接到现有项目
edgeone pages link sales-report-new

# 验证链接状态
ls -la .edgeone/project.json
```

#### 2.2 使用API Token部署（推荐方式）
由于当前项目为Git类型，不支持直接文件夹部署，需要使用API Token：

```bash
# 生产环境部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production

# 预览环境部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e preview
```

#### 2.3 验证部署
```bash
# 检查部署状态
edgeone pages list

# 查看项目详情
edgeone pages info sales-report-new
```

### 3. 静态文件配置

#### 3.1 edgeone.json 配置
确保 `edgeone.json` 配置正确：

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

#### 3.2 文件结构检查
确保 `reports/` 目录包含所有需要部署的HTML文件：

```bash
# 检查reports目录
ls -la reports/

# 确保有HTML文件
find reports/ -name "*.html" | head -10
```

### 4. 访问验证

#### 4.1 测试访问
```bash
# 测试Pages域名访问
curl -I https://sales-report-new.pages.edgeone.com/reports/

# 测试自定义域名访问
curl -I https://edge.haierht.cn/reports/
```

#### 4.2 检查文件可访问性
```bash
# 检查具体文件
curl -I https://edge.haierht.cn/reports/overall_daily_2025-07-29_101349.html
```

## 禁止的配置方式

### ❌ 禁止使用以下方式：
1. **Web控制台手动上传** - 禁止通过浏览器控制台上传文件
2. **API直接调用** - 禁止绕过CLI直接调用API
3. **第三方工具** - 禁止使用非官方CLI工具
4. **边缘函数代理** - Pages是静态托管，不需要边缘函数

### ✅ 仅允许的配置方式：
1. **EdgeOne CLI** - 使用官方CLI工具
2. **API Token部署** - 用于CI/CD流水线
3. **Git推送触发** - 自动部署

## 故障排除

### 问题1：部署失败
```bash
# 检查CLI状态
edgeone whoami
edgeone pages list

# 重新部署（使用API Token）
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production
```

### 问题2：文件404错误
```bash
# 检查文件是否在reports目录
ls -la reports/

# 检查edgeone.json配置
cat edgeone.json

# 重新部署
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production
```

### 问题3：域名访问失败
```bash
# 检查域名配置
edgeone pages domain list --project sales-report-new

# 重新配置域名
edgeone pages domain remove edge.haierht.cn --project sales-report-new
edgeone pages domain add edge.haierht.cn --project sales-report-new
```

### 问题4：项目类型不支持部署
```bash
# 使用API Token方式（推荐）
edgeone pages deploy reports -n sales-report-new -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc= -e production

# 或使用Git推送触发自动部署
git add reports/
git commit -m "Update reports"
git push origin master
```

## 监控和维护

### 1. 部署监控
```bash
# 查看部署状态
edgeone pages list

# 查看部署日志
edgeone pages logs sales-report-new
```

### 2. 文件监控
```bash
# 检查文件数量
find reports/ -name "*.html" | wc -l

# 检查文件大小
du -sh reports/
```

### 3. 定期维护
```bash
# 更新CLI工具
npm update -g edgeone

# 检查项目状态
edgeone pages info sales-report-new
```

## 注意事项

1. **静态托管特性**: EdgeOne Pages 是静态网站托管服务，不支持动态内容
2. **文件限制**: 确保所有文件都是静态文件（HTML、CSS、JS、图片等）
3. **部署方式**: 当前项目为Git类型，请使用API Token或Git推送方式部署
4. **缓存配置**: 合理配置缓存策略，提高访问速度

## 替代方案

如果静态托管方案不适用，可以考虑：
1. 使用 EdgeOne 边缘函数服务（独立服务）
2. 使用其他云服务的静态托管
3. 使用传统Web服务器

## 联系支持

如果遇到问题，可以：
1. 查看 [EdgeOne CLI 官方文档](https://edgeone.cloud.tencent.com/pages/document/162936923278893056)
2. 联系腾讯云技术支持
3. 在相关技术社区寻求帮助

---

**重要提醒**：
1. 严格遵循CLI配置方式，禁止其他任何配置方式
2. 所有部署操作必须通过官方CLI工具执行
3. 禁止通过Web控制台手动配置
4. 当前项目为Git类型，请使用API Token或Git推送方式部署
5. Pages是静态托管服务，不需要边缘函数代理

**配置完成后，EdgeOne Pages 应该能够正常提供静态文件访问，解决 404 错误问题。**