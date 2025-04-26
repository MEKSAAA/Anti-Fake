from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.news_detection import NewsDetectionHistory, news_detection_schema
import os
from werkzeug.utils import secure_filename
import json
import requests
from dotenv import load_dotenv
from .image_detection import translate_text,save_image
from .text_detection import detect_text_content
from .utils import api_response,extract_text_from_file,update_statistics
# 加载环境变量
load_dotenv()

from flask import Blueprint
news_detection_bp = Blueprint('news_detection', __name__)

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
    
    
@news_detection_bp.route('/image-detection', methods=['POST'])
def detect_image():
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
        # text=translate_text(content)
        text=content
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
                try:
                    detection = NewsDetectionHistory(
                        user_id=user_id,
                        source=source,
                        content=content,
                        image_path=image_path,
                        detect_image_path=result.get("detect_image_path"),
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