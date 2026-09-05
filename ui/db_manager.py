"""
Web UI Database Manager Module.
Delegates to centralized database database/db.db (database.db_manager).
Shared by Web UI and TUI modules.
"""
from typing import List, Dict, Any, Optional, Set
import database.db_manager as central_db


def get_ui_db_path() -> str:
    return central_db.get_central_db_path()


def get_connection(db_path: Optional[str] = None):
    return central_db.get_connection(db_path)


def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_hidden_file(filepath, filename, db_path)


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_hidden_file(filepath, db_path)


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_hidden_records(db_path)


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    return central_db.get_hidden_paths_set(db_path)


def add_synced_file(filepath: str, filename: str, device_serial: str, remote_dir: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_synced_file(filepath, filename, device_serial, remote_dir, db_path)


def get_all_synced_records(device_serial: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_synced_records(device_serial, db_path)
