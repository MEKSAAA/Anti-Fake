#!/bin/bash

echo "停止所有服务..."

# 停止主应用
if [ -f ~/flask.pid ]; then
    FLASK_PID=$(cat ~/flask.pid)
    kill -9 $FLASK_PID 2>/dev/null || true
    rm ~/flask.pid
    echo "已停止主应用，PID: $FLASK_PID"
else
    # 如果PID文件不存在，尝试通过进程名查找
    FLASK_PID=$(pgrep -f "python.*run.py")
    if [ -n "$FLASK_PID" ]; then
        kill -9 $FLASK_PID 2>/dev/null || true
        echo "已停止主应用，PID: $FLASK_PID"
    fi
fi

# 停止deepfake微服务
if [ -f ~/deepfake.pid ]; then
    DEEPFAKE_PID=$(cat ~/deepfake.pid)
    kill -9 $DEEPFAKE_PID 2>/dev/null || true
    rm ~/deepfake.pid
    echo "已停止deepfake微服务，PID: $DEEPFAKE_PID"
else
    # 如果PID文件不存在，尝试通过进程名查找
    DEEPFAKE_PID=$(pgrep -f "python.*deepfake_service.py")
    if [ -n "$DEEPFAKE_PID" ]; then
        kill -9 $DEEPFAKE_PID 2>/dev/null || true
        echo "已停止deepfake微服务，PID: $DEEPFAKE_PID"
    fi
fi

# 确保所有Python进程都已终止（可选，谨慎使用）
# pkill -9 -f "python.*run.py" 2>/dev/null || true
# pkill -9 -f "python.*deepfake_service.py" 2>/dev/null || true

# 停止MySQL
service mysql stop

echo "所有服务已停止"