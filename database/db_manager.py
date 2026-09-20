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
from device_providers import SongDeletable
from model import RestoredSongRecord, SongRecord, PlaylistRecord, PlaylistTrackRecord, TrackStatus
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
            logger.info(f"[Central DB] Migration note from {legacy}: {e}")

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
        # Ensure playlist_tracks has status and metadata columns for absent track support
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(playlist_tracks)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "status" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN status TEXT DEFAULT 'present'")
        if "original_path" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN original_path TEXT")
        if "readable_name" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN readable_name TEXT")
        if "title" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN title TEXT")
        if "artist" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN artist TEXT")
        if "album" not in existing_cols:
            conn.execute("ALTER TABLE playlist_tracks ADD COLUMN album TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_status ON playlist_tracks(playlist_id, status);")
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS local_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                title TEXT,
                artist TEXT,
                album TEXT,
                size INTEGER DEFAULT 0,
                size_formatted TEXT,
                mtime REAL DEFAULT 0,
                mtime_str TEXT,
                ctime REAL DEFAULT 0,
                ctime_str TEXT,
                duration_sec REAL DEFAULT 0,
                duration_formatted TEXT,
                bitrate_kbps TEXT,
                bitrate_val INTEGER DEFAULT 0,
                sample_rate_hz TEXT,
                channels TEXT,
                codec TEXT,
                searchable_text TEXT
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_local_songs_mtime ON local_songs(mtime DESC);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_local_songs_filepath ON local_songs(filepath);
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
        logger.error(f"[Central DB] Error fetching hidden set: {e}")
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
        logger.error(f"[Central DB] Error fetching hidden records: {e}")
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
        logger.info(f"[Central DB] Recorded synced track for [{device_serial}]: {filename}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error recording synced file: {e}")
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
        logger.error(f"[Central DB] Error fetching synced set: {e}")
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
        logger.error(f"[Central DB] Error fetching synced records: {e}")
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
        logger.error(f"[Central DB] Error removing synced record: {e}")
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
        logger.info(f"[Central DB] Saved IP host: {ip_address}:{port}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error adding IP host {ip_address}: {e}")
        return False
    finally:
        if conn:
            conn.close()


save_ip_host = add_ip_host


def remove_ip_host(ip_address: str, db_path: Optional[str] = None) -> bool:
    """Remove an IP host from centralized database."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM ip_hosts WHERE ip_address = ?", (ip_address.strip(),))
        logger.info(f"[Central DB] Removed IP host: {ip_address}")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error removing IP host: {e}")
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
        logger.error(f"[Central DB] Error fetching stored IP hosts: {e}")
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
        logger.error(f"[Central DB] Error updating IP status: {e}")
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
    """Get all playlists with track counts, present counts, and absent counts."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.created_at,
                   COUNT(pt.id) AS track_count,
                   COUNT(CASE WHEN pt.status = 'absent' THEN 1 END) AS absent_count,
                   COUNT(CASE WHEN pt.status != 'absent' OR pt.status IS NULL THEN pt.id END) AS present_count
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


def add_track_to_playlist(
    playlist_id: int,
    filepath: str,
    status: str = TrackStatus.PRESENT.value,
    original_path: Optional[str] = None,
    readable_name: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    db_path: Optional[str] = None
) -> bool:
    """Add a track to a playlist with status and metadata support."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(track_order) FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            max_row = cursor.fetchone()
            next_order = (max_row[0] + 1) if (max_row and max_row[0] is not None) else 1

            orig = original_path or filepath
            t_name = title or readable_name or os.path.basename(filepath)

            conn.execute(
                """
                INSERT INTO playlist_tracks (
                    playlist_id, filepath, original_path, readable_name,
                    title, artist, album, status, track_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(playlist_id, filepath) DO UPDATE SET
                    original_path = COALESCE(excluded.original_path, playlist_tracks.original_path),
                    readable_name = COALESCE(excluded.readable_name, playlist_tracks.readable_name),
                    title = COALESCE(excluded.title, playlist_tracks.title),
                    artist = COALESCE(excluded.artist, playlist_tracks.artist),
                    album = COALESCE(excluded.album, playlist_tracks.album),
                    status = excluded.status
                """,
                (playlist_id, filepath, orig, readable_name, t_name, artist, album, status, next_order)
            )
        logger.info(f"[Central DB] Added track '{filepath}' (status: {status}) to playlist ID {playlist_id}")
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


def resolve_playlist_track(
    playlist_id: int,
    original_path: str,
    resolved_filepath: str,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    track_id: Optional[int] = None,
    db_path: Optional[str] = None
) -> bool:
    """Permanently marks an absent playlist track as present and updates its local filepath."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            if track_id is not None and track_id > 0:
                conn.execute(
                    """
                    UPDATE playlist_tracks
                    SET filepath = ?, status = 'present',
                        title = COALESCE(?, title),
                        artist = COALESCE(?, artist),
                        album = COALESCE(?, album)
                    WHERE id = ? AND playlist_id = ?
                    """,
                    (resolved_filepath, title, artist, album, track_id, playlist_id)
                )
            else:
                conn.execute(
                    """
                    UPDATE playlist_tracks
                    SET filepath = ?, status = 'present',
                        title = COALESCE(?, title),
                        artist = COALESCE(?, artist),
                        album = COALESCE(?, album)
                    WHERE playlist_id = ? AND (original_path = ? OR filepath = ?)
                    """,
                    (resolved_filepath, title, artist, album, playlist_id, original_path, original_path)
                )
        logger.info(f"[Central DB] Resolved absent track in playlist {playlist_id} -> '{resolved_filepath}'")
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error resolving absent track: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_playlist_absent_tracks(playlist_id: Optional[int] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve absent tracks for a specific playlist, or all playlists if playlist_id is None."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        if playlist_id is not None:
            cursor.execute(
                """
                SELECT pt.id, pt.playlist_id, p.name as playlist_name,
                       pt.filepath, pt.original_path, pt.readable_name,
                       pt.title, pt.artist, pt.album, pt.status, pt.track_order, pt.added_at
                FROM playlist_tracks pt
                JOIN playlists p ON pt.playlist_id = p.id
                WHERE pt.playlist_id = ? AND pt.status = 'absent'
                ORDER BY pt.track_order ASC, pt.id ASC
                """,
                (playlist_id,)
            )
        else:
            cursor.execute(
                """
                SELECT pt.id, pt.playlist_id, p.name as playlist_name,
                       pt.filepath, pt.original_path, pt.readable_name,
                       pt.title, pt.artist, pt.album, pt.status, pt.track_order, pt.added_at
                FROM playlist_tracks pt
                JOIN playlists p ON pt.playlist_id = p.id
                WHERE pt.status = 'absent'
                ORDER BY p.name ASC, pt.track_order ASC, pt.id ASC
                """
            )
        rows = [dict(row) for row in cursor.fetchall()]
        for r in rows:
            orig = r.get("original_path") or r.get("filepath") or ""
            r["filename"] = os.path.basename(orig)
            if not r.get("readable_name"):
                r["readable_name"] = r.get("title") or r["filename"]
            if not r.get("original_path"):
                r["original_path"] = orig
        return rows
    except Exception as e:
        logger.error(f"[Central DB] Error fetching absent tracks: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_playlist_tracks(playlist_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all track filepaths and metadata in order for a playlist."""
    conn = None
    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, playlist_id, filepath, original_path, readable_name,
                   title, artist, album, status, track_order, added_at
            FROM playlist_tracks
            WHERE playlist_id = ?
            ORDER BY track_order ASC, id ASC
            """,
            (playlist_id,)
        )
        tracks = []
        for row in cursor.fetchall():
            d = dict(row)
            if not d.get("status"):
                d["status"] = "present"
            tracks.append(d)
        return tracks
    except Exception as e:
        logger.error(f"[Central DB] Error fetching tracks for playlist ID {playlist_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()


# --- DELETED SONGS METHODS ---

def add_deleted_song(record: SongRecord, db_path: Optional[str] = None) -> bool:
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


# --- AUDIO FINGERlogger.info METHODS ---

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


# --- LOCAL SONGS STORAGE & FAST QUERY METHODS ---

def save_local_songs(songs: list[RestoredSongRecord], purge_missing: bool = True, db_path: Optional[str] = None) -> int:
    """
    Save or update scanned local music library songs in database/db.db.
    Performs bulk upsert within an atomic transaction.
    If purge_missing is True, deletes database entries whose files no longer exist on disk.
    """
    if not songs and not purge_missing:
        return 0

    sanitized = []
    for s in (songs or []):
        fp = s.get("filepath") or s.get("_data") or ""
        if not fp:
            continue
        fn = s.get("filename") or os.path.basename(fp)
        sanitized.append({
            "filepath": fp,
            "filename": fn,
            "title": s.get("title") or os.path.splitext(fn)[0] or "Unknown",
            "artist": s.get("artist") or "Unknown",
            "album": s.get("album") or "Unknown",
            "size": s.get("size") or 0,
            "size_formatted": s.get("size_formatted") or "",
            "mtime": float(s.get("mtime") or 0.0),
            "mtime_str": str(s.get("mtime_str") or ""),
            "ctime": float(s.get("ctime") or 0.0),
            "ctime_str": str(s.get("ctime_str") or ""),
            "duration_sec": float(s.get("duration_sec") or 0.0),
            "duration_formatted": str(s.get("duration_formatted") or "00:00"),
            "bitrate_kbps": str(s.get("bitrate_kbps") or "Unknown"),
            "bitrate_val": int(s.get("bitrate_val") or 0),
            "sample_rate_hz": str(s.get("sample_rate_hz") or "Unknown"),
            "channels": str(s.get("channels") or "Stereo"),
            "codec": str(s.get("codec") or ""),
            "searchable_text": str(s.get("searchable_text") or f"{s.get('title','')} {s.get('artist','')} {s.get('album','')} {fn}".lower()),
        })

    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            if sanitized:
                # Batch upsert songs
                conn.executemany(
                    """
                    INSERT INTO local_songs (
                        filepath, filename, title, artist, album, size, size_formatted,
                        mtime, mtime_str, ctime, ctime_str, duration_sec, duration_formatted,
                        bitrate_kbps, bitrate_val, sample_rate_hz, channels, codec, searchable_text
                    ) VALUES (
                        :filepath, :filename, :title, :artist, :album, :size, :size_formatted,
                        :mtime, :mtime_str, :ctime, :ctime_str, :duration_sec, :duration_formatted,
                        :bitrate_kbps, :bitrate_val, :sample_rate_hz, :channels, :codec, :searchable_text
                    )
                    ON CONFLICT(filepath) DO UPDATE SET
                        filename = excluded.filename,
                        title = excluded.title,
                        artist = excluded.artist,
                        album = excluded.album,
                        size = excluded.size,
                        size_formatted = excluded.size_formatted,
                        mtime = excluded.mtime,
                        mtime_str = excluded.mtime_str,
                        ctime = excluded.ctime,
                        ctime_str = excluded.ctime_str,
                        duration_sec = excluded.duration_sec,
                        duration_formatted = excluded.duration_formatted,
                        bitrate_kbps = excluded.bitrate_kbps,
                        bitrate_val = excluded.bitrate_val,
                        sample_rate_hz = excluded.sample_rate_hz,
                        channels = excluded.channels,
                        codec = excluded.codec,
                        searchable_text = excluded.searchable_text;
                    """,
                    sanitized
                )

            # Purge entries that were deleted on disk if requested
            if purge_missing and sanitized:
                valid_paths = set(s["filepath"] for s in sanitized)
                cur = conn.execute("SELECT filepath FROM local_songs")
                db_paths = [r[0] for r in cur.fetchall()]
                missing = [p for p in db_paths if p not in valid_paths]
                if missing:
                    conn.executemany("DELETE FROM local_songs WHERE filepath = ?", [(p,) for p in missing])
                    logger.info(f"[Central DB] Purged {len(missing)} missing audio files from local_songs.")

        logger.info(f"[Central DB] Successfully saved/updated {len(sanitized)} songs in local_songs table.")
        return len(sanitized)
    except Exception as e:
        logger.error(f"[Central DB] Error saving local songs: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def get_stored_local_songs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all stored local songs from database/db.db sorted by mtime descending.
    Returns fully formatted song dictionaries compatible with the frontend and scanner.
    """
    conn = None
    try:
        conn = get_connection(db_path)
        cur = conn.execute("SELECT * FROM local_songs ORDER BY mtime DESC")
        rows = cur.fetchall()
        songs = []
        for idx, r in enumerate(rows, 1):
            s = {
                "_id": idx,
                "id": r["id"],
                "filepath": r["filepath"],
                "_data": r["filepath"],
                "filename": r["filename"] or os.path.basename(r["filepath"]),
                "title": r["title"] or "Unknown",
                "artist": r["artist"] or "Unknown",
                "album": r["album"] or "Unknown",
                "size": r["size"] or 0,
                "size_formatted": r["size_formatted"] or "",
                "mtime": r["mtime"] or 0.0,
                "mtime_str": r["mtime_str"] or "",
                "ctime": r["ctime"] or 0.0,
                "ctime_str": r["ctime_str"] or "",
                "duration_sec": r["duration_sec"] or 0.0,
                "duration_formatted": r["duration_formatted"] or "00:00",
                "bitrate_kbps": r["bitrate_kbps"] or "Unknown",
                "bitrate_val": r["bitrate_val"] or 0,
                "sample_rate_hz": r["sample_rate_hz"] or "Unknown",
                "channels": r["channels"] or "Stereo",
                "codec": r["codec"] or "",
                "searchable_text": r["searchable_text"] or f"{r['title']} {r['artist']} {r['album']} {r['filename']}".lower()
            }
            songs.append(s)
        return songs
    except Exception as e:
        logger.error(f"[Central DB] Error retrieving stored local songs: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_local_songs_count(db_path: Optional[str] = None) -> int:
    """Return count of stored songs in database/db.db local_songs table."""
    conn = None
    try:
        conn = get_connection(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM local_songs")
        row = cur.fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.error(f"[Central DB] Error counting local songs: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def delete_stored_local_song(filepath: str, db_path: Optional[str] = None) -> bool:
    """Delete a single song from local_songs table by filepath."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.execute("DELETE FROM local_songs WHERE filepath = ?", (filepath,))
        return True
    except Exception as e:
        logger.error(f"[Central DB] Error deleting local song '{filepath}': {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_stored_local_songs_batch(filepaths: List[str], db_path: Optional[str] = None) -> int:
    """Delete multiple songs from local_songs table by filepaths."""
    if not filepaths:
        return 0
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            conn.executemany("DELETE FROM local_songs WHERE filepath = ?", [(p,) for p in filepaths])
        return len(filepaths)
    except Exception as e:
        logger.error(f"[Central DB] Error batch deleting local songs: {e}")
        return 0
    finally:
        if conn:
            conn.close()
