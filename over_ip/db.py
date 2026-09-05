"""
SQLite Database Manager for Over-IP Host Storage.
Manages ip_hosts table in sync_hide_list.db.
"""
import os
import sys
import sqlite3
from typing import List, Dict, Any, Optional

import hide_list_db


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite connection and initialize ip_hosts table."""
    if not db_path:
        db_path = hide_list_db.get_default_db_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    with conn:
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
    return conn


def add_ip_host(ip_address: str, port: int = 5000, alias: str = "", db_path: Optional[str] = None) -> bool:
    """Add or update an IP host entry in SQLite database."""
    ip_address = ip_address.strip()
    if not ip_address:
        return False

    try:
        conn = _get_connection(db_path)
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
        print(f"[SQLite DB] Saved IP host: {ip_address}:{port}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[SQLite DB] Error adding IP host {ip_address}: {e}", file=sys.stderr)
        return False


def remove_ip_host(ip_address: str, db_path: Optional[str] = None) -> bool:
    """Remove an IP host from SQLite database."""
    try:
        conn = _get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM ip_hosts WHERE ip_address = ?", (ip_address.strip(),))
        print(f"[SQLite DB] Removed IP host: {ip_address}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[SQLite DB] Error removing IP host: {e}", file=sys.stderr)
        return False


def get_stored_ip_hosts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all stored IP hosts from SQLite database."""
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, ip_address, port, alias, last_seen, is_online FROM ip_hosts ORDER BY last_seen DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[SQLite DB] Error fetching stored IP hosts: {e}", file=sys.stderr)
        return []


def update_ip_status(ip_address: str, is_online: bool, db_path: Optional[str] = None) -> bool:
    """Update online status and last_seen timestamp for an IP host."""
    try:
        conn = _get_connection(db_path)
        with conn:
            conn.execute(
                "UPDATE ip_hosts SET is_online = ?, last_seen = CURRENT_TIMESTAMP WHERE ip_address = ?",
                (1 if is_online else 0, ip_address.strip())
            )
        return True
    except Exception as e:
        print(f"[SQLite DB] Error updating IP status: {e}", file=sys.stderr)
        return False
