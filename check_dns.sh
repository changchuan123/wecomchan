#!/bin/bash

echo "🔍 检查DNS解析和网络连接"
echo "========================="

SERVER_IP="212.64.57.87"
SERVER_PORT="5001"

# 检查DNS解析
echo "1️⃣ 检查DNS解析..."
if nslookup $SERVER_IP > /dev/null 2>&1; then
    echo "✅ DNS解析正常"
else
    echo "⚠️ DNS解析可能有问题，但IP地址应该直接可用"
fi

# 检查网络连通性
echo "2️⃣ 检查网络连通性..."
if ping -c 3 $SERVER_IP > /dev/null 2>&1; then
    echo "✅ 网络连通正常"
else
    echo "❌ 网络连通失败"
    exit 1
fi

# 检查端口连通性
echo "3️⃣ 检查端口连通性..."
if nc -z $SERVER_IP $SERVER_PORT 2>/dev/null; then
    echo "✅ 端口 $SERVER_PORT 连通正常"
else
    echo "❌ 端口 $SERVER_PORT 连通失败"
    echo "可能原因："
    echo "  - 服务未启动"
    echo "  - 防火墙阻止"
    echo "  - 安全组未开放"
fi

# 尝试HTTP请求
echo "4️⃣ 尝试HTTP请求..."
if curl -s --connect-timeout 5 "http://$SERVER_IP:$SERVER_PORT/health" > /dev/null; then
    echo "✅ HTTP请求成功"
    echo "📊 服务响应："
    curl -s "http://$SERVER_IP:$SERVER_PORT/health" | python3 -m json.tool 2>/dev/null || curl -s "http://$SERVER_IP:$SERVER_PORT/health"
else
    echo "❌ HTTP请求失败"
fi

echo ""
echo "🎯 建议检查项目："
echo "  - 腾讯云安全组是否开放TCP:5001"
echo "  - 服务器本地防火墙设置"
echo "  - 服务是否正常运行" 