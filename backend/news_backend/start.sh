#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动MySQL数据库
service mysql start

python run.py
# 先确保Nginx已停止
# nginx -s stop 2>/dev/null || true

# # 检查Nginx配置是否正确
# echo "检查Nginx配置..."
# nginx -t

# # 启动Nginx
# echo "启动Nginx..."
# nginx

# # 停止可能已运行的旧进程
# pkill gunicorn 2>/dev/null || true

# # 启动Gunicorn
# echo "启动Gunicorn..."
# gunicorn -c gunicorn_config.py run:app

# echo "所有服务已启动"
