
import hashlib
import shutil
from pathlib import Path


def calculate_checksum(file_path, chunk_size=1024 * 1024):
    """Calculate a SHA-256 checksum using bounded memory."""
    digest = hashlib.sha256()

    with Path(file_path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def store_bronze_file(source_path, bronze_root="data/bronze"):
    """Store a checksum-verified, versioned copy of a source file."""
    source_path = Path(source_path)
    bronze_root = Path(bronze_root)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    checksum = calculate_checksum(source_path)
    destination_dir = bronze_root / source_path.stem / checksum
    destination_file = destination_dir / source_path.name

    destination_dir.mkdir(parents=True, exist_ok=True)

    if destination_file.exists():
        existing_checksum = calculate_checksum(destination_file)

        if existing_checksum == checksum:
            return {
                "status": "EXISTS",
                "path": str(destination_file),
                "checksum": checksum,
            }

        raise RuntimeError(
            "Existing Bronze file failed checksum verification: "
            f"{destination_file}"
        )

    temporary_file = destination_dir / f".{source_path.name}.tmp"

    try:
        shutil.copyfile(source_path, temporary_file)

        if calculate_checksum(temporary_file) != checksum:
            raise IOError("Checksum mismatch after copying to Bronze.")

        temporary_file.replace(destination_file)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    return {
        "status": "STORED",
        "path": str(destination_file),
        "checksum": checksum,
    }
