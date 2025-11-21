from flask import Flask, render_template, request, jsonify, send_file
import threading
import time
from datetime import datetime
import pathlib
import sys
import os
import uuid

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
    "results_file_id": None,
    "last_update": time.time()
}

# 🔥 GLOBAL MAP: file_id → file_path
file_map = {}


def run_crawler(config_data):
    global crawler_status, file_map

    try:
        crawler_status["running"] = True
        crawler_status["error"] = None
        crawler_status["progress"] = "Đang khởi động crawler..."
        crawler_status["last_update"] = time.time()

        # Import crawler function
        from crawler_runner import run_crawler_with_config

        result = run_crawler_with_config(config_data, crawler_status)

        crawler_status["running"] = False
        crawler_status["progress"] = "Hoàn thành!"
        crawler_status["total_items"] = result.get("total_items", 0)
        crawler_status["current_url"] = result.get("url", "")
        crawler_status["last_update"] = time.time()

        file_id = str(uuid.uuid4())
        file_path = result.get("results_file", "")
        file_map[file_id] = file_path
        crawler_status["results_file_id"] = file_id

    except Exception as e:
        crawler_status["running"] = False
        crawler_status["error"] = str(e)
        crawler_status["progress"] = f"Lỗi: {str(e)}"
        crawler_status["last_update"] = time.time()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_crawler():
    global crawler_status

    if crawler_status["running"]:
        return jsonify({"error": "Crawler đang chạy"}), 400

    config_data = request.json

    if not config_data:
        return jsonify({"error": "Không có dữ liệu config"}), 400

    thread = threading.Thread(target=run_crawler, args=(config_data,))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "message": "Crawler đã được khởi động"})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Long Polling: chờ status thay đổi."""
    last_update = float(request.args.get("last_update", 0))
    timeout = 20  # giây
    interval = 0.5  # check mỗi 0.5s
    waited = 0

    while crawler_status["last_update"] <= last_update and waited < timeout:
        time.sleep(interval)
        waited += interval

    return jsonify(crawler_status)


@app.route('/api/stop', methods=['POST'])
def stop_crawler():
    global crawler_status
    crawler_status["running"] = False
    crawler_status["progress"] = "Đang dừng..."
    return jsonify({"status": "stopped"})


@app.route('/download')
def download_file():
    file_id = request.args.get("id")

    if not file_id or file_id not in file_map:
        return jsonify({"error": "File not found"}), 404

    filepath = file_map[file_id]

    if not os.path.exists(filepath):
        return jsonify({"error": "File missing on disk"}), 404

    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
