"""Bước 1 KDD — Kế hoạch lấy mẫu stratified 16 danh mục × target_count."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import get_categories, get_settings, resolve_path


def build_category_url(category: dict[str, Any]) -> str:
    path = category["path"]
    return f"https://www.lazada.vn/{path}/"


def build_sampling_plan() -> dict[str, Any]:
    settings = get_settings()
    categories = get_categories()
    crawl = settings["crawl"]
    project = settings["project"]
    target = project["target_records"]
    buffer_ratio = crawl.get("crawl_buffer_ratio", 1.1)

    items = []
    for cat in categories:
        target_count = cat["target_count"]
        crawl_target = int(target_count * buffer_ratio)
        items.append(
            {
                "category_name": cat["name"],
                "path": cat["path"],
                "category_url": build_category_url(cat),
                "search_url": build_category_url(cat),
                "target_count_clean": target_count,
                "target_count_crawl": crawl_target,
                "max_pages": crawl["max_pages_per_category"],
            }
        )

    total_clean = sum(i["target_count_clean"] for i in items)
    total_crawl = sum(i["target_count_crawl"] for i in items)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": project["platform"],
        "crawl_method": crawl.get("method", "requests_ajax"),
        "target_records_final": target,
        "total_planned_clean": total_clean,
        "total_planned_crawl_with_buffer": total_crawl,
        "crawl_buffer_ratio": buffer_ratio,
        "stratified": total_clean == target,
        "categories": items,
    }


def save_sampling_plan(output_dir: Path | None = None) -> Path:
    out_dir = output_dir or resolve_path("selection")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "sampling_plan.json"
    plan = build_sampling_plan()
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
