from app import db, ma
from datetime import datetime

class NewsDetectionHistory(db.Model):
    __tablename__ = 'news_detection_history'
    
    detection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    source = db.Column(db.String(255))
    content = db.Column(db.Text)
    detection_reason = db.Column(db.Text)
    related_news_links = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255))
    detect_image_path= db.Column(db.String(255))
    
    def __init__(self, user_id, source, content, detection_reason=None, related_news_links=None, image_path=None, detect_image_path=None):
        self.user_id = user_id
        self.source = source
        self.content = content
        self.detection_reason = detection_reason
        self.related_news_links = related_news_links
        self.image_path = image_path
        self.detect_image_path = detect_image_path
        
# 创建Schema
class NewsDetectionHistorySchema(ma.Schema):
    class Meta:
        fields = ('detection_id', 'user_id', 'source', 'content', 
                  'detection_reason', 'related_news_links', 'upload_date', 'image_path', 'detect_image_path')

# 初始化schema
news_detection_schema = NewsDetectionHistorySchema()
news_detections_schema = NewsDetectionHistorySchema(many=True) 