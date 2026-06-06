"""
CLI chạy pipeline.

Ví dụ:
  python -m src.pipeline.run --step selection
  python -m src.pipeline.run --step crawl
  python -m src.pipeline.run --step crawl --session 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STEPS = ("selection", "crawl", "clean", "features", "label", "encode", "train", "evaluate", "all")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lazada DM pipeline")
    parser.add_argument(
        "--step",
        choices=STEPS,
        required=True,
        help="Bước cần chạy",
    )
    parser.add_argument(
        "--session",
        type=int,
        default=None,
        help="Phiên crawl (chỉ với --step crawl)",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Chỉ merge raw (chỉ với --step crawl)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bỏ qua preferred_hours (chỉ với --step crawl)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Crawl liên tục đến hết danh mục pending (chỉ với --step crawl)",
    )
    parser.add_argument(
        "--no-rest",
        action="store_true",
        help="Không nghỉ giữa các phiên khi dùng --all",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Không dừng ngay khi 1 danh mục fail (mặc định: dừng nếu stop_on_failure trong config)",
    )
    parser.add_argument(
        "--keep-browser",
        action="store_true",
        help="Không đóng Chrome sau crawl",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()

    if args.step == "selection":
        from src.selection.run import run_selection

        run_selection()
        return

    if args.step == "crawl":
        from src.preprocessing.crawl_errors import CrawlFailureError

        stop_on_failure = not args.continue_on_failure
        try:
            if args.all:
                from src.preprocessing.crawl import run_crawl_all

                result = run_crawl_all(
                    keep_browser_open=args.keep_browser,
                    force_hours=args.force,
                    rest_between_sessions=not args.no_rest,
                    stop_on_failure=stop_on_failure,
                )
            else:
                from src.preprocessing.crawl import run_crawl_session

                result = run_crawl_session(
                    session=args.session,
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
        return

    if args.step == "clean":
        from src.preprocessing.clean import run_clean_hybrid

        result = run_clean_hybrid()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    raise NotImplementedError(
        f"Bước '{args.step}' chưa triển khai. "
        "Hiện có: selection, crawl, clean."
    )


if __name__ == "__main__":
    main()
