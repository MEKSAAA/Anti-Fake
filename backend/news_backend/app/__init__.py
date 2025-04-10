from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail

# 初始化Flask应用
app = Flask(__name__)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/news_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '1449235503@qq.com'  # QQ邮箱
app.config['MAIL_PASSWORD'] = 'tonnxnzjenambafi'  # QQ邮箱授权码
app.config['MAIL_DEFAULT_SENDER'] = 'Anti-Fake  <1449235503@qq.com>'
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

    



