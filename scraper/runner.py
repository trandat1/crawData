"""Module chung chứa logic scraping, có thể dùng cho cả CLI và Web interface."""
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from typing import Optional, Dict, Any, Callable

from scraper import config
from scraper.browser import init_driver
from scraper.collectors.detail import open_detail_and_extract
from scraper.collectors.listing import collect_list_items
from scraper.storage import load_previous_results, load_today_results, save_results
from scraper.utils import human_sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from . import utils

def find_and_click_next_page(driver):
    """Tìm và click nút next page."""
    prev_url = driver.current_url

    try:
        first_before = driver.find_elements(By.CSS_SELECTOR, "#product-lists-web a.js__product-link-for-product-id")
        first_pid_before = first_before[0].get_attribute("data-product-id") if first_before else None
    except:
        first_pid_before = None

    try:
        current_active = driver.find_element(By.CSS_SELECTOR, ".re__pagination-number.re__actived")
        current_pid = int(current_active.get_attribute("pid"))
    except:
        current_pid = 1

    next_pid = current_pid + 1

    next_href = None
    try:
        next_elem = driver.find_element(By.CSS_SELECTOR, f'a.re__pagination-number[pid="{next_pid}"]')
        next_href = next_elem.get_attribute("href")
    except:
        next_href = None

    if not next_href:
        print(f"[Pagination] No next page found after pid={current_pid}")
        return False

    try:
        driver.get(next_href)
    except Exception as e:
        print("[Pagination] Error loading next page:", e)
        return False

    for _ in range(30):
        time.sleep(0.5)
        if driver.current_url != prev_url:
            return True

        try:
            first_after = driver.find_elements(By.CSS_SELECTOR, "#product-lists-web a.js__product-link-for-product-id")
            if first_after:
                first_pid_after = first_after[0].get_attribute("data-product-id")
                if first_pid_before and first_pid_after and first_pid_after != first_pid_before:
                    return True
        except:
            pass

    return False


def apply_search_filters(driver, wait, location_filter):
    """Áp dụng filter địa điểm vào ô tìm kiếm."""
    if not location_filter or not location_filter.strip():
        return False
    
    try:
        # Tìm ô tìm kiếm
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "SuggestionSearch"))
        )


        # Xóa nội dung cũ và nhập filter
        search_input.clear()
        search_input.send_keys(location_filter)
        human_sleep(1, 2)
        
        # Tìm và click nút tìm kiếm
        search_button = driver.find_element(By.ID, "btnSearch")
        print(search_button)
        search_button.click()
        
        # Chờ trang load
        human_sleep(3, 5)
        
        print(f"[Filter] Đã áp dụng filter địa điểm: {location_filter}")
        return True
    except Exception as e:
        print(f"[Filter] Lỗi khi áp dụng filter địa điểm: {e}")
        return False


def build_url_with_filters(base_url, filters):
    """Xây dựng URL với các filter dạng query params."""
    if not filters:
        return base_url
    
    # Parse URL hiện tại
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    
    # Thêm các filter vào query params
    # gtn: giá từ
    if filters.get("price_from"):
        query_params["gtn"] = [filters["price_from"]]
    
    # gcn: giá đến
    if filters.get("price_to"):
        query_params["gcn"] = [filters["price_to"]]
    
    # dtnn: diện tích từ
    if filters.get("area_from"):
        query_params["dtnn"] = [filters["area_from"]]
    
    # dtln: diện tích đến
    if filters.get("area_to"):
        query_params["dtln"] = [filters["area_to"]]
    
    # h: hướng nhà
    if filters.get("direction"):
        query_params["h"] = [filters["direction"]]
    
    # frontage: mặt tiền (0-6: 0=Tất cả, 1=Dưới 5m, 2=5-7m, 3=7-10m, 4=10-12m, 5=12-15m, 6=Trên 12m)
    if filters.get("frontage") is not None and filters.get("frontage") != "":
        query_params["frontage"] = [str(filters["frontage"])]
    
    # road: đường vào (0-6: 0=Tất cả, 1=Dưới 5m, 2=5-7m, 3=7-10m, 4=10-12m, 5=12-15m, 6=Trên 12m)
    if filters.get("road") is not None and filters.get("road") != "":
        query_params["road"] = [str(filters["road"])]
    
    # Xây dựng lại URL
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def scrape_url(
    driver,
    wait,
    base_url,
    scraped_pids,
    scraped_hrefs,
    all_results,
    results_file,
    filters: Optional[Dict[str, Any]] = None,
    status_callback: Optional[Dict[str, Any]] = None
):
    """Scrape một URL cụ thể với filter tùy chọn."""
    print(f"\n{'='*60}")
    print(f"Starting scrape for URL: {base_url}")
    print(f"{'='*60}\n")
    
    try:
        # ===============================================================
        # 1) LOAD TRANG GỐC
        # ===============================================================
        driver.get(base_url)
        human_sleep(3, 6)

        # ===============================================================
        # 2) NẾU CÓ LOCATION → TÌM LOCATION TRƯỚC
        # ===============================================================
        if filters and filters.get("location"):
            applied = apply_search_filters(driver, wait, filters["location"])
            human_sleep(2, 4)

            if applied:
                # cập nhật base_url bằng URL sau khi tìm kiếm location
                base_url = driver.current_url
                print("[URL] Base URL mới sau location:", base_url)

        # ===============================================================
        # 3) XÂY DỰNG URL CUỐI CÙNG VỚI QUERY FILTER KHÁC
        # ===============================================================
        url_with_filters = build_url_with_filters(base_url, filters)
        print("[URL] URL cuối cùng để scrape:", url_with_filters)

        # ===============================================================
        # 4) LOAD URL ĐÃ BAO GỒM LOCATION + FILTERS
        # ===============================================================
        driver.get(url_with_filters)
        human_sleep(3, 6)

        # ===============================================================
        # 5) BẮT ĐẦU SCRAPE
        # ===============================================================
        page_idx = 0
        max_pages = filters.get("max_pages", config.MAX_PAGES) if filters else config.MAX_PAGES
        max_items_per_page = filters.get("max_items_per_page", config.MAX_ITEMS_PER_PAGE) if filters else config.MAX_ITEMS_PER_PAGE
        
        while page_idx < max_pages:
            page_idx += 1
            if status_callback:
                status_callback["current_page"] = page_idx
                status_callback["progress"] = f"Đang xử lý trang {page_idx}/{max_pages}"
            
            print(f"=== PROCESS PAGE {page_idx} ===")
            human_sleep(1, 3)
            current_list_url = driver.current_url

            collected, total_cards, skipped_pid, skipped_href = collect_list_items(
                driver,
                scraped_pids,
                scraped_hrefs,
                max_items_per_page,
                config.LIST_SCROLL_STEPS,
            )

            if not collected:
                print(
                    f"No new items found on this page (cards={total_cards}, skipped_pid={skipped_pid}, skipped_href={skipped_href})."
                )
                if page_idx >= max_pages:
                    print("Reached max pages, stopping.")
                    break
                print("Attempting to move to next page despite duplicates...")
                if not find_and_click_next_page(driver):
                    print("No further pages available, stopping.")
                    break
                continue

            print(f"Collected {len(collected)} new items meta on list page.")

            for i, item in enumerate(collected, start=1):
                if status_callback:
                    status_callback["total_items"] = len(all_results) + i
                    status_callback["progress"] = f"Trang {page_idx}/{max_pages} - Item {i}/{len(collected)}"
                
                print(f"[Page {page_idx}] Item {i}/{len(collected)} - PID {item.get('pid')}")
                human_sleep(2, 5)
                try:
                    full = open_detail_and_extract(
                        driver,
                        wait,
                        item,
                        current_list_url=current_list_url,
                        screenshot_dir=config.SCREENSHOT_DIR,
                        detail_scroll_steps=config.DETAIL_SCROLL_STEPS,
                        human_sleep=human_sleep,
                    )
                    # Lọc theo ngày
                    if filters and (filters.get("posted_date_from") and filters.get("posted_date_to")):
                        
                        posted_date_from = utils.normalize_date(filters["posted_date_from"])
                        posted_date_to = utils.normalize_date(filters["posted_date_to"])
                        posted_date = utils.normalize_date(full.get("posted_date", ""))

                        if posted_date and (posted_date < posted_date_from or posted_date > posted_date_to):
                            continue


                    all_results.append(full)
                    
                    if full.get("pid"):
                        scraped_pids.add(full.get("pid"))
                    if full.get("href"):
                        scraped_hrefs.add(full.get("href"))
                    print(f"  -> phone: {full.get('agent_phone')}, images: {len(full.get('images', []))}")
                except Exception as e:
                    print("  -> error on detail:", e)
                human_sleep(1, 3)

            save_results(all_results, results_file, scraped_pids, scraped_hrefs)
            
            if status_callback:
                status_callback["progress"] = f"Đã lưu {len(all_results)} items. Nghỉ {config.PAGE_COOLDOWN_SECONDS/60:.1f} phút..."
            
            print(f"Sleeping {config.PAGE_COOLDOWN_SECONDS/60:.1f} minutes before next page...")
            time.sleep(config.PAGE_COOLDOWN_SECONDS)
            
            if page_idx >= max_pages:
                break
            if not find_and_click_next_page(driver):
                break

    except Exception as e:
        print(f"Error scraping URL {base_url}: {e}")
        raise



def run_scraper(
    base_urls,
    filters: Optional[Dict[str, Any]] = None,
    debugger_address: Optional[str] = None,
    status_callback: Optional[Dict[str, Any]] = None
):
    """
    Hàm chính để chạy scraper.
    
    Args:
        base_urls: List các URL hoặc string URL đơn
        filters: Dict chứa các filter (location, price_from, price_to, area_from, area_to, direction, frontage, road, max_pages, max_items_per_page)
        debugger_address: Địa chỉ Chrome debugger (mặc định từ config)
        status_callback: Dict để cập nhật trạng thái (cho web interface)
    
    Returns:
        Dict chứa total_items và results_file
    """
    today, _, results_file = config.prepare_output_paths(datetime.now(), filters)
    
    scraped_pids, scraped_hrefs, _ = load_previous_results(config.OUTPUT_DIR, today)
    all_results = load_today_results(results_file, scraped_pids, scraped_hrefs)
    if filters:
        scraped_pids, scraped_hrefs, _ = load_previous_results(config.OUTPUT_DIR_FILTER, today)
        all_results = load_today_results(results_file, scraped_pids, scraped_hrefs)
        
    print(scraped_pids)
    print(scraped_hrefs)
    if all_results:
        print(
            f"Loaded {len(scraped_pids)} pids, {len(scraped_hrefs)} hrefs "
            f"and {len(all_results)} items from {results_file}"
        )
    
    driver, wait = init_driver(
        debugger_address or config.DEBUGGER_ADDRESS,
        config.PAGE_LOAD_TIMEOUT,
        config.WAIT_TIMEOUT
    )
    
    try:
        # Xử lý base_urls có thể là string hoặc list
        if isinstance(base_urls, str):
            base_urls = [base_urls]
        elif not isinstance(base_urls, list):
            raise ValueError(f"base_urls phải là string hoặc list, nhận được: {type(base_urls)}")
        
        for url_idx, base_url in enumerate(base_urls, start=1):
            if status_callback:
                status_callback["current_url"] = base_url
                status_callback["progress"] = f"URL {url_idx}/{len(base_urls)}: {base_url}"
            
            print(f"\n{'#'*60}")
            print(f"URL {url_idx}/{len(base_urls)}: {base_url}")
            print(f"{'#'*60}")
            
            try:
                scrape_url(
                    driver,
                    wait,
                    base_url,
                    scraped_pids,
                    scraped_hrefs,
                    all_results,
                    results_file,
                    filters=filters,
                    status_callback=status_callback
                )
            except Exception as e:
                print(f"Error processing URL {base_url}: {e}")
                if status_callback:
                    status_callback["error"] = str(e)
                print("Continuing with next URL...")
                continue
            
            # Nghỉ giữa các URLs (trừ URL cuối cùng)
            if url_idx < len(base_urls):
                print(f"\nCompleted URL {url_idx}/{len(base_urls)}. Sleeping before next URL...")
                time.sleep(config.PAGE_COOLDOWN_SECONDS)
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Saving current results...")
        save_results(all_results, results_file, scraped_pids, scraped_hrefs)
    finally:
        driver.quit()
    
    return {
        "total_items": len(all_results),
        "results_file": str(results_file),
        "url":base_url
    }

