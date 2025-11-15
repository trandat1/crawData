# Batdongsan Scraper

Web scraper cho batdongsan.com.vn sử dụng Selenium với Chrome remote debugging.

## Cấu trúc dự án

```
batdongsan/
├── scraper/              # Package chính
│   ├── __init__.py
│   ├── config.py         # Cấu hình (URLs, timeouts, paths)
│   ├── browser.py        # Khởi tạo Chrome driver
│   ├── storage.py        # Load/save JSON results
│   ├── utils.py          # Helper functions
│   └── collectors/       # Logic scraping
│       ├── __init__.py
│       ├── listing.py    # Thu thập danh sách từ trang list
│       └── detail.py     # Trích xuất chi tiết từ trang detail
├── craw/
│   └── play_batdongsan.py  # Script chính để chạy
├── output/               # Kết quả JSON theo tháng/ngày
│   └── YYYY-MM/
│       └── YYYY-MM-DD.json
├── screenshots_blocked/   # Screenshot khi phát hiện CAPTCHA
└── pyproject.toml         # Dependencies (Poetry)
```

## Yêu cầu

- Python 3.10+ (hoặc 3.14+ theo pyproject.toml)
- Chrome/Chromium với remote debugging enabled
- Dependencies: `selenium`, `requests` (xem `pyproject.toml`)

## Cài đặt

```bash
# Sử dụng Poetry (khuyến nghị)
poetry install

# Hoặc pip
pip install selenium requests
```

## Cách sử dụng

### 1. Khởi động Chrome với remote debugging

```bash
# Windows
chrome.exe --remote-debugging-port=9222

# Linux/Mac
google-chrome --remote-debugging-port=9222
# hoặc
chromium --remote-debugging-port=9222
```

### 2. Chạy scraper

```bash
# Từ thư mục gốc
python craw/play_batdongsan.py
```

## Cấu hình

Chỉnh sửa các hằng số trong `scraper/config.py`:

- `DEBUGGER_ADDRESS`: Địa chỉ Chrome debugger (mặc định: "127.0.0.1:9222")
- `BASE_URL`: URL trang list để bắt đầu (mặc định: "https://batdongsan.com.vn/ban-dat")
- `MAX_PAGES`: Số trang tối đa (mặc định: 5)
- `MAX_ITEMS_PER_PAGE`: Số item tối đa mỗi trang (mặc định: 20)
- `PAGE_COOLDOWN_SECONDS`: Thời gian chờ giữa các trang (mặc định: 300s = 5 phút)
- `OUTPUT_DIR`: Thư mục lưu kết quả (mặc định: "output")
- `SCREENSHOT_DIR`: Thư mục lưu screenshot CAPTCHA (mặc định: "screenshots_blocked")

## Dữ liệu thu thập

Mỗi item trong JSON output chứa:

- `pid`: Product ID
- `href`: URL chi tiết
- `title`: Tiêu đề
- `price`: Giá
- `area`: Diện tích
- `price_per_m2`: Giá/m²
- `location`: Địa chỉ
- `description`: Mô tả chi tiết
- `images`: Danh sách URL ảnh
- `posted_date`: Ngày đăng
- `agent_phone`: Số điện thoại đại lý
- `specs`: Đặc điểm bất động sản (dict)
- `config`: Thông tin cấu hình (dict)
- `map_coords`: Tọa độ bản đồ (lat,lng)
- `map_link`: Link Google Maps
- `pricing_info`: Biến động giá (dict)

## Tính năng

- ✅ Tránh trùng lặp: Load dữ liệu đã scrape từ các file JSON trước đó
- ✅ Xử lý CAPTCHA: Tự động phát hiện và chụp screenshot
- ✅ Pagination: Tự động chuyển trang, bỏ qua trang trùng nhiều
- ✅ Error handling: Xử lý lỗi gracefully, tiếp tục với item tiếp theo
- ✅ Human-like behavior: Random sleep, scroll tự nhiên
- ✅ Modular design: Dễ bảo trì và mở rộng

## Lưu ý

- Script sẽ tự động tạo thư mục `output/YYYY-MM/` và lưu file `YYYY-MM-DD.json`
- Nếu phát hiện CAPTCHA, screenshot sẽ được lưu vào `screenshots_blocked/`
- Script có thể dừng sớm nếu không tìm thấy item mới hoặc hết trang
- Nhấn `Ctrl+C` để dừng an toàn, dữ liệu đã scrape sẽ được lưu

## Troubleshooting

### Lỗi "No module named 'scraper'"
- Đảm bảo chạy script từ thư mục gốc của project
- Script tự động thêm project root vào `sys.path`

### Chrome không kết nối được
- Kiểm tra Chrome đã khởi động với `--remote-debugging-port=9222`
- Kiểm tra firewall không chặn port 9222

### Không lấy được số điện thoại
- Một số trang có thể yêu cầu tương tác thủ công
- Số điện thoại có thể bị ẩn hoặc yêu cầu đăng nhập

## License

MIT

