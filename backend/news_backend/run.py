from app import app

if __name__ == '__main__':
    # 在AutoDL上运行时，使用6006端口
    app.run(debug=True, host='0.0.0.0', port=6006) 
