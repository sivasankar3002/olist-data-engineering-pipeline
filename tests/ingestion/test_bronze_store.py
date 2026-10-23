
from pathlib import Path

from src.ingestion.bronze_store import store_bronze_file


def test_bronze_copy_preserves_content(tmp_path):
    source = tmp_path / "raw" / "orders.csv"
    source.parent.mkdir()
    source.write_text("id\n1\n2\n", encoding="utf-8")

    result = store_bronze_file(source, tmp_path / "bronze")

    destination = Path(result["path"])

    assert result["status"] == "STORED"
    assert destination.read_text(encoding="utf-8") == "id\n1\n2\n"


def test_repeated_copy_is_idempotent(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    bronze = tmp_path / "bronze"

    first = store_bronze_file(source, bronze)
    second = store_bronze_file(source, bronze)

    assert first["status"] == "STORED"
    assert second["status"] == "EXISTS"
    assert first["path"] == second["path"]


def test_changed_file_gets_a_separate_version(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    bronze = tmp_path / "bronze"

    first = store_bronze_file(source, bronze)

    source.write_text("id\n1\n2\n", encoding="utf-8")
    second = store_bronze_file(source, bronze)

    assert first["path"] != second["path"]
    assert Path(first["path"]).read_text(encoding="utf-8") == "id\n1\n"
    assert Path(second["path"]).read_text(encoding="utf-8") == "id\n1\n2\n"


def test_missing_source_is_rejected(tmp_path):
    missing = tmp_path / "missing.csv"

    try:
        store_bronze_file(missing, tmp_path / "bronze")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")
