@'
import os
import sys

from google.cloud import bigquery
from google.cloud import storage

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
BUCKET_NAME = os.environ["GCS_BUCKET"]
DATASET_ID = os.environ["BQ_DATASET"]

EXPECTED_RAW_FILES = 9

REQUIRED_TABLES = {
    "customers",
    "geolocation",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers",
    "category_translation",
    "silver_orders",
    "silver_order_items",
    "gold_order_metrics",
    "gold_daily_sales",
    "gold_seller_performance",
}


def main():
    print("Starting cloud resource validation...")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")

    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.get_bucket(BUCKET_NAME)

    raw_blobs = list(
        storage_client.list_blobs(
            bucket,
            prefix="raw/",
        )
    )
    raw_csvs = [
        blob.name
        for blob in raw_blobs
        if blob.name.lower().endswith(".csv")
    ]

    print(f"Raw CSV files found: {len(raw_csvs)}")

    if len(raw_csvs) != EXPECTED_RAW_FILES:
        raise RuntimeError(
            f"Expected {EXPECTED_RAW_FILES} raw CSV files; "
            f"found {len(raw_csvs)}."
        )

    bq_client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"

    actual_tables = {
        table.table_id
        for table in bq_client.list_tables(dataset_ref)
    }

    missing_tables = REQUIRED_TABLES - actual_tables

    print(f"BigQuery tables found: {len(actual_tables)}")

    if missing_tables:
        raise RuntimeError(
            "Missing required tables: "
            + ", ".join(sorted(missing_tables))
        )

    print("PASS: Cloud Storage and BigQuery validation succeeded.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
'@ | Set-Content -Encoding utf8 .\src\cloud\validate_cloud.py