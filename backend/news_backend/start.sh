#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动MySQL数据库
service mysql start

# 在后台启动主应用
nohup python run.py > flask_app.log 2>&1 &
FLASK_PID=$!
echo "主应用已启动，PID: $FLASK_PID"

echo "启动deepfake微服务..."
# 激活conda环境
source ~/miniconda3/etc/profile.d/conda.sh

# 使用 Bash 启动子进程来激活 conda 环境
bash -i -c "conda activate DGM4; cd ~/deepfake && python deepfake_service.py > deepfake_service.log 2>&1 &"
# 等待2秒让服务启动
sleep 2

# 使用pgrep查找实际的deepfake服务PID
DEEPFAKE_PID=$(pgrep -f "python.*deepfake_service.py")
if [ -n "$DEEPFAKE_PID" ]; then
    echo "deepfake微服务已启动，PID: $DEEPFAKE_PID"
    echo $DEEPFAKE_PID > ~/deepfake.pid
else
    echo "警告：未找到运行中的deepfake服务，请检查日志"
fi

echo "所有服务已启动"
echo "主应用日志: flask_app.log"
echo "deepfake微服务日志: deepfake_service.log"

# 保存PID到文件，方便之后关闭服务
# echo $FLASK_PID > ~/flask.pid
# echo $DEEPFAKE_PID > ~/deepfake.pid

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
