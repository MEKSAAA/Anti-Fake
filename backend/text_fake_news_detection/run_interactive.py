import os
import tempfile
from dotenv import load_dotenv
import json

from services.detector import FakeNewsDetector
from services.document_loader import DocumentLoader
from services.web_search import WebSearchTool

# 加载环境变量
load_dotenv()

def clear_screen():
    """清除控制台屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印程序标题"""
    print("="*60)
    print("             假新闻检测系统 - 交互式控制台             ")
    print("="*60)
    print("基于LangChain和DeepSeek API的假新闻检测工具")
    print("="*60)
    print()

def get_text_input():
    """获取用户文本输入"""
    print("请输入新闻文本（输入完成后按Ctrl+D或Ctrl+Z+Enter结束）：")
    print("-" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass
    
    return "\n".join(lines)

def display_result(result):
    """显示检测结果"""
    print("\n" + "="*60)
    print("检测结果：")
    print("-" * 60)
    
    if result is None:
        print("检测失败，请检查日志获取详细信息。")
        return
    
    is_fake = result.get('is_fake')
    confidence = result.get('confidence', 0)
    reasoning = result.get('reasoning', '无详细理由')
    evidence = result.get('evidence', [])
    processing_time = result.get('processing_time', 0)
    
    # 显示主要结论
    if is_fake is not None:
        status = "假新闻" if is_fake else "真实新闻"
        print(f"结论: 这很可能是{status}")
        print(f"置信度: {confidence}%")
    else:
        print("结论: 无法确定")
    
    print(f"\n处理时间: {processing_time}秒")
    
    # 显示详细推理
    print("\n详细理由:")
    print(reasoning)
    
    # 显示证据
    if evidence:
        print("\n支持证据:")
        for i, item in enumerate(evidence, 1):
            print(f"{i}. {item}")
    
    print("\n" + "="*60)

def main():
    """主函数，运行交互式检测程序"""
    # 初始化服务
    document_loader = DocumentLoader()
    web_search_tool = WebSearchTool()
    fake_news_detector = FakeNewsDetector()
    
    while True:
        clear_screen()
        print_header()
        
        print("请选择操作：")
        print("1. 输入文本进行检测")
        print("2. 提供文件路径进行检测")
        print("3. 退出程序")
        
        choice = input("\n请输入选项（1-3）：")
        
        if choice == '1':
            clear_screen()
            print_header()
            text = get_text_input()
            
            if not text.strip():
                print("\n错误：未提供文本内容")
                input("\n按Enter键继续...")
                continue
            
            print("\n是否使用以下增强功能？")
            use_rag = input("使用RAG内容增强 (y/n): ").lower() == 'y'
            use_web_search = input("使用网络搜索 (y/n): ").lower() == 'y'
            
            print("\n开始检测，请稍候...")
            result = fake_news_detector.detect(
                text,
                use_rag=use_rag,
                use_web_search=use_web_search,
                web_search_tool=web_search_tool if use_web_search else None
            )
            
            display_result(result)
            
        elif choice == '2':
            clear_screen()
            print_header()
            file_path = input("请输入文件路径（PDF或TXT）：")
            
            if not os.path.exists(file_path):
                print(f"\n错误：文件 '{file_path}' 不存在")
                input("\n按Enter键继续...")
                continue
            
            print("\n是否使用以下增强功能？")
            use_rag = input("使用RAG内容增强 (y/n): ").lower() == 'y'
            use_web_search = input("使用网络搜索 (y/n): ").lower() == 'y'
            
            print("\n开始加载文件并检测，请稍候...")
            
            try:
                text = document_loader.load_document(file_path)
                
                result = fake_news_detector.detect(
                    text,
                    use_rag=use_rag,
                    use_web_search=use_web_search,
                    web_search_tool=web_search_tool if use_web_search else None
                )
                
                display_result(result)
                
            except Exception as e:
                print(f"\n错误：无法处理文件 - {str(e)}")
            
        elif choice == '3':
            print("\n感谢使用假新闻检测系统，再见！")
            break
            
        else:
            print("\n无效选项，请重新选择")
        
        input("\n按Enter键继续...")

if __name__ == "__main__":
    main() 