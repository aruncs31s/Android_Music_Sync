"""
SQLite Hide List Database Manager.

Stores files hidden by the user in sync/reverse-sync interfaces into sync_hide_list.db.
Persists choices across sessions and filters hidden files from sync scans.
"""
import os
import sys
import sqlite3
from typing import Set, List, Dict, Any, Optional

DEFAULT_DB_NAME = "sync_hide_list.db"


def get_default_db_path() -> str:
    """Get absolute path to sync_hide_list.db in project root."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DEFAULT_DB_NAME)


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite database connection and initialize table if missing."""
    if not db_path:
        db_path = get_default_db_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hidden_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    return conn


def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    """
    Insert a file into the SQLite hide list database.
    """
    if not filename:
        filename = os.path.basename(filepath)

    try:
        conn = _get_connection(db_path)
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO hidden_files (filepath, filename) VALUES (?, ?)",
                (filepath, filename)
            )
        print(f"[SQLite DB] Added to Hide List: {filename}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[SQLite DB] Error inserting into hide list: {e}", file=sys.stderr)
        return False


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    """
    Remove a file from the SQLite hide list database.
    """
    try:
        conn = _get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files WHERE filepath = ?", (filepath,))
        print(f"[SQLite DB] Removed from Hide List: {filepath}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[SQLite DB] Error deleting from hide list: {e}", file=sys.stderr)
        return False


def clear_all_hidden(db_path: Optional[str] = None) -> bool:
    """
    Clear all entries from the SQLite hide list database.
    """
    try:
        conn = _get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files")
        print("[SQLite DB] Cleared all entries from Hide List.", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[SQLite DB] Error clearing hide list: {e}", file=sys.stderr)
        return False


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    """
    Retrieve set of all hidden filepaths for O(1) filtering.
    """
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM hidden_files")
        rows = cursor.fetchall()
        return set(row["filepath"] for row in rows)
    except Exception as e:
        print(f"[SQLite DB] Error fetching hidden paths set: {e}", file=sys.stderr)
        return set()


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve list of all hidden file records from SQLite database.
    """
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filepath, filename, hidden_at FROM hidden_files ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[SQLite DB] Error fetching hidden records: {e}", file=sys.stderr)
        return []
