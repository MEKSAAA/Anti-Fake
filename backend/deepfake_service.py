# deepfake_service.py
from flask import Flask, request, jsonify
from detect import DeepFakeDetector  

app = Flask(__name__)

detector = DeepFakeDetector('./configs/test.yaml', './HAMMER_checkpoint_best.pth')

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    image_path=data['image_path']
    text=data['text']
    if not image_path :
        return jsonify({"error": "没有上传图片"}), 400
    
    if not text :
        return jsonify({"error": "没有上传图片"}), 400
        
    try:
        result = detector.predict(image_path, text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 使用不同于主应用的端口
    app.run(host='0.0.0.0', port=5001)