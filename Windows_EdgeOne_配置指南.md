# Windows 环境 EdgeOne CLI 配置指南

## 问题描述

在Windows电脑执行EdgeOne Pages部署时遇到报错，通常是因为EdgeOne CLI未正确安装或配置。

## 🚀 快速解决方案（推荐）

### 方法一：使用自动化工具（最简单）

项目提供了完整的自动化诊断和修复工具：

#### 1. 环境诊断工具
```cmd
# 运行诊断工具，检查所有配置问题
windows_edgeone_diagnostic.bat
```

**功能特点**：
- ✅ 检查Node.js和npm环境
- ✅ 检查EdgeOne CLI安装状态
- ✅ 检查网络连接
- ✅ 检查项目文件结构
- ✅ 检查环境变量配置
- ✅ 生成详细的诊断报告和修复建议

#### 2. 一键修复工具
```cmd
# 以管理员身份运行修复工具
# 右键点击 → "以管理员身份运行"
windows_edgeone_fix.bat
```

**功能特点**：
- 🔧 自动安装EdgeOne CLI
- 🔧 配置npm镜像源
- 🔧 设置PowerShell执行策略
- 🔧 创建项目目录结构
- 🔧 生成EdgeOne配置文件
- 🔧 设置环境变量
- 🔧 创建测试文件
- 🔧 验证部署功能

#### 3. 使用步骤

```cmd
# 1. 诊断当前环境
windows_edgeone_diagnostic.bat

# 2. 如果诊断评分低于3分，运行修复工具
# 右键点击 → "以管理员身份运行"
windows_edgeone_fix.bat

# 3. 验证修复结果
windows_edgeone_diagnostic.bat

# 4. 开始部署
deploy_to_edgeone.bat
```

### 方法二：手动配置（备用方案）

如果自动化工具无法使用，请按以下步骤手动配置：

## 手动配置步骤

### 第一步：安装Node.js

EdgeOne CLI需要Node.js环境支持。

1. **下载Node.js**
   - 访问 [Node.js官网](https://nodejs.org/)
   - 下载LTS版本（推荐）
   - 选择Windows Installer (.msi)

2. **安装Node.js**
   - 运行下载的.msi文件
   - 按默认设置安装
   - 确保勾选"Add to PATH"选项

3. **验证安装**
   ```cmd
   node --version
   npm --version
   ```

### 第二步：安装EdgeOne CLI

1. **使用npm安装**
   ```cmd
   npm install -g @edgeone/cli
   ```

2. **如果安装失败，尝试使用淘宝镜像**
   ```cmd
   npm config set registry https://registry.npmmirror.com
   npm install -g @edgeone/cli
   ```

3. **验证安装**
   ```cmd
   edgeone --version
   ```

### 第三步：配置环境变量（如果需要）

如果`edgeone --version`命令失败，需要手动配置PATH：

1. **找到EdgeOne CLI安装路径**
   - 通常在：`C:\Users\[用户名]\AppData\Roaming\npm\`
   - 或者：`C:\Program Files\nodejs\`

2. **添加到系统PATH**
   - 右键"此电脑" → "属性"
   - 点击"高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"
   - 点击"编辑" → "新建"
   - 添加EdgeOne CLI的安装路径
   - 点击"确定"保存

3. **重启命令提示符**
   - 关闭当前cmd窗口
   - 重新打开cmd
   - 再次验证：`edgeone --version`

### 第四步：配置EdgeOne项目

1. **创建项目配置目录**
   ```cmd
   mkdir .edgeone
   ```

2. **创建项目配置文件**
   在`.edgeone`目录下创建`project.json`文件：
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

### 第五步：使用Windows部署脚本

项目已提供Windows专用的部署脚本：

1. **使用批处理脚本**
   ```cmd
   deploy_to_edgeone.bat
   ```

2. **或使用Python脚本**
   ```cmd
   python deploy_to_edgeone.py
   ```

## 常见问题解决

### 问题1："edgeone不是内部或外部命令"

**错误信息**：
```
'edgeone' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

**原因**：EdgeOne CLI未安装或PATH配置错误

**解决方案**：
```cmd
# 1. 检查Node.js是否安装
node --version
npm --version

# 2. 重新安装EdgeOne CLI
npm uninstall -g @edgeone/cli
npm install -g @edgeone/cli

# 3. 验证安装
edgeone --version

# 4. 如果仍然失败，手动查找安装路径
where edgeone
dir "C:\Users\%USERNAME%\AppData\Roaming\npm" | findstr edgeone
```

### 问题2：npm安装失败

**错误信息**：
```
npm ERR! code EACCES
npm ERR! syscall mkdir
npm ERR! path C:\Users\xxx\AppData\Roaming\npm
npm ERR! errno -4048
```

**原因**：权限问题或网络问题

**解决方案**：
```cmd
# 1. 以管理员身份运行命令提示符
# 右键点击"命令提示符" → "以管理员身份运行"

# 2. 配置npm镜像源（解决网络问题）
npm config set registry https://registry.npmmirror.com
npm config set @edgeone:registry https://registry.npmjs.org

# 3. 清理npm缓存
npm cache clean --force

# 4. 重新安装
npm install -g @edgeone/cli

# 5. 恢复默认镜像源（可选）
npm config set registry https://registry.npmjs.org
```

### 问题3：EdgeOne CLI安装成功但无法运行

**错误信息**：
```
C:\Users\xxx\AppData\Roaming\npm\edgeone.ps1 无法加载，因为在此系统上禁止运行脚本
```

**原因**：PowerShell执行策略限制

**解决方案**：
```powershell
# 1. 以管理员身份运行PowerShell
# 右键点击"Windows PowerShell" → "以管理员身份运行"

# 2. 修改执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. 确认修改
Y

# 4. 验证EdgeOne CLI
edgeone --version
```

### 问题4：部署时Token认证失败

**错误信息**：
```
Error: Authentication failed. Please check your token.
```

**原因**：EdgeOne Token配置错误或过期

**解决方案**：
```cmd
# 1. 检查Token是否正确设置
echo %EDGEONE_TOKEN%

# 2. 重新设置Token（临时）
set EDGEONE_TOKEN=YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=

# 3. 或者在脚本中直接使用Token
edgeone pages deploy .\reports -n sales-report -t YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=
```

### 问题5：部署超时或网络错误

**错误信息**：
```
Error: Request timeout
Error: connect ETIMEDOUT
```

**原因**：网络连接问题或防火墙阻止

**解决方案**：
```cmd
# 1. 检查网络连接
ping edgeone.ai
ping pages.edgeone.ai

# 2. 配置代理（如果使用代理）
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080

# 3. 临时关闭防火墙测试
# Windows Defender防火墙 → 关闭防火墙（测试后记得开启）

# 4. 使用VPN或更换网络环境
```

### 问题6：reports目录不存在或为空

**错误信息**：
```
Error: No files found in reports directory
❌ reports 目录不存在
```

**原因**：部署目录配置错误或文件未生成

**解决方案**：
```cmd
# 1. 检查当前目录
dir

# 2. 创建reports目录
mkdir reports

# 3. 检查是否有HTML文件
dir reports\*.html

# 4. 如果没有文件，先运行报告生成脚本
python 整体日报数据.py

# 5. 再次检查
dir reports\*.html
```

### 问题7：项目配置文件缺失

**错误信息**：
```
⚠️ 缺少EdgeOne项目配置文件: .edgeone/project.json
```

**原因**：EdgeOne项目配置文件未创建

**解决方案**：
```cmd
# 1. 创建.edgeone目录
mkdir .edgeone

# 2. 创建project.json文件
echo {
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
} > .edgeone\project.json
```

## 验证配置

完成配置后，运行以下命令验证：

```cmd
# 检查Node.js
node --version

# 检查npm
npm --version

# 检查EdgeOne CLI
edgeone --version

# 检查项目配置
dir .edgeone
type .edgeone\project.json

# 测试部署（如果有reports目录）
edgeone pages deploy .\reports -n sales-report -t YOUR_TOKEN
```

## 💡 手动配置脚本（备用方案）

如果自动化工具无法使用，可以使用以下PowerShell脚本：

```powershell
# Windows EdgeOne 手动配置脚本
# 以管理员身份运行PowerShell

# 检查Node.js
if (!(Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js未安装，请先安装Node.js" -ForegroundColor Red
    Start-Process "https://nodejs.org/"
    exit 1
}

# 配置npm镜像源
npm config set registry https://registry.npmmirror.com

# 安装EdgeOne CLI
Write-Host "🔧 安装EdgeOne CLI..." -ForegroundColor Yellow
npm install -g @edgeone/cli

# 配置PowerShell执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 验证安装
if (Get-Command "edgeone" -ErrorAction SilentlyContinue) {
    Write-Host "✅ EdgeOne CLI安装成功" -ForegroundColor Green
    edgeone --version
} else {
    Write-Host "❌ EdgeOne CLI安装失败" -ForegroundColor Red
    exit 1
}

# 创建项目配置
if (!(Test-Path ".edgeone")) {
    New-Item -ItemType Directory -Path ".edgeone"
    Write-Host "📁 创建.edgeone目录" -ForegroundColor Green
}

# 恢复npm镜像源
npm config set registry https://registry.npmjs.org

Write-Host "🎉 配置完成！" -ForegroundColor Green
Write-Host "现在可以运行: deploy_to_edgeone.bat" -ForegroundColor Cyan
```

## 联系支持

如果仍然遇到问题：

1. 首先运行诊断工具：`windows_edgeone_diagnostic.bat`
2. 尝试一键修复工具：`windows_edgeone_fix.bat`
3. 检查Windows版本兼容性
4. 尝试在不同的命令行工具中运行（cmd、PowerShell、Git Bash）
5. 查看EdgeOne官方文档
6. 联系技术支持

---

**注意**：确保Windows系统已安装最新的更新，某些旧版本可能存在兼容性问题。建议优先使用自动化工具进行配置和修复。