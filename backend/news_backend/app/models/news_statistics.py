from app import db, ma
from app.utils.time_util import china_time_now

class NewsStatistics(db.Model):
    __tablename__ = 'news_statistics'
    
    total_news_count = db.Column(db.Integer, default=0)
    total_fake_count = db.Column(db.Integer, default=0)
    total_real_count = db.Column(db.Integer, default=0)
    total_users = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=china_time_now, primary_key=True)
    
    def __init__(self, total_news_count=0, total_fake_count=0, 
                 total_real_count=0, total_users=0):
        self.total_news_count = total_news_count
        self.total_fake_count = total_fake_count
        self.total_real_count = total_real_count
        self.total_users = total_users

class NewsStatisticsByUser(db.Model):
    __tablename__ = 'news_statistics_by_user'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    total_news_count = db.Column(db.Integer, default=0)
    total_fake_count = db.Column(db.Integer, default=0)
    total_real_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=china_time_now)
    
    def __init__(self, user_id, total_news_count=0, total_fake_count=0, total_real_count=0):
        self.user_id = user_id
        self.total_news_count = total_news_count
        self.total_fake_count = total_fake_count
        self.total_real_count = total_real_count

# 创建Schema
class NewsStatisticsSchema(ma.Schema):
    class Meta:
        fields = ('total_news_count', 'total_fake_count',
                  'total_real_count', 'total_users', 'last_updated')

class NewsStatisticsByUserSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'total_news_count',
                  'total_fake_count', 'total_real_count', 'last_updated')

# 初始化schema
news_stats_schema = NewsStatisticsSchema()
news_stats_by_user_schema = NewsStatisticsByUserSchema()
news_stats_by_users_schema = NewsStatisticsByUserSchema(many=True) 