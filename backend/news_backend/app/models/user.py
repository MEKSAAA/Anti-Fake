from app import db, ma
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    wechat_openid = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    profile_image = db.Column(db.String(255))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    login_method = db.Column(db.String(20))
    
    # 关系: 添加反向引用给相关表
    detection_history = db.relationship('NewsDetectionHistory', backref='user', lazy=True)
    generation_history = db.relationship('NewsGenerationHistory', backref='user', lazy=True)
    summary_history = db.relationship('NewsSummaryHistory', backref='user', lazy=True)
    user_statistics = db.relationship('NewsStatisticsByUser', backref='user', lazy=True)
    
    def __init__(self, username, email=None, phone_number=None, wechat_openid=None,
                password_hash=None, profile_image=None, login_method=None, role_id=None):
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.wechat_openid = wechat_openid
        self.password_hash = password_hash
        self.profile_image = profile_image
        self.login_method = login_method
        self.role_id = role_id

# 创建Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'role_id', 'username', 'email', 'phone_number', 
                  'wechat_openid', 'profile_image', 'registration_date', 'login_method')

# 初始化schema
user_schema = UserSchema()
users_schema = UserSchema(many=True) 