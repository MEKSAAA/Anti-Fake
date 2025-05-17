from app import db, ma
from app.utils.time_util import china_time_now
from enum import Enum

# 定义文本优化风格枚举
class TextStyle(Enum):
    FORMAL = "formal"              # 正式风格
    CASUAL = "casual"              # 休闲风格
    ACADEMIC = "academic"          # 学术风格
    JOURNALISTIC = "journalistic"  # 新闻报道风格
    NARRATIVE = "narrative"        # 叙事风格
    PERSUASIVE = "persuasive"      # 说服力风格
    CONCISE = "concise"            # 简洁风格
    ELABORATE = "elaborate"        # 详细风格
    PROFESSIONAL = "professional"  # 专业风格

# 文本风格说明
TEXT_STYLE_DESCRIPTIONS = {
    TextStyle.FORMAL.value: "正式、规范的表达方式，适合官方文档和商务通讯",
    TextStyle.CASUAL.value: "轻松、日常的表达方式，适合博客和社交媒体",
    TextStyle.ACADEMIC.value: "严谨、引用丰富的表达方式，适合学术论文和研究报告",
    TextStyle.JOURNALISTIC.value: "客观、事实为主的表达方式，适合新闻报道",
    TextStyle.NARRATIVE.value: "讲故事的表达方式，有情节和场景描述",
    TextStyle.PERSUASIVE.value: "具有说服力的表达方式，适合评论和倡议文章",
    TextStyle.CONCISE.value: "简明扼要的表达方式，去除冗余",
    TextStyle.ELABORATE.value: "详细、全面的表达方式，提供更多背景和细节",
    TextStyle.PROFESSIONAL.value: "行业专业用语的表达方式，适合特定领域的文章"
}

class NewsTextOptimization(db.Model):
    """新闻文本优化记录表"""
    __tablename__ = 'news_text_optimization'
    
    optimization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    original_text = db.Column(db.Text)  # 原始文本
    target_style = db.Column(db.String(50))  # 目标风格
    optimized_text = db.Column(db.Text)  # 优化后的文本
    optimization_date = db.Column(db.DateTime, default=china_time_now)
    
    def __init__(self, user_id, original_text, target_style, optimized_text=None):
        self.user_id = user_id
        self.original_text = original_text
        self.target_style = target_style
        self.optimized_text = optimized_text

# 创建Schema
class NewsTextOptimizationSchema(ma.Schema):
    class Meta:
        fields = ('optimization_id', 'user_id', 'original_text', 
                  'target_style', 'optimized_text', 'optimization_date')

# 初始化schema
news_text_optimization_schema = NewsTextOptimizationSchema()
news_text_optimizations_schema = NewsTextOptimizationSchema(many=True)

# 获取所有可用的文本风格
def get_available_text_styles():
    """返回所有可用的文本优化风格及其描述"""
    return [{
        'value': style.value,
        'name': style.name,
        'description': TEXT_STYLE_DESCRIPTIONS[style.value]
    } for style in TextStyle] 