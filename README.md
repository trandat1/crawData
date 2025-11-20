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
│   ├── runner.py         # Module chung chứa logic scraping (tái sử dụng)
│   └── collectors/       # Logic scraping
│       ├── __init__.py
│       ├── listing.py    # Thu thập danh sách từ trang list
│       └── detail.py     # Trích xuất chi tiết từ trang detail
├── craw/
│   └── play_batdongsan.py  # Script CLI (sử dụng scraper.runner)
├── app.py                 # Flask web app (khuyến nghị)
├── crawler_runner.py      # Wrapper cho web interface (sử dụng scraper.runner)
├── templates/
│   └── index.html        # Web interface form
├── output/                # Kết quả JSON theo tháng/ngày
│   └── YYYY-MM/
│       └── YYYY-MM-DD.json
├── screenshots_blocked/   # Screenshot khi phát hiện CAPTCHA
└── pyproject.toml         # Dependencies (Poetry)
```

## Yêu cầu

- Python 3.10+ (hoặc 3.14+ theo pyproject.toml)
- Chrome/Chromium với remote debugging enabled
- Dependencies: `selenium`, `requests`, `flask` (xem `pyproject.toml`)

## Cài đặt

```bash
# Sử dụng Poetry (khuyến nghị)
poetry install

# Hoặc pip
pip install selenium requests
```

## Cách sử dụng

### Cách 1: Sử dụng Web Interface (Khuyến nghị)

1. **Khởi động Chrome với remote debugging**

```bash
# Windows
# Tìm vị trí chrome.exe bằng lệnh: where chrome
# Hoặc sử dụng: "C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/chrome-session"

# Linux/Mac
google-chrome --remote-debugging-port=9222
# hoặc
chromium --remote-debugging-port=9222
```

2. **Khởi động Flask web app**

```bash
# Từ thư mục gốc
python app.py
```

3. **Mở trình duyệt và truy cập**

```
http://127.0.0.1:5000
```

4. **Điền form filter và config, sau đó click "Bắt đầu Crawl"**

### Cách 2: Chạy trực tiếp script

```bash
# Từ thư mục gốc
python craw/play_batdongsan.py
```

## Cấu hình

Chỉnh sửa các hằng số trong `scraper/config.py`:

- `DEBUGGER_ADDRESS`: Địa chỉ Chrome debugger (mặc định: "127.0.0.1:9222")
- `BASE_URL`: URL trang list để bắt đầu. Có thể là:
  - String: một URL duy nhất (ví dụ: `"https://batdongsan.com.vn/ban-dat"`)
  - List: nhiều URLs (ví dụ: `["https://batdongsan.com.vn/ban-dat", "https://batdongsan.com.vn/ban-nha"]`)
  - Mặc định: `"https://batdongsan.com.vn/ban-dat"`
- `MAX_PAGES`: Số trang tối đa (mặc định: 5)
- `MAX_ITEMS_PER_PAGE`: Số item tối đa mỗi trang (mặc định: 20)
- `PAGE_COOLDOWN_SECONDS`: Thời gian chờ giữa các trang (mặc định: 300s = 5 phút)
- `OUTPUT_DIR`: Thư mục lưu kết quả (mặc định: "output")
- `SCREENSHOT_DIR`: Thư mục lưu screenshot CAPTCHA (mặc định: "screenshots_blocked")

## Dữ liệu thu thập

Mỗi item trong JSON output chứa:

### Thông tin cơ bản
- `pid`: Product ID (string)
- `href`: URL chi tiết của tin đăng
- `title`: Tiêu đề tin đăng
- `location`: Địa chỉ bất động sản
- `description`: Mô tả chi tiết

### Thông tin giá và diện tích
- `price`: Giá tổng (từ trường "ext", ví dụ: "~4 tỷ")
- `area`: Diện tích (ví dụ: "100 m²")
- `price_per_m2`: Giá trên m² (ví dụ: "40 triệu/m²")

### Hình ảnh
- `images`: Danh sách URL ảnh (array)
- `thumbnail`: URL ảnh thumbnail (có thể rỗng)

### Thông tin đăng tin
- `posted_date`: Ngày đăng (từ config, ví dụ: "16/11/2025")
- `agent_name`: Tên đại lý (có thể rỗng)
- `agent_phone`: Số điện thoại đại lý (có thể rỗng)

### Thông tin chi tiết
- `specs`: Đặc điểm bất động sản (dict, ví dụ: {"Khoảng giá": "40 triệu/m²", "Diện tích": "100 m²", "Hướng nhà": "Đông - Nam", ...})
- `config`: Thông tin cấu hình tin đăng (dict, chứa: "Ngày đăng", "Ngày hết hạn", "Loại tin", "Mã tin")

### Thông tin bản đồ
- `map_coords`: Tọa độ bản đồ dạng decimal (lat,lng, ví dụ: "20.9742669097552,105.52710803129803")
- `map_link`: Link Google Maps embed
- `map_dms`: Tọa độ bản đồ dạng độ-phút-giây (ví dụ: "20°58'27.36\" N, 105°31'37.59\" E")

## Tính năng

- ✅ **Web Interface**: Giao diện web đẹp mắt để cấu hình và điều khiển crawler
- ✅ **Filter tìm kiếm**: Hỗ trợ filter địa điểm (tự động nhập vào ô tìm kiếm) và filter URL (giá, diện tích, hướng, mặt tiền, đường vào)
- ✅ **Code tái sử dụng**: Logic scraping được tập trung trong `scraper/runner.py`, cả CLI và Web đều dùng chung, dễ bảo trì
- ✅ **Tránh trùng lặp**: Load dữ liệu đã scrape từ các file JSON trước đó, tự động bỏ qua item đã có
- ✅ **Xử lý CAPTCHA**: Tự động phát hiện và chụp screenshot khi gặp CAPTCHA
- ✅ **Hỗ trợ nhiều URLs**: Có thể scrape từ nhiều URL cùng lúc, lưu vào cùng một file
- ✅ **Pagination**: Tự động chuyển trang, bỏ qua trang trùng nhiều
- ✅ **Error handling**: Xử lý lỗi gracefully, tiếp tục với item tiếp theo khi có lỗi
- ✅ **Human-like behavior**: Random sleep, scroll tự nhiên để tránh bị phát hiện
- ✅ **Tự động lưu**: Lưu dữ liệu sau mỗi trang để tránh mất dữ liệu
- ✅ **Trích xuất đầy đủ**: Lấy tất cả thông tin chi tiết, hình ảnh, tọa độ bản đồ
- ✅ **Real-time status**: Theo dõi tiến trình crawler real-time qua web interface
- ✅ **Modular design**: Dễ bảo trì và mở rộng

## Lưu ý

- Script sẽ tự động tạo thư mục `output/YYYY-MM/` và lưu file `YYYY-MM-DD.json`
- Nếu `BASE_URL` là list, script sẽ scrape từng URL tuần tự và lưu tất cả vào cùng một file JSON
- Script tự động tránh trùng lặp dữ liệu dựa trên `pid` và `href`
- Nếu phát hiện CAPTCHA, screenshot sẽ được lưu vào `screenshots_blocked/`
- Script có thể dừng sớm nếu không tìm thấy item mới hoặc hết trang
- Nhấn `Ctrl+C` để dừng an toàn, dữ liệu đã scrape sẽ được lưu
- Dữ liệu được lưu tự động sau mỗi trang để tránh mất dữ liệu khi có lỗi

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

