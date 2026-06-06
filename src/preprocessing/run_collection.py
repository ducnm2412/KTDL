"""
CLI Collection — wrapper mỏng cho src.preprocessing.crawl.

Usage:
    python -m src.preprocessing.run_collection
    python -m src.preprocessing.run_collection --session 1
    python -m src.preprocessing.run_collection --merge-only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from src.preprocessing.crawl import run_crawl_session
from src.preprocessing.crawl_errors import CrawlFailureError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collection — crawl Lazada")
    parser.add_argument(
        "--session",
        type=int,
        default=None,
        help="Chỉ crawl phiên N (mỗi phiên 2 danh mục theo config)",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Chỉ gộp file categories/ → lazada_raw_merged.json",
    )
    parser.add_argument(
        "--keep-browser",
        action="store_true",
        help="Không đóng Chrome sau phiên (debug)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bỏ qua kiểm tra preferred_hours",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Crawl liên tục đến hết danh mục pending",
    )
    parser.add_argument(
        "--no-rest",
        action="store_true",
        help="Không nghỉ giữa các phiên khi dùng --all",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Không dừng ngay khi 1 danh mục fail",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        help="Chỉ crawl cho 1 sàn cụ thể (Lazada/Shopee/Tiki)",
    )
    args = parser.parse_args()

    stop_on_failure = not args.continue_on_failure
    try:
        if args.all:
            from src.preprocessing.crawl import run_crawl_all

            result = run_crawl_all(
                platform=args.platform,
                keep_browser_open=args.keep_browser,
                force_hours=args.force,
                rest_between_sessions=not args.no_rest,
                stop_on_failure=stop_on_failure,
            )
        else:
            result = run_crawl_session(
                session=args.session,
                platform=args.platform,
                merge_only=args.merge_only,
                keep_browser_open=args.keep_browser,
                force_hours=args.force,
                stop_on_failure=stop_on_failure,
            )
    except CrawlFailureError as exc:
        payload = {
            "status": "error",
            "error": str(exc),
            "category": exc.category,
            "blocked": exc.blocked,
            "count": exc.count,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
