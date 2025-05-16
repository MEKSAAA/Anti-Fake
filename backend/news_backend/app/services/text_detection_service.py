from openai import OpenAI
import os
import jieba
import jieba.analyse
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import random
# 加载环境变量
load_dotenv()
# 获取API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 文本假新闻检测的prompt模版
TEXT_DETECTION_PROMPT = """
你是一个专业的文本真假信息检测专家。请分析以下内容：

【待检测内容】
{content}

【我们搜索到的相关事实信息】
{search_results}

请根据待检测内容和我们提供的相关事实信息，进行真假判断。

请用自然语言回答，但必须在回答的第一句话中明确给出"真实"或"虚假"的判断。
然后详细说明你的判断理由，包括：
1. 事实核查（根据我们提供的搜索结果和你已有的知识进行核查）
2. 逻辑分析
3. 语言特征
4. 信息来源
5. 专业分析

请确保第一句话包含明确的判断结果。
"""

# 预定义的可信新闻源
TRUSTED_NEWS_SOURCES = {
    "政府与官方媒体": [
        {"name": "新华网", "url": "http://www.xinhuanet.com/"},
        {"name": "人民网", "url": "http://www.people.com.cn/"},
        {"name": "央视网", "url": "http://www.cctv.com/"},
        {"name": "中国政府网", "url": "http://www.gov.cn/"},
        {"name": "中国日报", "url": "http://www.chinadaily.com.cn/"}
    ],
    "主流媒体": [
        {"name": "澎湃新闻", "url": "https://www.thepaper.cn/"},
        {"name": "财新网", "url": "http://www.caixin.com/"},
        {"name": "南方周末", "url": "http://www.infzm.com/"},
        {"name": "第一财经", "url": "https://www.yicai.com/"},
        {"name": "界面新闻", "url": "https://www.jiemian.com/"}
    ],
    "事实核查网站": [
        {"name": "较真查证平台", "url": "https://fact.qq.com/"},
        {"name": "食品辟谣网", "url": "https://www.meiri8.com/"},
        {"name": "腾讯辟谣中心", "url": "https://piyao.qq.com/"},
        {"name": "中国互联网联合辟谣平台", "url": "https://www.piyao.org.cn/"}
    ],
    "国际媒体": [
        {"name": "BBC中文网", "url": "https://www.bbc.com/zhongwen"},
        {"name": "纽约时报中文网", "url": "https://cn.nytimes.com/"},
        {"name": "路透社中文网", "url": "https://cn.reuters.com/"},
        {"name": "法国国际广播电台中文版", "url": "https://www.rfi.fr/cn/"},
        {"name": "德国之声中文网", "url": "https://www.dw.com/zh/"}
    ]
}

# 搜索相关新闻的函数
def search_related_news(text, max_links=3):
    """
    搜索与给定文本相关的新闻链接
    使用文本的第一句话进行搜索，并结合可信新闻源
    """
    try:
        # 提取第一句话作为搜索关键词
        first_sentence = ""
        # 尝试按常见的标点符号分割，提取第一句话
        for delimiter in ["。", "！", "？", ".", "!", "?"]:
            if delimiter in text:
                first_sentence = text.split(delimiter)[0].strip()
                break
        
        # 如果无法通过标点符号分割，就取前100个字符
        if not first_sentence:
            first_sentence = text[:100].strip()
            
        # 确保搜索词不会太长
        search_query = first_sentence[:50]
        print(f"搜索关键词(第一句话): {search_query}")
        
        related_links = []
        
        # 1. 基于第一句话匹配预定义的新闻源
        # 随机选择一个分类
        category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
        # 从该分类中随机选择一个新闻源
        news_source = random.choice(TRUSTED_NEWS_SOURCES[category])
        # 构建一个基于第一句话的URL
        related_links.append({
            "title": f"{news_source['name']}相关报道",
            "link": f"{news_source['url']}search?q={search_query}"
        })
        
        # 2. 尝试使用百度搜索(简单模拟，实际使用时可能需要更复杂的处理)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.baidu.com/s?wd={search_query}"
            
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取搜索结果
                search_results = soup.select('.result.c-container')
                
                for result in search_results[:2]:  # 只取前2个结果
                    title_elem = result.select_one('.t a')
                    if title_elem:
                        title = title_elem.get_text()
                        link = title_elem.get('href', '')
                        if link and link.startswith('http'):
                            related_links.append({
                                "title": title,
                                "link": link
                            })
        except Exception as e:
            print(f"百度搜索失败: {str(e)}")
            # 如果百度搜索失败，添加一些预定义的辟谣网站
            related_links.append({
                "title": "较真查证平台",
                "link": "https://fact.qq.com/"
            })
            related_links.append({
                "title": "中国互联网联合辟谣平台",
                "link": "https://www.piyao.org.cn/"
            })
        
        # 如果没有找到足够的相关链接，添加一些默认的可信新闻源
        while len(related_links) < max_links:
            category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
            source = random.choice(TRUSTED_NEWS_SOURCES[category])
            link_info = {
                "title": source["name"],
                "link": source["url"]
            }
            if link_info not in related_links:
                related_links.append(link_info)
        
        # 只返回链接部分
        return [link_info["link"] for link_info in related_links[:max_links]]
        
    except Exception as e:
        print(f"搜索相关新闻失败: {str(e)}")
        # 返回一些默认的辟谣网站
        return [
            "https://fact.qq.com/",
            "https://www.piyao.org.cn/",
            "http://www.xinhuanet.com/"
        ][:max_links]

# 搜索相关新闻并获取内容的函数
def search_and_fetch_news(text, max_results=3):
    """
    搜索与给定文本相关的新闻并获取内容摘要
    """
    try:
        # 提取第一句话作为搜索关键词
        first_sentence = ""
        # 尝试按常见的标点符号分割，提取第一句话
        for delimiter in ["。", "！", "？", ".", "!", "?"]:
            if delimiter in text:
                first_sentence = text.split(delimiter)[0].strip()
                break
        
        # 如果无法通过标点符号分割，就取前100个字符
        if not first_sentence:
            first_sentence = text[:100].strip()
            
        # 确保搜索词不会太长
        search_query = first_sentence[:50]
        print(f"搜索关键词(第一句话): {search_query}")
        
        search_results = []
        fetched_content = ""
        
        # 1. 尝试使用百度搜索
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.baidu.com/s?wd={search_query}"
            
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取搜索结果
                search_results = soup.select('.result.c-container')
                
                for i, result in enumerate(search_results[:max_results]):
                    # 提取标题和摘要
                    title_elem = result.select_one('.t a')
                    abstract_elem = result.select_one('.c-abstract')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href', '')
                        abstract = abstract_elem.get_text().strip() if abstract_elem else "无摘要"
                        
                        # 添加到搜索结果摘要中
                        fetched_content += f"信息来源{i+1}：{title}\n"
                        fetched_content += f"摘要：{abstract}\n"
                        fetched_content += f"链接：{link}\n\n"
        except Exception as e:
            print(f"百度搜索失败: {str(e)}")
        
        # 2. 如果百度搜索失败或没有结果，添加一些预定义信息
        if not fetched_content:
            # 从预定义新闻源中获取一些基本信息
            fetched_content = "未找到确切相关信息，以下是一些可信新闻源供参考：\n\n"
            
            for i, category in enumerate(TRUSTED_NEWS_SOURCES.keys()):
                if i >= 2:  # 只取前两个分类
                    break
                    
                sources = TRUSTED_NEWS_SOURCES[category]
                fetched_content += f"权威{category}：\n"
                
                for j, source in enumerate(sources[:3]):  # 每个分类取前三个
                    fetched_content += f"- {source['name']}: {source['url']}\n"
                
                fetched_content += "\n"
        
        # 返回搜索到的内容摘要和相关链接
        related_links = []
        for result in search_results[:max_results]:
            title_elem = result.select_one('.t a')
            if title_elem and title_elem.get('href', '').startswith('http'):
                related_links.append(title_elem.get('href'))
        
        # 如果没有足够的链接，添加一些预定义的链接
        while len(related_links) < max_results:
            category = random.choice(list(TRUSTED_NEWS_SOURCES.keys()))
            source = random.choice(TRUSTED_NEWS_SOURCES[category])
            link = source["url"]
            if link not in related_links:
                related_links.append(link)
                
        return {
            "content_summary": fetched_content,
            "related_links": related_links[:max_results]
        }
        
    except Exception as e:
        print(f"搜索和获取新闻内容失败: {str(e)}")
        # 返回空结果和一些默认链接
        return {
            "content_summary": "搜索相关信息时发生错误，无法提供相关事实依据。",
            "related_links": [
                "https://fact.qq.com/",
                "https://www.piyao.org.cn/",
                "http://www.xinhuanet.com/"
            ][:max_results]
        }

def detect_text_content(content):
    """检测文本内容的真实性"""
    try:
        # 检查API密钥
        if not DEEPSEEK_API_KEY:
            raise ValueError("缺少DEEPSEEK_API_KEY配置")
            
        print(f"开始调用DeepSeek API，API密钥长度: {len(DEEPSEEK_API_KEY)}")
        
        # 首先搜索相关信息
        print("开始搜索相关新闻信息")
        search_result = search_and_fetch_news(content)
        search_content = search_result["content_summary"]
        related_links = search_result["related_links"]
        print(f"搜索到的相关信息: {search_content[:200]}...")
        print(f"找到相关链接: {related_links}")
        
        # 调用DeepSeek API
        try:
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            print("DeepSeek客户端创建成功")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的假新闻检测专家"},
                    {"role": "user", "content": TEXT_DETECTION_PROMPT.format(
                        content=content,
                        search_results=search_content
                    )}
                ],
                timeout=100
            )
            print("DeepSeek API调用成功")
            
        except Exception as api_error:
            print(f"DeepSeek API调用失败: {str(api_error)}")
            raise api_error
        
        # 获取回答内容
        answer = response.choices[0].message.content
        print(f"DeepSeek返回内容: {answer[:100]}...")
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(answer, topK=5)
        print(f"提取的关键词: {keywords}")
        
        # 判断真假
        is_fake = False
        if "虚假" in answer[:50] or "假" in answer[:50]:
            is_fake = True
        print(f"判断结果: {'虚假' if is_fake else '真实'}")
        
        # 不在这里创建数据库记录，只返回检测结果
        return {
            "success": True,
            "is_fake": is_fake,
            "reason": answer,
            "related_links": related_links
        }
        
    except Exception as e:
        print(f"检测过程中发生错误: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

