"""Delay helpers cho Collection crawl."""

from __future__ import annotations

import random
import time
from typing import Any


def smart_delay(min_sec: float, max_sec: float) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def get_crawl_delays(crawl_cfg: dict[str, Any]) -> dict[str, tuple[float, float]]:
    return {
        "quick": (1.5, 3.0),
        "normal": (
            crawl_cfg.get("sleep_min_seconds", 3),
            crawl_cfg.get("sleep_max_seconds", 7),
        ),
        "careful": (
            crawl_cfg.get("sleep_between_pages_min", 5),
            crawl_cfg.get("sleep_between_pages_max", 12),
        ),
        "between_categories": (
            crawl_cfg.get("sleep_between_categories_min", 15),
            crawl_cfg.get("sleep_between_categories_max", 30),
        ),
    }
