
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")


def load_csv(filename):
    """Load a CSV while preserving identifiers as strings."""
    return pd.read_csv(
        DATA_DIR / filename,
        dtype=str,
        keep_default_na=False,
    )


def find_duplicate_keys(df, key):
    """Return all rows with duplicate key values."""
    return df[df[key].duplicated(keep=False)]


def find_missing_values(df, columns):
    """Count blank values in required columns."""
    return {
        column: int(
            df[column].astype(str).str.strip().eq("").sum()
        )
        for column in columns
    }


def validate_foreign_key(child, child_key, parent, parent_key):
    """Return nonblank child keys missing from the parent."""
    child_values = set(child[child_key])
    parent_values = set(parent[parent_key])

    return sorted(
        value
        for value in child_values - parent_values
        if value.strip() != ""
    )


def run_quality_checks():
    customers = load_csv("olist_customers_dataset.csv")
    orders = load_csv("olist_orders_dataset.csv")
    items = load_csv("olist_order_items_dataset.csv")
    products = load_csv("olist_products_dataset.csv")
    sellers = load_csv("olist_sellers_dataset.csv")
    payments = load_csv("olist_order_payments_dataset.csv")
    reviews = load_csv("olist_order_reviews_dataset.csv")

    failed = False

    # 1. Primary key checks
    print("=== PRIMARY KEY CHECKS ===")

    primary_keys = [
        ("customers.customer_id", customers, "customer_id"),
        ("orders.order_id", orders, "order_id"),
        ("products.product_id", products, "product_id"),
        ("sellers.seller_id", sellers, "seller_id"),
    ]

    for name, df, key in primary_keys:
        duplicates = find_duplicate_keys(df, key)
        missing = find_missing_values(df, [key])[key]
        passed = duplicates.empty and missing == 0

        print(
            f"{'PASS' if passed else 'FAIL'} | {name} | "
            f"duplicate rows={len(duplicates)} | blanks={missing}"
        )

        if not passed:
            failed = True

    # 2. Required-value checks
    print("\n=== REQUIRED VALUE CHECKS ===")

    required_fields = [
        ("orders", orders, ["order_id", "customer_id"]),
        ("items", items, ["order_id", "product_id", "seller_id"]),
        ("payments", payments, ["order_id", "payment_value"]),
        ("reviews", reviews, ["review_id", "order_id"]),
    ]

    for name, df, columns in required_fields:
        missing = find_missing_values(df, columns)
        passed = sum(missing.values()) == 0

        print(
            f"{'PASS' if passed else 'FAIL'} | {name} | "
            f"blank counts={missing}"
        )

        if not passed:
            failed = True

    # 3. Referential integrity checks
    print("\n=== FOREIGN KEY CHECKS ===")

    relationships = [
        ("orders.customer_id", orders, "customer_id",
         customers, "customer_id"),
        ("items.order_id", items, "order_id",
         orders, "order_id"),
        ("items.product_id", items, "product_id",
         products, "product_id"),
        ("items.seller_id", items, "seller_id",
         sellers, "seller_id"),
        ("payments.order_id", payments, "order_id",
         orders, "order_id"),
        ("reviews.order_id", reviews, "order_id",
         orders, "order_id"),
    ]

    for name, child, child_key, parent, parent_key in relationships:
        invalid = validate_foreign_key(
            child, child_key, parent, parent_key
        )

        passed = len(invalid) == 0
        print(
            f"{'PASS' if passed else 'FAIL'} | {name} | "
            f"invalid references={len(invalid)}"
        )

        if invalid:
            print(f"  Examples: {invalid[:5]}")
            failed = True

    # 4. Business-value checks
    print("\n=== VALUE RANGE CHECKS ===")

    payment_values = pd.to_numeric(
        payments["payment_value"], errors="coerce"
    )
    invalid_payments = int(
        (payment_values.isna() | (payment_values < 0)).sum()
    )

    review_scores = pd.to_numeric(
        reviews["review_score"], errors="coerce"
    )
    invalid_reviews = int(
        (
            review_scores.isna()
            | ~review_scores.between(1, 5)
        ).sum()
    )

    for name, count in [
        ("payment values", invalid_payments),
        ("review scores outside 1-5", invalid_reviews),
    ]:
        print(f"{'PASS' if count == 0 else 'FAIL'} | {name}: {count}")

        if count:
            failed = True

    if failed:
        raise SystemExit(
            "\nQuality checks failed. Investigate the reported records."
        )

    print("\nAll configured data quality checks passed.")


if __name__ == "__main__":
    run_quality_checks()
