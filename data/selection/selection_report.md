# Báo cáo Bước 1 — Selection (KDD)

## Mục đích

Selection xác định **cái gì sẽ được khai thác** trước khi thu thập và xử lý:
- Phạm vi bài toán (4 lớp phân loại sản phẩm e-commerce)
- Biến cần thu thập từ API/crawl
- Cách lấy mẫu 17.000 sản phẩm (stratified 24 danh mục)
- Phạm vi nền tảng: Lazada, Shopee, Tiki
- Tiêu chí chất lượng bản ghi

Bước này **không crawl**, **không clean**, **không gán nhãn**.

## Đặc tả bài toán

- Dự án: ecommerce-product-classification
- Bài toán: multi_class_classification — 4 lớp
- Nền tảng: Lazada, Shopee, Tiki (ecommerce APIs/crawl snapshots (Lazada, Shopee, Tiki))
- Mục tiêu: 17,000 sản phẩm, stratified 24 danh mục
- Nhãn: Hot Trend, Best Seller, Best Deal, Normal

## Kết quả validate config

- Trạng thái: PASS

## Output sinh ra

- `problem_spec.json` — đặc tả bài toán
- `feature_selection.json` — biến thu thập + map nhãn
- `sampling_plan.json` — kế hoạch crawl theo danh mục và nền tảng
- `selection_report.md` — báo cáo tóm tắt (file này)

## Bước tiếp theo

Sau khi Selection PASS → chạy **Bước 2 (Preprocessing)**:
1. Collection: crawl theo `sampling_plan.json`
2. Clean: normalize, missing, outlier, dedup → file clean theo cấu hình
