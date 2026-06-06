#!/usr/bin/env bash
# Chạy Collection (crawl Lazada) — Selenium lấy cookie + requests AJAX

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d .venv ]; then
  source .venv/bin/activate
fi

SESSION="${1:-}"
FORCE="${2:---force}"

echo "=== Lazada Collection ==="
echo "Chrome mở qua Selenium để lấy cookie Lazada."

if [ -n "$SESSION" ]; then
  python -m src.pipeline.run --step crawl --session "$SESSION" $FORCE
else
  python -m src.pipeline.run --step crawl $FORCE
fi
