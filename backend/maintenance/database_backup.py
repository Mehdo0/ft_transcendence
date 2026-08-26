import argparse
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from core.database_config import DATABASE_PATH
from utils.env import read_non_empty_string, read_positive_int


BACKUP_DIRECTORY = Path(read_non_empty_string("BACKUP_DIRECTORY", "backups"))
BACKUP_FILE_PREFIX = read_non_empty_string("BACKUP_FILE_PREFIX", "game_data")
BACKUP_INTERVAL_SECONDS = read_positive_int("BACKUP_INTERVAL_SECONDS", 86400)
BACKUP_RETRY_SECONDS = read_positive_int("BACKUP_RETRY_SECONDS", 30)
BACKUP_RETENTION_COUNT = read_positive_int("BACKUP_RETENTION_COUNT", 14)


def validate_file_prefix(prefix: str) -> str:
    if Path(prefix).name != prefix:
        raise ValueError("BACKUP_FILE_PREFIX must be a file name")
    return prefix


def build_backup_path(directory: Path, prefix: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return directory / f"{prefix}-{timestamp}.db"


def copy_database(source_path: Path, destination_path: Path) -> None:
    source_uri = f"{source_path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source:
        with sqlite3.connect(destination_path) as destination:
            source.backup(destination)


def validate_database(database_path: Path) -> None:
    database_uri = f"{database_path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as database:
        result = database.execute("PRAGMA integrity_check").fetchone()
    if result != ("ok",):
        raise sqlite3.DatabaseError("Backup integrity check failed")


def create_backup(source_path: Path, directory: Path, prefix: str) -> Path:
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    directory.mkdir(parents=True, exist_ok=True)
    backup_path = build_backup_path(directory, prefix)
    temporary_path = backup_path.with_suffix(".tmp")
    temporary_path.unlink(missing_ok=True)

    try:
        copy_database(source_path, temporary_path)
        validate_database(temporary_path)
        temporary_path.replace(backup_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return backup_path


def prune_backups(directory: Path, prefix: str, retention_count: int) -> None:
    backups = sorted(
        directory.glob(f"{prefix}-*.db"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for backup_path in backups[retention_count:]:
        backup_path.unlink()


def run_backup() -> Path:
    prefix = validate_file_prefix(BACKUP_FILE_PREFIX)
    backup_path = create_backup(DATABASE_PATH, BACKUP_DIRECTORY, prefix)
    prune_backups(BACKUP_DIRECTORY, prefix, BACKUP_RETENTION_COUNT)
    return backup_path


def run_forever() -> None:
    while True:
        try:
            backup_path = run_backup()
            print(f"Database backup created: {backup_path.name}", flush=True)
            delay = BACKUP_INTERVAL_SECONDS
        except (OSError, sqlite3.Error) as error:
            print(f"Database backup failed: {error}", flush=True)
            delay = BACKUP_RETRY_SECONDS
        time.sleep(delay)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.once:
        backup_path = run_backup()
        print(f"Database backup created: {backup_path.name}")
        return
    run_forever()


if __name__ == "__main__":
    main()
