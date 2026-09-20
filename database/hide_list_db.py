"""
Hide List & Synced Tracks History Module.
Delegates to centralized database database/db.db (database.db_manager).
Maintains 100% backward compatibility for all TUI and CLI commands.
"""
from typing import Set, List, Dict, Any, Optional
import database.db_manager as central_db


def get_default_db_path() -> str:
    """Get absolute path to centralized db.db in database/ directory."""
    return central_db.get_central_db_path()


def _get_connection(db_path: Optional[str] = None):
    """Get SQLite database connection to centralized database/db.db."""
    return central_db.get_connection(db_path)


# --- HIDE LIST METHODS ---

def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_hidden_file(filepath, filename, db_path)


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_hidden_file(filepath, db_path)


def clear_all_hidden(db_path: Optional[str] = None) -> bool:
    return central_db.clear_all_hidden(db_path)


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    return central_db.get_hidden_paths_set(db_path)


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_hidden_records(db_path)


# --- SYNCED FILES HISTORY METHODS ---

def add_synced_file(
    filepath: str,
    filename: str,
    device_serial: str,
    remote_dir: str = "",
    db_path: Optional[str] = None
) -> bool:
    return central_db.add_synced_file(filepath, filename, device_serial, remote_dir, db_path)


def get_synced_paths_set(device_serial: str, db_path: Optional[str] = None) -> Set[str]:
    return central_db.get_synced_paths_set(device_serial, db_path)


def get_all_synced_records(device_serial: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_synced_records(device_serial, db_path)
