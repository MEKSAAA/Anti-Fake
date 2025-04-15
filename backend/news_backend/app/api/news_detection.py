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
import jieba
import jieba.analyse
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import random

# 加载环境变量
load_dotenv()

# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

news_detection_bp = Blueprint('news_detection', __name__)

# 假新闻检测的prompt模版
FAKE_NEWS_DETECTION_PROMPT = """
你是一个专业的假新闻检测专家，请基于以下新闻内容进行真实性评估：

{content}

请按照以下格式进行分析：
1. 内容真实性评估：给出"真实"或"虚假"的判断
2. 判断理由：详细阐述你判断的依据，包括：
   - 事实核查：内容中提到的具体事实是否可验证
   - 内容逻辑：是否存在逻辑矛盾或不合理之处
   - 语言特征：是否存在夸张、煽动性语言
   - 信息来源：是否提供了可靠的信息来源
   - 专业分析：从专业角度分析内容的可信度
3. 相关真实信息链接：如果有相关的真实信息来源，请提供

返回格式要求：
{
  "is_fake": true/false,
  "reason": "详细的判断理由，包含上述所有分析要点",
  "related_links": ["链接1", "链接2", ...]
}

分析时请注意以下几点：
1. 检查内容中是否有不一致或自相矛盾的地方
2. 考虑信息来源的可靠性
3. 评估内容的可验证性
4. 分析情感倾向和夸张表述
5. 查找是否有类似的已证实或已辟谣的消息

请确保回答严格按照JSON格式返回，不要有任何其他内容。
"""

# 文本假新闻检测的prompt模版
TEXT_DETECTION_PROMPT = """
你是一个专业的文本真假信息检测专家。请分析以下内容：

【待检测内容】
{content}

【我们搜索到的相关事实信息】
{search_results}

请根据待检测内容和我们提供的相关事实信息，进行真假判断。

请用自然语言回答，但必须在回答的第一句话中明确给出"真实"或"虚假"的判断。
然后详细说明你的判断理由，包括：
1. 事实核查（根据我们提供的搜索结果和你已有的知识进行核查）
2. 逻辑分析
3. 语言特征
4. 信息来源
5. 专业分析

请确保第一句话包含明确的判断结果。
"""

# 预定义的可信新闻源
TRUSTED_NEWS_SOURCES = {
    "政府与官方媒体": [
        {"name": "新华网", "url": "http://www.xinhuanet.com/"},
        {"name": "人民网", "url": "http://www.people.com.cn/"},
        {"name": "央视网", "url": "http://www.cctv.com/"},
        {"name": "中国政府网", "url": "http://www.gov.cn/"},
        {"name": "中国日报", "url": "http://www.chinadaily.com.cn/"}
    ],
    "主流媒体": [
        {"name": "澎湃新闻", "url": "https://www.thepaper.cn/"},
        {"name": "财新网", "url": "http://www.caixin.com/"},
        {"name": "南方周末", "url": "http://www.infzm.com/"},
        {"name": "第一财经", "url": "https://www.yicai.com/"},
        {"name": "界面新闻", "url": "https://www.jiemian.com/"}
    ],
    "事实核查网站": [
        {"name": "较真查证平台", "url": "https://fact.qq.com/"},
        {"name": "食品辟谣网", "url": "https://www.meiri8.com/"},
        {"name": "腾讯辟谣中心", "url": "https://piyao.qq.com/"},
        {"name": "中国互联网联合辟谣平台", "url": "https://www.piyao.org.cn/"}
    ],
    "国际媒体": [
        {"name": "BBC中文网", "url": "https://www.bbc.com/zhongwen"},
        {"name": "纽约时报中文网", "url": "https://cn.nytimes.com/"},
        {"name": "路透社中文网", "url": "https://cn.reuters.com/"},
        {"name": "法国国际广播电台中文版", "url": "https://www.rfi.fr/cn/"},
        {"name": "德国之声中文网", "url": "https://www.dw.com/zh/"}
    ]
}

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

# 这个API貌似没用 但我暂时不删吧
@news_detection_bp.route('/detect', methods=['POST'])
def detect_fake_news():
    """检测假新闻API"""
    # 检查是否有用户ID
    user_id = request.form.get('user_id')
    if not user_id:
        return api_response(False, "请先登录", status_code=401)
    
    # 获取检测内容
    content = None
    source = "用户输入"
    
    # 处理文件上传
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            try:
                content = extract_text_from_file(file)
                source = secure_filename(file.filename)
            except Exception as e:
                return api_response(False, f"文件处理错误: {str(e)}", status_code=400)
    else:
        # 处理直接输入的文本
        content = request.form.get('content')
    
    if not content:
        return api_response(False, "请提供需要检测的新闻内容", status_code=400)
    
    # 调用DeepSeek API进行检测
    try:
        # 从环境变量获取API密钥
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return api_response(False, "缺少API密钥配置", status_code=500)
            
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in fake news detection."},
                {"role": "user", "content": FAKE_NEWS_DETECTION_PROMPT.format(content=content)}
            ],
            stream=False
        )
        
        # 解析响应
        detection_result = response.choices[0].message.content
        
        # 尝试解析JSON响应
        try:
            result_json = json.loads(detection_result)
            is_fake = result_json.get('is_fake', False)
            reason = result_json.get('reason', '')
            related_links = ', '.join(result_json.get('related_links', []))
        except json.JSONDecodeError:
            # 如果无法解析为JSON，使用原始响应
            is_fake = "无法确定" in detection_result or "虚假" in detection_result
            reason = detection_result
            related_links = ""
        
        try:
            # 保存到数据库
            new_detection = NewsDetectionHistory(
                user_id=user_id,
                source=source,
                content=content,
                detection_reason=reason,
                related_news_links=related_links
            )
            
            db.session.add(new_detection)
            
            # 确保记录已添加到数据库会话
            db.session.flush()
            
            # 更新统计信息
            update_statistics(int(user_id), is_fake)
            
            # 确保所有更改都已提交
            db.session.commit()
        except Exception as db_error:
            # 如果数据库操作失败，回滚事务
            db.session.rollback()
            return api_response(False, f"数据库更新失败: {str(db_error)}", status_code=500)
        
        # 返回检测结果
        return api_response(
            True, 
            "检测完成", 
            {
                "detection": news_detection_schema.dump(new_detection),
                "is_fake": is_fake,
                "reason": reason,
                "related_links": related_links
            }
        )
        
    except Exception as e:
        # 确保任何异常情况下都回滚数据库事务
        db.session.rollback()
        return api_response(False, f"检测失败: {str(e)}", status_code=500)

# 搜索相关新闻的函数
def search_related_news(text, max_links=3):
    """
    搜索与给定文本相关的新闻链接
    使用文本的第一句话进行搜索，并结合可信新闻源
    """
    try:
        # 提取第一句话作为搜索关键词
        first_sentence = ""
        # 尝试按常见的标点符号分割，提取第一句话
        for delimiter in ["。", "！", "？", ".", "!", "?"]:
            if delimiter in text:
                first_sentence = text.split(delimiter)[0].strip()
                break
        
        # 如果无法通过标点符号分割，就取前100个字符
        if not first_sentence:
            first_sentence = text[:100].strip()
            
        # 确保搜索词不会太长
        search_query = first_sentence[:50]
        print(f"搜索关键词(第一句话): {search_query}")
        
        related_links = []
        
        # 1. 基于第一句话匹配预定义的新闻源
        # 随机选择一个分类
        category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
        # 从该分类中随机选择一个新闻源
        news_source = random.choice(TRUSTED_NEWS_SOURCES[category])
        # 构建一个基于第一句话的URL
        related_links.append({
            "title": f"{news_source['name']}相关报道",
            "link": f"{news_source['url']}search?q={search_query}"
        })
        
        # 2. 尝试使用百度搜索(简单模拟，实际使用时可能需要更复杂的处理)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.baidu.com/s?wd={search_query}"
            
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取搜索结果
                search_results = soup.select('.result.c-container')
                
                for result in search_results[:2]:  # 只取前2个结果
                    title_elem = result.select_one('.t a')
                    if title_elem:
                        title = title_elem.get_text()
                        link = title_elem.get('href', '')
                        if link and link.startswith('http'):
                            related_links.append({
                                "title": title,
                                "link": link
                            })
        except Exception as e:
            print(f"百度搜索失败: {str(e)}")
            # 如果百度搜索失败，添加一些预定义的辟谣网站
            related_links.append({
                "title": "较真查证平台",
                "link": "https://fact.qq.com/"
            })
            related_links.append({
                "title": "中国互联网联合辟谣平台",
                "link": "https://www.piyao.org.cn/"
            })
        
        # 如果没有找到足够的相关链接，添加一些默认的可信新闻源
        while len(related_links) < max_links:
            category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
            source = random.choice(TRUSTED_NEWS_SOURCES[category])
            link_info = {
                "title": source["name"],
                "link": source["url"]
            }
            if link_info not in related_links:
                related_links.append(link_info)
        
        # 只返回链接部分
        return [link_info["link"] for link_info in related_links[:max_links]]
        
    except Exception as e:
        print(f"搜索相关新闻失败: {str(e)}")
        # 返回一些默认的辟谣网站
        return [
            "https://fact.qq.com/",
            "https://www.piyao.org.cn/",
            "http://www.xinhuanet.com/"
        ][:max_links]

# 搜索相关新闻并获取内容的函数
def search_and_fetch_news(text, max_results=3):
    """
    搜索与给定文本相关的新闻并获取内容摘要
    """
    try:
        # 提取第一句话作为搜索关键词
        first_sentence = ""
        # 尝试按常见的标点符号分割，提取第一句话
        for delimiter in ["。", "！", "？", ".", "!", "?"]:
            if delimiter in text:
                first_sentence = text.split(delimiter)[0].strip()
                break
        
        # 如果无法通过标点符号分割，就取前100个字符
        if not first_sentence:
            first_sentence = text[:100].strip()
            
        # 确保搜索词不会太长
        search_query = first_sentence[:50]
        print(f"搜索关键词(第一句话): {search_query}")
        
        search_results = []
        fetched_content = ""
        
        # 1. 尝试使用百度搜索
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.baidu.com/s?wd={search_query}"
            
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取搜索结果
                search_results = soup.select('.result.c-container')
                
                for i, result in enumerate(search_results[:max_results]):
                    # 提取标题和摘要
                    title_elem = result.select_one('.t a')
                    abstract_elem = result.select_one('.c-abstract')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href', '')
                        abstract = abstract_elem.get_text().strip() if abstract_elem else "无摘要"
                        
                        # 添加到搜索结果摘要中
                        fetched_content += f"信息来源{i+1}：{title}\n"
                        fetched_content += f"摘要：{abstract}\n"
                        fetched_content += f"链接：{link}\n\n"
        except Exception as e:
            print(f"百度搜索失败: {str(e)}")
        
        # 2. 如果百度搜索失败或没有结果，添加一些预定义信息
        if not fetched_content:
            # 从预定义新闻源中获取一些基本信息
            fetched_content = "未找到确切相关信息，以下是一些可信新闻源供参考：\n\n"
            
            for i, category in enumerate(TRUSTED_NEWS_SOURCES.keys()):
                if i >= 2:  # 只取前两个分类
                    break
                    
                sources = TRUSTED_NEWS_SOURCES[category]
                fetched_content += f"权威{category}：\n"
                
                for j, source in enumerate(sources[:3]):  # 每个分类取前三个
                    fetched_content += f"- {source['name']}: {source['url']}\n"
                
                fetched_content += "\n"
        
        # 返回搜索到的内容摘要和相关链接
        related_links = []
        for result in search_results[:max_results]:
            title_elem = result.select_one('.t a')
            if title_elem and title_elem.get('href', '').startswith('http'):
                related_links.append(title_elem.get('href'))
        
        # 如果没有足够的链接，添加一些预定义的链接
        while len(related_links) < max_results:
            category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
            source = random.choice(TRUSTED_NEWS_SOURCES[category])
            link = source["url"]
            if link not in related_links:
                related_links.append(link)
                
        return {
            "content_summary": fetched_content,
            "related_links": related_links[:max_results]
        }
        
    except Exception as e:
        print(f"搜索和获取新闻内容失败: {str(e)}")
        # 返回空结果和一些默认链接
        return {
            "content_summary": "搜索相关信息时发生错误，无法提供相关事实依据。",
            "related_links": [
                "https://fact.qq.com/",
                "https://www.piyao.org.cn/",
                "http://www.xinhuanet.com/"
            ][:max_results]
        }

def detect_text_content(content):
    """检测文本内容的真实性"""
    try:
        # 检查API密钥
        if not DEEPSEEK_API_KEY:
            raise ValueError("缺少DEEPSEEK_API_KEY配置")
            
        print(f"开始调用DeepSeek API，API密钥长度: {len(DEEPSEEK_API_KEY)}")
        
        # 首先搜索相关信息
        print("开始搜索相关新闻信息")
        search_result = search_and_fetch_news(content)
        search_content = search_result["content_summary"]
        related_links = search_result["related_links"]
        print(f"搜索到的相关信息: {search_content[:200]}...")
        print(f"找到相关链接: {related_links}")
        
        # 调用DeepSeek API
        try:
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            print("DeepSeek客户端创建成功")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的假新闻检测专家"},
                    {"role": "user", "content": TEXT_DETECTION_PROMPT.format(
                        content=content,
                        search_results=search_content
                    )}
                ],
                timeout=100
            )
            print("DeepSeek API调用成功")
            
        except Exception as api_error:
            print(f"DeepSeek API调用失败: {str(api_error)}")
            raise api_error
        
        # 获取回答内容
        answer = response.choices[0].message.content
        print(f"DeepSeek返回内容: {answer[:100]}...")
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(answer, topK=5)
        print(f"提取的关键词: {keywords}")
        
        # 判断真假
        is_fake = False
        if "虚假" in answer[:50] or "假" in answer[:50]:
            is_fake = True
        print(f"判断结果: {'虚假' if is_fake else '真实'}")
        
        # 不在这里创建数据库记录，只返回检测结果
        return {
            "success": True,
            "is_fake": is_fake,
            "reason": answer,
            "related_links": related_links
        }
        
    except Exception as e:
        print(f"检测过程中发生错误: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@news_detection_bp.route('/text-detection', methods=['POST'])
def detect_text_content_api():
    """文本内容真假检测API"""
    try:
        # 检查是否有用户ID
        user_id = request.form.get('user_id')
        if not user_id:
            return api_response(False, "请先登录", status_code=401)
        
        # 获取检测内容
        content = None
        source = "文本检测"
        
        # 处理文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                try:
                    content = extract_text_from_file(file)
                    source = secure_filename(file.filename)
                except Exception as e:
                    return api_response(False, f"文件处理错误: {str(e)}", status_code=400)
        else:
            # 处理直接输入的文本
            content = request.form.get('content')
        
        if not content:
            return api_response(False, "请提供需要检测的文本内容", status_code=400)
        
        # 调用检测函数
        result = detect_text_content(content)
        
        if not result["success"]:
            return api_response(False, f"检测失败: {result['error']}", status_code=500)
        
        # 尝试保存到数据库，如果失败，仍然返回检测结果
        try:
            # 创建检测记录
            detection = NewsDetectionHistory(
                user_id=user_id,
                source=source,
                content=content,
                detection_reason=result["reason"],
                related_news_links=", ".join(result["related_links"]) if result["related_links"] else ""
            )
            
            db.session.add(detection)
            
            # 更新统计信息
            try:
                update_statistics(int(user_id), result["is_fake"])
            except Exception as stat_error:
                print(f"更新统计信息失败: {str(stat_error)}")
                # 继续执行，不中断流程
            
            # 提交事务
            db.session.commit()
            
            # 成功保存到数据库的情况
            return api_response(
                True,
                "检测完成",
                {
                    "detection": news_detection_schema.dump(detection),
                    "is_fake": result["is_fake"],
                    "reason": result["reason"],
                    "related_links": result["related_links"]
                }
            )
        except Exception as db_error:
            print(f"数据库操作失败: {str(db_error)}")
            try:
                db.session.rollback()
            except:
                pass
            
            # 数据库操作失败，但仍然返回检测结果
            return api_response(
                True,
                "检测完成 (注意: 结果未能保存到数据库)",
                {
                    "is_fake": result["is_fake"],
                    "reason": result["reason"],
                    "related_links": result["related_links"]
                }
            )
            
    except Exception as e:
        print(f"检测过程发生错误: {str(e)}")
        return api_response(False, f"检测过程中发生错误: {str(e)}", status_code=500)

@news_detection_bp.route('/history/<user_id>', methods=['GET'])
def get_detection_history(user_id):
    """获取用户的检测历史"""
    try:
        history = NewsDetectionHistory.query.filter_by(user_id=user_id).order_by(
            NewsDetectionHistory.upload_date.desc()).all()
        from app.models.news_detection import news_detections_schema
        return api_response(True, "获取历史记录成功", news_detections_schema.dump(history))
    except Exception as e:
        return api_response(False, f"获取历史记录失败: {str(e)}", status_code=500) 