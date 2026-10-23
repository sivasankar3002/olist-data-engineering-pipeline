
import pandas as pd

from src.quality.data_quality import (
    find_duplicate_keys,
    find_missing_values,
    validate_foreign_key,
)


def test_duplicate_key_detection():
    df = pd.DataFrame({"id": ["A", "B", "B", "C"]})
    assert len(find_duplicate_keys(df, "id")) == 2


def test_missing_value_detection():
    df = pd.DataFrame({"id": ["A", "", "C"]})
    assert find_missing_values(df, ["id"])["id"] == 1


def test_foreign_key_detection():
    child = pd.DataFrame({"customer_id": ["A", "B", "C"]})
    parent = pd.DataFrame({"customer_id": ["A", "B"]})

    invalid = validate_foreign_key(
        child, "customer_id", parent, "customer_id"
    )

    assert invalid == ["C"]
