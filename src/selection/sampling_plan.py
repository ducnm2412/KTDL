"""Bước 1 KDD — Kế hoạch lấy mẫu stratified đa sàn theo target_count."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import get_categories, get_settings, resolve_path


def build_category_url(category: dict[str, Any]) -> str:
    platform = (category.get("platform") or "Lazada").strip().lower()
    path = str(category.get("path") or "").strip().strip("/")
    if not path:
        return ""

    if path.startswith("http://") or path.startswith("https://"):
        return path

    base_by_platform = {
        "lazada": "https://www.lazada.vn",
        "shopee": "https://shopee.vn",
        "tiki": "https://tiki.vn",
    }
    base = base_by_platform.get(platform, "https://www.lazada.vn")
    return f"{base}/{path}/"


def build_sampling_plan() -> dict[str, Any]:
    settings = get_settings()
    categories = get_categories()
    crawl = settings["crawl"]
    project = settings["project"]
    target = project["target_records"]
    buffer_ratio = crawl.get("crawl_buffer_ratio", 1.1)

    items = []
    by_platform: dict[str, dict[str, int]] = {}
    for cat in categories:
        platform = cat.get("platform") or project.get("platform", "Lazada")
        target_count = int(cat["target_count"])
        crawl_target = int(target_count * buffer_ratio)
        by_platform.setdefault(
            platform,
            {"planned_clean": 0, "planned_crawl_with_buffer": 0, "categories": 0},
        )
        by_platform[platform]["planned_clean"] += target_count
        by_platform[platform]["planned_crawl_with_buffer"] += crawl_target
        by_platform[platform]["categories"] += 1
        items.append(
            {
                "platform": platform,
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
        "platforms": project.get("platforms") or [project.get("platform", "Lazada")],
        "crawl_method": crawl.get("method", "requests_ajax"),
        "target_records_final": target,
        "total_planned_clean": total_clean,
        "total_planned_crawl_with_buffer": total_crawl,
        "crawl_buffer_ratio": buffer_ratio,
        "stratified": total_clean == target,
        "per_platform": by_platform,
        "categories": items,
    }


def save_sampling_plan(output_dir: Path | None = None) -> Path:
    out_dir = output_dir or resolve_path("selection")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "sampling_plan.json"
    plan = build_sampling_plan()
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
