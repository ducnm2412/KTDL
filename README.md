# Lazada Product Classification

Đề tài Data Mining: xây dựng bộ dữ liệu sản phẩm Lazada để phân loại 4 lớp:
`Hot Trend`, `Best Seller`, `Best Deal`, `Normal`.

## 1) Yêu cầu môi trường

- macOS/Linux, Python 3.11+ (khuyên dùng 3.12/3.13)
- Chrome (phục vụ lấy cookie khi crawl)

## 2) Cài đặt

```bash
cd shopee-product-classification
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Nếu dùng terminal mới, nhớ chạy lại:

```bash
source .venv/bin/activate
```

## 3) Cấu trúc pipeline đang hỗ trợ

CLI chính:

```bash
python -m src.pipeline.run --step <selection|crawl|clean>
```

Hiện tại project đã triển khai:

- `selection`
- `crawl`
- `clean`

Các bước `features`, `label`, `encode`, `train`, `evaluate` chưa mở trong CLI.

## 4) Chạy từng bước

### Bước 1 - Selection

```bash
python -m src.pipeline.run --step selection
```

Output chính:

- `data/selection/sampling_plan.json`
- `data/selection/selection_report.md`

### Bước 2a - Crawl (Collection)

Chạy 1 phiên (mặc định 2 danh mục):

```bash
python -m src.pipeline.run --step crawl --force
```

Chạy toàn bộ danh mục pending:

```bash
python -m src.pipeline.run --step crawl --all --force
```

Chạy toàn bộ, không nghỉ giữa phiên:

```bash
python -m src.pipeline.run --step crawl --all --no-rest --force
```

Cho phép bỏ qua lỗi 1 danh mục để chạy tiếp:

```bash
python -m src.pipeline.run --step crawl --all --continue-on-failure --force
```

Output crawl:

- `data/raw/categories/lazada_*.json`
- `data/raw/crawl_progress.json`
- `data/raw/lazada_raw_merged.json` (khi merge)

Chi tiết thêm: [docs/collection_guide.md](docs/collection_guide.md)

### Bước 2b - Clean

```bash
python -m src.pipeline.run --step clean
```

Luồng clean hiện tại:

1. Mapping raw -> schema clean bằng pandas
2. Parse numeric fields
3. Xử lý missing + rule nghiệp vụ
4. Outlier theo percentile từ `config/settings.yaml`
5. Dedup theo khóa kép `platform + id` (sort chất lượng trước)
6. Stratified sampling theo `data/selection/sampling_plan.json`

Output clean:

- `data/clean/lazada_10k_clean.json`

## 5) File cấu hình quan trọng

- `config/settings.yaml`
  - `crawl.schedule.*` (session, retry, stop_on_failure...)
  - `clean.*` (percentile outlier)
- `data/selection/sampling_plan.json`
  - target stratified theo category

## 6) Lỗi thường gặp

- `ModuleNotFoundError`:
  - Chưa activate virtualenv hoặc chưa `pip install -r requirements.txt`
- Crawl lỗi `Expecting value...`:
  - Lazada trả HTML thay vì JSON (cookie/rate-limit)
  - Thử chạy lại sau, hoặc dùng `--continue-on-failure`
- `clean` bị thiếu mẫu:
  - Do chưa crawl đủ category; xem `stratified_stats.total_deficit` trong output JSON
