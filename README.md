
# Olist E-Commerce Data Engineering Pipeline

A cloud-based data engineering portfolio project built with Python, SQL, Google BigQuery, Google Cloud Storage, Docker, and Google Cloud Run Jobs. This project processes Brazilian e-commerce data into structured analytical tables for order, sales, and seller performance analysis.

## Project Overview

The goal of this project is to build a data pipeline that validates source data, transforms raw records into clean analytical datasets, and produces business-level metrics in BigQuery.

### Architecture

![Olist E-Commerce Data Engineering Pipeline Architecture](https://i.ibb.co/yC2f6wP/Olist-E-Commerce-Data-Pipeline-Architecture.png)

*End-to-end data flow using Google Cloud Storage, BigQuery Bronze/Silver/Gold layers, Cloud Run ETL and validation jobs, and analytics consumers.*

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Ingestion, validation, and ETL execution |
| SQL | Data transformations and analytical queries |
| Google BigQuery | Cloud data warehouse |
| Google Cloud Storage | Raw CSV storage |
| Google Cloud Run Jobs | Containerized ETL execution |
| Docker | Containerization |
| pytest | Automated testing |

## Dataset

This project uses the Brazilian E-Commerce Public Dataset by Olist, which contains information about orders, customers, sellers, products, payments, reviews, and geolocation.

The source CSV files are stored in Google Cloud Storage and loaded into BigQuery for processing.

## Pipeline Layers

### 1. Raw Data and Ingestion

The ingestion components support loading CSV datasets and tracking ingestion metadata.

Raw BigQuery tables include:

- `customers`
- `geolocation`
- `orders`
- `order_items`
- `order_payments`
- `order_reviews`
- `products`
- `sellers`
- `category_translation`

### 2. Silver Layer — Data Cleaning

The Silver layer standardizes source records and identifies data quality issues.

**`silver_orders`**

- Trims order and customer identifiers.
- Normalizes order statuses.
- Flags missing order IDs, customer IDs, statuses, and purchase timestamps.

**`silver_order_items`**

- Normalizes order, product, and seller identifiers.
- Safely converts item IDs, prices, freight values, and shipping timestamps.
- Flags missing identifiers and invalid price or freight values.

Both tables contain a `data_quality_status` field to identify valid and invalid records.

### 3. Gold Layer — Analytics

The Gold layer provides business-level metrics for downstream analysis.

| Table | Description |
|---|---|
| `gold_order_metrics` | Order-level item counts, merchandise value, and freight value |
| `gold_daily_sales` | Daily order counts, delivered orders, item counts, and sales totals |
| `gold_seller_performance` | Seller-level order counts, items sold, merchandise value, and freight value |

## Google Cloud Deployment

The ETL workflow runs as a Google Cloud Run Job and executes five BigQuery transformations:

1. `silver_orders`
2. `silver_order_items`
3. `gold_order_metrics`
4. `gold_daily_sales`
5. `gold_seller_performance`

After executing the transformations, the runner checks expected table row counts and verifies that the Silver tables contain no records marked invalid.

A separate Cloud Run Job, `olist-cloud-validator`, checks expected cloud resources and dataset objects.

### Cloud Configuration

| Resource | Configuration |
|---|---|
| BigQuery dataset | `olist_analytics` |
| BigQuery location | `asia-south1` |
| Cloud Storage bucket | `olist-pipeline-e8e9a808-data` |
| ETL Cloud Run Job | `olist-etl` |
| Validation Cloud Run Job | `olist-cloud-validator` |

## Verified Execution Results

The following row counts were observed during a successful ETL execution.

| BigQuery table | Rows |
|---|---:|
| `silver_orders` | 99,441 |
| `silver_order_items` | 112,650 |
| `gold_order_metrics` | 99,441 |
| `gold_daily_sales` | 634 |
| `gold_seller_performance` | 3,095 |

The ETL execution logs showed all five transformations completing and the expected row counts matching.

These counts reflect the development dataset and are not guaranteed for future runs if the source data or transformation logic changes.

## Project Evidence

The following screenshots document the Google Cloud resources and pipeline execution.




## Project Evidence

### 1. BigQuery Dataset and Tables

![BigQuery dataset and tables](https://i.ibb.co/Lz5CXNH4/Screenshot-2026-10-23-192147.png)

### 2. BigQuery SQL Query Development

![BigQuery SQL query development](https://i.ibb.co/C31FbtNQ/Screenshot-2026-10-23-192227.png)

### 3. Google Cloud Shell — Job Configuration

![Google Cloud Run job configuration](https://i.ibb.co/DP4Z8pYK/Screenshot-2026-10-23-192647.png)

### 4. Google Cloud Shell — Successful ETL Execution

![Successful ETL execution logs](https://i.ibb.co/2x55mth/Screenshot-2026-10-23-192746.png)

### 5. Google Cloud Storage — Raw Datasets

![Google Cloud Storage raw datasets](https://i.ibb.co/DggTsQMw/Screenshot-2026-10-23-192902.png)


> If an embedded image does not display, use its screenshot link above. The embedded ImgBB URLs should be checked against the direct-image URLs supplied by ImgBB.

## Repository Structure

```text
olist-project/
├── src/
│   ├── cloud/
│   │   ├── run_etl.py
│   │   └── validate_cloud.py
│   ├── gold/
│   ├── ingestion/
│   ├── quality/
│   ├── transform/
│   └── validate_dataset.py
├── tests/
│   ├── gold/
│   ├── ingestion/
│   └── transform/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Testing and Data Quality

The repository contains pytest tests covering ingestion, metadata tracking, Silver transformations, Gold analytics, and data quality validation.

Additional BigQuery checks were executed during development to check duplicate keys, invalid Silver records, and negative analytical metrics.

## Current Limitations

- Raw CSV ingestion is not yet fully automated from source to warehouse.
- A recurring schedule for ETL execution has not been configured.
- Pipeline orchestration, retry policies, and alerting can be improved.
- A business intelligence dashboard can be added for reporting and visualization.

## Future Improvements

- Automate raw data ingestion.
- Schedule recurring ETL jobs.
- Add orchestration, monitoring, and failure alerts.
- Build dashboards for business metrics.
- Expand automated data quality checks and reporting.

## Data Source

Brazilian E-Commerce Public Dataset by Olist, available through Kaggle.

Review the original dataset's license and terms before redistributing source data.

## Author

Siva Sankar Sahu.
