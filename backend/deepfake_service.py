# deepfake_service.py
from flask import Flask, request, jsonify
from detect import DeepFakeDetector  

app = Flask(__name__)

detector = DeepFakeDetector('./configs/test.yaml', './HAMMER_checkpoint_best.pth')

@app.route('/detect', methods=['POST'])
def detect():
    """处理deepfake检测请求
    
    接收包含图片路径和文本的JSON请求，调用DeepFakeDetector进行检测
    
    参数:
        从请求JSON获取:
        image_path (str): 要检测的图片路径
        text (str): 与图片相关的文本
    
    返回:
        dict: 检测结果的JSON响应，包含是否为假图、概率等信息
    
    异常:
        Exception: 当检测过程出错时抛出
    """
    data = request.json
    image_path = data['image_path']
    text = data['text']
    if not image_path:
        return jsonify({"error": "没有上传图片"}), 400
    
    if not text:
        return jsonify({"error": "没有上传文本"}), 400
        
    try:
        result = detector.predict(image_path, text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 使用不同于主应用的端口
    app.run(host='0.0.0.0', port=5001)