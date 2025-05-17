from app import db, ma
from enum import Enum
from app.utils.time_util import china_time_now
# 定义图像风格枚举
class ImageStyle(Enum):
    REALISTIC = "realistic"            # 写实风格
    WATERCOLOR = "watercolor"          # 水彩风格
    OIL_PAINTING = "oil_painting"      # 油画风格
    INK_PAINTING = "ink_painting"      # 水墨风格
    ANIME = "anime"                    # 动漫风格(日本二次元)
    MINIMALIST = "minimalist"          # 极简风格
    TECH = "tech"                      # 科技感风格
    CARTOON_3D = "cartoon_3d"          # 3D卡通风格
    ABSTRACT = "abstract"              # 抽象风格

# 图像风格说明
IMAGE_STYLE_DESCRIPTIONS = {
    ImageStyle.REALISTIC.value: "真实逼真的摄影表现风格，注重细节和自然光影效果，清晰呈现事件场景",
    ImageStyle.WATERCOLOR.value: "水彩绘画效果，色彩通透自然，具有轻盈流动的质感和柔和的色彩过渡",
    ImageStyle.OIL_PAINTING.value: "油画艺术风格，色彩厚重饱满，具有明显的笔触层次和深厚的艺术质感",
    ImageStyle.INK_PAINTING.value: "中国传统水墨画风格，黑白灰层次丰富，线条流畅，意境悠远，展现东方美学",
    ImageStyle.ANIME.value: "日本动漫二次元风格，色彩明亮，线条简洁，人物特征夸张，具有鲜明的卡通特点",
    ImageStyle.MINIMALIST.value: "极简主义设计，减少干扰元素，突出主体，采用简洁的线条、形状和有限的色彩",
    ImageStyle.TECH.value: "现代科技风格，融合科幻、霓虹与机械元素，具有未来感，使用蓝色调、网格、全息和数字元素，展现高科技氛围",
    ImageStyle.CARTOON_3D.value: "三维立体卡通风格，角色和场景具有体积感，色彩鲜艳，类似现代动画电影效果",
    ImageStyle.ABSTRACT.value: "抽象艺术表现手法，不拘泥于具象再现，通过形状、色彩和构图传达情感和概念"
}

class ImageGeneration(db.Model):
    """图像生成记录表"""
    __tablename__ = 'image_generation'
    
    generation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    prompt_text = db.Column(db.Text)  # 生成图片的提示文本
    image_style = db.Column(db.String(50))  # 图片风格
    image_size = db.Column(db.String(50))  # 图片尺寸
    image_num = db.Column(db.Integer)  # 生成图片数量
    image_paths = db.Column(db.Text)  # 生成的图片路径集合，以JSON字符串形式存储
    generation_date = db.Column(db.DateTime, default=china_time_now)
    task_id = db.Column(db.String(255))  # API任务ID
    
    def __init__(self, user_id, prompt_text, image_style, image_size, image_num=1, image_paths=None, task_id=None):
        self.user_id = user_id
        self.prompt_text = prompt_text
        self.image_style = image_style
        self.image_size = image_size
        self.image_num = image_num
        self.image_paths = image_paths
        self.task_id = task_id

# 创建Schema
class ImageGenerationSchema(ma.Schema):
    class Meta:
        fields = ('generation_id', 'user_id', 'prompt_text', 'image_style', 
                  'image_size', 'image_num', 'image_paths', 'generation_date', 'task_id')

# 初始化schema
image_generation_schema = ImageGenerationSchema()
image_generations_schema = ImageGenerationSchema(many=True)

# 获取所有可用的图像风格
def get_available_image_styles():
    """返回所有可用的图像风格及其描述"""
    return [{
        'value': style.value,
        'name': style.name,
        'description': IMAGE_STYLE_DESCRIPTIONS[style.value]
    } for style in ImageStyle] 