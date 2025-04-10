from app import db, ma
from datetime import datetime

class NewsSummaryHistory(db.Model):
    __tablename__ = 'news_summary_history'
    
    summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    content = db.Column(db.Text)
    summary_content = db.Column(db.Text)
    generation_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, content, summary_content=None):
        self.user_id = user_id
        self.content = content
        self.summary_content = summary_content

# 创建Schema
class NewsSummaryHistorySchema(ma.Schema):
    class Meta:
        fields = ('summary_id', 'user_id', 'content', 'summary_content', 'generation_date')

# 初始化schema
news_summary_schema = NewsSummaryHistorySchema()
news_summaries_schema = NewsSummaryHistorySchema(many=True) 