# Collection — Crawl Lazada (Bước 2a)

Thu thập dữ liệu từ **lazada.vn** qua AJAX API.

## Cài đặt

```bash
pip install requests selenium webdriver-manager
```

## Chạy

```bash
# Một phiên (2 danh mục) rồi thoát — phải chạy lại lệnh cho phiên tiếp
python -m src.pipeline.run --step crawl --force

# Chạy liên tục hết 16 danh mục (nghỉ 5 phút giữa mỗi phiên 2 DM)
python -m src.pipeline.run --step crawl --all --force

# Chạy liên tục, không nghỉ giữa phiên
python -m src.pipeline.run --step crawl --all --no-rest --force

python -m src.pipeline.run --step crawl --session 1 --force
python -m src.pipeline.run --step crawl --merge-only
```

## Output

```
data/raw/
├── categories/lazada_*.json
├── crawl_progress.json
└── lazada_raw_merged.json
```

## Lịch crawl

- 2 danh mục / phiên, 8 phiên tổng
- Mặc định **mỗi lần chạy lệnh = 1 phiên** rồi process thoát (tránh bị Lazada chặn khi crawl quá lâu một lần)
- `rest_between_sessions_minutes` (5 phút) chỉ **in log** khi chạy 1 phiên; chỉ **thực sự sleep** khi dùng `--all`
- `--all`: tự lặp phiên đến hết pending; `--no-rest`: bỏ sleep giữa phiên
- `--force` bỏ qua `preferred_hours` (9–11h, 14–16h)
- Mặc định **dừng ngay** khi 1 DM bị chặn (`stop_on_failure: true`); dùng `--continue-on-failure` để chạy tiếp DM khác như trước
