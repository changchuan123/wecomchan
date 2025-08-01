# EdgeOne 边缘函数配置指南

## 问题描述
当前 EdgeOne Pages 部署后访问报告文件时返回 404 错误，这是因为 EdgeOne Pages 是静态网站托管服务，无法直接访问动态的 Flask 服务器内容。

## 解决方案
使用 EdgeOne 边缘函数创建代理，将请求转发到 Flask 服务器。

## 配置步骤

### 1. 登录 EdgeOne 控制台
访问：https://console.cloud.tencent.com/edgeone

### 2. 进入站点管理
- 选择您的站点（sales-report）
- 确保域名 `edge.haierht.cn` 已正确配置

### 3. 创建边缘函数

#### 3.1 进入边缘函数页面
- 点击左侧菜单 **"边缘函数"**
- 点击 **"新建函数"**

#### 3.2 基本信息配置
- **函数名称**: `flask-proxy`
- **描述**: `代理请求到 Flask 服务器，解决 EdgeOne Pages 404 错误`
- **运行时**: `JavaScript`

#### 3.3 函数代码
将以下代码复制到函数编辑器中：

```javascript
// EdgeOne 边缘函数 - 代理到 Flask 服务器
// 解决 EdgeOne Pages 404 错误，将请求代理到后端 Flask 服务器

// Flask 服务器配置
const FLASK_SERVER = 'http://212.64.57.87:5002';

// 边缘函数入口
addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event));
});

/**
 * 处理请求的主函数
 * @param {FetchEvent} event - 请求事件
 * @returns {Promise<Response>} - 响应
 */
async function handleRequest(event) {
  const { request } = event;
  const url = new URL(request.url);
  
  try {
    // 构建代理到 Flask 服务器的 URL
    const proxyUrl = `${FLASK_SERVER}${url.pathname}${url.search}`;
    
    console.log(`代理请求: ${request.url} -> ${proxyUrl}`);
    
    // 创建新的请求，保持原始请求的方法、头部和 body
    const proxyRequest = new Request(proxyUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: 'follow'
    });
    
    // 发起代理请求到 Flask 服务器
    const response = await fetch(proxyRequest, {
      eo: {
        timeoutSetting: {
          connectTimeout: 30000,  // 30秒连接超时
          readTimeout: 30000,     // 30秒读取超时
          writeTimeout: 30000     // 30秒写入超时
        }
      }
    });
    
    // 创建新的响应，保持原始响应的状态和头部
    const modifiedResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
    
    // 添加 CORS 头部（如果需要）
    modifiedResponse.headers.set('Access-Control-Allow-Origin', '*');
    modifiedResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    modifiedResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    console.log(`代理响应状态: ${response.status}`);
    
    return modifiedResponse;
    
  } catch (error) {
    console.error('代理请求失败:', error);
    
    // 返回错误响应
    return new Response(
      JSON.stringify({
        error: '代理服务器错误',
        message: error.message,
        timestamp: new Date().toISOString()
      }),
      {
        status: 502,
        statusText: 'Bad Gateway',
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    );
  }
}
```

#### 3.4 触发规则配置
- **触发条件**: URL 路径
- **匹配模式**: `/*` （匹配所有路径）
- **HTTP 方法**: 选择 `全部` 或 `GET, POST, PUT, DELETE, OPTIONS`

#### 3.5 环境变量（可选）
如果需要，可以添加环境变量：
- `FLASK_SERVER`: `http://212.64.57.87:5002`

### 4. 保存并发布
- 点击 **"保存"**
- 点击 **"发布"**
- 等待函数部署完成（通常需要几分钟）

### 5. 验证部署

#### 5.1 测试访问
访问以下 URL 验证是否正常工作：
- https://edge.haierht.cn/reports/
- https://edge.haierht.cn/reports/overall_daily_2025-07-29_101349.html

#### 5.2 检查日志
在 EdgeOne 控制台的边缘函数页面，可以查看函数执行日志，确认代理是否正常工作。

## 故障排除

### 问题1：函数部署失败
- 检查代码语法是否正确
- 确保触发规则配置正确
- 查看部署日志获取详细错误信息

### 问题2：代理请求失败
- 确认 Flask 服务器 `212.64.57.87:5002` 正常运行
- 检查网络连接是否正常
- 查看边缘函数执行日志

### 问题3：仍然返回 404
- 确认边缘函数已成功发布
- 检查触发规则是否匹配请求路径
- 等待 CDN 缓存刷新（可能需要几分钟）

### 问题4：CORS 错误
- 确认代码中已添加 CORS 头部
- 检查浏览器开发者工具的网络请求

## 注意事项

1. **性能考虑**: 边缘函数会增加一定的延迟，但可以提供更好的全球访问体验
2. **成本考虑**: EdgeOne 边缘函数按请求次数计费，请关注使用量
3. **安全考虑**: 确保 Flask 服务器的安全配置，避免暴露敏感信息
4. **监控**: 定期检查边缘函数的执行日志和性能指标

## 替代方案

如果边缘函数方案不适用，可以考虑：
1. 直接使用 Flask 服务器，不通过 EdgeOne
2. 将报告生成为静态文件，直接部署到 EdgeOne Pages
3. 使用其他 CDN 服务的代理功能

## 联系支持

如果遇到问题，可以：
1. 查看 EdgeOne 官方文档
2. 联系腾讯云技术支持
3. 在相关技术社区寻求帮助

---

**配置完成后，EdgeOne 域名应该能够正常代理到 Flask 服务器，解决 404 错误问题。**