"""
Collection crawl — Lazada (requests + AJAX).

Entry point:
    run_crawl_session(session=1)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

from src.config_loader import PROJECT_ROOT, get_settings, resolve_path
from src.constants import OUTPUT_FILES
from src.preprocessing.crawl_progress import (
    count_total_collected,
    init_pending,
    load_category_products,
    load_progress,
    merge_raw_files,
    save_category_products,
    save_progress,
)
from src.preprocessing.crawl_errors import CrawlFailureError
from src.preprocessing.crawl_utils import get_crawl_delays, smart_delay
from src.preprocessing.lazada_crawler import crawl_category as crawl_lazada_category

logger = logging.getLogger(__name__)


def load_sampling_plan() -> dict[str, Any]:
    path = resolve_path("selection") / "sampling_plan.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Chưa có {path}. Chạy Bước 1 trước: python -m src.selection.run"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _configured_platforms(settings: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    project = settings.get("project", {})
    if project.get("platforms"):
        return list(project["platforms"])
    if project.get("platform"):
        return [project["platform"]]
    if plan.get("platforms"):
        return list(plan["platforms"])
    return ["Lazada"]


def _pick_crawler(platform: str):
    if platform.lower() == "lazada":
        return crawl_lazada_category
    return None


def _within_preferred_hours(schedule: dict[str, Any]) -> bool:
    preferred = schedule.get("preferred_hours") or []
    if not preferred:
        return True
    return datetime.now().hour in preferred


def _pick_session_categories(
    all_categories: list[dict[str, Any]],
    completed: list[str],
    per_session: int,
    session_index: int | None,
    failed: list[str] | None = None,
) -> list[dict[str, Any]]:
    name_to_cat = {c["category_name"]: c for c in all_categories}
    done = set(completed)
    failed_set = set(failed or [])

    if session_index is not None:
        start = (session_index - 1) * per_session
        end = start + per_session
        slot_names = [c["category_name"] for c in all_categories][start:end]
        return [name_to_cat[n] for n in slot_names if n in name_to_cat and n not in done]

    pending_names = [c["category_name"] for c in all_categories if c["category_name"] not in done]
    # Ưu tiên danh mục chưa fail — tránh kẹt retry vô hạn 2 DM lỗi đầu hàng đợi
    fresh = [n for n in pending_names if n not in failed_set]
    retry = [n for n in pending_names if n in failed_set]
    ordered = fresh + retry
    pick = ordered[:per_session]
    return [name_to_cat[n] for n in pick]


def run_crawl_session(
    *,
    session: int | None = None,
    platform: str | None = None,
    merge_only: bool = False,
    keep_browser_open: bool = False,
    force_hours: bool = False,
    stop_on_failure: bool | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    plan = load_sampling_plan()
    platforms = _configured_platforms(settings, plan)
    active_platform = platform or platforms[0]
    crawl_cfg = settings["crawl"]
    schedule = crawl_cfg.get("schedule", {})
    raw_dir = resolve_path("raw")
    all_categories = [
        c for c in plan["categories"] if (c.get("platform") or active_platform) == active_platform
    ]
    all_names = [c["category_name"] for c in all_categories]
    per_session = schedule.get("categories_per_session", 2)
    delays = get_crawl_delays(crawl_cfg)
    if stop_on_failure is None:
        stop_on_failure = schedule.get("stop_on_failure", True)

    if merge_only:
        merged_name = f"{active_platform.lower()}_{OUTPUT_FILES['raw_merged']}"
        merged = merge_raw_files(
            raw_dir, merged_name, platform=active_platform
        )
        progress = load_progress(raw_dir, active_platform)
        progress["platform"] = active_platform
        progress["total_raw_collected"] = count_total_collected(
            raw_dir, progress.get("completed", []), platform=active_platform
        )
        save_progress(raw_dir, progress)
        logger.info("Merge xong: %s (%s bản ghi)", merged, progress["total_raw_collected"])
        return {"merged": str(merged), "total": progress["total_raw_collected"]}

    if not force_hours and not _within_preferred_hours(schedule):
        preferred = schedule.get("preferred_hours", [])
        raise RuntimeError(
            f"Giờ hiện tại ({datetime.now().hour}h) ngoài preferred_hours {preferred}. "
            "Dùng --force để bỏ qua."
        )

    progress = load_progress(raw_dir, active_platform)
    progress["platform"] = active_platform
    if not progress.get("pending") and not progress.get("completed"):
        progress["pending"] = list(all_names)
        progress["completed"] = []
        progress["failed"] = []

    completed = progress.get("completed", [])
    # Đồng bộ completed từ file đã có sẵn trên đĩa (an toàn khi mất progress file)
    existing_completed = [
        name
        for name in all_names
        if len(load_category_products(raw_dir, name, platform=active_platform)) > 0
    ]
    if existing_completed:
        completed = list(dict.fromkeys(completed + existing_completed))
        progress["completed"] = completed

    pending = init_pending(all_names, completed)
    progress["pending"] = pending
    progress["total_raw_collected"] = count_total_collected(
        raw_dir, progress["completed"], platform=active_platform
    )
    save_progress(raw_dir, progress)

    if not pending:
        merged_name = f"{active_platform.lower()}_{OUTPUT_FILES['raw_merged']}"
        merged = merge_raw_files(
            raw_dir, merged_name, platform=active_platform
        )
        logger.info("Tất cả danh mục đã crawl [%s]. Merged: %s", active_platform, merged)
        return {"status": "done", "platform": active_platform, "merged": str(merged)}

    batch = _pick_session_categories(
        all_categories,
        completed,
        per_session,
        session,
        progress.get("failed", []),
    )
    if not batch:
        return {
            "status": "skipped",
            "session": session,
            "completed": completed,
            "pending": pending,
        }

    logger.info(
        "Phiên crawl [%s]: %s danh mục — %s",
        active_platform,
        len(batch),
        [c["category_name"] for c in batch],
    )

    max_retries = schedule.get("max_retries_per_category", 2)
    session_results: list[dict[str, Any]] = []

    for i, cat in enumerate(batch):
        name = cat["category_name"]
        cat_platform = cat.get("platform") or active_platform
        products: list[dict[str, Any]] = []
        blocked = False

        # Nếu category đã có dữ liệu thì bỏ qua, không crawl lại
        cached = load_category_products(raw_dir, name, platform=active_platform)
        if cached:
            progress["completed"] = list(
                dict.fromkeys(progress.get("completed", []) + [name])
            )
            progress["pending"] = init_pending(all_names, progress["completed"])
            progress["failed"] = [f for f in progress.get("failed", []) if f != name]
            progress["total_raw_collected"] = count_total_collected(
                raw_dir, progress["completed"], platform=active_platform
            )
            save_progress(raw_dir, progress)
            session_results.append(
                {
                    "category": name,
                    "platform": cat_platform,
                    "count": len(cached),
                    "status": "cached_skip",
                }
            )
            continue

        crawler = _pick_crawler(cat_platform)
        if crawler is None:
            logger.warning(
                "Chưa hỗ trợ crawler cho platform=%s (category=%s). Bỏ qua.",
                cat_platform,
                name,
            )
            session_results.append(
                {
                    "category": name,
                    "platform": cat_platform,
                    "count": 0,
                    "status": "unsupported",
                }
            )
            continue

        for attempt in range(1, max_retries + 1):
            products, blocked = crawler(cat, crawl_cfg, PROJECT_ROOT)
            if products:
                break
            if blocked and schedule.get("stop_on_captcha", True):
                logger.warning("Dừng retry %s do lỗi HTTP/cookie", name)
                break
            logger.warning("Retry %s/%s cho %s", attempt, max_retries, name)

        if products and schedule.get("save_checkpoint_per_category", True):
            save_category_products(raw_dir, name, products, platform=active_platform)
            progress["completed"] = list(
                dict.fromkeys(progress.get("completed", []) + [name])
            )
            progress["pending"] = init_pending(all_names, progress["completed"])
            progress["failed"] = [f for f in progress.get("failed", []) if f != name]
            progress["total_raw_collected"] = count_total_collected(
                raw_dir, progress["completed"], platform=active_platform
            )
            save_progress(raw_dir, progress)
            session_results.append(
                {"category": name, "platform": cat_platform, "count": len(products), "status": "ok"}
            )
        else:
            failed = list(dict.fromkeys(progress.get("failed", []) + [name]))
            progress["failed"] = failed
            save_progress(raw_dir, progress)
            fail_info = {
                "category": name,
                "platform": cat_platform,
                "count": len(products),
                "status": "failed",
                "blocked": blocked,
            }
            session_results.append(fail_info)
            logger.error(
                "CRAWL FAIL [%s]: blocked=%s, thu được %s SP — xem log phía trên "
                "(Expecting value / cookie / HTTP)",
                name,
                blocked,
                len(products),
            )
            if stop_on_failure and blocked:
                raise CrawlFailureError(
                    name,
                    blocked=blocked,
                    count=len(products),
                )

        if i < len(batch) - 1:
            smart_delay(*delays["between_categories"])

    merged_path = None
    if not progress.get("pending"):
        merged_name = f"{active_platform.lower()}_{OUTPUT_FILES['raw_merged']}"
        merged_path = merge_raw_files(
            raw_dir, merged_name, platform=active_platform
        )

    rest_min = schedule.get("rest_between_sessions_minutes", 45)
    if progress.get("pending"):
        logger.info(
            "Còn %s danh mục pending. Nghỉ ~%s phút trước phiên tiếp theo.",
            len(progress["pending"]),
            rest_min,
        )

    return {
        "platform": active_platform,
        "session": session,
        "session_results": session_results,
        "completed": progress.get("completed", []),
        "pending": progress.get("pending", []),
        "failed": progress.get("failed", []),
        "total_raw_collected": progress.get("total_raw_collected", 0),
        "merged": str(merged_path) if merged_path else None,
        "rest_minutes_suggested": rest_min if progress.get("pending") else 0,
    }


def run_crawl_all(
    *,
    platform: str | None = None,
    keep_browser_open: bool = False,
    force_hours: bool = False,
    rest_between_sessions: bool = True,
    stop_on_failure: bool | None = None,
) -> dict[str, Any]:
    """
    Chạy liên tục các phiên crawl cho đến khi hết danh mục pending.

    Mỗi phiên = `categories_per_session` danh mục (mặc định 2), có delay
    giữa danh mục trong phiên. Giữa các phiên: nghỉ theo config (hoặc bỏ
    qua với rest_between_sessions=False / --no-rest).
    """
    settings = get_settings()
    plan = load_sampling_plan()
    schedule = settings["crawl"].get("schedule", {})
    platforms = [platform] if platform else _configured_platforms(settings, plan)
    rest_min = schedule.get("rest_between_sessions_minutes", 5)
    sessions_run: list[dict[str, Any]] = []
    total = 0
    completed: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    merged: list[str] = []

    for pf in platforms:
        prev_pending: list[str] | None = None
        stall_count = 0
        while True:
            result = run_crawl_session(
                session=None,
                platform=pf,
                keep_browser_open=keep_browser_open,
                force_hours=force_hours,
                stop_on_failure=stop_on_failure,
            )
            sessions_run.append(result)

            status = result.get("status")
            platform_pending = result.get("pending") or []
            if status == "done" or not platform_pending:
                break
            if status == "skipped":
                break

            session_ok = sum(
                1 for r in result.get("session_results", []) if r.get("status") == "ok"
            )
            if session_ok == 0 and platform_pending == prev_pending:
                stall_count += 1
                if stall_count >= 3:
                    logger.warning(
                        "Dừng --all [%s]: 3 phiên liên tiếp không crawl được DM mới. "
                        "Chạy lại sau hoặc crawl thủ công DM trong failed.",
                        pf,
                    )
                    break
            else:
                stall_count = 0
            prev_pending = list(platform_pending)

            if rest_between_sessions and rest_min > 0:
                logger.info(
                    "Nghỉ %s phút trước phiên tiếp theo [%s] (%s danh mục còn lại)...",
                    rest_min,
                    pf,
                    len(platform_pending),
                )
                time.sleep(rest_min * 60)

        if sessions_run:
            last = sessions_run[-1]
            total += int(last.get("total_raw_collected", 0))
            completed.extend(last.get("completed", []))
            pending.extend(last.get("pending", []))
            failed.extend(last.get("failed", []))
            if last.get("merged"):
                merged.append(last["merged"])

    return {
        "mode": "all",
        "platforms": platforms,
        "sessions_count": len(sessions_run),
        "sessions": sessions_run,
        "total_raw_collected": total,
        "merged": merged,
        "completed": completed,
        "pending": pending,
        "failed": failed,
    }


run_collection = run_crawl_session
