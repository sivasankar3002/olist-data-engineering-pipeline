
import pandas as pd

from src.transform.silver_transform import (
    transform_orders,
    transform_order_items,
)


def test_orders_transformation(tmp_path):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    version = bronze / "olist_orders_dataset" / "version1"
    version.mkdir(parents=True)

    pd.DataFrame({
        "order_id": ["o1", "o2"],
        "customer_id": ["c1", "c2"],
        "order_status": ["DELIVERED", "shipped"],
        "order_purchase_timestamp": [
            "2017-01-01 10:00:00",
            "2017-01-02 11:00:00",
        ],
        "order_approved_at": ["", "2017-01-02 11:30:00"],
        "order_delivered_carrier_date": ["", ""],
        "order_delivered_customer_date": ["", ""],
        "order_estimated_delivery_date": [
            "2017-01-05 00:00:00",
            "2017-01-06 00:00:00",
        ],
    }).to_csv(version / "olist_orders_dataset.csv", index=False)

    result = transform_orders(bronze, silver)
    output = pd.read_parquet(result["path"])

    assert result["rows"] == 2
    assert output["order_status"].tolist() == ["delivered", "shipped"]
    assert pd.api.types.is_datetime64_any_dtype(
        output["order_purchase_timestamp"]
    )


def test_order_items_transformation(tmp_path):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    version = bronze / "olist_order_items_dataset" / "version1"
    version.mkdir(parents=True)

    pd.DataFrame({
        "order_id": ["o1", "o1"],
        "order_item_id": ["1", "2"],
        "product_id": ["p1", "p2"],
        "seller_id": ["s1", "s2"],
        "price": ["10.50", "20.00"],
        "freight_value": ["2.50", "3.00"],
    }).to_csv(version / "olist_order_items_dataset.csv", index=False)

    result = transform_order_items(bronze, silver)
    output = pd.read_parquet(result["path"])

    assert result["rows"] == 2
    assert output["order_item_id"].dtype == "int64"
    assert output["price"].tolist() == [10.5, 20.0]
