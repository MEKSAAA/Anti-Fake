import os
import pdfplumber
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional

class DocumentLoader:
    """文档加载器，支持PDF和TXT文件"""
    
    def load_document(self, file_path: str) -> str:
        """
        加载文档并返回其文本内容
        
        Args:
            file_path: 文档的路径
            
        Returns:
            str: 文档的文本内容
            
        Raises:
            ValueError: 如果文件类型不支持
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif file_extension == '.txt':
            return self._extract_text_from_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        从PDF文件中提取文本，尝试使用两种不同的方法
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        # 首先尝试使用pdfplumber
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text() or ""
                    text += extracted + "\n\n"
                    
            # 如果提取的文本非空，则返回
            if text.strip():
                return text
        except Exception as e:
            print(f"pdfplumber提取失败: {str(e)}")
        
        # 如果pdfplumber失败或返回空文本，尝试使用PyMuPDF
        try:
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n\n"
            doc.close()
            return text
        except Exception as e:
            print(f"PyMuPDF提取失败: {str(e)}")
            raise ValueError(f"无法从PDF文件中提取文本: {str(e)}")
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """
        从TXT文件中提取文本
        
        Args:
            file_path: TXT文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read() 