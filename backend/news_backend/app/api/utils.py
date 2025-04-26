from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.news_detection import NewsDetectionHistory, news_detection_schema
from app.models.news_statistics import NewsStatistics, NewsStatisticsByUser
from openai import OpenAI
import os
from werkzeug.utils import secure_filename
import tempfile
import docx2txt
import PyPDF2
import datetime
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def update_statistics(user_id, is_fake):
    """更新统计信息"""
    # 更新全局统计
    global_stats = NewsStatistics.query.first()
    if not global_stats:
        global_stats = NewsStatistics()
        db.session.add(global_stats)
    
    global_stats.total_news_count += 1
    if is_fake:
        global_stats.total_fake_count += 1
    else:
        global_stats.total_real_count += 1
    global_stats.last_updated = datetime.datetime.utcnow()
    
    # 更新用户统计
    user_stats = NewsStatisticsByUser.query.filter_by(user_id=user_id).first()
    if not user_stats:
        user_stats = NewsStatisticsByUser(user_id=user_id)
        db.session.add(user_stats)
    
    user_stats.total_news_count += 1
    if is_fake:
        user_stats.total_fake_count += 1
    else:
        user_stats.total_real_count += 1
    user_stats.last_updated = datetime.datetime.utcnow()
    
    # 不在这里提交事务，让调用者负责提交
    # db.session.commit()

def extract_text_from_file(file):
    """从不同类型的文件中提取文本内容"""
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        file.save(temp.name)
        temp_path = temp.name
    
    try:
        if extension == 'pdf':
            # 处理PDF文件
            text = ""
            with open(temp_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
            return text
        
        elif extension == 'docx':
            # 处理Word文件
            return docx2txt.process(temp_path)
        
        elif extension == 'txt':
            # 处理文本文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        else:
            raise ValueError(f"不支持的文件类型: {extension}")
    
    finally:
        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

def api_response(success=True, message="", data=None, status_code=200):
    """统一API响应格式"""
    return jsonify({
        "success": success,
        "message": message,
        "data": data
    }), status_code