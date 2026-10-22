#!/usr/bin/env python3
"""Back up the BAS Bot SQLite database, keeping the most recent N copies.

Usage:
    python3 scripts/backup_db.py
    python3 scripts/backup_db.py --keep 30

Meant to be run on a schedule (cron on Linux/macOS, Task Scheduler on
Windows) -- see the README for a sample crontab line. Uses SQLite's own
backup API rather than a plain file copy, so it's safe to run even while
the bot is writing to the database.
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config  # noqa: E402


def backup_database(keep: int) -> Path:
    db_path = Path(config.DATABASE_PATH)
    if not db_path.exists():
        raise SystemExit(f"No database found at {db_path} -- run the bot at least once first.")

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-{timestamp}.db"

    # Use SQLite's backup API (not shutil.copy) so this is safe to run
    # while the bot process has the database open.
    source = sqlite3.connect(str(db_path))
    dest = sqlite3.connect(str(backup_path))
    with dest:
        source.backup(dest)
    source.close()
    dest.close()

    _prune_old_backups(backup_dir, db_path.stem, keep)
    return backup_path


def _prune_old_backups(backup_dir: Path, stem: str, keep: int) -> None:
    backups = sorted(backup_dir.glob(f"{stem}-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=14, help="Number of backups to retain (default: 14)")
    args = parser.parse_args()

    path = backup_database(args.keep)
    print(f"Backed up database to {path}")


if __name__ == "__main__":
    main()
