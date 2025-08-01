// EdgeOne 边缘函数 - 代理到 Flask 服务器
// 解决 EdgeOne Pages 404 错误，将请求代理到后端 Flask 服务器

// Flask 服务器配置
const FLASK_SERVER = 'http://212.64.57.87:5002';

// 边缘函数入口
addeventListener('fetch', (event) => {
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

/**
 * 处理 OPTIONS 预检请求
 * @param {Request} request - 请求对象
 * @returns {Response} - CORS 响应
 */
function handleCORS(request) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    }
  });
}