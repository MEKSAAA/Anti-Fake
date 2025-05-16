from flask import Blueprint, request, jsonify
from app import db
from app.models.news_statistics import (
    NewsStatistics, NewsStatisticsByUser, 
    news_stats_schema, news_stats_by_user_schema, news_stats_by_users_schema
)
from app.models.news_detection import NewsDetectionHistory
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta
from app.utils.common import api_response

news_statistics_bp = Blueprint('news_statistics', __name__)

@news_statistics_bp.route('/global', methods=['GET'])
def get_global_statistics():
    """
    获取全局统计数据
    
    返回:
        JSON: 包含全局统计数据的响应
        
    异常:
        500: 获取全局统计数据失败
    """
    try:
        # 获取全局统计信息
        stats = NewsStatistics.query.first()
        
        if not stats:
            # 如果没有统计记录，创建一个新的
            stats = NewsStatistics()
            db.session.add(stats)
            db.session.commit()
        
        # 返回统计数据
        return api_response(True, "获取全局统计数据成功", news_stats_schema.dump(stats))
    
    except Exception as e:
        return api_response(False, f"获取全局统计数据失败: {str(e)}", status_code=500)

@news_statistics_bp.route('/user/<user_id>', methods=['GET'])
def get_user_statistics(user_id):
    """
    获取指定用户的统计数据
    
    参数:
        user_id (str): 用户ID (URL参数)
    
    返回:
        JSON: 包含用户统计数据的响应
        
    异常:
        404: 未找到指定用户的统计记录
        500: 获取用户统计数据失败
    """
    try:
        # 获取用户统计信息
        stats = NewsStatisticsByUser.query.filter_by(user_id=user_id).first()
        
        if not stats:
            # 如果没有统计记录，返回提示信息
            return api_response(False, f"未找到ID为{user_id}的用户统计记录", status_code=404)
        
        # 返回统计数据
        return api_response(True, "获取用户统计数据成功", news_stats_by_user_schema.dump(stats))
    
    except Exception as e:
        return api_response(False, f"获取用户统计数据失败: {str(e)}", status_code=500)

@news_statistics_bp.route('/trend', methods=['GET'])
def get_detection_trend():
    """
    获取检测趋势数据
    
    参数:
        days (int, 可选): 要查询的天数，默认为7天 (查询参数)
    
    返回:
        JSON: 包含检测趋势数据的响应
        
    异常:
        500: 获取检测趋势数据失败
    """
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)  # 默认过去7天
        
        # 计算起始日期
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 按日期分组统计检测数量
        daily_counts = db.session.query(
            func.date(NewsDetectionHistory.upload_date).label('date'),
            func.count().label('count'),
            func.sum(case((NewsDetectionHistory.detection_reason.ilike('%虚假%'), 1), else_=0)).label('fake_count'),
            func.sum(case((~NewsDetectionHistory.detection_reason.ilike('%虚假%'), 1), else_=0)).label('real_count')
        ).filter(
            NewsDetectionHistory.upload_date >= start_date
        ).group_by(
            func.date(NewsDetectionHistory.upload_date)
        ).order_by(
            func.date(NewsDetectionHistory.upload_date)
        ).all()
        
        # 如果没有数据，返回空数组而不是404
        if not daily_counts:
            return api_response(True, f"过去{days}天内无检测数据", [])
        
        # 格式化结果
        trend_data = [{
            'date': str(day.date),
            'total_count': day.count,
            'fake_count': day.fake_count,
            'real_count': day.real_count
        } for day in daily_counts]
        
        return api_response(True, "获取检测趋势数据成功", trend_data)
    
    except Exception as e:
        return api_response(False, f"获取检测趋势数据失败: {str(e)}", status_code=500)

@news_statistics_bp.route('/detection-types', methods=['GET'])
def get_detection_types():
    """
    获取不同检测类型的统计数据
    
    返回:
        JSON: 包含不同检测类型统计数据的响应
        
    异常:
        500: 获取检测类型统计数据失败
    """
    try:
        # 统计图像检测和文本检测的数量
        image_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.isnot(None)
        ).scalar() or 0
        
        text_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.is_(None)
        ).scalar() or 0
        
        # 统计检测结果（真假）
        fake_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        real_count = db.session.query(func.count()).filter(
            ~NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        # 按照图像检测和文本检测分别统计真假结果
        image_fake_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.isnot(None),
            NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        image_real_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.isnot(None),
            ~NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        text_fake_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.is_(None),
            NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        text_real_count = db.session.query(func.count()).filter(
            NewsDetectionHistory.image_path.is_(None),
            ~NewsDetectionHistory.detection_reason.ilike('%虚假%')
        ).scalar() or 0
        
        # 组装结果
        result = {
            'total': {
                'total_count': image_count + text_count,
                'fake_count': fake_count,
                'real_count': real_count
            },
            'image_detection': {
                'total_count': image_count,
                'fake_count': image_fake_count,
                'real_count': image_real_count
            },
            'text_detection': {
                'total_count': text_count,
                'fake_count': text_fake_count,
                'real_count': text_real_count
            }
        }
        
        return api_response(True, "获取检测类型统计数据成功", result)
    
    except Exception as e:
        return api_response(False, f"获取检测类型统计数据失败: {str(e)}", status_code=500)

@news_statistics_bp.route('/recent-detections', methods=['GET'])
def get_recent_detections():
    """
    获取最近的检测记录统计
    
    参数:
        limit (int, 可选): 要获取的记录数量，默认为10条 (查询参数)
    
    返回:
        JSON: 包含最近检测记录的响应
        
    异常:
        404: 暂无检测记录
        500: 获取最近检测记录失败
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)  # 默认最近10条
        
        # 查询最近的检测记录
        recent_detections = NewsDetectionHistory.query.order_by(
            NewsDetectionHistory.upload_date.desc()
        ).limit(limit).all()
        
        if not recent_detections:
            return api_response(False, "暂无检测记录", status_code=404)
            
        # 使用现有的schema转换结果
        from app.models.news_detection import news_detections_schema
        result = news_detections_schema.dump(recent_detections)
        
        # 添加额外信息
        for item in result:
            # 确定记录类型
            if item.get('image_path'):
                item['detection_type'] = 'image'
            else:
                item['detection_type'] = 'text'
                
            # 判断是否为虚假内容
            if item.get('detection_reason') and '虚假' in item['detection_reason']:
                item['is_fake'] = True
            else:
                item['is_fake'] = False
        
        return api_response(True, "获取最近检测记录成功", result)
    
    except Exception as e:
        return api_response(False, f"获取最近检测记录失败: {str(e)}", status_code=500) 