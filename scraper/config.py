import os
from datetime import datetime

# === Default configuration ===
DEBUGGER_ADDRESS = "127.0.0.1:9222"
BASE_URL = "https://batdongsan.com.vn/ban-dat"
MAX_PAGES = 5
MAX_ITEMS_PER_PAGE = 20
PAGE_COOLDOWN_SECONDS = 5 * 60
PAGE_LOAD_TIMEOUT = 60
WAIT_TIMEOUT = 20
LIST_SCROLL_STEPS = 6
DETAIL_SCROLL_STEPS = 6

SCREENSHOT_DIR = "screenshots_blocked"
OUTPUT_DIR = "output"


def ensure_directories():
    """Create top-level directories required for scraping."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def prepare_output_paths(today: datetime | None = None):
    """Return (today, month_folder, results_file) and ensure directories exist."""
    ensure_directories()
    today = today or datetime.now()
    month_folder = os.path.join(OUTPUT_DIR, today.strftime("%Y-%m"))
    os.makedirs(month_folder, exist_ok=True)
    results_file = os.path.join(month_folder, f"{today.strftime('%Y-%m-%d')}.json")
    return today, month_folder, results_file

