# Data Dictionary

## ProductRaw (sau crawl)

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| crawl_timestamp | datetime | Thời điểm thu thập (realtime) |
| platform | enum | Luôn `Lazada` |
| category_name | string | Danh mục tìm kiếm |
| id | string | ID sản phẩm |
| shop_id | string? | ID shop |
| name | string | Tên SP |
| price | float | Giá hiện tại (VND) |
| original_price | float? | Giá gốc |
| discount_rate | float? | % giảm |
| rating_average | float? | 0–5 |
| review_count | int? | Số đánh giá |
| quantity_sold_value | int? | Đã bán (số) |
| quantity_sold_text | string? | Đã bán (text API) |
| brand | string? | Thương hiệu |
| location | string? | Khu vực shop |
| url | string | Link sản phẩm |

## ProductClean (10k sau preprocessing)

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| id | string | PK |
| crawl_date | datetime | Ngày crawl |
| category | string | Danh mục |
| product_name | string | Tên |
| current_price | float | Giá > 0 |
| original_price | float | Giá gốc |
| discount_rate | float | 0–95 |
| rating_average | float | 1–5 |
| num_reviews | int | ≥ 0 |
| quantity_sold | int | ≥ 0 |
| brand | string | Mặc định Unknown |
| seller_location | string | Mặc định Unknown |
| product_url | string | URL Lazada |

## ProductFeatures (+ engineered)

Các score chính: `popularity_score`, `engagement_score`, `trend_momentum`, `value_score`, `deal_quality_score`

Categorical: `popularity_category`, `price_segment`, `quality_tier`, `discount_intensity`, `product_age`

## ProductLabeled (+ target)

| Cột | Giá trị |
|-----|---------|
| label | Hot Trend \| Best Seller \| Best Deal \| Normal |
| label_source | rule_seed \| model \| rule_full |
| label_encoded | 0=Best Deal, 1=Best Seller, 2=Hot Trend, 3=Normal |

## File output

| Giai đoạn | File | Thư mục |
|-----------|------|---------|
| Raw gộp | lazada_raw_merged.json | data/raw/ |
| Clean 10k | lazada_10k_clean.json | data/clean/ |
| Features | lazada_10k_features.json | data/features/ |
| Labeled | lazada_10k_labeled.json | data/labeled/ |
| Train/Test | train.json, test.json | data/model_ready/ |
| Model | rf_classifier.pkl | models/ |
