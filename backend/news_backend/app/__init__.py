from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail
import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

load_dotenv()

# 初始化Flask应用
app = Flask(__name__, static_folder='../static')
CORS(app)
# print("MAIL_PASSWORD from env:", os.environ.get("MAIL_PASSWORD"))

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@127.0.0.1/news_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # QQ邮箱
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # QQ邮箱授权码
app.config['MAIL_DEFAULT_SENDER'] = 'Anti-Fake'
db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)
# with app.app_context():
#     print("Dropping all tables...")
#     db.drop_all()
#     print("All tables dropped.")
#     print("Creating all tables...")
#     db.create_all()
#     print("All tables created.")
# 导入并注册蓝图
from app.api.auth import auth
app.register_blueprint(auth, url_prefix='/auth')

# 导入蓝图
from app.api.news_detection import news_detection_bp
app.register_blueprint(news_detection_bp, url_prefix='/news_detection')

from app.api.image_generation import image_generation_bp
app.register_blueprint(image_generation_bp,url_prefix='/image_generation')

from app.api.news_statistics import news_statistics_bp
app.register_blueprint(news_statistics_bp, url_prefix='/statistics')

# 导入新添加的蓝图
from app.api.news_title import news_title_bp
app.register_blueprint(news_title_bp, url_prefix='/news_title')

from app.api.news_summary import news_summary_bp
app.register_blueprint(news_summary_bp, url_prefix='/news_summary')

from app.api.text_optimization import text_optimization_bp
app.register_blueprint(text_optimization_bp, url_prefix='/text_optimization')

# 创建数据库表
with app.app_context():
    db.create_all()


