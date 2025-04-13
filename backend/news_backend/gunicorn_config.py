
bind = "127.0.0.1:8000"  # 绑定IP和端口
workers = 4  # 建议设置为 CPU 核心数 * 2 + 1
worker_class = "sync"  # 也可以使用 "gevent" 或 "eventlet" 以获得更好的性能
timeout = 120  # 超时时间
accesslog = "/root/news_backend/logs/access.log"  # 访问日志
errorlog = "/root/news_backend/logs/error.log"  # 错误日志
loglevel = "info"  # 日志级别