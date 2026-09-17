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


LEGACY_MIGRATION_FLAG = "legacy_data_migrated"


def _migrate_legacy_data(conn: sqlite3.Connection):
    """
    Migrate records from legacy database files (sync_hide_list.db & ui/db.db)
    into the centralized database database/db.db. Runs only once per installation.
    """
    try:
        done = conn.execute(
            "SELECT value FROM dashboard_settings WHERE key = ?", (LEGACY_MIGRATION_FLAG,)
        ).fetchone()
        if done is not None:
            return
    except sqlite3.OperationalError:
        return

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
            old_conn = sqlite3.connect(legacy, timeout=2.0)
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

    try:
        conn.execute(
            "INSERT OR REPLACE INTO dashboard_settings (key, value) VALUES (?, ?)",
            (LEGACY_MIGRATION_FLAG, "1")
        )
    except sqlite3.OperationalError:
        pass


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite database connection to centralized database/db.db with WAL mode & 30s timeout."""
    if not db_path:
        db_path = get_central_db_path()

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deleted_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                tmp_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                title TEXT,
                artist TEXT,
                album TEXT,
                bitrate_kbps TEXT,
                sample_rate_hz TEXT,
                codec TEXT,
                size_bytes INTEGER,
                file_created_at TEXT,
                file_modified_at TEXT,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                filepath TEXT NOT NULL,
                track_order INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
                UNIQUE(playlist_id, filepath)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audio_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL NOT NULL,
                duration REAL NOT NULL,
                fingerprint TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fp_hash ON audio_fingerprints(fingerprint);
        """)
        _migrate_legacy_data(conn)
    return conn


# --- HIDE LIST METHODS ---

def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    """Insert a file into centralized hide list."""
    if not filename:
        filename = os.path.basename(filepath)
    conn = None
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
    finally:
        if conn:
            conn.close()


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    """Remove a file from centralized hide list."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files WHERE filepath = ?", (filepath,))
        logger.info(f"[Central DB] Removed from Hide List: {filepath}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error removing from hide list: {e}")
        return False
    finally:
        if conn:
            conn.close()


def clear_all_hidden(db_path: Optional[str] = None) -> bool:
    """Clear all hidden files from centralized database."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM hidden_files")
        logger.info("[Central DB] Cleared all entries from Hide List.")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error clearing hide list: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    """Retrieve set of hidden filepaths for fast filtering."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM hidden_files")
        return set(row["filepath"] for row in cursor.fetchall())
    except Exception as e:
        print(f"[Central DB] Error fetching hidden set: {e}", file=sys.stderr)
        return set()
    finally:
        if conn:
            conn.close()


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all hidden file records."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filepath, filename, hidden_at FROM hidden_files ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[Central DB] Error fetching hidden records: {e}", file=sys.stderr)
        return []
    finally:
        if conn:
            conn.close()


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
    conn = None
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
    finally:
        if conn:
            conn.close()


def get_synced_paths_set(device_serial: str, db_path: Optional[str] = None) -> Set[str]:
    """Retrieve set of local filepaths already synced to a device serial."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM synced_files WHERE device_serial = ?", (device_serial,))
        return set(row["filepath"] for row in cursor.fetchall())
    except Exception as e:
        print(f"[Central DB] Error fetching synced set: {e}", file=sys.stderr)
        return set()
    finally:
        if conn:
            conn.close()


def get_all_synced_records(device_serial: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all synced file records."""
    conn = None
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
    finally:
        if conn:
            conn.close()


def remove_synced_file(device_serial: str, filename: str, db_path: Optional[str] = None) -> bool:
    """Remove record from synced_files when a track is deleted from a target device."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            cursor = conn.execute(
                "DELETE FROM synced_files WHERE device_serial = ? AND (filename = ? OR filepath LIKE ?)",
                (device_serial, filename, f"%/{filename}")
            )
            return cursor.rowcount > 0
    except Exception as e:
        print(f"[Central DB] Error removing synced record: {e}", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()



# --- OVER-IP HOST STORAGE METHODS ---

def add_ip_host(ip_address: str, port: int = 5000, alias: str = "", db_path: Optional[str] = None) -> bool:
    """Add or update an IP host entry in centralized database."""
    ip_address = ip_address.strip()
    if not ip_address:
        return False
    conn = None
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
    finally:
        if conn:
            conn.close()


def remove_ip_host(ip_address: str, db_path: Optional[str] = None) -> bool:
    """Remove an IP host from centralized database."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM ip_hosts WHERE ip_address = ?", (ip_address.strip(),))
        print(f"[Central DB] Removed IP host: {ip_address}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[Central DB] Error removing IP host: {e}", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()


def get_stored_ip_hosts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of all stored IP hosts."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, ip_address, port, alias, last_seen, is_online FROM ip_hosts ORDER BY last_seen DESC")
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"[Central DB] Error fetching stored IP hosts: {e}", file=sys.stderr)
        return []
    finally:
        if conn:
            conn.close()


def update_ip_status(ip_address: str, is_online: bool, db_path: Optional[str] = None) -> bool:
    """Update online status for an IP host."""
    conn = None
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
    finally:
        if conn:
            conn.close()


# --- PLAYLIST MANAGEMENT METHODS ---

def create_playlist(name: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new playlist in database/db.db."""
    name = name.strip()
    if not name:
        return None
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            cursor = conn.execute(
                "INSERT INTO playlists (name) VALUES (?)",
                (name,)
            )
            playlist_id = cursor.lastrowid
        logger.info(f"[Central DB] Created playlist '{name}' (ID: {playlist_id})")
        return {"id": playlist_id, "name": name, "track_count": 0}
    except Exception as e:
        logger.error(f"[Central DB] Error creating playlist '{name}': {e}")
        return None
    finally:
        if conn:
            conn.close()


def delete_playlist(playlist_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a playlist and all its tracks from database/db.db."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        logger.info(f"[Central DB] Deleted playlist ID: {playlist_id}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error deleting playlist ID {playlist_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_playlists(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all playlists with track counts."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.created_at, COUNT(pt.id) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
            GROUP BY p.id, p.name, p.created_at
            ORDER BY p.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[Central DB] Error fetching playlists: {e}")
        return []
    finally:
        if conn:
            conn.close()


def add_track_to_playlist(playlist_id: int, filepath: str, db_path: Optional[str] = None) -> bool:
    """Add a track filepath to a playlist."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(track_order) FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            max_row = cursor.fetchone()
            next_order = (max_row[0] + 1) if (max_row and max_row[0] is not None) else 1

            conn.execute(
                """
                INSERT OR IGNORE INTO playlist_tracks (playlist_id, filepath, track_order)
                VALUES (?, ?, ?)
                """,
                (playlist_id, filepath, next_order)
            )
        logger.info(f"[Central DB] Added track '{filepath}' to playlist ID {playlist_id}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error adding track to playlist: {e}")
        return False
    finally:
        if conn:
            conn.close()


def remove_track_from_playlist(playlist_id: int, filepath: str, db_path: Optional[str] = None) -> bool:
    """Remove a track filepath from a playlist."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ? AND filepath = ?",
                (playlist_id, filepath)
            )
        logger.info(f"[Central DB] Removed track '{filepath}' from playlist ID {playlist_id}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error removing track from playlist: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_playlist_tracks(playlist_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all track filepaths in order for a playlist."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, playlist_id, filepath, track_order, added_at
            FROM playlist_tracks
            WHERE playlist_id = ?
            ORDER BY track_order ASC, id ASC
            """,
            (playlist_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[Central DB] Error fetching tracks for playlist ID {playlist_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()


# --- DELETED SONGS METHODS ---

def add_deleted_song(record: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Insert a deleted song record into the centralized database."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                """
                INSERT INTO deleted_songs (
                    filepath, tmp_path, filename, title, artist, album,
                    bitrate_kbps, sample_rate_hz, codec, size_bytes,
                    file_created_at, file_modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("filepath"),
                    record.get("tmp_path"),
                    record.get("filename") or os.path.basename(record.get("filepath") or ""),
                    record.get("title"),
                    record.get("artist"),
                    record.get("album"),
                    record.get("bitrate_kbps"),
                    record.get("sample_rate_hz"),
                    record.get("codec"),
                    record.get("size_bytes"),
                    record.get("file_created_at"),
                    record.get("file_modified_at")
                )
            )
        logger.info(f"[Central DB] Recorded deleted song: {record.get('filename') or record.get('filepath')}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error recording deleted song: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_deleted_songs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all deleted song records, newest first."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM deleted_songs ORDER BY id DESC"
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"[Central DB] Error fetching deleted songs: {e}")
        return []
    finally:
        if conn:
            conn.close()


def remove_deleted_song(record_id: int, db_path: Optional[str] = None) -> bool:
    """Remove a single deleted song record by id."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM deleted_songs WHERE id = ?", (record_id,))
        logger.info(f"[Central DB] Removed deleted song record ID {record_id}.")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error removing deleted song record {record_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def clear_deleted_songs(db_path: Optional[str] = None) -> bool:
    """Remove all deleted song records from the centralized database."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM deleted_songs")
        logger.info("[Central DB] Cleared deleted songs history.")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error clearing deleted songs history: {e}")
        return False
    finally:
        if conn:
            conn.close()


# --- AUDIO FINGERPRINT METHODS ---

def get_cached_fingerprint(
    filepath: str, file_size: int, file_mtime: float, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached fingerprint for a file if size and mtime match.
    """
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT duration, fingerprint, file_size, file_mtime FROM audio_fingerprints WHERE filepath = ?",
            (filepath,)
        )
        row = cursor.fetchone()
        if row:
            if row["file_size"] == file_size and abs(float(row["file_mtime"]) - float(file_mtime)) < 1.0:
                return {
                    "duration": float(row["duration"]),
                    "fingerprint": str(row["fingerprint"]),
                }
    except Exception as e:
        logger.error(f"[Central DB] Error retrieving cached fingerprint for {filepath}: {e}")
    finally:
        if conn:
            conn.close()
    return None


def save_cached_fingerprint(
    filepath: str,
    file_size: int,
    file_mtime: float,
    duration: float,
    fingerprint: str,
    db_path: Optional[str] = None,
) -> bool:
    """
    Store or update an audio fingerprint in the centralized database.
    """
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audio_fingerprints 
                (filepath, file_size, file_mtime, duration, fingerprint, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (filepath, file_size, file_mtime, duration, fingerprint),
            )
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error saving audio fingerprint for {filepath}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_all_cached_fingerprints_map(
    db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Load all stored audio fingerprints as a dictionary mapping filepath -> dict.
    Enables fast in-memory matching without repeated single-file SQL queries.
    """
    conn = None
    fp_map = {}
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT filepath, file_size, file_mtime, duration, fingerprint FROM audio_fingerprints")
        for row in cursor.fetchall():
            fp_map[row["filepath"]] = {
                "file_size": int(row["file_size"]),
                "file_mtime": float(row["file_mtime"]),
                "duration": float(row["duration"]),
                "fingerprint": str(row["fingerprint"]),
            }
    except Exception as e:
        logger.error(f"[Central DB] Error loading cached fingerprints map: {e}")
    finally:
        if conn:
            conn.close()
    return fp_map


