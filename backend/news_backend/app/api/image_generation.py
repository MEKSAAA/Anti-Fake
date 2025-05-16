from flask import request, Blueprint
import time
import json
from app import app, db
from app.utils.common import api_response, extract_text_from_file
from werkzeug.utils import secure_filename
from app.models.image_generation import (
    ImageGeneration, image_generation_schema, image_generations_schema,
    get_available_image_styles, ImageStyle
)
from app.services.image_gen_service import create_image_task, get_task_result, save_generated_image
image_generation_bp = Blueprint('image_generation', __name__)
# DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')

@image_generation_bp.route('/styles', methods=['GET'])
def get_styles():
    """
    获取所有可用的图像风格
    
    返回:
        JSON: 包含可用图像风格列表的响应
        
    异常:
        500: 获取图像风格列表失败
    """
    try:
        styles = get_available_image_styles()
        return api_response(True, "获取图像风格列表成功", styles)
    except Exception as e:
        return api_response(False, f"获取图像风格列表失败: {str(e)}", status_code=500)

@image_generation_bp.route('/generate', methods=['POST'])     
def generate_image():
    """
    根据文本描述生成图像
    
    参数(表单):
        user_id (str): 用户ID
        content (str): 文本描述内容，或上传的文本文件
        size (str, 可选): 图像尺寸，默认为1024*1024
        num_images (int, 可选): 生成图像数量，默认为1
        style (str, 可选): 图像风格
        
    返回:
        JSON: 包含生成图像URL的响应
        
    异常:
        400: 参数错误或文件处理错误
        401: 未提供用户ID
        408: 任务超时
        500: 创建任务失败或执行任务失败
    """
    user_id = request.form.get('user_id')
    if not user_id:
        return api_response(False, "请先登录", status_code=401)
    # 获取文本内容
    content = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            try:
                content = extract_text_from_file(file)
                source = secure_filename(file.filename)
            except Exception as e:
                return api_response(False, f"文件处理错误: {str(e)}", status_code=400)
    else:
        content = request.form.get('content')
    if not content:
        return api_response(False, "请提供需要生成图片的文本内容", status_code=400)
    prompt = content
    
    # 获取图像参数
    size = request.form.get('size', '1024*1024')
    num_images = int(request.form.get('num_images', '1'))
    style = request.form.get('style')
    
    # 验证风格是否有效
    if style:
        valid_styles = [s.value for s in ImageStyle]
        if style not in valid_styles:
            return api_response(False, f"无效的图像风格，可用选项: {', '.join(valid_styles)}", status_code=400)
    else:
        style = ImageStyle.REALISTIC.value  # 默认使用写实风格
    # 获取风格描述
    style_description = next((item['description'] for item in get_available_image_styles() if item['value'] == style), "")
    prompt = f"{prompt}。图片的风格为：{style_description}"

    # 步骤1: 创建任务获取task_id
    task_id = create_image_task(prompt, size, num_images)
    
    if not task_id:
        return api_response(False, "没有创建图片生成任务", status_code=500)
    
    # 创建数据库记录
    image_generation = ImageGeneration(
        user_id=user_id,
        prompt_text=content,
        image_style=style,
        image_size=size,
        image_num=num_images,
        task_id=task_id
    )
    db.session.add(image_generation)
    db.session.commit()
    
    # 步骤2: 轮询查询任务结果
    max_retries = 30
    retry_interval = 2  # 每2秒查询一次
    
    for i in range(max_retries):
        result = get_task_result(task_id)
        
        if not result:
            return api_response(False, "没有得到返回结果", status_code=500)
        
        task_status = result.get('output', {}).get('task_status')
        
        if task_status == 'SUCCEEDED':
            # 任务成功，返回图片URL
            results = result.get('output', {}).get('results', [])
            
            # 保存图片到本地
            saved_images = []
            image_paths_array = []
            
            for idx, image_result in enumerate(results):
                image_url = image_result.get('url')
                if image_url:
                    try:
                        # 下载并保存图片
                        image_path = save_generated_image(user_id, image_url, idx)
                        # 添加本地路径到结果中
                        image_result['local_path'] = image_path
                        saved_images.append(image_result)
                        
                        # 收集所有图片路径
                        image_paths_array.append(image_path)
                    except Exception as e:
                        app.logger.error(f"保存图片失败: {str(e)}")
            
            # 将所有图片路径作为JSON字符串存储到数据库
            if image_paths_array:
                image_generation.image_paths = json.dumps(image_paths_array)
                db.session.commit()
            
            return api_response(
                True, 
                "成功生成图片", 
                {
                    'task_id': task_id,
                    'images': saved_images
                })
        
        elif task_status == 'FAILED':
            return api_response(
                False, 
                "任务失败", 
                {
                    'task_id': task_id,
                    'details': result.get('output', {})
                },
                status_code=500)
        
        elif task_status in ['PENDING', 'RUNNING']:
            # 任务仍在进行中，等待后再次查询
            time.sleep(retry_interval)
            continue
        
        else:
            return api_response(
                False, 
                f"未知状态:{task_status}", 
                {
                    'task_id': task_id,
                },
                status_code=500)
    
    # 超过最大重试次数，返回超时错误
    return api_response(
                False, 
                "超时", 
                {
                    'task_id': task_id,
                },
                status_code=408)

@image_generation_bp.route('/history/<user_id>', methods=['GET'])
def get_generation_history(user_id):
    """
    获取用户的图像生成历史
    
    参数:
        user_id (str): 用户ID (URL参数)
    
    返回:
        JSON: 包含用户图像生成历史的响应
    
    异常:
        404: 未找到用户的图像生成历史
        500: 获取历史记录失败
    """
    try:
        # 查询历史记录
        history = ImageGeneration.query.filter_by(user_id=user_id).order_by(
            ImageGeneration.generation_date.desc()
        ).all()
        
        if not history:
            return api_response(False, f"未找到用户 {user_id} 的图像生成历史", status_code=404)
        
        # 处理所有记录中的图片路径，从JSON字符串转换为数组
        history_data = image_generations_schema.dump(history)
        for item in history_data:
            if item.get('image_paths'):
                try:
                    item['image_paths'] = json.loads(item['image_paths'])
                except:
                    item['image_paths'] = []
        
        # 返回历史记录
        return api_response(True, "获取图像生成历史成功", history_data)
    
    except Exception as e:
        return api_response(False, f"获取图像生成历史失败: {str(e)}", status_code=500)

# def save_generated_image(user_id, image_url, index=0):
#     """
#     下载并保存生成的图片
#     :param user_id: 用户ID
#     :param image_url: 图片URL
#     :param index: 图片索引（用于同一批次多张图片）
#     :return: 保存的图片路径
#     """
#     # 创建保存路径
#     static_dir = os.path.join(current_app.root_path, '..','static')
#     static_dir = os.path.abspath(static_dir)
#     if not os.path.exists(static_dir):
#         os.makedirs(static_dir)
    
#     generate_dir = os.path.join(static_dir, 'image_generation')
#     if not os.path.exists(generate_dir):
#         os.makedirs(generate_dir)
    
#     user_dir = os.path.join(generate_dir, user_id)
#     if not os.path.exists(user_dir):
#         os.makedirs(user_dir)
        
#     # 从URL中提取文件扩展名
#     url_path = image_url.split('?')[0]
#     file_extension = os.path.splitext(os.path.basename(url_path))[1]
#     if not file_extension:
#         # 如果URL中没有扩展名，默认使用.png
#         file_extension = '.png'
    
#     # 使用时间戳命名
#     timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
#     # 如果是批次中的第一张图片，不添加索引
#     if index == 0:
#         filename = f"{timestamp}{file_extension}"
#     else:
#         # 对于批次中的其他图片，添加索引
#         filename = f"{timestamp}_{index}{file_extension}"
    
#     # 保存路径
#     image_path = os.path.join(user_dir, filename)
    
#     # 下载图片
#     urllib.request.urlretrieve(image_url, image_path)
    
#     return image_path

# def create_image_task(prompt, size='1024*1024', n=1):
#     """创建图像生成任务，获取task_id"""
#     url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis'
    
#     headers = {
#         'X-DashScope-Async': 'enable',
#         'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
#         'Content-Type': 'application/json'
#     }
    
#     data = {
#         'model': 'wanx2.1-t2i-turbo',
#         'input': {
#             'prompt': prompt
#         },
#         'parameters': {
#             'size': size,
#             'n': n
#         }
#     }
    
#     try:
#         response = requests.post(url, headers=headers, json=data)
#         response.raise_for_status()
        
#         result = response.json()
#         task_id = result.get('output', {}).get('task_id')
        
#         return task_id
#     except Exception as e:
#         app.logger.error(f"创建图像任务失败: {str(e)}")
#         return None

# def get_task_result(task_id):
#     """根据task_id查询任务结果"""
#     url = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
    
#     headers = {
#         'Authorization': f'Bearer {DASHSCOPE_API_KEY}'
#     }
    
#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
        
#         return response.json()
#     except Exception as e:
#         app.logger.error(f"查询任务结果失败: {str(e)}")
#         return None