from __future__ import annotations

import os
import re
from typing import Callable

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def clean_image_url(url: str | None):
    if not url or "no-photo" in url:
        return None
    m = re.search(r"(https://file4\.batdongsan\.com\.vn)/(?:resize|crop)/[^/]+/(.+)", url)
    if m:
        return m.group(1) + "/" + m.group(2)
    return url


def _scroll_detail(driver, steps: int, human_sleep: Callable[[float, float], None]):
    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, 1000);")
        human_sleep(0.5, 2.0)


def _extract_short_info(driver):
    price = ""
    area = ""
    price_per_m2 = ""
    try:
        short_items = driver.find_elements(By.CSS_SELECTOR, ".re__pr-short-info .re__pr-short-info-item")
        for si in short_items:
            try:
                label = ""
                try:
                    label = si.find_element(By.CSS_SELECTOR, ".re__pr-short-info-item-title").text.strip().lower()
                except Exception:
                    label = si.get_attribute("innerText").strip().lower()
                value = si.find_element(By.CSS_SELECTOR, ".re__pr-short-info-item-value").text.strip()

                if not price and ("giá" in label and "m²" not in label and "m2" not in label):
                    price = value
                if not area and ("diện tích" in label or label.startswith("dt") or "m²" in value or "m2" in value):
                    area = value
                if not price_per_m2 and ("giá/m" in label or "giá/m²" in label or "giá/m2" in label):
                    price_per_m2 = value
            except Exception:
                continue
    except Exception:
        pass
    return price, area, price_per_m2


def _extract_specs(driver):
    specs_map = {}
    try:
        spec_items = driver.find_elements(By.CSS_SELECTOR, ".re__pr-specs-content-item")
        for spec in spec_items:
            try:
                key = spec.find_element(By.CSS_SELECTOR, ".re__pr-specs-content-item-title").text.strip()
                val = spec.find_element(By.CSS_SELECTOR, ".re__pr-specs-content-item-value").text.strip()
                specs_map[key] = val
            except Exception:
                continue
    except Exception:
        specs_map = {}
    return specs_map


def _extract_images(driver):
    images: list[str] = []
    try:
        thumbs = driver.find_elements(By.CSS_SELECTOR, ".re__media-thumbs img")
        for img in thumbs:
            src = img.get_attribute("src") or img.get_attribute("data-src")
            clean_src = clean_image_url(src)
            if clean_src and clean_src not in images:
                images.append(clean_src)
    except Exception:
        pass
    return images


def _extract_config(driver):
    config = {}
    try:
        config_items = driver.find_elements(By.CSS_SELECTOR, ".re__pr-short-info-item.js__pr-config-item")
        for ci in config_items:
            try:
                t = ci.find_element(By.CSS_SELECTOR, ".title").text.strip()
                v = ci.find_element(By.CSS_SELECTOR, ".value").text.strip()
                config[t] = v
            except Exception:
                continue
    except Exception:
        config = {}
    return config


def _extract_phone(driver, wait, human_sleep: Callable[[float, float], None]):
    return ""
    phone_text = ""
    try:
        btn = driver.find_element(
            By.CSS_SELECTOR, 'div[kyc-tracking-id="lead-phone-ldp"], div[kyc-tracking-id="lead-phone-ldp"] .re__btn'
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn)
        human_sleep(0.5, 1.0)
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));", btn)

        try:
            wait.until(lambda d: ("*" not in (btn.text or "")) and re.search(r"\d{7,}", btn.text or "") is not None)
            phone_text = (btn.text or "").strip()
        except Exception:
            m = re.search(r"(0\d{8,10}|\+84\d{8,10})", driver.page_source.replace(" ", ""))
            phone_text = m.group(0) if m else ""
    except Exception:
        phone_text = ""
    return phone_text


def _extract_map(driver, wait):
    map_coords = ""
    map_link = ""

    try:
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.re__pr-map iframe")))
        map_link = iframe.get_attribute("src") or iframe.get_attribute("data-src") or ""

        match = re.search(r'!3d([0-9\.\-]+)!4d([0-9\.\-]+)', map_link)
        if match:
            lat, lng = match.group(1), match.group(2)
            map_coords = f"{lat},{lng}"
        else:
            match2 = re.search(r'q=([0-9\.\-]+),([0-9\.\-]+)', map_link)
            if match2:
                lat, lng = match2.group(1), match2.group(2)
                map_coords = f"{lat},{lng}"

    except Exception:
        pass

    return map_coords, map_link



def _extract_pricing(driver, wait):
    pricing = {}
    return pricing

    # Chờ toàn bộ khối pricing load (Vue render xong)
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".re__chart-subsapo")
    ))

    cols = driver.find_elements(By.CSS_SELECTOR, ".re__chart-subsapo .re__chart-col")

    for col in cols:

        classes = col.get_attribute("class") or ""
        if "no-data" in classes:
            continue

        try:
            # Tìm trong scope của col, không phải toàn bộ document
            big_elem = col.find_element(By.CSS_SELECTOR, ".text-big strong")
            big = big_elem.text.strip()

            small_elem = col.find_element(By.CSS_SELECTOR, ".text-small")
            small = small_elem.text.strip()

            if small and big:
                pricing[small] = big

        except Exception as e:
            print("Vue/AJAX element not ready:", e)
            print(col.get_attribute("outerHTML"))
            continue

    return pricing



def open_detail_and_extract(
    driver,
    wait,
    item: dict,
    *,
    current_list_url: str,
    screenshot_dir: str,
    detail_scroll_steps: int,
    human_sleep: Callable[[float, float], None],
):
    href = item["href"]
    pid = item["pid"]
    print(f"  -> Opening detail: {href}")

    try:
        driver.get(href)
    except WebDriverException:
        driver.get(href)
    human_sleep(3, 5)

    _scroll_detail(driver, detail_scroll_steps, human_sleep)

    cur_url = driver.current_url.lower()
    page_source = driver.page_source.lower()

    if "captcha" in cur_url or "captcha" in page_source[:3000]:
        fname = os.path.join(screenshot_dir, f"captcha_detail_{pid}.png")
        try:
            driver.save_screenshot(fname)
        except Exception:
            pass
        print("CAPTCHA detected:", href)
        driver.get(current_list_url)
        human_sleep(2, 4)
        return item

    try:
        title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.re__pr-title")))
        item["title"] = title_el.text.strip()
    except Exception:
        item["title"] = ""

    price, area, price_per_m2 = _extract_short_info(driver)
    specs_map = _extract_specs(driver)

    if not price and ("Khoảng giá" in specs_map):
        price = specs_map.get("Khoảng giá", "")
    if not area and ("Diện tích" in specs_map):
        area = specs_map.get("Diện tích", "")
    if not price_per_m2 and ("Giá/m²" in specs_map):
        price_per_m2 = specs_map.get("Giá/m²", "")

    item["price"] = price
    item["area"] = area
    item["price_per_m2"] = price_per_m2

    try:
        addr_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#product-detail-web span.re__pr-short-description.js__pr-address"))
        )
        item["location"] = addr_el.text.strip()
    except Exception:
        item["location"] = ""

    try:
        desc_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.re__section-body.re__detail-content.js__section-body.js__pr-description")
            )
        )
        item["description"] = desc_el.text.strip()
    except Exception:
        item["description"] = ""

    item["images"] = _extract_images(driver)

    config = _extract_config(driver)
    item["config"] = config
    item["posted_date"] = config.get("Ngày đăng", "")

    item["specs"] = specs_map
    item["agent_phone"] = _extract_phone(driver, wait, human_sleep)

    map_coords, map_link = _extract_map(driver, wait)
    item["map_coords"] = map_coords
    item["map_link"] = map_link

    item["pricing_info"] = _extract_pricing(driver, wait)

    human_sleep(2, 4)
    try:
        driver.get(current_list_url)
        human_sleep(2, 4)
    except Exception:
        pass

    return item

