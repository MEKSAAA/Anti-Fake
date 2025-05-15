from flask import Blueprint, request, jsonify
from app import db
from app.models.news_title_generation import (
    NewsTitleGeneration, news_title_generation_schema, news_title_generations_schema,
    get_available_title_styles, TitleStyle
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

# 标题生成的提示模板
TITLE_GENERATION_PROMPT = """
你是一个专业的新闻编辑，擅长为文章创建吸引人的标题。请为以下内容生成一个{style_description}风格的标题：

【文章内容】
{content}

请只输出标题，不要有任何解释或额外内容。标题字数控制在30字以内。
"""

news_title_bp = Blueprint('news_title', __name__)

@news_title_bp.route('/styles', methods=['GET'])
def get_styles():
    """获取所有可用的标题风格"""
    try:
        styles = get_available_title_styles()
        return api_response(True, "获取标题风格列表成功", styles)
    except Exception as e:
        return api_response(False, f"获取标题风格列表失败: {str(e)}", status_code=500)

@news_title_bp.route('/generate', methods=['POST'])
def generate_title():
    """生成新闻标题"""
    try:
        # 检查是否有用户ID
        user_id = request.form.get('user_id')
        if not user_id:
            return api_response(False, "请先登录", status_code=401)
        
        # 获取内容和风格
        content = request.form.get('content')
        if not content:
            return api_response(False, "请提供新闻内容", status_code=400)
        
        style = request.form.get('style')
        if not style:
            style = TitleStyle.INFORMATIVE.value  # 默认使用信息型风格
        
        # 验证风格是否有效
        valid_styles = [s.value for s in TitleStyle]
        if style not in valid_styles:
            return api_response(False, f"无效的标题风格，可用选项: {', '.join(valid_styles)}", status_code=400)
        
        # 获取风格描述
        style_description = next((item['description'] for item in get_available_title_styles() if item['value'] == style), "")
        
        # 调用 DeepSeek API 生成标题
        try:
            if not DEEPSEEK_API_KEY:
                return api_response(False, "缺少API密钥配置", status_code=500)
            
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻编辑，擅长为文章创建符合指定风格的标题。"},
                    {"role": "user", "content": TITLE_GENERATION_PROMPT.format(
                        style_description=style_description,
                        content=content
                    )}
                ],
                max_tokens=100,
                temperature=0.7,
                timeout=60
            )
            
            generated_title = response.choices[0].message.content.strip()
            
            # 保存到数据库
            title_generation = NewsTitleGeneration(
                user_id=user_id,
                original_content=content,
                title_style=style,
                generated_title=generated_title
            )
            
            db.session.add(title_generation)
            db.session.commit()
            
            return api_response(True, "标题生成成功", {
                "title": generated_title,
                "style": style,
                "style_description": style_description
            })
            
        except Exception as api_error:
            return api_response(False, f"标题生成失败: {str(api_error)}", status_code=500)
            
    except Exception as e:
        return api_response(False, f"处理请求时发生错误: {str(e)}", status_code=500)

@news_title_bp.route('/history/<user_id>', methods=['GET'])
def get_title_history(user_id):
    """获取用户的标题生成历史"""
    try:
        # 查询历史记录
        history = NewsTitleGeneration.query.filter_by(user_id=user_id).order_by(
            NewsTitleGeneration.generation_date.desc()
        ).all()
        
        if not history:
            return api_response(False, f"未找到用户 {user_id} 的标题生成历史", status_code=404)
        
        # 返回历史记录
        return api_response(True, "获取标题生成历史成功", news_title_generations_schema.dump(history))
    
    except Exception as e:
        return api_response(False, f"获取标题生成历史失败: {str(e)}", status_code=500) 