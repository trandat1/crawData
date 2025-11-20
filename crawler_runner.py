"""Module để chạy crawler với config động từ web interface."""
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper import config
from scraper.runner import run_scraper


def run_crawler_with_config(config_data, status_callback=None):
    """
    Chạy crawler với config được truyền vào từ web interface.
    
    Args:
        config_data: Dict chứa config từ form web
        status_callback: Dict để cập nhật trạng thái real-time
    
    Returns:
        Dict chứa total_items và results_file
    """
    # Parse base URLs
    base_urls_str = config_data.get("base_urls", "")
    if base_urls_str:
        base_urls = [url.strip() for url in base_urls_str.split(";") if url.strip()]
    else:
        base_urls = [config.BASE_URL]
    
    # Parse filters
    filters = {}
    
    # Filter địa điểm (sẽ nhập vào ô tìm kiếm)
    location = config_data.get("location", "").strip()
    if location:
        filters["location"] = location
    
    # Filter URL params
    price_from = config_data.get("price_from", "").strip()
    if price_from:
        filters["price_from"] = price_from
    
    price_to = config_data.get("price_to", "").strip()
    if price_to:
        filters["price_to"] = price_to
    
    area_from = config_data.get("area_from", "").strip()
    if area_from:
        filters["area_from"] = area_from
    
    area_to = config_data.get("area_to", "").strip()
    if area_to:
        filters["area_to"] = area_to
    
    direction = config_data.get("direction", "").strip()
    if direction:
        filters["direction"] = direction
    
    frontage = config_data.get("frontage", "")
    if frontage is not None and frontage != "":
        filters["frontage"] = frontage
    
    road = config_data.get("road", "")
    if road is not None and road != "":
        filters["road"] = road
        
    posted_date_from = config_data.get("posted_date_from", "").strip()
    if posted_date_from:
        filters["posted_date_from"] = posted_date_from

    posted_date_to = config_data.get("posted_date_to", "").strip()
    if posted_date_to:
        filters["posted_date_to"] = posted_date_to 
    
    # Config luôn có giá trị
    filters["max_pages"] = int(config_data.get("max_pages", config.MAX_PAGES))
    filters["max_items_per_page"] = int(config_data.get("max_items_per_page", config.MAX_ITEMS_PER_PAGE))
    
    # Chạy scraper với filter
    result = run_scraper(
        base_urls=base_urls,
        filters=filters,
        debugger_address=config_data.get("debugger_address", config.DEBUGGER_ADDRESS),
        status_callback=status_callback
    )
    
    
    return result

