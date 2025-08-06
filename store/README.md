# 库存分析系统

## 项目概述
这是一个综合的库存分析系统，能够从多个数据库表格获取库存数据，按仓库类型聚合，生成报告并推送到企业微信。

## 主要功能

### 1. 数据源集成
- **wdt数据库**: 获取常规仓和顺丰仓库存数据
- **jinrongstore**: 获取金融仓数据（数量-已赎货）
- **rrsstore**: 获取云仓可用库存数据
- **tongstore**: 获取统仓数据
- **jdstore**: 获取京仓可用库存数据
- **matchstore**: 产品名称映射关系

### 2. 数据处理
- 统一产品名称（使用规格名称作为最终产品名）
- 按仓库类型聚合库存数据
- 计算合计数量和到仓位数量

### 3. 报告生成
- 生成HTML格式的库存分析报告
- 保存CSV格式的详细数据
- 支持英文文件名，避免URL编码问题

### 4. 部署功能
- 自动部署到EdgeOne Pages
- 严格验证URL可访问性
- 支持影刀RPA环境

### 5. 消息推送
- 企业微信消息推送
- CSV文件信息推送
- 在线报告链接推送

## 技术栈

- **Python 3.x**: 主要开发语言
- **PyMySQL**: 数据库连接和查询
- **Pandas**: 数据处理和聚合
- **Requests**: HTTP请求和URL验证
- **Subprocess**: CLI命令执行
- **EdgeOne CLI**: 静态网站部署
- **WecomChan**: 企业微信消息推送

## 配置说明

### 数据库配置
```python
DB_CONFIG_WDT = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'wdt',
    'charset': 'utf8mb4'
}

DB_CONFIG_DATE = {
    'host': '212.64.57.87',
    'user': 'root',
    'password': 'c973ee9b500cc638',
    'database': 'Date',
    'charset': 'utf8mb4'
}
```

### EdgeOne部署配置
```python
EDGEONE_CONFIG = {
    'cli_path': r"C:\Users\weicu\AppData\Roaming\npm\edgeone.cmd",
    'token': "YxsKLIORJJqehzWS0UlrPKr4qgMJjikkqdJwTQ/SOYc=",
    'project_name': "sales-report",
    'domain': "edge.haierht.cn"
}
```

### 企业微信配置
```python
WECOM_CONFIG = {
    'corpid': os.getenv('WECOM_CID', ''),
    'corpsecret': os.getenv('WECOM_SECRET', ''),
    'agentid': os.getenv('WECOM_AID', ''),
    'touser': os.getenv('WECOM_TOUID', 'weicungang')
}
```

## 使用说明

### 1. 环境要求
- Python 3.x
- EdgeOne CLI已安装
- 网络连接正常
- 数据库访问权限

### 2. 执行步骤
1. 运行脚本：`python3 库存分析脚本.py`
2. 脚本自动连接数据库并获取数据
3. 生成HTML报告和CSV文件
4. 部署到EdgeOne Pages
5. 推送消息到企业微信

### 3. 输出文件
- HTML报告：`inventory_analysis_YYYYMMDD_HHMMSS.html`
- CSV数据：`inventory_analysis_YYYYMMDD_HHMMSS.csv`
- 日志文件：`库存分析.log`

## 更新日志

### 2025-08-06 v3.0
- ✅ 修复URL中文编码问题，使用英文文件名
- ✅ 优化CSV文件推送，只发送文件信息不发送内容
- ✅ 保持报告内容为中文，只改文件名
- ✅ 确保URL可正常访问，解决404错误
- ✅ 完善部署验证机制

### 2025-08-06 v2.0
- ✅ 修复EdgeOne CLI命令参数格式
- ✅ 将文件名改为英文格式，避免URL编码问题
- ✅ 添加CSV文件推送到企业微信功能
- ✅ 完善URL验证机制，确保可访问性
- ✅ 优化影刀RPA环境兼容性

### 2025-08-06 v1.0
- ✅ 实现多数据库库存数据聚合
- ✅ 添加EdgeOne Pages部署功能
- ✅ 实现企业微信消息推送
- ✅ 添加严格URL验证机制

## 故障排除

### 1. EdgeOne部署问题
- 检查CLI路径是否正确
- 验证token是否有效
- 确认网络连接正常

### 2. 数据库连接问题
- 检查数据库服务器状态
- 验证连接参数是否正确
- 确认防火墙设置

### 3. 企业微信推送问题
- 检查WecomChan服务器状态
- 验证企业微信凭证
- 确认消息格式正确

## 注意事项

1. **文件名格式**: 使用英文文件名避免URL编码问题
2. **URL验证**: 严格验证确保URL可访问
3. **错误处理**: 完善的异常处理和日志记录
4. **重试机制**: URL验证最多重试5次
5. **超时设置**: 部署超时300秒，URL验证超时15秒
6. **内容语言**: 报告内容保持中文，只改文件名为英文

---

**最后更新时间**: 2025-08-06  
**版本**: 3.0  
**维护者**: AI Assistant