import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import sys
from typing import Dict, Any, Optional

# 添加服务目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.document_loader import DocumentLoader

# 加载环境变量
load_dotenv()

class WebSearchTool:
    """简单的网络搜索工具"""
    
    def search(self, query, num_results=3):
        """
        使用Bing搜索引擎搜索信息
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            List: 搜索结果列表
        """
        try:
            # 构建搜索URL
            search_url = f"https://cn.bing.com/search?q={query}"
            
            # 设置User-Agent以模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # 发送请求
            response = requests.get(search_url, headers=headers, timeout=10)
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"搜索请求失败，状态码: {response.status_code}")
                return []
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取搜索结果
            results = []
            search_items = soup.select(".b_algo")[:num_results]  # Bing搜索结果的CSS选择器
            
            for item in search_items:
                title_element = item.select_one("h2 a")
                link_element = item.select_one("h2 a")
                snippet_element = item.select_one(".b_caption p")
                
                if title_element and link_element and snippet_element:
                    title = title_element.text
                    link = link_element.get("href", "")
                    snippet = snippet_element.text
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
            
            return results
        except Exception as e:
            print(f"网络搜索出错: {str(e)}")
            return []

class SimpleFakeNewsDetector:
    """使用DeepSeek API进行假新闻检测的简化服务"""
    
    def __init__(self):
        """初始化假新闻检测器"""
        # 加载环境变量
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("未找到DEEPSEEK_API_KEY环境变量")
        
        # 初始化OpenAI客户端(用于DeepSeek API)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 初始化网络搜索工具
        self.web_search_tool = WebSearchTool()
        
        # 初始化文档加载器
        self.document_loader = DocumentLoader()
    
    def detect_text(self, text: str) -> Dict[str, Any]:
        """
        检测文本是否为假新闻
        
        Args:
            text: 待检测的文本
            
        Returns:
            Dict[str, Any]: 包含检测结果的字典
        """
        # 进行网络搜索
        search_results = self.web_search_tool.search(text[:100])  # 使用前100个字符作为搜索查询
        
        # 构建搜索上下文
        search_context = ""
        if search_results:
            search_context = "搜索结果:\n"
            for i, result in enumerate(search_results):
                search_context += f"结果 {i+1}:\n"
                search_context += f"标题: {result['title']}\n"
                search_context += f"摘要: {result['snippet']}\n"
                search_context += f"链接: {result['link']}\n\n"
        else:
            search_context = "未找到相关搜索结果。\n"
        
        # 构建完整提示
        prompt = self._build_prompt(text, search_context)
        
        try:
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的假新闻检测专家。你需要基于搜索结果判断新闻的真实性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2000,
                stream=False
            )
            
            # 获取响应内容
            content = response.choices[0].message.content
            
            # 提取JSON部分
            json_content = self._extract_json(content)
            
            # 解析JSON
            parsed_result = json.loads(json_content)
            return parsed_result
        except Exception as e:
            print(f"API调用出错: {str(e)}")
            return {"error": f"API调用失败: {str(e)}"}
    
    def detect_file(self, file_path: str) -> Dict[str, Any]:
        """
        检测文件中的内容是否为假新闻
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 包含检测结果的字典
        """
        try:
            # 加载文档内容
            text = self.document_loader.load_document(file_path)
            
            # 使用文本检测
            return self.detect_text(text)
        except Exception as e:
            print(f"文件处理出错: {str(e)}")
            return {"error": f"文件处理失败: {str(e)}"}
    
    def _build_prompt(self, text: str, search_context: str) -> str:
        """构建提示模板"""
        return f"""请分析以下新闻文本，判断其是否为假新闻。

新闻文本：
{text}

为帮助你判断，这里是关于该新闻的网络搜索结果：
{search_context}

请基于上述搜索结果和以下几点分析这篇新闻的真实性：
1. 来源可信度：新闻是否来自可靠来源
2. 事实核查：搜索结果中是否有支持或反驳该新闻的信息
3. 内容一致性：新闻内容是否与其他来源报道一致
4. 可验证性：新闻中的关键信息是否可以通过搜索结果验证

请以JSON格式返回你的分析结果（只返回JSON，不要有其他文字）：
```json
{{
  "is_fake": true或false，表示是否是假新闻,
  "reasoning": "详细的分析理由，特别是基于搜索结果的分析",
  "evidence": [
    "支持你判断的关键证据1",
    "支持你判断的关键证据2"
  ]
}}
```"""
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON部分"""
        # 如果响应中包含```json和```标记，则提取中间部分
        if "```json" in text and "```" in text.split("```json", 1)[1]:
            return text.split("```json", 1)[1].split("```", 1)[0].strip()
        # 如果只有```标记，则提取中间部分
        elif "```" in text and "```" in text.split("```", 1)[1]:
            return text.split("```", 1)[1].split("```", 1)[0].strip()
        # 否则返回原始文本
        return text.strip()

# 使用示例
if __name__ == "__main__":
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="假新闻检测工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="要检测的文本内容")
    group.add_argument("--file", help="要检测的文件路径")
    parser.add_argument("--output", help="输出结果到文件")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建检测器
    detector = SimpleFakeNewsDetector()
    
    # 根据参数选择检测方式
    if args.text:
        print(f"检测文本内容...")
        result = detector.detect_text(args.text)
    else:
        print(f"检测文件: {args.file}")
        result = detector.detect_file(args.file)
    
    # 显示结果
    print("检测结果:")
    formatted_result = json.dumps(result, ensure_ascii=False, indent=2)
    print(formatted_result)
    
    # 如果指定了输出文件，将结果保存到文件
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_result)
        print(f"结果已保存到: {args.output}") 