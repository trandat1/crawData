import time
from random import uniform   
from datetime import datetime

def human_sleep(a: float = 3, b: float = 8):
    time.sleep(uniform(a, b))

def decimal_to_dms(value):
    """Convert decimal degrees → DMS (độ–phút–giây)."""
    deg = int(value)
    minutes_float = abs(value - deg) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return deg, minutes, seconds

def format_dms(lat, lng):
    lat = float(lat)
    lng = float(lng)

    lat_deg, lat_min, lat_sec = decimal_to_dms(lat)
    lng_deg, lng_min, lng_sec = decimal_to_dms(lng)

    lat_dir = "N" if lat >= 0 else "S"
    lng_dir = "E" if lng >= 0 else "W"

    return (f"{abs(lat_deg)}°{lat_min}'{lat_sec:.2f}\" {lat_dir}, "
            f"{abs(lng_deg)}°{lng_min}'{lng_sec:.2f}\" {lng_dir}")
    
    
def normalize_date(date_str):
    """
    Chuẩn hóa ngày về dạng YYYY-MM-DD để dễ so sánh.
    Hỗ trợ cả định dạng:
        - YYYY-MM-DD (input từ HTML)
        - DD/MM/YYYY (data scrape)
    """
    if not date_str:
        return None
    
    # Trường hợp input HTML: 2025-11-09
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        pass

    # Trường hợp scrape: 09/11/2025
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except:
        pass

    return None
    