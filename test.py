import os
import requests
from urllib.parse import urlparse

# URL hình ảnh
url = "https://file4.batdongsan.com.vn/2025/11/25/20251125101431-afb1_wm.jpg"

# Parse URL để lấy path không kèm domain
parsed = urlparse(url)
path = parsed.path.lstrip("/")  # -> "2025/11/25/20251125101431-afb1_wm.jpg"

# Thư mục gốc để lưu ảnh
base_folder = "images"

# Tách folder và tên file
folder_path = os.path.join(base_folder, os.path.dirname(path))
file_path = os.path.join(base_folder, path)

# Tạo folder nếu chưa có
os.makedirs(folder_path, exist_ok=True)

# Tải ảnh
response = requests.get(url)

# Lưu ảnh đúng theo path
with open(file_path, "wb") as f:
    f.write(response.content)

print("Đã tải ảnh vào:", file_path)
