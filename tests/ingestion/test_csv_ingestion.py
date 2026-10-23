
import sqlite3

from src.ingestion.csv_ingestion import (
    calculate_checksum,
    ingest_csv,
)


def test_checksum_changes_when_file_changes(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id,value\n1,A\n", encoding="utf-8")
    first_checksum = calculate_checksum(file_path)

    file_path.write_text("id,value\n1,B\n", encoding="utf-8")
    second_checksum = calculate_checksum(file_path)

    assert first_checksum != second_checksum


def test_ingestion_records_row_count(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id,value\n1,A\n2,B\n", encoding="utf-8")
    db_path = tmp_path / "metadata.db"
    bronze_root = tmp_path / "bronze"

    result = ingest_csv(file_path, db_path, bronze_root)

    assert result["status"] == "SUCCESS"
    assert result["rows"] == 2
    assert result["bronze_status"] == "STORED"

    with sqlite3.connect(db_path) as connection:
        row = connection.execute("""
            SELECT status, row_count
            FROM ingestion_runs
            WHERE source_file = ?
        """, ("sample.csv",)).fetchone()

    assert row == ("SUCCESS", 2)


def test_unchanged_file_is_skipped(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id\n1\n", encoding="utf-8")
    db_path = tmp_path / "metadata.db"
    bronze_root = tmp_path / "bronze"

    first = ingest_csv(file_path, db_path, bronze_root)
    second = ingest_csv(file_path, db_path, bronze_root)

    assert first["status"] == "SUCCESS"
    assert second["status"] == "SKIPPED"


def test_changed_file_is_ingested_again(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id\n1\n", encoding="utf-8")
    db_path = tmp_path / "metadata.db"
    bronze_root = tmp_path / "bronze"

    first = ingest_csv(file_path, db_path, bronze_root)

    file_path.write_text("id\n1\n2\n", encoding="utf-8")
    second = ingest_csv(file_path, db_path, bronze_root)

    assert first["status"] == "SUCCESS"
    assert second["status"] == "SUCCESS"
    assert second["rows"] == 2
    assert first["bronze_path"] != second["bronze_path"]


def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "missing.csv"

    try:
        ingest_csv(
            missing_file,
            tmp_path / "metadata.db",
            tmp_path / "bronze",
        )
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")
