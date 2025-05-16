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
import requests
from bs4 import BeautifulSoup
import random
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


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

# def search_related_news(text, max_links=3):
#     """
#     搜索与给定文本相关的新闻链接
#     :param text: 用户输入的文本内容
#     :param max_links: 最大返回链接数量
#     :return: 相关新闻链接列表
#     """
#     try:
#         # 提取第一句话作为搜索关键词
#         first_sentence = ""
#         # # 尝试按常见的标点符号分割，提取第一句话
#         # for delimiter in ["。", "！", "？", ".", "!", "?"]:
#         #     if delimiter in text:
#         #         first_sentence = text.split(delimiter)[0].strip()
#         #         break
        
#         # # 如果无法通过标点符号分割，就取前100个字符
#         # if not first_sentence:
#         #     first_sentence = text[:100].strip()
#         first_sentence = text
            
#         # 确保搜索词不会太长
#         search_query = first_sentence[:50]
#         print(f"搜索关键词: {search_query}")
        
#         related_links = []
        
#         # 1. 尝试使用百度搜索
#         try:
#             headers = {
#                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#             }
#             search_url = f"https://www.baidu.com/s?wd={search_query}"
            
#             response = requests.get(search_url, headers=headers, timeout=5)
            
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.text, 'html.parser')
#                 # 提取搜索结果
#                 search_results = soup.select('.result.c-container')
                
#                 for result in search_results[:max_links]:  # 取前max_links个结果
#                     title_elem = result.select_one('.t a')
#                     if title_elem:
#                         link = title_elem.get('href', '')
#                         if link and link.startswith('http'):
#                             related_links.append(link)
#         except Exception as e:
#             print(f"百度搜索失败: {str(e)}")
        
#         # 2. 如果没有找到足够的相关链接，添加一些默认的可信新闻源
#         while len(related_links) < max_links:
#             category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
#             source = random.choice(TRUSTED_NEWS_SOURCES[category])
#             link = source["url"]
#             if link not in related_links:
#                 related_links.append(link)
        
#         return related_links[:max_links]
        
#     except Exception as e:
#         print(f"搜索相关新闻失败: {str(e)}")
#         # 返回一些默认的辟谣网站
#         default_links = [
#             "https://fact.qq.com/",
#             "https://www.piyao.org.cn/",
#             "http://www.xinhuanet.com/"
#         ]
#         return default_links[:max_links]
    
    
    