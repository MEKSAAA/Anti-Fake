from flask import request, current_app
from openai import OpenAI
import os
from .utils import DEEPSEEK_API_KEY
from werkzeug.utils import secure_filename


# 翻译提示模板
TEXT_TRANSLATE_PROMPT = """
你是一个专业的文本翻译专家。请将以下中文内容翻译为英文：

【待翻译内容】
{content}

只需要输出翻译结果，不要输出任何解释。
"""

# 检测理由生成模板
DETECTION_REASON_PROMPT = """
你是一个专业的图像鉴定专家，请根据以下信息生成一段专业的图像伪造检测理由：

【图像操纵类型】：{manipulation_types}
【伪造文本内容】：{fake_words}
【图像相关文本】：{text}
【伪造可能性】：{fake_probability}

请详细解释为什么这张图片被判定为伪造，解释要专业且具体：
1. 如果涉及face_swap（替换图片中主要人物的脸），请说明检测到的具体证据和特征
2. 如果涉及face_attribute（修改人物脸部属性但不改变其身份），请描述具体修改了哪些属性
3. 如果涉及text_swap（替换整个文本但保留主要实体名），请解释文本内容不匹配的地方
4. 如果涉及text_attribute（改变文本的情感倾向），请指出文本情感倾向被如何操纵

仅输出专业的鉴定理由，不要包含额外解释或引言。理由应当专业、客观、具体且有说服力，但不要夸大。
"""

def translate_text(content):
    try:
        # 检查API密钥
        if not DEEPSEEK_API_KEY:
            raise ValueError("缺少DEEPSEEK_API_KEY配置")
            
        print(f"开始调用DeepSeek API，API密钥长度: {len(DEEPSEEK_API_KEY)}")
        try:
            print("开始翻译")
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            print("DeepSeek客户端创建成功")

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in translation."},
                    {"role": "user", "content": TEXT_TRANSLATE_PROMPT.format(content=content)}
                ],
                timeout=100,
                stream=False
            )
            print("DeepSeek API调用成功")
        except Exception as api_error:
            print(f"DeepSeek API调用失败: {str(api_error)}")
            raise api_error

        translated_text = response.choices[0].message.content
        print(f"Translated Text: {translated_text}")
        return translated_text
    except Exception as e:
        print(f"翻译过程中发生错误: {str(e)}")
        return None

def generate_detection_reason(manipulation_types, fake_words, text, fake_probability):
    """
    生成图像检测理由
    :param manipulation_types: 操纵类型列表，例如["face_swap", "text_swap"]
    :param fake_words: 检测到的伪造文本词列表
    :param text: 与图像相关的文本
    :param fake_probability: 伪造可能性（0-1之间的浮点数）
    :return: 生成的检测理由文本
    """
    try:
        # 检查API密钥
        if not DEEPSEEK_API_KEY:
            raise ValueError("缺少DEEPSEEK_API_KEY配置")
        
        # 准备提示内容
        manipulation_types_str = "、".join(manipulation_types) if manipulation_types else "未检测到明确的操纵类型"
        fake_words_str = "、".join(fake_words) if fake_words else "未检测到明确的伪造文本内容"
        fake_probability_str = f"{fake_probability * 100:.2f}%" if fake_probability else "未知"
        
        prompt = DETECTION_REASON_PROMPT.format(
            manipulation_types=manipulation_types_str,
            fake_words=fake_words_str,
            text=text,
            fake_probability=fake_probability_str
        )
        
        # 调用DeepSeek API
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional expert in image authentication and forgery detection."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3,  # 降低温度以保持输出的专业性和一致性
            timeout=100,
            stream=False
        )
        
        # 提取并返回理由
        reason = response.choices[0].message.content
        return reason.strip()
    except Exception as e:
        print(f"生成检测理由时发生错误: {str(e)}")
        # 如果发生错误，返回一个基本的理由
        types_text = "、".join(manipulation_types) if manipulation_types else "未知类型"
        return f"检测到图像可能存在伪造（{types_text}），伪造可能性为{fake_probability * 100:.2f}%。"

def save_image(user_id, image_file):
    filename = secure_filename(image_file.filename)
    _, file_extension = os.path.splitext(filename)
    static_dir = os.path.join(current_app.root_path, '..', 'static','news_image')
    static_dir = os.path.abspath(static_dir)  # 转换为绝对路径
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    user_dir = os.path.join(static_dir, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    existing_files = [f for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
    if not existing_files:
        next_number = 1
    else:
        file_numbers = []
        for f in existing_files:
            try:
                num = int(os.path.splitext(f)[0].split('_')[-1])
                file_numbers.append(num)
            except ValueError:
                pass
        next_number = max(file_numbers) + 1
    filename = f"{user_id}_{next_number}{file_extension}"
    image_path = os.path.join(user_dir, filename)
    image_file.save(image_path)
    return image_path
