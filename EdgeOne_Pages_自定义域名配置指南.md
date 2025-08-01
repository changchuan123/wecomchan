# EdgeOne Pages 自定义域名配置指南

## 概述

本指南将详细介绍如何为EdgeOne Pages项目配置自定义域名，实现从默认的`.edgeone.app`域名切换到您自己的域名（如`edge.haierht.cn`）。

## 当前项目配置状态

### 现有配置
- **项目名称**: `sales-report`
- **当前自定义域名**: `https://edge.haierht.cn`
- **EdgeOne Token**: 已配置
- **部署脚本**: `deploy_to_edgeone.py`

### 项目结构
```
/Users/weixiaogang/AI/wecomchan/
├── deploy_to_edgeone.py          # 主要部署脚本
├── deploy_to_edgeone.bat         # Windows部署脚本
├── reports/                      # 报告文件目录
├── .gitignore                    # 包含.edgeone配置
└── (缺失) .edgeone/
    └── project.json              # EdgeOne项目配置文件
```

## 配置方法

### 方法一：通过EdgeOne控制台配置（推荐）

1. **登录EdgeOne控制台**
   - 访问 [EdgeOne控制台](https://edgeone.ai/)
   - 使用您的腾讯云账号登录

2. **进入Pages项目管理**
   - 找到您的`sales-report`项目
   - 点击进入项目详情页面

3. **添加自定义域名**
   - 点击「项目设置」→「域名管理」→「添加域名」
   - 输入您的域名：`edge.haierht.cn`
   - 点击「下一步」

4. **配置DNS解析**
   - 前往您的域名服务商（如阿里云、腾讯云DNS等）
   - 添加CNAME解析记录：
     ```
     记录类型: CNAME
     主机记录: edge
     记录值: [EdgeOne提供的CNAME值]
     TTL: 600（或默认值）
     ```

5. **验证域名**
   - 返回EdgeOne控制台
   - 点击「验证域名」
   - 等待DNS解析生效（通常5-10分钟）

6. **SSL证书自动配置**
   - EdgeOne会自动为您的域名签发SSL证书
   - 证书提供商：TrustAsia
   - 证书类型：RSA2048单域名DV证书
   - 有效期：3个月（自动续期）

### 方法二：通过配置文件配置

1. **创建.edgeone目录和配置文件**
   ```bash
   mkdir -p .edgeone
   ```

2. **创建project.json配置文件**
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
     }
   }
   ```

3. **创建edgeone.json配置文件（可选）**
   在项目根目录创建`edgeone.json`用于高级配置：
   ```json
   {
     "redirects": [
       {
         "source": "/reports/:path*",
         "destination": "/:path*",
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
     ]
   }
   ```

### 方法三：通过EdgeOne CLI配置

1. **安装EdgeOne CLI**
   ```bash
   npm install -g @edgeone/cli
   ```

2. **登录EdgeOne**
   ```bash
   edgeone login
   ```

3. **配置项目**
   ```bash
   edgeone pages domain add edge.haierht.cn --project sales-report
   ```

## 验证配置

### 1. DNS解析验证
```bash
# 检查CNAME解析
nslookup edge.haierht.cn

# 或使用dig命令
dig edge.haierht.cn CNAME
```

### 2. HTTP访问验证
```bash
# 测试HTTP访问
curl -I https://edge.haierht.cn

# 测试具体报告页面
curl -I https://edge.haierht.cn/reports/
```

### 3. SSL证书验证
```bash
# 检查SSL证书
openssl s_client -connect edge.haierht.cn:443 -servername edge.haierht.cn
```

## 常见问题解决

### 1. DNS解析不生效
- **原因**: DNS缓存或解析记录配置错误
- **解决**: 
  - 检查DNS解析记录配置
  - 清除本地DNS缓存：`sudo dscacheutil -flushcache`
  - 等待DNS全球传播（最多24小时）

### 2. SSL证书问题
- **原因**: 证书签发失败或未完成
- **解决**:
  - 确保域名解析正确指向EdgeOne
  - 等待证书自动签发完成
  - 联系EdgeOne技术支持

### 3. 404错误
- **原因**: 路径配置或文件部署问题
- **解决**:
  - 检查`reports`目录下的文件
  - 确认部署脚本正确执行
  - 检查EdgeOne项目配置

### 4. 访问速度慢
- **原因**: 边缘节点缓存未生效
- **解决**:
  - 配置适当的缓存策略
  - 使用EdgeOne的全球加速功能
  - 优化静态资源

## 最佳实践

### 1. 域名管理
- 使用有意义的子域名（如`edge.haierht.cn`）
- 保持域名结构简洁明了
- 定期检查域名解析状态

### 2. 缓存策略
- 为静态资源设置合适的缓存时间
- 使用版本控制避免缓存问题
- 配置适当的Cache-Control头

### 3. 安全配置
- 启用HTTPS强制跳转
- 配置安全头（HSTS、CSP等）
- 定期更新SSL证书

### 4. 监控和维护
- 定期检查域名解析状态
- 监控网站访问性能
- 及时处理SSL证书续期

## 相关链接

- [EdgeOne Pages 官方文档](https://edgeone.ai/document/173731777508691968)
- [EdgeOne CLI 使用指南](https://edgeone.ai/document/177158578324279296)
- [DNS CNAME 配置说明](https://edgeone.ai/learning/what-is-cname)
- [EdgeOne Pages MCP 服务](https://lobehub.com/mcp/tencentedgeone-edgeone-pages-mcp)

## 技术支持

如果在配置过程中遇到问题，可以：
1. 查看EdgeOne控制台的错误日志
2. 联系EdgeOne技术支持
3. 参考官方文档和社区资源

---

**注意**: 本指南基于当前EdgeOne Pages服务的功能特性编写，具体配置方法可能会随着服务更新而变化，请以官方最新文档为准。