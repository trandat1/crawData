from flask import Flask, render_template, request, jsonify
import threading
import time
from datetime import datetime
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

app = Flask(__name__)

# Trạng thái crawler
crawler_status = {
    "running": False,
    "paused": False,         
    "progress": "",
    "current_url": "",
    "current_page": 0,
    "total_items": 0,
    "error": None,
    "results_file": "",      
    "all_results": [],        
}


def run_crawler(config_data):
    """Chạy crawler với config được truyền vào."""
    global crawler_status
    
    try:
        crawler_status["running"] = True
        crawler_status["error"] = None
        crawler_status["progress"] = "Đang khởi động crawler..."
        
        # Import crawler function
        from crawler_runner import run_crawler_with_config
        
        # Chạy crawler
        result = run_crawler_with_config(config_data, crawler_status)
        
        crawler_status["running"] = False
        crawler_status["progress"] = "Hoàn thành!"
        crawler_status["total_items"] = result.get("total_items", 0)
        crawler_status['current_url'] = result.get("url", "")
        crawler_status["results_file"] = result.get("results_file", "")
        
    except Exception as e:
        crawler_status["running"] = False
        crawler_status["error"] = str(e)
        crawler_status["progress"] = f"Lỗi: {str(e)}"

@app.route('/')
def index():
    """Trang chủ với form filter."""
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_crawler():
    """API endpoint để bắt đầu crawler."""
    global crawler_status
    
    if crawler_status["running"]:
        return jsonify({"error": "Crawler đang chạy"}), 400
    
    config_data = request.json
    
    # Validate config
    if not config_data:
        return jsonify({"error": "Không có dữ liệu config"}), 400
    
    # Chạy crawler trong thread riêng
    thread = threading.Thread(target=run_crawler, args=(config_data,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "message": "Crawler đã được khởi động"})

@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint để lấy trạng thái crawler."""
    return jsonify(crawler_status)

@app.route('/api/stop', methods=['POST'])
def stop_crawler():
    """API endpoint để dừng crawler."""
    global crawler_status
    crawler_status["running"] = False
    crawler_status["progress"] = "Đang dừng..."
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

