"""
Simple utility to back up the biometric SQLite database.

Usage (from project root, with venv activated if you use one):

    python backup_db.py

This will create a timestamped copy of the database under the "backups" folder.
"""

import datetime
import os
import shutil

from config import BASE_DIR, DATABASE
from utils.logger import get_logger


logger = get_logger(__name__)


def create_backup() -> str | None:
    """Create a timestamped backup of the DATABASE file. Returns path or None on failure."""
    db_path = DATABASE
    if not os.path.isabs(db_path):
        db_path = os.path.join(BASE_DIR, db_path)

    if not os.path.exists(db_path):
        msg = f"Database file not found at {db_path}"
        logger.error(msg)
        print(msg)
        return None

    backups_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"biometric_{timestamp}.db"
    backup_path = os.path.join(backups_dir, backup_name)

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backup created at {backup_path}")
        print(f"Database backup created at: {backup_path}")
        return backup_path
    except Exception as exc:
        logger.error(f"Failed to create database backup: {exc}", exc_info=True)
        print(f"Failed to create database backup: {exc}")
        return None


if __name__ == "__main__":
    create_backup()

