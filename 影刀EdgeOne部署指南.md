# 影刀环境 EdgeOne Pages 部署指南

## 🤖 概述

本指南专门针对影刀RPA环境中的EdgeOne Pages部署问题，提供了优化的解决方案。

### 影刀环境特点
- 软件路径：`D:\软件\ShadowBot\ShadowBot.exe`
- 可能运行在特殊的Windows容器环境中
- EdgeOne CLI路径检测需要特殊处理
- 网络访问可能有特殊配置

## 🚀 快速部署

### 方法一：使用影刀专用脚本（推荐）

1. **运行影刀专用批处理脚本**
   ```cmd
   deploy_to_edgeone_yingdao.bat
   ```

2. **或直接运行Python脚本**
   ```cmd
   python deploy_to_edgeone_yingdao.py
   ```

### 方法二：使用通用一键修复工具

```cmd
一键修复EdgeOne.bat
```

## 📁 文件说明

### 影刀专用文件

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `deploy_to_edgeone_yingdao.py` | 影刀环境专用Python部署脚本 | 智能路径检测、环境适配 |
| `deploy_to_edgeone_yingdao.bat` | 影刀环境专用批处理脚本 | 一键启动部署流程 |
| `影刀EdgeOne部署指南.md` | 本文档 | 使用说明和故障排除 |

### 通用文件

| 文件名 | 说明 | 兼容性 |
|--------|------|--------|
| `一键修复EdgeOne.bat` | 通用一键修复工具 | ✅ 影刀兼容 |
| `deploy_to_edgeone.py` | 标准部署脚本 | ⚠️ 可能需要路径调整 |
| `test_launcher.bat` | 环境测试工具 | ✅ 影刀兼容 |

## 🔧 影刀环境优化特性

### 1. 智能路径检测

影刀专用脚本会按以下优先级搜索EdgeOne CLI：

```
1. D:\软件\ShadowBot\nodejs\edgeone.cmd          # 影刀内置Node.js
2. D:\软件\ShadowBot\node_modules\.bin\edgeone.cmd # 影刀模块路径
3. C:\Users\{用户名}\AppData\Roaming\npm\edgeone.cmd # 用户npm路径
4. C:\Program Files\nodejs\edgeone.cmd            # 系统Node.js路径
5. edgeone.cmd / edgeone                          # 环境变量路径
```

### 2. 环境检测

- 自动检测是否在影刀环境中运行
- 设置影刀专用环境变量
- 优化超时时间适应影刀响应速度

### 3. 错误处理

- 增强的错误诊断信息
- 影刀环境特殊问题的解决建议
- 详细的部署日志输出

## 🔍 故障排除

### 问题1：找不到EdgeOne CLI

**现象：**
```
❌ 未找到EdgeOne CLI，请确保已安装并配置PATH
```

**解决方案：**

1. **检查Node.js安装**
   ```cmd
   node --version
   npm --version
   ```

2. **安装EdgeOne CLI**
   ```cmd
   npm install -g @edgeone/cli
   ```

3. **检查影刀内置Node.js**
   - 查看 `D:\软件\ShadowBot\nodejs\` 目录
   - 确认EdgeOne CLI是否安装在影刀环境中

4. **手动配置PATH**
   ```cmd
   set PATH=%PATH%;D:\软件\ShadowBot\nodejs
   set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Roaming\npm
   ```

### 问题2：网络连接问题

**现象：**
```
❌ 部署超时（5分钟）
Error: connect ETIMEDOUT
```

**解决方案：**

1. **检查影刀网络权限**
   - 确保影刀有外网访问权限
   - 检查防火墙设置

2. **配置代理（如需要）**
   ```cmd
   set HTTP_PROXY=http://proxy.company.com:8080
   set HTTPS_PROXY=http://proxy.company.com:8080
   ```

3. **测试网络连接**
   ```cmd
   ping edgeone.ai
   ping pages.edgeone.ai
   ```

### 问题3：权限问题

**现象：**
```
❌ 权限不足
Access denied
```

**解决方案：**

1. **以管理员身份运行影刀**
2. **检查文件权限**
   ```cmd
   icacls reports /grant %USERNAME%:F /T
   ```

3. **临时目录权限**
   ```cmd
   mkdir %TEMP%\edgeone_deploy
   cd %TEMP%\edgeone_deploy
   ```

### 问题4：字符编码问题

**现象：**
```
乱码或特殊字符显示错误
```

**解决方案：**

1. **设置UTF-8编码**
   ```cmd
   chcp 65001
   ```

2. **使用v2版本脚本**
   ```cmd
   一键修复EdgeOne.bat  # 自动使用v2版本
   ```

## 📋 部署检查清单

### 部署前检查

- [ ] 影刀软件正常运行
- [ ] Python环境已安装
- [ ] Node.js和npm已安装
- [ ] EdgeOne CLI已安装
- [ ] 网络连接正常
- [ ] reports目录存在且有HTML文件

### 部署后验证

- [ ] 部署命令执行成功
- [ ] 访问主域名：https://edge.haierht.cn
- [ ] 访问备用域名：https://sales-report.pages.edgeone.ai
- [ ] 所有HTML文件正常显示
- [ ] 图表和样式正常加载

## 🛠️ 高级配置

### 自定义EdgeOne CLI路径

如果EdgeOne CLI安装在特殊位置，可以设置环境变量：

```cmd
set EDGEONE_CLI_PATH=D:\custom\path\edgeone.cmd
```

### 自定义部署配置

编辑 `.edgeone/project.json` 文件：

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

### 影刀专用环境变量

```cmd
set YINGDAO_ENV=true
set SHADOWBOT_HOME=D:\软件\ShadowBot
set EDGEONE_TIMEOUT=300
set EDGEONE_RETRY_COUNT=3
```

## 📞 技术支持

### 日志文件位置

- 部署日志：控制台输出
- EdgeOne日志：EdgeOne控制台
- 影刀日志：影刀软件日志

### 常用诊断命令

```cmd
# 检查环境
python deploy_to_edgeone_yingdao.py --check-only

# 详细日志
python deploy_to_edgeone_yingdao.py --verbose

# 测试连接
test_launcher.bat
```

### 联系方式

如遇到无法解决的问题，请提供以下信息：

1. 影刀版本信息
2. 错误信息截图
3. 部署日志
4. 系统环境信息

---

**更新时间：** 2025-01-30  
**版本：** 1.0.0  
**适用环境：** 影刀RPA (ShadowBot)