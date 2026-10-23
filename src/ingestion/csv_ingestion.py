
import hashlib
from pathlib import Path

import pandas as pd

from src.ingestion.bronze_store import store_bronze_file
from src.ingestion.metadata_store import (
    DEFAULT_DB_PATH,
    finish_run,
    has_successful_run,
    initialize_metadata_store,
    start_run,
)

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")
CHUNK_SIZE = 50_000


def calculate_checksum(file_path, chunk_size=1024 * 1024):
    """Calculate a SHA-256 checksum using bounded memory."""
    digest = hashlib.sha256()

    with Path(file_path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def ingest_csv(file_path, db_path=None, bronze_root=BRONZE_DIR):
    """
    Read a CSV, store a verified Bronze copy, and track its status.

    Previously successful runs are reconciled with Bronze storage:
    if the corresponding copy is missing, it is recreated.
    """
    file_path = Path(file_path)
    bronze_root = Path(bronze_root)
    database_path = Path(db_path) if db_path else DEFAULT_DB_PATH

    if not file_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    initialize_metadata_store(database_path)

    source_file = file_path.name
    checksum = calculate_checksum(file_path)

    # Recover older successful runs that predate Bronze integration.
    if has_successful_run(source_file, checksum, database_path):
        bronze_result = store_bronze_file(
            file_path,
            bronze_root=bronze_root,
        )

        return {
            "file": source_file,
            "status": (
                "RECOVERED"
                if bronze_result["status"] == "STORED"
                else "SKIPPED"
            ),
            "reason": (
                "Missing Bronze copy recovered"
                if bronze_result["status"] == "STORED"
                else "Successful run and verified Bronze copy already exist"
            ),
            "rows": None,
            "checksum": checksum,
            "bronze_path": bronze_result["path"],
            "bronze_status": bronze_result["status"],
        }

    run_id = start_run(source_file, checksum, database_path)

    if run_id is None:
        return {
            "file": source_file,
            "status": "SKIPPED",
            "reason": "Unchanged file already processed",
        }

    try:
        # Parse the CSV in chunks to limit memory usage.
        row_count = 0

        for chunk in pd.read_csv(
            file_path,
            dtype=str,
            keep_default_na=False,
            chunksize=CHUNK_SIZE,
        ):
            row_count += len(chunk)

        # Bronze must be stored and checksum-verified before SUCCESS.
        bronze_result = store_bronze_file(
            file_path,
            bronze_root=bronze_root,
        )

        finish_run(
            run_id,
            "SUCCESS",
            row_count=row_count,
            db_path=database_path,
        )

        return {
            "file": source_file,
            "status": "SUCCESS",
            "rows": row_count,
            "checksum": checksum,
            "bronze_path": bronze_result["path"],
            "bronze_status": bronze_result["status"],
        }

    except Exception as exc:
        finish_run(
            run_id,
            "FAILED",
            error_message=str(exc)[:1000],
            db_path=database_path,
        )
        raise


def ingest_all_csvs(
    raw_dir=RAW_DIR,
    db_path=None,
    bronze_root=BRONZE_DIR,
):
    """Ingest every CSV in the raw directory in sorted order."""
    raw_dir = Path(raw_dir)

    if not raw_dir.is_dir():
        raise NotADirectoryError(
            f"Raw data directory not found: {raw_dir}"
        )

    files = sorted(raw_dir.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}"
        )

    results = []

    for file_path in files:
        result = ingest_csv(
            file_path,
            db_path=db_path,
            bronze_root=bronze_root,
        )
        results.append(result)

        status = result["status"]

        if status in {"SUCCESS", "RECOVERED"}:
            print(
                f"PASS | {result['file']} | "
                f"status={status} | "
                f"bronze={result['bronze_status']}"
            )
        elif status == "SKIPPED":
            print(
                f"SKIP | {result['file']} | "
                f"{result['reason']}"
            )

    return results


if __name__ == "__main__":
    ingest_all_csvs()
