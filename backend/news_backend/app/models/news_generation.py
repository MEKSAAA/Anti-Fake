from app import db, ma
from datetime import datetime

class NewsGenerationHistory(db.Model):
    __tablename__ = 'news_generation_history'
    
    generation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    content = db.Column(db.Text)
    generated_title = db.Column(db.String(255))
    generated_content = db.Column(db.Text)
    generation_date = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.String(255))
    
    def __init__(self, user_id, content, generated_title=None, 
                 generated_content=None, generated_by=None):
        self.user_id = user_id
        self.content = content
        self.generated_title = generated_title
        self.generated_content = generated_content
        self.generated_by = generated_by

# 创建Schema
class NewsGenerationHistorySchema(ma.Schema):
    class Meta:
        fields = ('generation_id', 'user_id', 'content', 'generated_title',
                  'generated_content', 'generation_date', 'generated_by')

# 初始化schema
news_generation_schema = NewsGenerationHistorySchema()
news_generations_schema = NewsGenerationHistorySchema(many=True) 