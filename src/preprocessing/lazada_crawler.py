"""Crawl 1 danh mục Lazada qua AJAX API (?ajax=true&page=N)."""

from __future__ import annotations

import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests

from src.preprocessing.lazada_browser import get_fresh_cookies_lazada
from src.preprocessing.crawl_utils import smart_delay

logger = logging.getLogger(__name__)


def _parse_sold(sold_text: str) -> int | None:
    if not sold_text:
        return None
    numbers = re.findall(r"\d+", sold_text.replace(",", ""))
    if not numbers:
        return None
    value = int(numbers[0])
    if "k" in sold_text.lower():
        value *= 1000
    return value


def _parse_item(item: dict[str, Any], category_name: str) -> dict[str, Any] | None:
    item_id = item.get("itemId")
    if not item_id:
        return None

    sold_text = (item.get("itemSoldCntShow") or "").strip()
    item_url = item.get("itemUrl")
    if item_url and not item_url.startswith("http"):
        item_url = "https:" + item_url

    return {
        "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "Lazada",
        "category_name": category_name,
        "id": str(item_id),
        "shop_id": str(item.get("sellerId") or item.get("shopId") or ""),
        "name": item.get("name"),
        "price": item.get("priceShow") or item.get("price"),
        "original_price": item.get("originalPriceShow") or item.get("originalPrice"),
        "discount_rate": item.get("discount"),
        "rating_average": item.get("ratingScore"),
        "review_count": item.get("review"),
        "quantity_sold_value": _parse_sold(sold_text),
        "quantity_sold_text": sold_text,
        "brand": item.get("brandName"),
        "location": item.get("location"),
        "seller_name": item.get("sellerName"),
        "url": item_url,
    }


def crawl_category(
    category: dict[str, Any],
    crawl_cfg: dict[str, Any],
    project_root,
    *,
    max_pages: int | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Crawl Lazada category qua requests + cookies.

    Returns:
        (products, blocked) — blocked=True khi HTTP lỗi liên tục
    """
    _ = project_root
    name = category["category_name"]
    path = category.get("path") or category["category_url"].rstrip("/").split("/")[-2]
    base_url = f"https://www.lazada.vn/{path}/"
    target = category.get(
        "target_count_crawl",
        crawl_cfg.get("target_per_category_raw", 687),
    )
    pages_limit = max_pages or category.get(
        "max_pages",
        crawl_cfg.get("max_pages_per_category", 15),
    )
    timeout = crawl_cfg.get("request_timeout_seconds", 20)
    max_retries = crawl_cfg.get("schedule", {}).get("max_retries_per_category", 2)

    page_sleep_min = crawl_cfg.get("sleep_between_pages_min", 5) / 3
    page_sleep_max = crawl_cfg.get("sleep_between_pages_max", 12) / 3
    cat_sleep_min = crawl_cfg.get("sleep_between_categories_min", 15)
    cat_sleep_max = crawl_cfg.get("sleep_between_categories_max", 30)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": base_url,
        "X-Requested-With": "XMLHttpRequest",
    }

    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    cookies = get_fresh_cookies_lazada(
        path, wait_time=crawl_cfg.get("login_wait_seconds", 10)
    )
    if not cookies:
        logger.error("Không lấy được cookie Lazada cho %s", name)
        return [], True

    logger.info(
        "Crawl Lazada: %s (mục tiêu ~%s SP, tối đa %s trang)",
        name,
        target,
        pages_limit,
    )

    page = 1
    blocked = False

    while page <= pages_limit and len(products) < target:
        params = {"ajax": "true", "page": page}
        success = False
        retry = 0

        while retry < max_retries and not success:
            try:
                resp = requests.get(
                    base_url,
                    headers=headers,
                    cookies=cookies,
                    params=params,
                    timeout=timeout,
                )

                if resp.status_code != 200:
                    logger.warning(
                        "%s trang %s: HTTP %s — refresh cookie",
                        name,
                        page,
                        resp.status_code,
                    )
                    cookies = get_fresh_cookies_lazada(path)
                    retry += 1
                    smart_delay(cat_sleep_min, cat_sleep_max)
                    continue

                data = resp.json()
                items = data.get("mods", {}).get("listItems", [])
                if not items:
                    logger.info("%s — hết dữ liệu trang %s", name, page)
                    return products, blocked

                new_count = 0
                for item in items:
                    product = _parse_item(item, name)
                    if product and product["id"] not in seen:
                        seen.add(product["id"])
                        products.append(product)
                        new_count += 1

                logger.info(
                    "%s trang %s: +%s SP (tổng %s)",
                    name,
                    page,
                    new_count,
                    len(products),
                )
                success = True
                page += 1
                smart_delay(page_sleep_min, page_sleep_max)

            except Exception as exc:
                retry += 1
                logger.error("%s trang %s lỗi: %s", name, page, exc)
                smart_delay(cat_sleep_min, cat_sleep_max)

        if not success:
            blocked = True
            break

    return products, blocked
