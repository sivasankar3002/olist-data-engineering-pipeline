
from pathlib import Path

import pandas as pd

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")


def find_bronze_csv(filename, bronze_dir=BRONZE_DIR):
    """Find the versioned Bronze copy of a CSV."""
    matches = list(
        (Path(bronze_dir) / Path(filename).stem).glob(
            f"*/{filename}"
        )
    )

    if not matches:
        raise FileNotFoundError(
            f"No Bronze version found for {filename}"
        )

    # Latest modification time is a fallback when multiple versions exist.
    return max(matches, key=lambda path: path.stat().st_mtime)


def read_bronze_csv(filename, bronze_dir=BRONZE_DIR):
    """Read a versioned Bronze CSV as strings."""
    path = find_bronze_csv(filename, bronze_dir)
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def transform_orders(bronze_dir=BRONZE_DIR, silver_dir=SILVER_DIR):
    """Clean order records and write a typed Silver Parquet file."""
    df = read_bronze_csv(
        "olist_orders_dataset.csv",
        bronze_dir,
    )

    required = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
    ]

    missing_columns = sorted(set(required) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Orders dataset missing columns: {missing_columns}"
        )

    df = df.drop_duplicates(subset=["order_id"], keep="last").copy()

    df["order_status"] = df["order_status"].str.strip().str.lower()

    timestamp_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for column in timestamp_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column].replace("", pd.NA),
                errors="coerce",
            )

    if df["order_id"].eq("").any():
        raise ValueError("Orders contains blank order IDs.")

    if df["customer_id"].eq("").any():
        raise ValueError("Orders contains blank customer IDs.")

    if df["order_status"].eq("").any():
        raise ValueError("Orders contains blank order statuses.")

    output_dir = Path(silver_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "orders.parquet"
    df.to_parquet(output_path, index=False)

    return {
        "table": "orders",
        "rows": len(df),
        "path": str(output_path),
    }


def transform_order_items(
    bronze_dir=BRONZE_DIR,
    silver_dir=SILVER_DIR,
):
    """Validate order items and convert numeric fields."""
    df = read_bronze_csv(
        "olist_order_items_dataset.csv",
        bronze_dir,
    )

    required = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
    ]

    missing_columns = sorted(set(required) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Order items dataset missing columns: {missing_columns}"
        )

    df = df.drop_duplicates(
        subset=["order_id", "order_item_id"],
        keep="last",
    ).copy()

    for column in ["price", "freight_value"]:
        df[column] = pd.to_numeric(
            df[column].replace("", pd.NA),
            errors="coerce",
        )

    if df[required[:4]].eq("").any().any():
        raise ValueError("Order items contain blank required identifiers.")

    if df[["price", "freight_value"]].isna().any().any():
        raise ValueError("Order items contain invalid numeric values.")

    if (df[["price", "freight_value"]] < 0).any().any():
        raise ValueError("Order items contain negative amounts.")

    df["order_item_id"] = pd.to_numeric(
        df["order_item_id"],
        errors="raise",
    ).astype("int64")

    output_dir = Path(silver_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "order_items.parquet"
    df.to_parquet(output_path, index=False)

    return {
        "table": "order_items",
        "rows": len(df),
        "path": str(output_path),
    }


def run_silver_transformations(
    bronze_dir=BRONZE_DIR,
    silver_dir=SILVER_DIR,
):
    """Run all currently implemented Silver transformations."""
    results = [
        transform_orders(bronze_dir, silver_dir),
        transform_order_items(bronze_dir, silver_dir),
    ]

    for result in results:
        print(
            f"PASS | {result['table']} | rows={result['rows']} "
            f"| output={result['path']}"
        )

    return results


if __name__ == "__main__":
    run_silver_transformations()
