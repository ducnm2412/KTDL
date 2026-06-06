"""Lấy cookies Lazada qua Selenium (dùng khi requests bị 403)."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def get_fresh_cookies_lazada(category_path: str, wait_time: int = 10) -> dict[str, str]:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as exc:
        raise ImportError(
            "Cần cài selenium và webdriver-manager: pip install selenium webdriver-manager"
        ) from exc

    url = f"https://www.lazada.vn/{category_path}/"
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(wait_time)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(3)
        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
        logger.info("Lấy %s cookies từ Lazada (%s)", len(cookies), category_path)
        return cookies
    except Exception as exc:
        logger.error("Lỗi lấy cookies Lazada: %s", exc)
        return {}
    finally:
        driver.quit()
