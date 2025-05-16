from flask import Blueprint, request
from app import db
from app.models.news_detection import NewsDetectionHistory, news_detection_schema
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
from app.services.image_detection_service import translate_text, save_image, generate_detection_reason
from app.services.text_detection_service import detect_text_content, search_related_news
from app.utils.common import api_response, extract_text_from_file, update_statistics
# 加载环境变量
load_dotenv()

from flask import Blueprint
news_detection_bp = Blueprint('news_detection', __name__)

@news_detection_bp.route('/text-detection', methods=['POST'])
def detect_text_content_api():
    """
    文本内容真假检测API
    
    参数(表单):
        user_id (str): 用户ID
        content (str): 文本内容，或上传的文本文件
        
    返回:
        JSON: 包含检测结果的响应
        
    异常:
        400: 参数缺失或文件处理错误
        401: 未提供用户ID
        500: 检测过程中发生错误
    """
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
    """
    获取用户的检测历史
    
    参数:
        user_id (str): 用户ID (URL参数)
        type (str, 可选): 过滤历史记录类型，可选值: image, text (查询参数)
    
    返回:
        JSON: 包含用户检测历史的响应
        
    异常:
        500: 获取历史记录失败
    """
    try:
        # 获取查询参数
        detection_type = request.args.get('type')  # 可选参数，用于过滤历史记录类型
        
        # 构建查询
        query = NewsDetectionHistory.query.filter_by(user_id=user_id)
        
        # 如果指定了类型，进行过滤
        if detection_type:
            if detection_type == 'image':
                # 图像检测记录（图像路径不为空）
                query = query.filter(NewsDetectionHistory.image_path.isnot(None))
            elif detection_type == 'text':
                # 文本检测记录（图像路径为空）
                query = query.filter(NewsDetectionHistory.image_path.is_(None))
        
        # 按上传时间降序排序并获取结果
        history = query.order_by(NewsDetectionHistory.upload_date.desc()).all()
        
        # 格式化结果
        from app.models.news_detection import news_detections_schema
        history_data = news_detections_schema.dump(history)
        
        # 对结果进行后处理，添加额外信息
        for item in history_data:
            # 确定记录类型
            if item.get('image_path'):
                item['detection_type'] = 'image'
                # 如果有检测后的图像路径，添加到结果中
                if item.get('detect_image_path'):
                    item['has_detection_result'] = True
                else:
                    item['has_detection_result'] = False
            else:
                item['detection_type'] = 'text'
            
            # 处理相关链接，从字符串转为数组
            if item.get('related_news_links'):
                item['related_news_links'] = [link.strip() for link in item['related_news_links'].split(',') if link.strip()]
            else:
                item['related_news_links'] = []
        
        return api_response(True, "获取历史记录成功", history_data)
    except Exception as e:
        return api_response(False, f"获取历史记录失败: {str(e)}", status_code=500) 
    
    
@news_detection_bp.route('/image-detection', methods=['POST'])
def detect_image():
    """
    图像与文本联合检测API
    
    参数(表单):
        user_id (str): 用户ID
        content (str): 文本内容，或上传的文本文件
        image (file): 图像文件
        
    返回:
        JSON: 包含检测结果的响应
        
    异常:
        400: 参数缺失或文件处理错误
        401: 未提供用户ID
        500: 检测过程中发生错误
    """
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return api_response(False, "请先登录", status_code=401)
        source = "图片检测"
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
            return api_response(False, "请提供需要检测的文本内容", status_code=400)
        # 调用DeepSeek API进行翻译
        translated_text = translate_text(content)
        if not translated_text:
            # 如果翻译失败，使用原始内容
            print("翻译失败，使用原始内容")
            text = content
        else:
            print(f"翻译成功: {translated_text[:100]}...")
            text = translated_text
        
        # 获取图片文件
        image_path = None
        if 'image' in request.files:
            image_file = request.files['image']
            image_path = save_image(user_id, image_file)
            print(image_path)
        else:
            return api_response(False, "请提供需要检测的图片文件", status_code=400)
                
        # 调用微服务API
        try:
            json_data = {
                'image_path': image_path,
                'text': text,
            }
            response = requests.post('http://localhost:5001/detect', json=json_data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                # 生成检测理由
                detection_reason = None
                related_news_links = []
                
                try:
                    # 生成检测理由
                    if result.get("is_fake"):
                        manipulation_types = result.get("manipulation_types", [])
                        fake_words = result.get("fake_words", [])
                        detection_reason = generate_detection_reason(
                            manipulation_types=manipulation_types,
                            fake_words=fake_words,
                            text=content,  # 使用原始中文内容生成理由
                            fake_probability=result.get("fake_probability", 0)
                        )
                    
                    # 搜索相关新闻链接
                    related_news_links = search_related_news(content)  # 使用原始中文内容搜索新闻
                    
                    # 将新生成的字段添加到结果中
                    result["detection_reason"] = detection_reason
                    result["related_news_links"] = related_news_links
                except Exception as ai_error:
                    print(f"生成检测理由或相关新闻链接失败: {str(ai_error)}")
                    # 失败时也不中断流程
                
                try:
                    detection = NewsDetectionHistory(
                        user_id=user_id,
                        source=source,
                        content=content,
                        image_path=image_path,
                        detect_image_path=result.get("detect_image_path"),
                        detection_reason=detection_reason,
                        related_news_links=", ".join(related_news_links) if related_news_links else ""
                    )
                    db.session.add(detection)
                    # 更新统计信息
                    try:
                        update_statistics(int(user_id), result["is_fake"])
                    except Exception as stat_error:
                        print(f"更新统计信息失败: {str(stat_error)}")                    
                    # 提交事务
                    db.session.commit()
                    # 成功保存到数据库的情况
                    return api_response(
                        True,
                        "检测完成",
                        data=result
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
                        data=result
                    )
            else:
                return api_response(False, f"检测失败: {response.text}", status_code=response.status_code)
        except requests.RequestException as e:
            return api_response(False, f"调用检测服务失败: {str(e)}", status_code=500)
    except Exception as e:
        return api_response(False, f"检测过程中发生错误: {str(e)}", status_code=500)