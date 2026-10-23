
from pathlib import Path
import sqlite3

DEFAULT_DB_PATH = Path("data/metadata/ingestion.db")


def initialize_metadata_store(db_path=DEFAULT_DB_PATH):
    """Create the ingestion metadata database and table."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                checksum TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('STARTED', 'SUCCESS', 'FAILED')),
                row_count INTEGER,
                started_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                ),
                completed_at TEXT,
                error_message TEXT,
                UNIQUE (source_file, checksum)
            )
        """)


def get_connection(db_path=DEFAULT_DB_PATH):
    """Open the existing metadata database."""
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(
            f"Metadata database not found: {db_path}"
        )

    return sqlite3.connect(db_path)


def has_successful_run(source_file, checksum, db_path=DEFAULT_DB_PATH):
    """Check whether this exact file version succeeded previously."""
    with get_connection(db_path) as connection:
        result = connection.execute("""
            SELECT 1
            FROM ingestion_runs
            WHERE source_file = ?
              AND checksum = ?
              AND status = 'SUCCESS'
            LIMIT 1
        """, (source_file, checksum)).fetchone()

    return result is not None


def start_run(source_file, checksum, db_path=DEFAULT_DB_PATH):
    """Create a STARTED record and return its run ID."""
    with get_connection(db_path) as connection:
        cursor = connection.execute("""
            INSERT INTO ingestion_runs (
                source_file, checksum, status
            )
            VALUES (?, ?, 'STARTED')
            ON CONFLICT(source_file, checksum) DO UPDATE SET
                status = 'STARTED',
                row_count = NULL,
                started_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                completed_at = NULL,
                error_message = NULL
            WHERE ingestion_runs.status != 'SUCCESS'
        """, (source_file, checksum))

        row = connection.execute("""
            SELECT run_id, status
            FROM ingestion_runs
            WHERE source_file = ? AND checksum = ?
        """, (source_file, checksum)).fetchone()

        if row is None:
            raise RuntimeError("Unable to create ingestion run.")

        run_id, status = row

        if status == "SUCCESS":
            return None

        return run_id


def finish_run(
    run_id,
    status,
    row_count=None,
    error_message=None,
    db_path=DEFAULT_DB_PATH,
):
    """Mark a run as SUCCESS or FAILED."""
    if status not in {"SUCCESS", "FAILED"}:
        raise ValueError("Final status must be SUCCESS or FAILED.")

    if status == "SUCCESS" and row_count is None:
        raise ValueError("row_count is required for successful runs.")

    with get_connection(db_path) as connection:
        cursor = connection.execute("""
            UPDATE ingestion_runs
            SET status = ?,
                row_count = ?,
                error_message = ?,
                completed_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE run_id = ? AND status = 'STARTED'
        """, (status, row_count, error_message, run_id))

        if cursor.rowcount != 1:
            raise ValueError(
                f"Run {run_id} does not exist or is not STARTED."
            )


def get_run_history(db_path=DEFAULT_DB_PATH):
    """Return ingestion history, newest run first."""
    with get_connection(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT *
            FROM ingestion_runs
            ORDER BY run_id DESC
        """).fetchall()

    return [dict(row) for row in rows]
