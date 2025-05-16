from flask import current_app
import requests
import os
import time
import urllib.request
from app import app
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')

def save_generated_image(user_id, image_url, index=0):
    """
    下载并保存生成的图片
    
    参数:
        user_id (str): 用户ID
        image_url (str): 图片URL
        index (int, 可选): 图片索引（用于同一批次多张图片），默认为0
    
    返回:
        str: 保存的图片路径
    """
    # 创建保存路径
    static_dir = os.path.join(current_app.root_path, '..', 'static')
    static_dir = os.path.abspath(static_dir)
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    generate_dir = os.path.join(static_dir, 'image_generation')
    if not os.path.exists(generate_dir):
        os.makedirs(generate_dir)
    
    user_dir = os.path.join(generate_dir, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        
    # 从URL中提取文件扩展名
    url_path = image_url.split('?')[0]
    file_extension = os.path.splitext(os.path.basename(url_path))[1]
    if not file_extension:
        # 如果URL中没有扩展名，默认使用.png
        file_extension = '.png'
    
    # 使用时间戳命名
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
    # 如果是批次中的第一张图片，不添加索引
    if index == 0:
        filename = f"{timestamp}{file_extension}"
    else:
        # 对于批次中的其他图片，添加索引
        filename = f"{timestamp}_{index}{file_extension}"
    
    # 保存路径
    image_path = os.path.join(user_dir, filename)
    
    # 下载图片
    urllib.request.urlretrieve(image_url, image_path)
    
    return image_path

def create_image_task(prompt, size='1024*1024', n=1):
    """
    创建图像生成任务，获取task_id
    
    参数:
        prompt (str): 图像描述提示词
        size (str, 可选): 图像尺寸，默认为'1024*1024'
        n (int, 可选): 生成图像数量，默认为1
    
    返回:
        str: 任务ID，失败时返回None  
    """
    url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis'
    
    headers = {
        'X-DashScope-Async': 'enable',
        'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'wanx2.1-t2i-turbo',
        'input': {
            'prompt': prompt
        },
        'parameters': {
            'size': size,
            'n': n
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        task_id = result.get('output', {}).get('task_id')
        
        return task_id
    except Exception as e:
        app.logger.error(f"创建图像任务失败: {str(e)}")
        return None

def get_task_result(task_id):
    """
    根据task_id查询任务结果
    
    参数:
        task_id (str): 任务ID
    
    返回:
        dict: 任务结果，失败时返回None
    """
    url = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
    
    headers = {
        'Authorization': f'Bearer {DASHSCOPE_API_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        app.logger.error(f"查询任务结果失败: {str(e)}")
        return None