from app import db, ma
from app.utils.time_util import china_time_now
from enum import Enum

# 定义概括类型枚举
class SummaryType(Enum):
    BRIEF = "brief"           # 简短摘要
    DETAILED = "detailed"     # 详细摘要
    KEY_POINTS = "key_points" # 要点提取
    ANALYTICAL = "analytical" # 分析性摘要
    NEWS_FLASH = "news_flash" # 新闻快讯

# 概括类型说明
SUMMARY_TYPE_DESCRIPTIONS = {
    SummaryType.BRIEF.value: "简短扼要的内容摘要，通常不超过100字",
    SummaryType.DETAILED.value: "详细的内容摘要，包含主要信息点和关键细节",
    SummaryType.KEY_POINTS.value: "以要点列表形式提取文章的主要观点和信息",
    SummaryType.ANALYTICAL.value: "带有分析性质的摘要，解释文章的背景和意义",
    SummaryType.NEWS_FLASH.value: "极简的新闻快讯形式，只包含最核心信息"
}

class NewsSummary(db.Model):
    """新闻内容概括记录表"""
    __tablename__ = 'news_summary'
    
    summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    original_content = db.Column(db.Text)  # 原始新闻内容
    summary_type = db.Column(db.String(50))  # 概括类型
    summary_content = db.Column(db.Text)  # 概括结果
    summary_date = db.Column(db.DateTime, default=china_time_now)
    
    def __init__(self, user_id, original_content, summary_type, summary_content=None):
        self.user_id = user_id
        self.original_content = original_content
        self.summary_type = summary_type
        self.summary_content = summary_content

# 创建Schema
class NewsSummarySchema(ma.Schema):
    class Meta:
        fields = ('summary_id', 'user_id', 'original_content',
                  'summary_type', 'summary_content', 'summary_date')

# 初始化schema
news_summary_schema = NewsSummarySchema()
news_summaries_schema = NewsSummarySchema(many=True)

# 获取所有可用的概括类型
def get_available_summary_types():
    """返回所有可用的概括类型及其描述"""
    return [{
        'value': summary_type.value,
        'name': summary_type.name,
        'description': SUMMARY_TYPE_DESCRIPTIONS[summary_type.value]
    } for summary_type in SummaryType] 