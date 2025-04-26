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

def save_image(user_id, image_file):
    filename = secure_filename(image_file.filename)
    _, file_extension = os.path.splitext(filename)
    static_dir = os.path.join(current_app.root_path, '..', 'static')
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
