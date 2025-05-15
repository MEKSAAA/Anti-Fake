from app import db, ma
from datetime import datetime
from enum import Enum

# 定义标题风格枚举
class TitleStyle(Enum):
    INFORMATIVE = "informative"  # 信息型
    ATTRACTIVE = "attractive"    # 吸引型
    QUESTIONING = "questioning"  # 疑问型
    DRAMATIC = "dramatic"        # 戏剧型
    NEUTRAL = "neutral"          # 中立型
    CONCISE = "concise"          # 简洁型
    EMOTIONAL = "emotional"      # 情感型

# 标题风格说明
TITLE_STYLE_DESCRIPTIONS = {
    TitleStyle.INFORMATIVE.value: "清晰准确地传达核心信息，适合严肃新闻",
    TitleStyle.ATTRACTIVE.value: "引人注目、吸引读者点击，适合热点和娱乐新闻",
    TitleStyle.QUESTIONING.value: "以疑问形式引发思考，适合评论和分析文章",
    TitleStyle.DRAMATIC.value: "强调冲突和情节，适合重大事件报道",
    TitleStyle.NEUTRAL.value: "客观平和，不带感情色彩，适合政治和国际新闻",
    TitleStyle.CONCISE.value: "简短精炼，适合快讯和摘要",
    TitleStyle.EMOTIONAL.value: "带有情感色彩，引起共鸣，适合社会和人文新闻"
}

class NewsTitleGeneration(db.Model):
    """新闻标题生成记录表"""
    __tablename__ = 'news_title_generation'
    
    generation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    original_content = db.Column(db.Text)  # 原始新闻内容
    title_style = db.Column(db.String(50))  # 标题风格
    generated_title = db.Column(db.String(255))  # 生成的标题
    generation_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, original_content, title_style, generated_title=None):
        self.user_id = user_id
        self.original_content = original_content
        self.title_style = title_style
        self.generated_title = generated_title

# 创建Schema
class NewsTitleGenerationSchema(ma.Schema):
    class Meta:
        fields = ('generation_id', 'user_id', 'original_content', 
                  'title_style', 'generated_title', 'generation_date')

# 初始化schema
news_title_generation_schema = NewsTitleGenerationSchema()
news_title_generations_schema = NewsTitleGenerationSchema(many=True)

# 获取所有可用的标题风格
def get_available_title_styles():
    """返回所有可用的标题风格及其描述"""
    return [{
        'value': style.value,
        'name': style.name,
        'description': TITLE_STYLE_DESCRIPTIONS[style.value]
    } for style in TitleStyle] 