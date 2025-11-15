from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def init_driver(
    debugger_address: str,
    page_load_timeout: int,
    wait_timeout: int,
):
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", debugger_address)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(page_load_timeout)
    wait = WebDriverWait(driver, wait_timeout)
    return driver, wait

