# Bước 1 — Selection: Mục đích & Cách làm

## Selection là gì?

**Selection (Lựa chọn dữ liệu)** là bước KDD đầu tiên: quyết định **thu thập cái gì, bao nhiêu, vì mục đích gì** — trước khi crawl hay làm sạch.

| Selection **làm** | Selection **không làm** |
|-------------------|-------------------------|
| Chốt bài toán 4 lớp | Crawl Lazada |
| Chọn biến thu thập | Normalize / clean |
| Lập kế hoạch 10k stratified | Feature engineering |
| Validate config | Train model |

---

## Mục đích (tại sao cần Bước 1)

1. **Tránh thu thập dư thừa** — biết trước cần 10k, 16 danh mục, biến nào.
2. **Đảm bảo bài toán rõ ràng** — 4 nhãn, nguồn Lazada, snapshot realtime.
3. **Làm căn cứ báo cáo đề tài** — mục "Phạm vi nghiên cứu / Dữ liệu".
4. **Kiểm tra config sớm** — phát hiện lỗi (tổng danh mục ≠ 10k) trước khi crawl mất thời gian.

---

## Cần làm những gì (theo kế hoạch)

| # | Việc | Output |
|---|------|--------|
| 1 | Viết đặc tả bài toán | `data/selection/problem_spec.json` |
| 2 | Chọn biến thu thập + map nhãn | `data/selection/feature_selection.json` |
| 3 | Lập kế hoạch 16 danh mục × 625 SP | `data/selection/sampling_plan.json` |
| 4 | Validate config | PASS/FAIL trong `selection_report.md` |
| 5 | Báo cáo tóm tắt Selection | `data/selection/selection_report.md` |

---

## Cách chạy

```bash
cd shopee-product-classification
python -m src.selection.run
```

Hoặc qua pipeline:

```bash
python -m src.pipeline.run --step selection
```

---

## Map với 5 bước KDD

| KDD | Bước plan | Module |
|-----|-----------|--------|
| **1. Selection** | Bước 1 | `src/selection/` |
| 2. Preprocessing (Collection + Clean) | Bước 2 | `src/preprocessing/` |
| 3. Transformation | Bước 3 | `src/transformation/` |
| 4. Data Mining | Bước 4 | `src/mining/` |
| 5. Evaluation | Bước 5 | `src/evaluation/` |

---

## Nguồn cấu hình

- [`config/settings.yaml`](../config/settings.yaml) — 10k, 4 nhãn, ngưỡng
- [`config/categories.yaml`](../config/categories.yaml) — 16 danh mục
- [`src/schema/product.py`](../src/schema/product.py) — schema biến `ProductRaw`
