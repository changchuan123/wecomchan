# EdgeOne Pages 自定义域名配置

本项目提供了完整的EdgeOne Pages自定义域名配置解决方案，包括部署脚本、域名验证工具和配置文件。

## 📁 文件结构

```
/Users/weixiaogang/AI/wecomchan/
├── 📄 deploy_to_edgeone.py              # 主要部署脚本
├── 📄 deploy_to_edgeone.bat             # Windows部署脚本
├── 📄 verify_domain_config.py           # 域名配置验证脚本
├── 📄 deploy_and_verify.py              # 一键部署和验证脚本
├── 📄 EdgeOne_Pages_自定义域名配置指南.md  # 详细配置指南
├── 📄 README_EdgeOne_自定义域名.md       # 本文件
├── ⚙️  .edgeone/
│   └── 📄 project.json                  # EdgeOne项目配置
├── ⚙️  edgeone.json                     # EdgeOne高级配置
├── 📁 reports/                          # HTML报告目录
└── 📁 edgeone-pages-mcp/               # EdgeOne Pages MCP服务
```

## 🚀 快速开始

### 方法一：一键部署和验证（推荐）

```bash
# 完整部署和验证
python deploy_and_verify.py

# 仅部署，跳过验证
python deploy_and_verify.py --skip-verify

# 仅验证，跳过部署
python deploy_and_verify.py --skip-deploy

# 使用自定义域名
python deploy_and_verify.py --domain your-domain.com
```

### 方法二：分步执行

```bash
# 1. 部署到EdgeOne Pages
python deploy_to_edgeone.py

# 2. 验证域名配置
python verify_domain_config.py

# 3. 验证特定域名
python verify_domain_config.py --domain your-domain.com
```

## ⚙️ 配置文件说明

### 1. `.edgeone/project.json` - 项目配置

```json
{
  "name": "sales-report",
  "domains": [
    {
      "domain": "edge.haierht.cn",
      "type": "custom"
    }
  ],
  "build": {
    "outputDirectory": "reports",
    "buildCommand": "",
    "installCommand": ""
  },
  "environment": {
    "production": {
      "EDGEONE_TOKEN": "${EDGEONE_TOKEN}"
    }
  },
  "routes": [
    {
      "src": "/reports/(.*)",
      "dest": "/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/reports/$1"
    }
  ]
}
```

### 2. `edgeone.json` - 高级配置

```json
{
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
          "value": "public, max-age=3600"
        }
      ]
    }
  ],
  "trailingSlash": true,
  "cleanUrls": true
}
```

## 🔧 环境要求

### 必需软件
- Python 3.6+
- EdgeOne CLI
- 网络连接

### Python依赖
```bash
pip install requests
```

### EdgeOne CLI安装
```bash
# 使用npm安装
npm install -g @edgeone/cli

# 验证安装
edgeone --version
```

## 🌐 域名配置步骤

### 1. DNS解析配置

在您的域名服务商（如阿里云、腾讯云DNS）添加CNAME记录：

```
记录类型: CNAME
主机记录: edge
记录值: [EdgeOne提供的CNAME值]
TTL: 600
```

### 2. EdgeOne控制台配置

1. 登录 [EdgeOne控制台](https://edgeone.ai/)
2. 进入Pages项目管理
3. 找到 `sales-report-new` 项目
4. 添加自定义域名 `edge.haierht.cn`
5. 验证域名解析
6. 等待SSL证书自动签发

### 3. 验证配置

```bash
# 验证DNS解析
nslookup edge.haierht.cn

# 验证HTTP访问
curl -I https://edge.haierht.cn

# 使用验证脚本
python verify_domain_config.py
```

## 📊 脚本功能说明

### `deploy_to_edgeone.py`
- ✅ 跨平台EdgeOne CLI路径检测
- ✅ 环境检查和配置验证
- ✅ 自动创建index.html
- ✅ 执行EdgeOne Pages部署
- ✅ 生成访问URL列表
- ✅ 部署结果测试

### `verify_domain_config.py`
- ✅ DNS解析验证
- ✅ SSL证书检查
- ✅ HTTP访问测试
- ✅ EdgeOne配置验证
- ✅ 详细验证报告

### `deploy_and_verify.py`
- ✅ 一键部署和验证
- ✅ 灵活的执行选项
- ✅ 智能等待机制
- ✅ 综合结果报告
- ✅ 错误处理和建议

## 🔍 故障排除

### 常见问题

#### 1. DNS解析失败
```bash
# 检查DNS配置
nslookup edge.haierht.cn
dig edge.haierht.cn CNAME

# 清除DNS缓存
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns            # Windows
```

#### 2. SSL证书问题
```bash
# 检查SSL证书
openssl s_client -connect edge.haierht.cn:443 -servername edge.haierht.cn

# 验证证书链
curl -vI https://edge.haierht.cn
```

#### 3. 部署失败
```bash
# 检查EdgeOne CLI
edgeone --version

# 检查Token
echo $EDGEONE_TOKEN

# 手动部署测试
edgeone pages deploy ./reports -n sales-report -t YOUR_TOKEN
```

#### 4. 访问404错误
- 检查reports目录中的文件
- 确认index.html存在
- 验证EdgeOne项目配置
- 检查路由配置

### 日志分析

```bash
# 查看详细部署日志
python deploy_to_edgeone.py 2>&1 | tee deploy.log

# 查看验证详情
python verify_domain_config.py --domain edge.haierht.cn 2>&1 | tee verify.log
```

## 📈 性能优化

### 缓存策略
- HTML文件：1小时缓存
- CSS/JS文件：24小时缓存
- 图片文件：7天缓存

### 安全配置
- 强制HTTPS跳转
- 安全头配置（CSP、HSTS等）
- XSS保护

### 监控建议
- 定期检查域名解析状态
- 监控SSL证书有效期
- 跟踪网站访问性能
- 设置告警通知

## 🔗 相关链接

- [EdgeOne Pages 官方文档](https://edgeone.ai/document/173731777508691968)
- [EdgeOne CLI 使用指南](https://edgeone.ai/document/177158578324279296)
- [DNS CNAME 配置说明](https://edgeone.ai/learning/what-is-cname)
- [EdgeOne Pages MCP 服务](https://lobehub.com/mcp/tencentedgeone-edgeone-pages-mcp)

## 📞 技术支持

如果在配置过程中遇到问题：

1. 查看本文档的故障排除部分
2. 运行验证脚本获取详细信息
3. 检查EdgeOne控制台的错误日志
4. 联系EdgeOne技术支持
5. 参考官方文档和社区资源

## 📝 更新日志

### v1.0.0 (2025-01-30)
- ✅ 初始版本发布
- ✅ 完整的部署和验证脚本
- ✅ 详细的配置文件
- ✅ 全面的文档说明

---

**注意**: 本项目基于当前EdgeOne Pages服务的功能特性开发，具体配置方法可能会随着服务更新而变化，请以官方最新文档为准。