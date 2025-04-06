import os
import argparse
from dotenv import load_dotenv
import json

from services.detector import FakeNewsDetector
from services.document_loader import DocumentLoader
from services.web_search import WebSearchTool

# 加载环境变量
load_dotenv()

def detect_fake_news(text_content=None, file_path=None, use_rag=False, use_web_search=False):
    """
    检测文本或文件内容是否为假新闻
    
    Args:
        text_content: 文本内容
        file_path: 文件路径
        use_rag: 是否使用RAG
        use_web_search: 是否使用网络搜索
    
    Returns:
        检测结果
    """
    # 初始化服务
    document_loader = DocumentLoader()
    web_search_tool = WebSearchTool() if use_web_search else None
    fake_news_detector = FakeNewsDetector()
    
    # 获取文本内容
    if file_path:
        try:
            text = document_loader.load_document(file_path)
            print(f"已加载文件: {file_path}")
        except Exception as e:
            print(f"文件处理错误: {str(e)}")
            return None
    elif text_content:
        text = text_content
    else:
        print("错误: 需要提供文本内容或文件路径")
        return None
    
    # 执行检测
    try:
        result = fake_news_detector.detect(
            text,
            use_rag=use_rag,
            use_web_search=use_web_search,
            web_search_tool=web_search_tool
        )
        return result
    except Exception as e:
        print(f"检测过程中出错: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='假新闻检测工具')
    
    # 添加命令行参数
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', type=str, help='要检测的文本内容')
    input_group.add_argument('--file', type=str, help='要检测的文件路径')
    
    parser.add_argument('--rag', action='store_true', help='使用RAG增强检测')
    parser.add_argument('--web-search', action='store_true', help='使用网络搜索增强检测')
    parser.add_argument('--output', type=str, help='输出结果到文件')
    
    args = parser.parse_args()
    
    # 执行检测
    result = detect_fake_news(
        text_content=args.text,
        file_path=args.file,
        use_rag=args.rag,
        use_web_search=args.web_search
    )
    
    if result:
        # 格式化输出结果
        formatted_result = json.dumps(result, ensure_ascii=False, indent=2)
        
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_result)
            print(f"结果已保存到文件: {args.output}")
        else:
            print("\n检测结果:")
            print(formatted_result)
        
        # 输出简要结论
        is_fake = result.get('is_fake')
        confidence = result.get('confidence', 0)
        
        if is_fake is not None:
            status = "假新闻" if is_fake else "真实新闻"
            print(f"\n结论: 这很可能是{status} (置信度: {confidence}%)")

if __name__ == "__main__":
    main() 