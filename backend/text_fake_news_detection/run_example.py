import os
from dotenv import load_dotenv
import json

from services.detector import FakeNewsDetector
from services.web_search import WebSearchTool

# 加载环境变量
load_dotenv()

# 初始化服务
fake_news_detector = FakeNewsDetector()
web_search_tool = WebSearchTool()

# 示例1：假新闻示例
fake_news_example = """
震惊！科学家发现喝水会导致癌症

近日，一项由国际顶尖研究机构进行的研究表明，日常饮用的普通水可能会导致癌症。据该研究负责人张教授介绍，他们在为期10年的研究中发现，所有癌症患者生前都曾饮用过水，这一惊人发现表明水与癌症之间存在不可忽视的联系。

该研究团队分析了全球50个国家的数据，发现癌症发病率与人均用水量呈正相关。"这不是巧合，"张教授强调，"我们已经确定了水中的二氢一氧化物是主要致癌物质。"

世界卫生组织已经紧急召开会议，准备发布全球饮水警告。与此同时，多家矿泉水公司股价暴跌，市值蒸发超过500亿美元。

专家建议，民众应立即停止饮水，改用其他液体如可乐、果汁等替代品。政府也计划投入巨资开发无水替代品。
"""

# 示例2：真实新闻示例
real_news_example = """
研究表明适量饮水有益健康

据最新医学研究显示，每天保持充足的水分摄入对人体健康具有多方面的益处。哈佛医学院的一项研究发现，成年人每天饮水量达到2升以上的群体，肾脏疾病发病率明显低于饮水不足的群体。

"水是生命之源，它参与人体几乎所有的生理过程，"研究负责人李教授解释道，"从细胞代谢到温度调节，水都扮演着不可替代的角色。"

美国疾病控制与预防中心(CDC)建议，成年男性每天应摄入约3.7升液体，女性约为2.7升，其中包括从食物中获取的水分。

研究同时指出，许多人存在轻微脱水状态而不自知，这可能导致注意力不集中、疲劳等问题。专家建议，即使没有口渴感，也应养成定时饮水的习惯。
"""

def run_detection(text, title):
    """运行检测并显示结果"""
    print("="*80)
    print(f"示例: {title}")
    print("="*80)
    print(text)
    print("-"*80)
    
    # 不使用增强功能
    print("检测中（基础模式）...")
    result_basic = fake_news_detector.detect(text)
    
    is_fake = result_basic.get('is_fake')
    confidence = result_basic.get('confidence', 0)
    
    if is_fake is not None:
        status = "假新闻" if is_fake else "真实新闻"
        print(f"基础检测结果: 这很可能是{status} (置信度: {confidence}%)")
    else:
        print("基础检测结果: 无法确定")
    
    # 使用网络搜索
    print("\n检测中（使用网络搜索）...")
    result_web = fake_news_detector.detect(
        text,
        use_web_search=True,
        web_search_tool=web_search_tool
    )
    
    is_fake = result_web.get('is_fake')
    confidence = result_web.get('confidence', 0)
    
    if is_fake is not None:
        status = "假新闻" if is_fake else "真实新闻"
        print(f"网络搜索检测结果: 这很可能是{status} (置信度: {confidence}%)")
    else:
        print("网络搜索检测结果: 无法确定")
    
    print("\n详细理由:")
    print(result_web.get('reasoning', '无详细理由'))
    
    print("\n" + "="*80)
    print("\n")

def main():
    """运行示例检测"""
    print("假新闻检测系统 - 示例运行")
    print("\n注意: 这个脚本会运行两个示例，并使用网络搜索功能。请确保已设置好DeepSeek API密钥。\n")
    
    # 检测假新闻示例
    run_detection(fake_news_example, "假新闻示例")
    
    # 检测真实新闻示例
    run_detection(real_news_example, "真实新闻示例")

if __name__ == "__main__":
    main() 