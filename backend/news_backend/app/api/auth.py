# auth.py
from flask import current_app, request, jsonify, Blueprint
from app import db, mail
from app.models.user import User, UserRegistrationSchema, UserResponseSchema
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta
import hashlib

auth = Blueprint('auth', __name__)

verification_codes = {}
# 发送验证码的路由
@auth.route('/send_code', methods=['POST'])
def send_code():
    data = request.json
    email = data['email']
    if not email:
        return jsonify({'error': '邮箱不能为空'}), 400
    
    # 检查邮箱格式
    if not email.endswith('@qq.com'):
        return jsonify({'error': '请输入QQ邮箱'}), 400
    if verification_codes.get(email):
        return jsonify({'error': '请勿重复发送验证码'}), 400
    # 生成6位随机验证码
    code = ''.join(random.choices(string.digits, k=6))
    verification_codes[email] = {
        'code': code,
        'expires': datetime.now() + timedelta(minutes=5)
    }
    
    # 发送邮件
    msg = Message('验证码', 
                 sender=current_app.config['MAIL_USERNAME'],
                 recipients=[email])
    msg.body = f'您的验证码是：{code}，5分钟内有效。'
    
    try:
        mail.send(msg)
        return jsonify({'message': '验证码已发送', 'code': code}), 200
    except Exception as e:
        return jsonify({'error': '邮件发送失败'}), 500

@auth.route('/register', methods=['POST'])
def register():
    data = request.json
    errors = UserRegistrationSchema().validate(data)
    if errors:
        return jsonify({'error': errors}), 400
    
    email = data['email']
    stored_code = verification_codes.get(email)
    
    if not stored_code:
        return jsonify({'error': '请先获取验证码'}), 400
    
    if datetime.now() > stored_code['expires']:
        del verification_codes[email]
        return jsonify({'error': '验证码已过期'}), 400
    
    if data['verification_code'] != stored_code['code']:
        return jsonify({'error': '验证码错误'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 400
    
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    new_user = User(
        username=data['username'],
        email=email,
        password_hash=password_hash
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        del verification_codes[email]
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500


# 登陆用户的路由
@auth.route('/login/password', methods=['POST'])
def login():
    data = request.json
    if not data.get('identifier') or not data.get('password'):
        return jsonify({'error': '用户名/邮箱和密码不能为空'}), 400
    
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    user = User.query.filter(
        (User.username == data['identifier']) | 
        (User.email == data['identifier'])
    ).first()
    
    if not user or user.password_hash != password_hash:
        return jsonify({'error': '用户名/邮箱或密码错误'}), 401
    
    return jsonify({
        'message': '登录成功',
        'user': UserResponseSchema().dump(user)
    }), 200 

@auth.route('/login/code', methods=['POST'])
def login_with_code():
    data = request.json
    if not data.get('email') or not data.get('verification_code'):
        return jsonify({'error': '邮箱和验证码不能为空'}), 400
    
    email = data['email']
    stored_code = verification_codes.get(email)
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if not stored_code:
        return jsonify({'error': '请先获取验证码'}), 400
    
    if datetime.now() > stored_code['expires']:
        del verification_codes[email]
        return jsonify({'error': '验证码已过期'}), 400
    
    if data['verification_code'] != stored_code['code']:
        return jsonify({'error': '验证码错误'}), 400
    del verification_codes[email]
    
    return jsonify({
        'message': '登录成功',
        'user': UserResponseSchema().dump(user)
    }), 200 

    

