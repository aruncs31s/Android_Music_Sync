"""
Centralized SQLite Database Manager for Antigravity Music Manager.
Location: database/db.db
Shared by both UI (Flask Dashboard) and TUI (Terminal Curses UI & CLI).

Manages tables:
1. hidden_files (Hide list)
2. synced_files (Synced tracks history by device serial)
3. ip_hosts (Over-IP peer host storage & status)
4. dashboard_settings (UI & application settings)
"""
import os
import sys
import sqlite3
from typing import List, Dict, Any, Optional, Set
from utils import get_logger

logger = get_logger()

DEFAULT_DB_REL_PATH = os.path.join("database", "db.db")


def get_central_db_path() -> str:
    """Get absolute path to database/db.db in project root."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "database", "db.db")


def _migrate_legacy_data(conn: sqlite3.Connection):
    """
    Migrate records from legacy database files (sync_hide_list.db & ui/db.db)
    into the centralized database database/db.db.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    legacy_paths = [
        os.path.join(base_dir, "sync_hide_list.db"),
        os.path.join(base_dir, "ui", "db.db")
    ]

    central_db_path = get_central_db_path()

    for legacy in legacy_paths:
        if not os.path.exists(legacy) or os.path.abspath(legacy) == os.path.abspath(central_db_path):
            continue

        try:
            old_conn = sqlite3.connect(legacy)
            old_conn.row_factory = sqlite3.Row
            cursor = old_conn.cursor()

            # 1. Migrate hidden_files
            try:
                cursor.execute("SELECT filepath, filename FROM hidden_files")
                for r in cursor.fetchall():
                    conn.execute(
                        "INSERT OR IGNORE INTO hidden_files (filepath, filename) VALUES (?, ?)",
                        (r["filepath"], r["filename"])
                    )
            except sqlite3.OperationalError:
                pass

            # 2. Migrate synced_files
            try:
                cursor.execute("SELECT filepath, filename, device_serial, remote_dir FROM synced_files")
                for r in cursor.fetchall():
                    conn.execute(
                        "INSERT OR IGNORE INTO synced_files (filepath, filename, device_serial, remote_dir) VALUES (?, ?, ?, ?)",
                        (r["filepath"], r["filename"], r["device_serial"], r["remote_dir"])
                    )
            except sqlite3.OperationalError:
                pass

            # 3. Migrate ip_hosts
            try:
                cursor.execute("SELECT ip_address, port, alias FROM ip_hosts")
                for r in cursor.fetchall():
                    conn.execute(
                        "INSERT OR IGNORE INTO ip_hosts (ip_address, port, alias) VALUES (?, ?, ?)",
                        (r["ip_address"], r["port"], r["alias"])
                    )
            except sqlite3.OperationalError:
                pass

            old_conn.close()
        except Exception as e:
            print(f"[Central DB] Migration note from {legacy}: {e}", file=sys.stderr)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite database connection to centralized database/db.db."""
    if not db_path:
        db_path = get_central_db_path()

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS synced_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                filename TEXT NOT NULL,
                device_serial TEXT NOT NULL,
                remote_dir TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filepath, device_serial)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ip_hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                port INTEGER DEFAULT 5000,
                alias TEXT DEFAULT '',
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_online INTEGER DEFAULT 0
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        _migrate_legacy_data(conn)
    return conn


# --- HIDE LIST METHODS ---

def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    """Insert a file into centralized hide list."""
    if not filename:
        filename = os.path.basename(filepath)
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO hidden_files (filepath, filename) VALUES (?, ?)",
                (filepath, filename)
            )
        logger.info(f"[Central DB] Added to Hide List: {filename}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error adding to hide list: {e}")
        return False


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    """Remove a file from centralized hide list."""
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files WHERE filepath = ?", (filepath,))
        logger.info(f"[Central DB] Removed from Hide List: {filepath}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error removing from hide list: {e}")
        return False


def clear_all_hidden(db_path: Optional[str] = None) -> bool:
    """Clear all hidden files from centralized database."""
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files")
        logger.info("[Central DB] Cleared all entries from Hide List.")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error clearing hide list: {e}")
        return False


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    """Retrieve set of hidden filepaths for fast filtering."""
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM hidden_files")
        return set(row["filepath"] for row in cursor.fetchall())
    except Exception as e:
        print(f"[Central DB] Error fetching hidden set: {e}", file=sys.stderr)
        return set()


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all hidden file records."""
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filepath, filename, hidden_at FROM hidden_files ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[Central DB] Error fetching hidden records: {e}", file=sys.stderr)
        return []


# --- SYNCED TRACKS HISTORY METHODS ---

def add_synced_file(
    filepath: str,
    filename: str,
    device_serial: str,
    remote_dir: str = "",
    db_path: Optional[str] = None
) -> bool:
    """Record a synced file for a specific device serial in centralized database."""
    if not filename:
        filename = os.path.basename(filepath)
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO synced_files (filepath, filename, device_serial, remote_dir)
                VALUES (?, ?, ?, ?)
                """,
                (filepath, filename, device_serial, remote_dir)
            )
        print(f"[Central DB] Recorded synced track for [{device_serial}]: {filename}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Central DB] Error recording synced file: {e}", file=sys.stderr)
        return False


def get_synced_paths_set(device_serial: str, db_path: Optional[str] = None) -> Set[str]:
    """Retrieve set of local filepaths already synced to a device serial."""
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM synced_files WHERE device_serial = ?", (device_serial,))
        return set(row["filepath"] for row in cursor.fetchall())
    except Exception as e:
        print(f"[Central DB] Error fetching synced set: {e}", file=sys.stderr)
        return set()


def get_all_synced_records(device_serial: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all synced file records."""
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        if device_serial:
            cursor.execute(
                "SELECT id, filepath, filename, device_serial, remote_dir, synced_at FROM synced_files WHERE device_serial = ? ORDER BY id DESC",
                (device_serial,)
            )
        else:
            cursor.execute(
                "SELECT id, filepath, filename, device_serial, remote_dir, synced_at FROM synced_files ORDER BY id DESC"
            )
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[Central DB] Error fetching synced records: {e}", file=sys.stderr)
        return []


# --- OVER-IP HOST STORAGE METHODS ---

def add_ip_host(ip_address: str, port: int = 5000, alias: str = "", db_path: Optional[str] = None) -> bool:
    """Add or update an IP host entry in centralized database."""
    ip_address = ip_address.strip()
    if not ip_address:
        return False
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                """
                INSERT INTO ip_hosts (ip_address, port, alias, last_seen)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(ip_address) DO UPDATE SET
                    port = excluded.port,
                    alias = CASE WHEN excluded.alias != '' THEN excluded.alias ELSE ip_hosts.alias END,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (ip_address, port, alias)
            )
        print(f"[Central DB] Saved IP host: {ip_address}:{port}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Central DB] Error adding IP host {ip_address}: {e}", file=sys.stderr)
        return False


def remove_ip_host(ip_address: str, db_path: Optional[str] = None) -> bool:
    """Remove an IP host from centralized database."""
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM ip_hosts WHERE ip_address = ?", (ip_address.strip(),))
        print(f"[Central DB] Removed IP host: {ip_address}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Central DB] Error removing IP host: {e}", file=sys.stderr)
        return False


def get_stored_ip_hosts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all stored IP hosts."""
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, ip_address, port, alias, last_seen, is_online FROM ip_hosts ORDER BY last_seen DESC")
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[Central DB] Error fetching stored IP hosts: {e}", file=sys.stderr)
        return []


def update_ip_status(ip_address: str, is_online: bool, db_path: Optional[str] = None) -> bool:
    """Update online status for an IP host."""
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                "UPDATE ip_hosts SET is_online = ?, last_seen = CURRENT_TIMESTAMP WHERE ip_address = ?",
                (1 if is_online else 0, ip_address.strip())
            )
        return True
    except Exception as e:
        print(f"[Central DB] Error updating IP status: {e}", file=sys.stderr)
        return False
