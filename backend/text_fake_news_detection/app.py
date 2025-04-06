import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json
import tempfile
import time

from services.detector import FakeNewsDetector
from services.document_loader import DocumentLoader
from services.web_search import WebSearchTool

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 初始化服务
document_loader = DocumentLoader()
web_search = WebSearchTool()
fake_news_detector = FakeNewsDetector()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/detect', methods=['POST'])
def detect_fake_news():
    """检测提供的文本是否为假新闻"""
    if 'text' not in request.form and 'file' not in request.files:
        return jsonify({"error": "请提供文本或文件"}), 400
    
    use_rag = request.form.get('use_rag', 'false').lower() == 'true'
    use_web_search = request.form.get('use_web_search', 'false').lower() == 'true'
    
    # 处理直接输入的文本
    if 'text' in request.form:
        text = request.form['text']
        
    # 处理上传的文件
    elif 'file' in request.files:
        file = request.files['file']
        
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)
        
        try:
            # 加载文档内容
            text = document_loader.load_document(temp_file_path)
        except Exception as e:
            return jsonify({"error": f"文件处理错误: {str(e)}"}), 500
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            os.rmdir(temp_dir)
    
    # 执行假新闻检测
    try:
        result = fake_news_detector.detect(
            text, 
            use_rag=use_rag, 
            use_web_search=use_web_search,
            web_search_tool=web_search if use_web_search else None
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"检测过程中出错: {str(e)}"}), 500

@app.route('/web-search', methods=['POST'])
def search_web():
    """执行网络搜索并返回结果"""
    if 'query' not in request.json:
        return jsonify({"error": "请提供搜索查询"}), 400
    
    query = request.json['query']
    
    try:
        results = web_search.search(query)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": f"网络搜索出错: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 