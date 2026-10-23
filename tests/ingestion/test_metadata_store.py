
import pytest

from src.ingestion.metadata_store import (
    finish_run,
    get_run_history,
    has_successful_run,
    initialize_metadata_store,
    start_run,
)


def setup_db(tmp_path):
    db_path = tmp_path / "metadata" / "ingestion.db"
    initialize_metadata_store(db_path)
    return db_path


def test_new_run_can_succeed(tmp_path):
    db_path = setup_db(tmp_path)

    run_id = start_run("orders.csv", "hash123", db_path)
    finish_run(run_id, "SUCCESS", row_count=100, db_path=db_path)

    assert has_successful_run("orders.csv", "hash123", db_path)
    history = get_run_history(db_path)
    assert history[0]["status"] == "SUCCESS"
    assert history[0]["row_count"] == 100


def test_failed_run_can_be_retried(tmp_path):
    db_path = setup_db(tmp_path)

    first_id = start_run("orders.csv", "hash123", db_path)
    finish_run(
        first_id, "FAILED", error_message="temporary error",
        db_path=db_path,
    )

    retry_id = start_run("orders.csv", "hash123", db_path)

    assert retry_id == first_id
    assert get_run_history(db_path)[0]["status"] == "STARTED"


def test_successful_version_is_not_started_again(tmp_path):
    db_path = setup_db(tmp_path)

    run_id = start_run("orders.csv", "hash123", db_path)
    finish_run(run_id, "SUCCESS", row_count=100, db_path=db_path)

    assert start_run("orders.csv", "hash123", db_path) is None


def test_changed_checksum_creates_new_run(tmp_path):
    db_path = setup_db(tmp_path)

    first_id = start_run("orders.csv", "hash123", db_path)
    finish_run(first_id, "SUCCESS", row_count=100, db_path=db_path)

    second_id = start_run("orders.csv", "hash456", db_path)

    assert second_id is not None
    assert second_id != first_id


def test_invalid_final_status_is_rejected(tmp_path):
    db_path = setup_db(tmp_path)
    run_id = start_run("orders.csv", "hash123", db_path)

    with pytest.raises(ValueError):
        finish_run(run_id, "STARTED", db_path=db_path)


def test_success_requires_row_count(tmp_path):
    db_path = setup_db(tmp_path)
    run_id = start_run("orders.csv", "hash123", db_path)

    with pytest.raises(ValueError):
        finish_run(run_id, "SUCCESS", db_path=db_path)
