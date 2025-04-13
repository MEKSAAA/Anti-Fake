# 新闻分析后端

本项目是一个基于Flask+MySQL+Nginx+Gunicorn的新闻分析后端系统。

## 项目结构

```
news_backend/
├── app/                  # 应用代码
│   ├── __init__.py       # 应用初始化
│   ├── models/           # 数据模型
│   ├── static/           # 静态文件
│   ├── templates/        # 模板文件
│   └── api/              # API路由
├── venv/                 # 虚拟环境
├── run.py                # 应用运行入口
├── gunicorn_config.py    # gunicorn配置
└── nginx_config          # Nginx配置
```

## 使用步骤
直接运行 ./start.sh
### 1. 初始化和运行数据库

```bash
source venv/bin/activate
service mysql start

```

### 2. 运行Flask应用

```bash
# 开发模式运行
python run.py
```

### 3. 使用gunicorn和Nginx部署
autodl里说：
>注意：开放端口需要进行企业认证，认证入口在【控制台】→【账号】→【账号安全】，如果您是个人用户可选择使用SSH隧道工具代理任意端口到本地访问
>
> 由于实例无独立公网IP，因此不能开放任意端口。但是AutoDL为每个实例的6006端口都映射了一个可公网访问的地址，也就是将实例中的6006端口映射到公网可供访问的ip:port上，映射的协议支持TCP或HTTP，协议可自行选择，ip:port可在「自定义服务」入口获取：
```bash
gunicorn -c gunicorn_config.py run:app

# 停止
# uwsgi --stop /root/news_backend/uwsgi.pid

# 配置并重启Nginx
sudo ln -sf /root/news_backend/nginx_config /etc/nginx/sites-available/news_app
sudo ln -sf /etc/nginx/sites-available/news_app /etc/nginx/sites-enabled/
sudo service nginx restart
```

```