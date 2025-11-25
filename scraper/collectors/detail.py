from __future__ import annotations

import os
import re
from typing import Callable

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .. import utils


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
    price = ""           # giá tổng (ext)
    area = ""            # diện tích
    price_per_m2 = ""    # giá/m2

    per_m_pattern = re.compile(r'(triệu|tỷ|đ|dong|vnđ).*(/m2|/m²|/m)', re.IGNORECASE)
    area_pattern = re.compile(r'\b[0-9]+(?:[.,][0-9]+)?\s*(m²|m2|m)\b', re.IGNORECASE)

    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".re__pr-short-info .re__pr-short-info-item")
        for it in items:
            try:
                label = ""
                try:
                    label = it.find_element(By.CSS_SELECTOR, "span.title").text.strip().lower()
                except:
                    label = (it.get_attribute("innerText") or "").splitlines()[0].strip().lower()

                # value
                try:
                    value = it.find_element(By.CSS_SELECTOR, "span.value").text.strip()
                except:
                    parts = (it.get_attribute("innerText") or "").splitlines()
                    value = parts[1].strip() if len(parts) > 1 else ""

                # ext = giá tổng
                try:
                    ext = it.find_element(By.CSS_SELECTOR, "span.ext").text.strip()
                except:
                    ext = ""

                low_value = value.lower()
                low_label = label.lower()

                # ---- AREA ----
                # Ưu tiên kiểm tra label "diện tích" trước
                if not area and (low_label.startswith("diện tích") or (not low_label.startswith("giá") and area_pattern.search(low_value))):
                    m = area_pattern.search(value)
                    area = m.group(0) if m else value

                # ---- PRICE và PRICE_PER_M2 ----
                # Kiểm tra nếu label có chứa "giá" hoặc "khoảng giá"
                if "giá" in low_label or "khoảng giá" in low_label:
                    # value = giá tổng (ví dụ: "6,3 tỷ")
                    # ext = giá/m² (ví dụ: "~5,99 triệu/m²")
                    
                    # PRICE (tổng) = value
                    if not price and value:
                        price = value
                    
                    # PRICE_PER_M2 = ext (nếu ext có pattern giá/m²)
                    if not price_per_m2 and ext:
                        if per_m_pattern.search(ext.lower()) or "/m" in ext.lower() or "m²" in ext.lower():
                            price_per_m2 = ext
                        # Nếu ext không phải giá/m², có thể là giá tổng bổ sung
                        elif not price:
                            price = ext

            except:
                continue

    except:
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
    """
    Extract phone number và contact name từ phone button.
    Returns: (phone_text, contact_name)
    """
    phone_text = ""
    contact_name = ""
    try:
        btn = driver.find_element(
            By.CSS_SELECTOR, 'div[kyc-tracking-id="lead-phone-ldp"], div[kyc-tracking-id="lead-phone-ldp"] .re__btn'
        )
        
        # Lấy contact name từ data-kyc-name
        try:
            contact_name = btn.get_attribute("data-kyc-name") or ""
            contact_name = contact_name.strip()
        except:
            pass
        
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
        contact_name = ""
    return phone_text, contact_name


def _extract_map(driver, wait):
    map_coords = ""
    map_link = ""
    map_dms = ""

    try:
        iframe = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.re__pr-map iframe")
        ))

        map_link = iframe.get_attribute("src") or iframe.get_attribute("data-src") or ""
        
        if not map_link:
            return "", "", ""

        # Pattern 1: Google Maps embed với !3d và !4d (ví dụ: ...!3d21.1136798508057!4d105.495305786485)
        match = re.search(r'!3d([0-9\.\-]+)!4d([0-9\.\-]+)', map_link)
        if match:
            lat_str, lng_str = match.group(1), match.group(2)
        else:
            # Pattern 2: Google Maps embed với q=lat,lng (ví dụ: ...?q=21.1136798508057,105.495305786485&key=...)
            match2 = re.search(r'q=([0-9\.\-]+),([0-9\.\-]+)', map_link)
            if match2:
                lat_str, lng_str = match2.group(1), match2.group(2)
            else:
                return "", map_link, ""

        # Chuyển đổi sang float và kiểm tra tính hợp lệ
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            
            # Kiểm tra phạm vi hợp lệ (lat: -90 đến 90, lng: -180 đến 180)
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                map_coords = f"{lat},{lng}"
                map_dms = utils.format_dms(lat, lng)
            else:
                # Tọa độ ngoài phạm vi hợp lệ
                return "", map_link, ""
        except (ValueError, TypeError):
            # Không thể chuyển đổi sang float
            return "", map_link, ""

    except Exception:
        # Không tìm thấy iframe hoặc lỗi khác
        pass

    return map_coords, map_link, map_dms



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
    phone_text, contact_name = _extract_phone(driver, wait, human_sleep)
    item["agent_phone"] = phone_text
    item["agent_name"] = contact_name

    map_coords, map_link, map_dms = _extract_map(driver, wait)
    item["map_coords"] = map_coords
    item["map_link"] = map_link
    item["map_dms"] = map_dms

    # item["pricing_info"] = _extract_pricing(driver, wait)

    human_sleep(2, 4)
    try:
        driver.get(current_list_url)
        human_sleep(2, 4)
    except Exception:
        pass

    return item

