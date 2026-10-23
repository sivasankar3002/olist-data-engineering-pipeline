
import pandas as pd

from src.gold.gold_analytics import (
    build_daily_sales,
    build_order_metrics,
    build_seller_performance,
)


def test_order_metrics_has_one_row_per_order(tmp_path):
    silver = tmp_path / "silver"
    silver.mkdir()

    pd.DataFrame({
        "order_id": ["o1", "o2"],
        "customer_id": ["c1", "c2"],
        "order_status": ["delivered", "shipped"],
        "order_purchase_timestamp": [
            pd.Timestamp("2018-01-01"),
            pd.Timestamp("2018-01-01"),
        ],
    }).to_parquet(silver / "orders.parquet", index=False)

    pd.DataFrame({
        "order_id": ["o1", "o1", "o2"],
        "order_item_id": [1, 2, 1],
        "product_id": ["p1", "p2", "p3"],
        "seller_id": ["s1", "s1", "s2"],
        "price": [10.0, 15.0, 20.0],
        "freight_value": [2.0, 3.0, 4.0],
    }).to_parquet(silver / "order_items.parquet", index=False)

    result = build_order_metrics(silver)

    assert len(result) == 2
    assert result["order_id"].is_unique
    assert result.loc[result["order_id"] == "o1", "item_count"].iloc[0] == 2


def test_daily_sales_totals_match_order_metrics():
    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "order_status": ["delivered", "shipped", "delivered"],
        "order_purchase_timestamp": [
            pd.Timestamp("2018-01-01"),
            pd.Timestamp("2018-01-01"),
            pd.Timestamp("2018-01-02"),
        ],
        "item_count": [2, 1, 3],
        "merchandise_value": [25.0, 20.0, 30.0],
        "freight_value": [5.0, 4.0, 6.0],
    })

    daily = build_daily_sales(orders)

    assert daily["total_orders"].sum() == 3
    assert daily["delivered_orders"].sum() == 2
    assert daily["merchandise_value"].sum() == 75.0
    assert daily["freight_value"].sum() == 15.0


def test_seller_performance_aggregates_correctly(tmp_path):
    silver = tmp_path / "silver"
    silver.mkdir()

    pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "order_item_id": [1, 1, 2],
        "product_id": ["p1", "p2", "p3"],
        "seller_id": ["s1", "s1", "s2"],
        "price": [10.0, 20.0, 30.0],
        "freight_value": [2.0, 3.0, 4.0],
    }).to_parquet(silver / "order_items.parquet", index=False)

    result = build_seller_performance(silver)
    seller_one = result[result["seller_id"] == "s1"].iloc[0]

    assert seller_one["unique_orders"] == 2
    assert seller_one["items_sold"] == 2
    assert seller_one["merchandise_value"] == 30.0
    assert seller_one["freight_value"] == 5.0
