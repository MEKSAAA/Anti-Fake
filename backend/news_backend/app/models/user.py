from app import db, ma
from datetime import datetime
from marshmallow import validate
from marshmallow import ValidationError

def validate_qq_email(email):
    if not email.endswith('@qq.com'):
        raise ValidationError('请输入QQ邮箱')

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    # profile_image = db.Column(db.String(255))
    
    # 关系: 添加反向引用给相关表
    detection_history = db.relationship('NewsDetectionHistory', backref='user', lazy=True)
    generation_history = db.relationship('NewsGenerationHistory', backref='user', lazy=True)
    summary_history = db.relationship('NewsSummaryHistory', backref='user', lazy=True)
    user_statistics = db.relationship('NewsStatisticsByUser', backref='user', lazy=True)
    
    def __init__(self, username, email=None, phone_number=None, wechat_openid=None,
                password_hash=None, profile_image=None, login_method=None, role_id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.profile_image = profile_image

# 用于用户注册的 Schema，只包含必要字段
class UserRegistrationSchema(ma.Schema):
    username = ma.String(required=True, validate=validate.Length(min=3, max=20))
    email = ma.Email(required=True, validate=[validate.Email(), validate_qq_email])
    password = ma.String(required=True, validate=validate.Length(min=6))
    verification_code = ma.String(required=True, validate=validate.Length(equal=6))
    class Meta:
        fields = ('username', 'email', 'password', 'verification_code')

class UserResponseSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'username', 'email')

# 初始化 schemas
user_registration_schema = UserRegistrationSchema()
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True) 
