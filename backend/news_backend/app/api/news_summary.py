from flask import Blueprint, request, jsonify
from app import db
from app.models.news_summary import (
    NewsSummary, news_summary_schema, news_summaries_schema,
    get_available_summary_types, SummaryType
)
from datetime import datetime
from .utils import api_response
from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 内容概括的提示模板
SUMMARY_PROMPT = """
你是一个专业的新闻编辑，擅长对新闻内容进行概括。请为以下新闻内容生成一个{summary_type_description}：

【新闻内容】
{content}

请仅输出概括结果，不要有任何解释或额外内容。
"""

news_summary_bp = Blueprint('news_summary', __name__)

@news_summary_bp.route('/types', methods=['GET'])
def get_types():
    """获取所有可用的概括类型"""
    try:
        types = get_available_summary_types()
        return api_response(True, "获取概括类型列表成功", types)
    except Exception as e:
        return api_response(False, f"获取概括类型列表失败: {str(e)}", status_code=500)

@news_summary_bp.route('/summarize', methods=['POST'])
def summarize_content():
    """生成新闻内容概括"""
    try:
        # 检查是否有用户ID
        user_id = request.form.get('user_id')
        if not user_id:
            return api_response(False, "请先登录", status_code=401)
        
        # 获取内容和概括类型
        content = request.form.get('content')
        if not content:
            return api_response(False, "请提供新闻内容", status_code=400)
        
        summary_type = request.form.get('summary_type')
        if not summary_type:
            summary_type = SummaryType.BRIEF.value  # 默认使用简短摘要
        
        # 验证概括类型是否有效
        valid_types = [t.value for t in SummaryType]
        if summary_type not in valid_types:
            return api_response(False, f"无效的概括类型，可用选项: {', '.join(valid_types)}", status_code=400)
        
        # 获取概括类型描述
        summary_type_description = next((item['description'] for item in get_available_summary_types() if item['value'] == summary_type), "")
        
        # 调用 DeepSeek API 生成概括
        try:
            if not DEEPSEEK_API_KEY:
                return api_response(False, "缺少API密钥配置", status_code=500)
            
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            
            # 根据不同的概括类型设置不同的参数
            max_tokens = 1000
            temperature = 0.5
            
            if summary_type == SummaryType.BRIEF.value:
                max_tokens = 200
            elif summary_type == SummaryType.DETAILED.value:
                max_tokens = 800
            elif summary_type == SummaryType.NEWS_FLASH.value:
                max_tokens = 100
                temperature = 0.3
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的内容摘要专家，擅长生成各种类型的内容概括。"},
                    {"role": "user", "content": SUMMARY_PROMPT.format(
                        summary_type_description=summary_type_description,
                        content=content
                    )}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=120
            )
            
            summary_content = response.choices[0].message.content.strip()
            
            # 保存到数据库
            news_summary = NewsSummary(
                user_id=user_id,
                original_content=content,
                summary_type=summary_type,
                summary_content=summary_content
            )
            
            db.session.add(news_summary)
            db.session.commit()
            
            return api_response(True, "内容概括生成成功", {
                "summary": summary_content,
                "summary_type": summary_type,
                "summary_type_description": summary_type_description
            })
            
        except Exception as api_error:
            return api_response(False, f"内容概括生成失败: {str(api_error)}", status_code=500)
            
    except Exception as e:
        return api_response(False, f"处理请求时发生错误: {str(e)}", status_code=500)

@news_summary_bp.route('/history/<user_id>', methods=['GET'])
def get_summary_history(user_id):
    """获取用户的内容概括历史"""
    try:
        # 查询历史记录
        history = NewsSummary.query.filter_by(user_id=user_id).order_by(
            NewsSummary.summary_date.desc()
        ).all()
        
        if not history:
            return api_response(False, f"未找到用户 {user_id} 的内容概括历史", status_code=404)
        
        # 返回历史记录
        return api_response(True, "获取内容概括历史成功", news_summaries_schema.dump(history))
    
    except Exception as e:
        return api_response(False, f"获取内容概括历史失败: {str(e)}", status_code=500) 