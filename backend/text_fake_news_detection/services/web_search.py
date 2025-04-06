import os
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import time
import re

class WebSearchTool:
    """网络搜索工具，用于获取与查询相关的网页信息"""
    
    def __init__(self, max_results: int = 5):
        """
        初始化网络搜索工具
        
        Args:
            max_results: 返回的最大结果数量
        """
        self.max_results = max_results
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        执行网络搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含标题、链接和摘要
        """
        try:
            results = []
            with DDGS() as ddgs:
                ddgs_results = list(ddgs.text(query, max_results=self.max_results))
                for result in ddgs_results:
                    results.append({
                        'title': result.get('title', ''),
                        'link': result.get('href', ''),
                        'snippet': result.get('body', '')
                    })
            return results
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {str(e)}")
            return []
    
    def get_page_content(self, url: str) -> Optional[str]:
        """
        获取网页内容
        
        Args:
            url: 网页URL
            
        Returns:
            Optional[str]: 网页文本内容，如果失败则返回None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.extract()
            
            # 获取文本并清理
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            print(f"获取页面内容失败 {url}: {str(e)}")
            return None
    
    def search_and_get_content(self, query: str, max_content_results: int = 3) -> List[Dict[str, Any]]:
        """
        搜索并获取页面内容
        
        Args:
            query: 搜索查询
            max_content_results: 获取内容的最大结果数量
            
        Returns:
            List[Dict[str, Any]]: 包含搜索结果和页面内容的列表
        """
        search_results = self.search(query)
        content_results = []
        
        for i, result in enumerate(search_results):
            if i >= max_content_results:
                break
                
            content = self.get_page_content(result['link'])
            if content:
                result['content'] = content
                content_results.append(result)
            
            # 防止请求过于频繁
            time.sleep(1)
        
        return content_results 