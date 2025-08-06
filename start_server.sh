#!/bin/bash

# 启动wecomchan服务器的脚本

echo "🚀 启动wecomchan服务器..."

# 检查是否已经有服务器在运行
if pgrep -f "wecomchan_server.py" > /dev/null; then
    echo "⚠️ 检测到已有wecomchan服务器在运行，正在停止..."
    pkill -f "wecomchan_server.py"
    sleep 2
fi

# 检查端口5001是否被占用
if lsof -i :5001 > /dev/null 2>&1; then
    echo "⚠️ 端口5001被占用，正在释放..."
    lsof -ti :5001 | xargs kill -9
    sleep 2
fi

# 启动服务器
echo "📡 启动服务器在端口5001..."
cd wecomchan
nohup python3 wecomchan_server.py > ../wecomchan.log 2>&1 &

# 等待服务器启动
sleep 3

# 检查服务器状态
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ 服务器启动成功！"
    echo "📍 服务器地址: http://localhost:5001"
    echo "🔧 健康检查: http://localhost:5001/health"
    echo "📝 使用方法:"
    echo "   GET:  http://localhost:5001/?sendkey=set_a_sendkey&msg=消息内容"
    echo "   POST: http://localhost:5001/send (form-data: sendkey, msg)"
    echo "📋 日志文件: wecomchan.log"
else
    echo "❌ 服务器启动失败，请检查日志文件"
fi 