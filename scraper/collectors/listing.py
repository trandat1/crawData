from __future__ import annotations

import time
from typing import List, Tuple

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By


def _scroll_listing(driver, steps: int):
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        for _ in range(steps):
            driver.execute_script("window.scrollBy(0, 1200);")
            time.sleep(0.3)
    except Exception:
        pass


def collect_list_items(
    driver,
    scraped_pids: set[str],
    scraped_hrefs: set[str],
    max_items: int,
    scroll_steps: int,
) -> Tuple[list[dict], int, int, int]:
    """
    Return (items, total_cards, skipped_pid, skipped_href).
    """
    _scroll_listing(driver, scroll_steps)

    out: List[dict] = []
    els = []
    for _ in range(20):
        els = driver.find_elements(By.CSS_SELECTOR, "#product-lists-web a.js__product-link-for-product-id")
        if els:
            break
        time.sleep(1)

    skipped_pid = skipped_href = 0
    for el in els:
        try:
            pid = el.get_attribute("data-product-id")
            href = el.get_attribute("href")
            if not href:
                continue
            if pid and pid in scraped_pids:
                skipped_pid += 1
                continue
            if (not pid) and href in scraped_hrefs:
                skipped_href += 1
                continue

            out.append(
                {
                    "href": href,
                    "pid": pid,
                    "title": "",
                    "price": "",
                    "area": "",
                    "price_per_m2": "",
                    "location": "",
                    "description": "",
                    "thumbnail": "",
                    "posted_date": "",
                    "agent_name": "",
                    "agent_phone": "",
                    "images": [],
                    "specs": {},
                    "config": {},
                    "map_coords": "",
                    "map_link": "",
                    "map_dms":""
                    # "pricing_info": {},
                }
            )
        except StaleElementReferenceException as e:
            print(e)
            continue

    if not out:
        print(
            f"[collect_list_items] Found {len(els)} cards but skipped {skipped_pid} by pid and {skipped_href} by href."
        )
    return out[:max_items], len(els), skipped_pid, skipped_href

