from flask import Blueprint, request, jsonify
from app import db
from app.models.news_text_optimization import (
    NewsTextOptimization, news_text_optimization_schema, news_text_optimizations_schema,
    get_available_text_styles, TextStyle
)
from datetime import datetime
from app.utils.common import api_response
from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 文本优化的提示模板
TEXT_OPTIMIZATION_PROMPT = """
你是一位专业的文本优化专家，请将以下文本改写成{style_description}：

【原始文本】
{text}

请只输出优化后的文本，保持原意不变，不要有任何解释或额外内容。
"""

text_optimization_bp = Blueprint('text_optimization', __name__)

@text_optimization_bp.route('/styles', methods=['GET'])
def get_styles():
    """获取所有可用的文本风格
    
    返回:
        dict: 包含状态、消息和文本风格列表的API响应
    
    异常:
        Exception: 当获取风格列表失败时抛出
    """
    try:
        styles = get_available_text_styles()
        return api_response(True, "获取文本风格列表成功", styles)
    except Exception as e:
        return api_response(False, f"获取文本风格列表失败: {str(e)}", status_code=500)

@text_optimization_bp.route('/optimize', methods=['POST'])
def optimize_text():
    """优化新闻文本
    
    从请求中获取原始文本和目标风格，调用DeepSeek API进行文本优化，并保存到数据库
    
    参数:
        从表单获取:
        user_id (str): 用户ID
        text (str): 需要优化的原始文本
        style (str, 可选): 目标文本风格，默认为新闻报道风格
    
    返回:
        dict: 包含状态、消息和优化结果的API响应
    
    异常:
        Exception: 当文本优化失败或处理请求出错时抛出
    """
    try:
        # 检查是否有用户ID
        user_id = request.form.get('user_id')
        if not user_id:
            return api_response(False, "请先登录", status_code=401)
        
        # 获取原始文本和目标风格
        original_text = request.form.get('text')
        if not original_text:
            return api_response(False, "请提供需要优化的文本", status_code=400)
        
        target_style = request.form.get('style')
        if not target_style:
            target_style = TextStyle.JOURNALISTIC.value  # 默认使用新闻报道风格
        
        # 验证风格是否有效
        valid_styles = [s.value for s in TextStyle]
        if target_style not in valid_styles:
            return api_response(False, f"无效的文本风格，可用选项: {', '.join(valid_styles)}", status_code=400)
        
        # 获取风格描述
        style_description = next((item['description'] for item in get_available_text_styles() if item['value'] == target_style), "")
        
        # 调用 DeepSeek API 优化文本
        try:
            if not DEEPSEEK_API_KEY:
                return api_response(False, "缺少API密钥配置", status_code=500)
            
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            
            # 根据不同的文本风格设置不同的参数
            temperature = 0.7
            
            if target_style == TextStyle.ACADEMIC.value:
                temperature = 0.4  # 学术风格应更精确
            elif target_style == TextStyle.FORMAL.value:
                temperature = 0.5  # 正式风格应较为严谨
            elif target_style == TextStyle.CASUAL.value:
                temperature = 0.8  # 休闲风格可以更有创意
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本优化专家，擅长将文本改写成不同的风格，同时保持原意不变。"},
                    {"role": "user", "content": TEXT_OPTIMIZATION_PROMPT.format(
                        style_description=style_description,
                        text=original_text
                    )}
                ],
                max_tokens=2000,
                temperature=temperature,
                timeout=120
            )
            
            optimized_text = response.choices[0].message.content.strip()
            
            # 保存到数据库
            text_optimization = NewsTextOptimization(
                user_id=user_id,
                original_text=original_text,
                target_style=target_style,
                optimized_text=optimized_text
            )
            
            db.session.add(text_optimization)
            db.session.commit()
            
            return api_response(True, "文本优化成功", {
                "original_text": original_text,
                "optimized_text": optimized_text,
                "style": target_style,
                "style_description": style_description
            })
            
        except Exception as api_error:
            return api_response(False, f"文本优化失败: {str(api_error)}", status_code=500)
            
    except Exception as e:
        return api_response(False, f"处理请求时发生错误: {str(e)}", status_code=500)

@text_optimization_bp.route('/history/<user_id>', methods=['GET'])
def get_optimization_history(user_id):
    """获取用户的文本优化历史
    
    查询指定用户的所有文本优化历史记录，按时间降序排列
    
    参数:
        user_id (str): 用户ID，从URL路径获取
    
    返回:
        dict: 包含状态、消息和历史记录列表的API响应
    
    异常:
        Exception: 当获取历史记录失败时抛出
    """
    try:
        # 查询历史记录
        history = NewsTextOptimization.query.filter_by(user_id=user_id).order_by(
            NewsTextOptimization.optimization_date.desc()
        ).all()
        
        if not history:
            return api_response(False, f"未找到用户 {user_id} 的文本优化历史", status_code=404)
        
        # 返回历史记录
        return api_response(True, "获取文本优化历史成功", news_text_optimizations_schema.dump(history))
    
    except Exception as e:
        return api_response(False, f"获取文本优化历史失败: {str(e)}", status_code=500) 