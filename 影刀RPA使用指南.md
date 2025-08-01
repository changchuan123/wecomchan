# 影刀RPA数据库上传使用指南

## 概述
本指南说明如何在Windows环境下通过影刀RPA程序运行数据库上传脚本，实现自动化数据导入功能。

## 系统要求

### 硬件要求
- **操作系统**: Windows 10/11
- **内存**: 至少4GB RAM（推荐8GB以上）
- **存储**: 至少2GB可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **Node.js**: 版本14.0或更高
- **影刀RPA**: 最新版本
- **Excel文件**: 待上传的数据文件

## 安装配置

### 1. 安装Node.js
```bash
# 下载并安装Node.js
# 访问 https://nodejs.org/ 下载Windows版本
# 安装时选择"Add to PATH"选项
```

### 2. 验证安装
```bash
# 打开命令提示符，验证Node.js安装
node --version
npm --version
```

### 3. 准备脚本文件
确保以下文件在同一目录：
- `数据库上传_影刀版.js` - 主脚本文件
- `config.js` - 配置文件
- `影刀运行脚本.bat` - Windows启动脚本

## 影刀RPA配置

### 1. 创建影刀项目
1. 打开影刀RPA设计器
2. 创建新项目
3. 设置项目名称为"数据库上传自动化"

### 2. 添加执行步骤
在影刀流程中添加以下步骤：

#### 步骤1: 环境检查
```javascript
// 检查Node.js环境
const { exec } = require('child_process');
exec('node --version', (error, stdout, stderr) => {
    if (error) {
        console.log('❌ Node.js未安装');
        return false;
    }
    console.log('✅ Node.js版本:', stdout);
    return true;
});
```

#### 步骤2: 文件检查
```javascript
// 检查必要文件是否存在
const fs = require('fs');
const requiredFiles = [
    '数据库上传_影刀版.js',
    'config.js',
    '影刀运行脚本.bat'
];

for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
        console.log(`❌ 缺少文件: ${file}`);
        return false;
    }
}
console.log('✅ 所有必要文件检查通过');
```

#### 步骤3: 执行数据库上传
```javascript
// 执行数据库上传脚本
const { spawn } = require('child_process');

const child = spawn('node', ['数据库上传_影刀版.js'], {
    stdio: 'pipe',
    env: {
        ...process.env,
        NODE_OPTIONS: '--max-old-space-size=2048 --expose-gc'
    }
});

child.stdout.on('data', (data) => {
    console.log(`📊 输出: ${data}`);
});

child.stderr.on('data', (data) => {
    console.error(`❌ 错误: ${data}`);
});

child.on('close', (code) => {
    console.log(`🎉 脚本执行完成，退出码: ${code}`);
});
```

### 3. 错误处理
添加错误处理步骤：

```javascript
// 错误处理逻辑
try {
    // 执行数据库上传
    const result = await executeDatabaseUpload();
    
    if (result.success) {
        console.log('✅ 数据库上传成功');
        // 发送成功通知
        await sendSuccessNotification(result);
    } else {
        console.log('❌ 数据库上传失败');
        // 发送失败通知
        await sendFailureNotification(result.error);
    }
} catch (error) {
    console.error('💥 执行过程中发生错误:', error);
    // 发送错误通知
    await sendErrorNotification(error);
}
```

## 运行方式

### 方式1: 直接运行脚本
```bash
# 在命令提示符中运行
node 数据库上传_影刀版.js
```

### 方式2: 使用批处理文件
```bash
# 双击运行批处理文件
影刀运行脚本.bat
```

### 方式3: 通过影刀RPA
1. 在影刀RPA中打开项目
2. 点击"运行"按钮
3. 监控执行过程

## 监控和日志

### 1. 实时监控
脚本运行时会输出详细的执行信息：
- 📊 性能统计
- 💾 内存使用情况
- ⏱️ 执行时间
- ✅ 成功/失败记录

### 2. 日志文件
脚本会自动生成日志文件：
- `upload_log_YYYYMMDD_HHMMSS.txt`
- 包含详细的执行记录
- 错误信息和调试信息

### 3. 企业微信通知
- 成功时发送成功报告
- 失败时发送错误报告
- 包含详细的执行统计

## 故障排除

### 常见问题

#### 1. "Maximum call stack size exceeded"错误
**原因**: 内存使用过多或递归调用
**解决方案**: 
- 检查数据量是否过大
- 重启影刀程序
- 清理临时文件

#### 2. 数据库连接失败
**原因**: 网络问题或数据库配置错误
**解决方案**:
- 检查网络连接
- 验证数据库配置
- 确认数据库服务状态

#### 3. 文件读取失败
**原因**: 文件路径错误或权限问题
**解决方案**:
- 检查文件路径
- 确认文件权限
- 验证文件格式

### 性能优化

#### 1. 内存优化
```javascript
// 启用垃圾回收
if (global.gc) {
    global.gc();
}
```

#### 2. 批量处理优化
```javascript
// 降低批量大小
batchSize: 100, // 从1000降低到100
```

#### 3. 并发控制
```javascript
// 限制并发数量
maxConcurrentBatches: 2,
```

## 安全注意事项

### 1. 数据安全
- 确保数据库连接使用加密
- 定期备份重要数据
- 限制数据库访问权限

### 2. 网络安全
- 使用VPN连接（如需要）
- 定期更新安全补丁
- 监控异常访问

### 3. 系统安全
- 定期更新影刀RPA
- 使用最新版本的Node.js
- 定期清理临时文件

## 维护和更新

### 1. 定期维护
- 每周检查日志文件
- 每月清理临时文件
- 每季度更新依赖包

### 2. 版本更新
- 关注Node.js更新
- 更新影刀RPA版本
- 测试新版本兼容性

### 3. 性能监控
- 监控内存使用情况
- 跟踪执行时间
- 分析错误率

## 联系支持

如遇到问题，请提供以下信息：
1. 错误日志
2. 系统环境信息
3. 执行步骤描述
4. 预期结果和实际结果

---

**版本**: 1.0  
**更新日期**: 2025年7月31日  
**适用环境**: Windows + 影刀RPA 