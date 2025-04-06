import os
from typing import List, Dict, Any, Optional, Tuple
import json
import nltk
from nltk.tokenize import sent_tokenize
import torch
import numpy as np
import time
import re

# LangChain导入
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# DeepSeek API导入
from langchain_openai import ChatOpenAI

class FakeNewsDetector:
    """使用LLM和RAG进行假新闻检测的服务"""
    
    def __init__(self):
        """初始化假新闻检测器"""
        # 下载NLTK资源
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        # 加载环境变量
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("警告: 未找到DEEPSEEK_API_KEY环境变量")
        
        # 初始化嵌入模型
        self.embeddings = self._init_embeddings()
        
        # 初始化LLM
        self.llm = self._init_llm()
        
        # 设置文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _init_embeddings(self):
        """初始化嵌入模型"""
        # 使用轻量级的本地嵌入模型
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
        )
    
    def _init_llm(self):
        """初始化语言模型"""
        # 使用DeepSeek API
        return ChatOpenAI(
            api_key=self.api_key,
            model_name="deepseek-chat",
            temperature=0,
            max_tokens=4000
        )
    
    def detect(self, text: str, use_rag: bool = False, use_web_search: bool = False, 
              web_search_tool = None) -> Dict[str, Any]:
        """
        检测文本是否为假新闻
        
        Args:
            text: 待检测的文本
            use_rag: 是否使用RAG增强
            use_web_search: 是否使用网络搜索
            web_search_tool: 网络搜索工具实例
            
        Returns:
            Dict[str, Any]: 包含检测结果的字典
        """
        start_time = time.time()
        
        # 准备上下文信息
        context = ""
        web_search_results = []
        
        # 如果启用了网络搜索
        if use_web_search and web_search_tool:
            # 从文本中提取关键短语作为搜索查询
            search_query = self._extract_search_query(text)
            web_search_results = web_search_tool.search(search_query)
            
            # 为每个搜索结果添加到上下文
            for i, result in enumerate(web_search_results[:3]):
                context += f"\n来源 {i+1}: {result['title']}\n"
                context += f"摘要: {result['snippet']}\n"
                context += f"链接: {result['link']}\n\n"
        
        # 如果启用了RAG，使用RAG获取相关上下文
        rag_contexts = []
        if use_rag:
            rag_contexts = self._get_rag_context(text)
            if rag_contexts:
                context += "\n相关上下文:\n" + "\n\n".join(rag_contexts)
        
        # 构建提示模板
        prompt_template = self._build_prompt_template(use_rag, use_web_search)
        
        # 创建LLM链
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            verbose=False
        )
        
        # 运行LLM链获取结果
        inputs = {
            "text": text,
            "context": context if context else "没有额外上下文信息。"
        }
        
        result = chain.invoke(inputs)
        llm_output = result.get("text", "")
        
        # 解析LLM输出为JSON格式
        try:
            json_output = self._parse_llm_output_to_json(llm_output)
        except:
            # 如果解析失败，提供一个基本结构
            json_output = {
                "is_fake": None,
                "confidence": 0,
                "reasoning": llm_output,
                "evidence": []
            }
        
        # 添加元数据
        json_output["processing_time"] = round(time.time() - start_time, 2)
        json_output["web_search_results"] = web_search_results
        json_output["rag_contexts"] = rag_contexts
        
        return json_output
    
    def _extract_search_query(self, text: str) -> str:
        """从文本中提取搜索查询"""
        # 简单方法：使用前几个句子作为搜索查询
        sentences = sent_tokenize(text)
        first_sentences = " ".join(sentences[:min(3, len(sentences))])
        # 限制长度
        if len(first_sentences) > 200:
            first_sentences = first_sentences[:200]
        return first_sentences
    
    def _get_rag_context(self, text: str) -> List[str]:
        """获取RAG上下文"""
        try:
            # 分割文本
            chunks = self.text_splitter.split_text(text)
            
            # 如果文本太短，不需要RAG
            if len(chunks) <= 1:
                return []
            
            # 创建文档对象
            docs = [Document(page_content=chunk) for chunk in chunks]
            
            # 创建向量存储
            vectorstore = FAISS.from_documents(docs, self.embeddings)
            
            # 使用文本的前200个字符作为查询
            query = text[:min(len(text), 200)]
            
            # 检索相关上下文
            retrieved_docs = vectorstore.similarity_search(query, k=3)
            
            # 提取上下文
            contexts = [doc.page_content for doc in retrieved_docs]
            
            return contexts
        except Exception as e:
            print(f"RAG上下文检索失败: {str(e)}")
            return []
    
    def _build_prompt_template(self, use_rag: bool, use_web_search: bool) -> PromptTemplate:
        """构建提示模板"""
        base_prompt = """你是一个专门负责检测假新闻的AI助手。请分析以下新闻文本，判断其是否为假新闻。

{context}

新闻文本：
{text}

请详细分析这篇新闻是否是假新闻，并按以下JSON格式返回你的分析结果（请只返回JSON，不要有其他文字）：
```json
{{
  "is_fake": true或false，表示是否是假新闻,
  "confidence": 0-100之间的数字，表示你对判断的确信度,
  "reasoning": "详细解释你为什么做出这个判断的理由",
  "evidence": [
    "支持你判断的证据1",
    "支持你判断的证据2"
  ]
}}
```
"""
        
        # 根据RAG和网络搜索的使用情况自定义提示
        if use_rag and use_web_search:
            base_prompt = base_prompt.replace("{context}", "相关网络搜索结果和文本内部上下文信息如下：\n{context}")
        elif use_rag:
            base_prompt = base_prompt.replace("{context}", "从文本内部提取的相关上下文信息如下：\n{context}")
        elif use_web_search:
            base_prompt = base_prompt.replace("{context}", "相关网络搜索结果如下：\n{context}")
        else:
            base_prompt = base_prompt.replace("{context}\n\n", "")
        
        return PromptTemplate(
            template=base_prompt,
            input_variables=["text", "context"]
        )
    
    def _parse_llm_output_to_json(self, output: str) -> Dict[str, Any]:
        """将LLM输出解析为JSON格式"""
        # 尝试提取JSON部分
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试查找没有标记的JSON
            json_match = re.search(r'({[\s\S]*})', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                raise ValueError("无法从输出中提取JSON")
        
        # 解析JSON
        result = json.loads(json_str)
        
        # 验证必需的字段
        required_fields = ["is_fake", "confidence", "reasoning"]
        for field in required_fields:
            if field not in result:
                result[field] = None if field == "is_fake" else "" if field == "reasoning" else 0
        
        # 确保evidence是一个列表
        if "evidence" not in result or not isinstance(result["evidence"], list):
            result["evidence"] = []
        
        return result 