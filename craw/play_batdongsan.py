import pathlib
import sys
import time
from datetime import datetime

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scraper import config
from scraper.browser import init_driver
from scraper.collectors.detail import open_detail_and_extract
from scraper.collectors.listing import collect_list_items
from scraper.storage import load_previous_results, load_today_results, save_results
from scraper.utils import human_sleep
from selenium.webdriver.common.by import By


def find_and_click_next_page(driver):
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



def main():
    today, _, results_file = config.prepare_output_paths(datetime.now())

    scraped_pids, scraped_hrefs, _ = load_previous_results(config.OUTPUT_DIR, today)
    all_results = load_today_results(results_file, scraped_pids, scraped_hrefs)
    if all_results:
        print(
            f"Loaded {len(scraped_pids)} pids, {len(scraped_hrefs)} hrefs "
            f"and {len(all_results)} items from {results_file}"
        )

    driver, wait = init_driver(config.DEBUGGER_ADDRESS, config.PAGE_LOAD_TIMEOUT, config.WAIT_TIMEOUT)

    try:
        driver.get(config.BASE_URL)
        human_sleep(4, 8)
        page_idx = 0
        while page_idx < config.MAX_PAGES:
            page_idx += 1
            print(f"=== PROCESS PAGE {page_idx} ===")
            human_sleep(1, 3)
            current_list_url = driver.current_url

            collected, total_cards, skipped_pid, skipped_href = collect_list_items(
                driver,
                scraped_pids,
                scraped_hrefs,
                config.MAX_ITEMS_PER_PAGE,
                config.LIST_SCROLL_STEPS,
            )

            if not collected:
                print(
                    f"No new items found on this page (cards={total_cards}, skipped_pid={skipped_pid}, skipped_href={skipped_href})."
                )
                if page_idx >= config.MAX_PAGES:
                    print("Reached max pages, stopping.")
                    break
                print("Attempting to move to next page despite duplicates...")
                if not find_and_click_next_page(driver):
                    print("No further pages available, stopping.")
                    break
                continue

            print(f"Collected {len(collected)} new items meta on list page.")

            for i, item in enumerate(collected, start=1):
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
            print(f"Sleeping {config.PAGE_COOLDOWN_SECONDS/60:.1f} minutes before next page...")
            time.sleep(config.PAGE_COOLDOWN_SECONDS)
            if page_idx >= config.MAX_PAGES:
                break
            if not find_and_click_next_page(driver):
                break
    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Saving current results...")
        save_results(all_results, results_file, scraped_pids, scraped_hrefs)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
