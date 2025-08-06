#!/bin/bash

# 设置环境变量
export WECHAT_CORP_ID="your_corp_id"
export WECHAT_CORP_SECRET="your_corp_secret"
export WECHAT_AGENT_ID="your_agent_id"
export MYSQL_HOST="localhost"
export MYSQL_PORT="3306"
export MYSQL_USER="root"
export MYSQL_PASSWORD="your_mysql_password"
export MYSQL_DATABASE="your_database"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖
pip install -r requirements.txt

# 运行主脚本
python main.py

echo "脚本执行完成"