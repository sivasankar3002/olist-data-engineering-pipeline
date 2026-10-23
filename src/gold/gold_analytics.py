
from pathlib import Path

import pandas as pd

SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")


def build_order_metrics(silver_dir=SILVER_DIR):
    """Build one analytical row per order."""
    silver_dir = Path(silver_dir)

    orders = pd.read_parquet(silver_dir / "orders.parquet")
    items = pd.read_parquet(silver_dir / "order_items.parquet")

    item_metrics = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("order_item_id", "count"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )

    result = orders.merge(
        item_metrics,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    result["item_count"] = result["item_count"].fillna(0).astype("int64")
    result["merchandise_value"] = result["merchandise_value"].fillna(0.0)
    result["freight_value"] = result["freight_value"].fillna(0.0)

    return result


def build_daily_sales(order_metrics):
    """Aggregate order metrics by purchase date."""
    df = order_metrics.copy()
    df["purchase_date"] = pd.to_datetime(
        df["order_purchase_timestamp"],
        errors="coerce",
    ).dt.date

    df = df.dropna(subset=["purchase_date"])

    return (
        df.groupby("purchase_date", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            delivered_orders=(
                "order_status",
                lambda values: values.eq("delivered").sum(),
            ),
            item_count=("item_count", "sum"),
            merchandise_value=("merchandise_value", "sum"),
            freight_value=("freight_value", "sum"),
        )
        .sort_values("purchase_date")
        .reset_index(drop=True)
    )


def build_seller_performance(silver_dir=SILVER_DIR):
    """Aggregate sales and order activity per seller."""
    items = pd.read_parquet(
        Path(silver_dir) / "order_items.parquet"
    )

    return (
        items.groupby("seller_id", as_index=False)
        .agg(
            unique_orders=("order_id", "nunique"),
            items_sold=("order_item_id", "count"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
        .sort_values("merchandise_value", ascending=False)
        .reset_index(drop=True)
    )


def run_gold_analytics(
    silver_dir=SILVER_DIR,
    gold_dir=GOLD_DIR,
):
    """Build and save the initial Gold analytical tables."""
    gold_dir = Path(gold_dir)
    gold_dir.mkdir(parents=True, exist_ok=True)

    orders = build_order_metrics(silver_dir)
    daily_sales = build_daily_sales(orders)
    seller_performance = build_seller_performance(silver_dir)

    outputs = {
        "order_metrics": orders,
        "daily_sales": daily_sales,
        "seller_performance": seller_performance,
    }

    for name, dataframe in outputs.items():
        output_path = gold_dir / f"{name}.parquet"
        dataframe.to_parquet(output_path, index=False)
        print(
            f"PASS | {name} | rows={len(dataframe)} "
            f"| output={output_path}"
        )

    return outputs


if __name__ == "__main__":
    run_gold_analytics()
