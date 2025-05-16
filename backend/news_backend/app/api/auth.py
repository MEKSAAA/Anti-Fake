# auth.py
from flask import current_app, request, Blueprint, url_for
from app import db, mail
from app.models.user import User, UserRegistrationSchema, UserResponseSchema
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta
import os
from app.utils.common import api_response
from app.services.auth_service import hash_password, verify_password
from app.utils.file_util import ensure_dir, allowed_file
auth = Blueprint('auth', __name__)

# 验证码存储(邮箱 -> {code, expires})
VERIFICATION_CODES = {}

# def hash_password(password):
#     salt = secrets.token_hex(16)
#     password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
#     return f"{password_hash}:{salt}"

# def verify_password(stored_hash, provided_password):
#     if ':' not in stored_hash:
#         return stored_hash == hashlib.sha256(provided_password.encode()).hexdigest()
    
#     hash_val, salt = stored_hash.split(':')
#     provided_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
#     return hash_val == provided_hash

# def ensure_dir(dir_path):
#     if not os.path.exists(dir_path):
#         os.makedirs(dir_path)
#     return dir_path

# def allowed_file(filename):
#     ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/send_code', methods=['POST'])
def send_code():
    """
    发送验证码到用户邮箱
    
    参数(JSON):
        email (str): 用户邮箱地址
    
    返回:
        JSON: 包含状态和消息的响应
        
    异常:
        400: 邮箱格式错误或验证码已发送
        500: 邮件发送失败
    """
    data = request.json
    email = data.get('email')
    
    if not email:
        return api_response(False, "邮箱不能为空", status_code=400)
    
    # 检查邮箱格式
    if not email.endswith('@qq.com'):
        return api_response(False, "请输入QQ邮箱", status_code=400)
        
    if VERIFICATION_CODES.get(email):
        if datetime.now() > VERIFICATION_CODES[email]['expires']:
            del VERIFICATION_CODES[email]
        else:
            return api_response(False, "请勿重复发送验证码", status_code=400)        
        
    # 生成6位随机验证码
    code = ''.join(random.choices(string.digits, k=6))
    VERIFICATION_CODES[email] = {
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
        return api_response(True, "验证码已发送", {"code": code})
    except Exception as e:
        return api_response(False, "邮件发送失败", status_code=500)

@auth.route('/register', methods=['POST'])
def register():
    """
    用户注册
    
    参数(JSON):
        username (str): 用户名
        email (str): 邮箱
        password (str): 密码
        verification_code (str): 验证码
    
    返回:
        JSON: 包含状态和消息的响应
        
    异常:
        400: 数据验证失败、验证码错误、用户名/邮箱已存在
        500: 注册失败
    """
    data = request.json
    errors = UserRegistrationSchema().validate(data)
    if errors:
        return api_response(False, "数据验证失败", errors, status_code=400)
    
    email = data['email']
    stored_code = VERIFICATION_CODES.get(email)
    
    if not stored_code:
        return api_response(False, "请先获取验证码", status_code=400)
    
    if datetime.now() > stored_code['expires']:
        del VERIFICATION_CODES[email]
        return api_response(False, "验证码已过期", status_code=400)
    
    if data['verification_code'] != stored_code['code']:
        return api_response(False, "验证码错误", status_code=400)
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return api_response(False, "用户名已存在", status_code=400)
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return api_response(False, "邮箱已被注册", status_code=400)
    
    password_hash = hash_password(data['password'])
    
    new_user = User(
        username=data['username'],
        email=email,
        password_hash=password_hash
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        del VERIFICATION_CODES[email]
        return api_response(True, "注册成功", status_code=201)
    except Exception as e:
        db.session.rollback()
        return api_response(False, "注册失败", status_code=500)


@auth.route('/login/password', methods=['POST'])
def login():
    """
    用户密码登录
    
    参数(JSON):
        identifier (str): 用户名或邮箱
        password (str): 密码
    
    返回:
        JSON: 包含用户信息的响应
        
    异常:
        400: 参数不完整
        401: 用户名/邮箱或密码错误
    """
    data = request.json
    if not data.get('identifier') or not data.get('password'):
        return api_response(False, "用户名/邮箱和密码不能为空", status_code=400)
    
    user = User.query.filter(
        (User.username == data['identifier']) | 
        (User.email == data['identifier'])
    ).first()
    
    if not user or not verify_password(user.password_hash, data['password']):
        return api_response(False, "用户名/邮箱或密码错误", status_code=401)
    
    return api_response(
        True, 
        "登录成功", 
        {
            "user": UserResponseSchema().dump(user)
        }
    )

@auth.route('/login/code', methods=['POST'])
def login_with_code():
    """
    用户验证码登录
    
    参数(JSON):
        email (str): 邮箱
        verification_code (str): 验证码
    
    返回:
        JSON: 包含用户信息的响应
        
    异常:
        400: 参数不完整、验证码错误
        404: 用户不存在
    """
    data = request.json
    if not data.get('email') or not data.get('verification_code'):
        return api_response(False, "邮箱和验证码不能为空", status_code=400)
    
    email = data['email']
    stored_code = VERIFICATION_CODES.get(email)
    user = User.query.filter_by(email=email).first()
    if not user:
        return api_response(False, "用户不存在", status_code=404)
    
    if not stored_code:
        return api_response(False, "请先获取验证码", status_code=400)
    
    if datetime.now() > stored_code['expires']:
        del VERIFICATION_CODES[email]
        return api_response(False, "验证码已过期", status_code=400)
    
    if data['verification_code'] != stored_code['code']:
        return api_response(False, "验证码错误", status_code=400)
    del VERIFICATION_CODES[email]
    
    return api_response(
        True,
        "登录成功",
        {
            "user": UserResponseSchema().dump(user)
        }
    )

@auth.route('/update/user_name', methods=['POST'])
def update_user_name():
    """
    更新用户名
    
    参数(JSON):
        user_id (int): 用户ID
        new_user_name (str): 新用户名
    
    返回:
        JSON: 包含更新后的用户信息的响应
        
    异常:
        400: 参数不完整、用户名不符合要求或已被使用
        404: 用户不存在
        500: 更新失败
    """
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return api_response(False, "用户ID不能为空", status_code=400)
    
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return api_response(False, "用户不存在", status_code=404)

    new_user_name = data.get('new_user_name')
    if not new_user_name:
        return api_response(False, "新用户名不能为空", status_code=400)
    if len(new_user_name) < 3 or len(new_user_name) > 20:
        return api_response(False, "用户名长度必须在3-20个字符之间", status_code=400)

    if user.username == new_user_name:
        return api_response(False, "新用户名不能与当前用户名相同", status_code=400)
    
    existing_user = User.query.filter_by(username=new_user_name).first()
    if existing_user and existing_user.user_id != user.user_id:
        return api_response(False, "该用户名已被使用", status_code=400)
    
    old_username = user.username
    user.username = new_user_name
    try:
        db.session.commit()
        return api_response(True, "用户名更新成功", {
            "user": UserResponseSchema().dump(user)        })
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"用户名更新失败: {str(e)}", status_code=500)
    
@auth.route('/update/password', methods=['POST'])
def update_password():
    """
    更新用户密码
    
    参数(JSON):
        user_id (int): 用户ID
        current_password (str): 当前密码
        new_password (str): 新密码
    
    返回:
        JSON: 包含用户ID的响应
        
    异常:
        400: 参数不完整或密码不符合要求
        401: 当前密码错误
        404: 用户不存在
        500: 更新失败
    """
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return api_response(False, "用户ID不能为空", status_code=400)
    
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return api_response(False, "用户不存在", status_code=404)

    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return api_response(False, "当前密码和新密码不能为空", status_code=400)
    
    if not verify_password(user.password_hash, current_password):
        return api_response(False, "当前密码错误", status_code=401)

    if len(new_password) < 6:
        return api_response(False, "新密码长度不能少于6个字符", status_code=400)
    
    if current_password == new_password:
        return api_response(False, "新密码不能与当前密码相同", status_code=400)
    
    user.password_hash = hash_password(new_password)
    try:
        db.session.commit()
        return api_response(True, "密码更新成功", {
            "user_id": user.user_id
        })
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"密码更新失败: {str(e)}", status_code=500)

@auth.route('/update/avatar', methods=['POST'])
def update_avatar():
    """
    更新用户头像
    
    参数(表单):
        user_id (str): 用户ID
        avatar (file): 头像文件(jpg/jpeg/png)
    
    返回:
        JSON: 包含更新后的用户信息的响应
        
    异常:
        400: 未上传文件、文件类型不允许或参数不完整
        404: 用户不存在
        500: 更新失败
    """
    if 'avatar' not in request.files:
        return api_response(False, "没有上传文件", status_code=400)
    
    file = request.files['avatar']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return api_response(False, "用户ID不能为空", status_code=400)
    
    if file.filename == '':
        return api_response(False, "未选择文件", status_code=400)
    
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return api_response(False, "用户不存在", status_code=404)
    
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        profile_dir = ensure_dir(os.path.join(current_app.root_path, '..','static', 'avator'))
        if user.avatar:
            try:
                old_filename = os.path.basename(user.avatar)
                old_file_path = os.path.join(profile_dir, old_filename)
                
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    print(f"已删除旧头像: {old_file_path}")
                
                for ext_type in ['jpg', 'jpeg', 'png']:
                    potential_old_file = os.path.join(profile_dir, f"{user_id}.{ext_type}")
                    if os.path.exists(potential_old_file) and potential_old_file != os.path.join(profile_dir, f"{user_id}.{ext}"):
                        os.remove(potential_old_file)
                        print(f"已删除其他格式的旧头像: {potential_old_file}")
            except Exception as e:
                print(f"删除旧头像时出错: {str(e)}")
        filename = f"{user_id}.{ext}"
        file_path = os.path.join(profile_dir, filename)
        
        file.save(file_path)
        
        avatar_url = url_for('static', filename=f'avator/{filename}', _external=True)
        
        user.avatar = avatar_url
        
        try:
            db.session.commit()
            return api_response(True, "头像上传成功", {
                "user": UserResponseSchema().dump(user)
            })
        except Exception as e:
            db.session.rollback()
            return api_response(False, f"头像更新失败: {str(e)}", status_code=500)
    
    return api_response(False, "文件类型不允许", status_code=400)

# 获取头像(我也不知道需不需要)
@auth.route('/get_avatar/<int:user_id>')
def get_avatar(user_id):
    """
    获取用户头像URL
    
    参数(URL):
        user_id (int): 用户ID
    
    返回:
        JSON: 包含头像URL的响应
        
    异常:
        404: 头像不存在
    """
    user = User.query.filter_by(user_id=user_id).first()
    if not user or user.avatar==None:
        return api_response(False, "头像不存在", status_code=404)
    
    return api_response(True, "获取头像成功", {
        "avatar": user.avatar
    })

@auth.route('/find_password', methods=['POST'])
def find_password():
    """
    找回密码
    
    参数(JSON):
        user_id (int): 用户ID
        email (str): 用户邮箱
        verification_code (str): 验证码
        new_password (str): 新密码
    
    返回:
        JSON: 包含用户ID的响应
        
    异常:
        400: 参数不完整、验证码错误或邮箱不匹配
        404: 用户不存在
        500: 更新失败
    """
    data = request.json
    if not data.get('email') or not data.get('verification_code'):
        return api_response(False, "邮箱和验证码不能为空", status_code=400)
    user_id=data.get('user_id')
    if not user_id:
        return api_response(False, "用户ID不能为空", status_code=400)
    new_password = data.get('new_password')
    
    if not new_password:
        return api_response(False, "新密码不能为空", status_code=400)
    
    if len(new_password) < 6:
        return api_response(False, "新密码长度不能少于6个字符", status_code=400)

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return api_response(False, "用户不存在", status_code=404)
    email = data.get('email')
    stored_code = VERIFICATION_CODES.get(email)
    if user.email!=email:
        return api_response(False, "邮箱与注册邮箱不同", status_code=400)
    
    if not stored_code:
        return api_response(False, "请先获取验证码", status_code=400)
    
    if datetime.now() > stored_code['expires']:
        del VERIFICATION_CODES[email]
        return api_response(False, "验证码已过期", status_code=400)
    
    if data['verification_code'] != stored_code['code']:
        return api_response(False, "验证码错误", status_code=400)
    
    user.password_hash = hash_password(new_password)
    try:
        db.session.commit()
        del VERIFICATION_CODES[email]
        return api_response(True, "密码更新成功", {
            "user_id": user.user_id
        })
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"密码更新失败: {str(e)}", status_code=500)
