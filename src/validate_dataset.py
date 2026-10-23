
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")

EXPECTED_FILES = {
    "olist_customers_dataset.csv": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "olist_orders_dataset.csv": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
    ],
    "olist_order_items_dataset.csv": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
        "review_score",
    ],
    "olist_products_dataset.csv": [
        "product_id",
        "product_category_name",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id",
        "seller_city",
        "seller_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
}


def validate_dataset():
    errors = []

    for filename, required_columns in EXPECTED_FILES.items():
        path = DATA_DIR / filename

        if not path.exists():
            errors.append(f"MISSING FILE: {filename}")
            continue

        try:
            # Read only the header first.
            columns = pd.read_csv(path, nrows=0).columns.tolist()

            missing_columns = set(required_columns) - set(columns)

            if missing_columns:
                errors.append(
                    f"{filename}: missing columns "
                    f"{sorted(missing_columns)}"
                )
                continue

            # Read the full CSV to verify it is parseable.
            df = pd.read_csv(path, low_memory=False)

            print(
                f"PASS | {filename} | "
                f"rows={len(df):,} | columns={len(df.columns)}"
            )

        except Exception as exc:
            errors.append(f"INVALID CSV: {filename}: {exc}")

    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"ERROR | {error}")
        raise SystemExit(1)

    print("\nAll nine CSV files passed the initial validation.")


if __name__ == "__main__":
    validate_dataset()
