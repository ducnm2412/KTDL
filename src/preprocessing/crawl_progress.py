"""Checkpoint và merge file raw sau Collection."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.constants import platform_file_prefix

PROGRESS_FILENAME = "crawl_progress_{prefix}.json"


def slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug.strip())
    return slug or "unknown"


def category_filename(category_name: str, prefix: str) -> str:
    return f"{prefix}_{slugify(category_name)}.json"


def progress_path(raw_dir: Path, platform: str) -> Path:
    prefix = platform_file_prefix(platform)
    return raw_dir / PROGRESS_FILENAME.format(prefix=prefix)


def load_progress(raw_dir: Path, platform: str) -> dict[str, Any]:
    path = progress_path(raw_dir, platform)
    default = {
        "platform": platform,
        "completed": [],
        "pending": [],
        "failed": [],
        "last_session_at": None,
        "total_raw_collected": 0,
    }
    if not path.exists():
        return default

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("platform") != platform:
        return default
    return data


def save_progress(raw_dir: Path, progress: dict[str, Any]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    progress["last_session_at"] = datetime.now(timezone.utc).isoformat()
    platform = progress.get("platform", "Lazada")
    progress_path(raw_dir, platform).write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_category_products(
    raw_dir: Path,
    category_name: str,
    products: list[dict[str, Any]],
    *,
    platform: str,
) -> Path:
    prefix = platform_file_prefix(platform)
    categories_dir = raw_dir / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    path = categories_dir / category_filename(category_name, prefix)
    path.write_text(
        json.dumps(products, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_category_products(
    raw_dir: Path, category_name: str, *, platform: str
) -> list[dict[str, Any]]:
    prefix = platform_file_prefix(platform)
    path = raw_dir / "categories" / category_filename(category_name, prefix)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def count_total_collected(
    raw_dir: Path, completed: list[str], *, platform: str
) -> int:
    total = 0
    for name in completed:
        total += len(load_category_products(raw_dir, name, platform=platform))
    return total


def merge_raw_files(
    raw_dir: Path,
    output_name: str,
    *,
    platform: str,
) -> Path:
    prefix = platform_file_prefix(platform)
    categories_dir = raw_dir / "categories"
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    if categories_dir.exists():
        for path in sorted(categories_dir.glob(f"{prefix}_*.json")):
            items = json.loads(path.read_text(encoding="utf-8"))
            for item in items:
                pid = str(item.get("id", ""))
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    merged.append(item)

    out_path = raw_dir / output_name
    out_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def init_pending(category_names: list[str], completed: list[str]) -> list[str]:
    done = set(completed)
    return [n for n in category_names if n not in done]
