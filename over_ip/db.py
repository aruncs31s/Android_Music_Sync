"""
Over-IP Host Storage Module.
Delegates to centralized database database/db.db (database.db_manager).
Shared by UI and TUI modules.
"""
from typing import List, Dict, Any, Optional
import database.db_manager as central_db


def add_ip_host(ip_address: str, port: int = 5000, alias: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_ip_host(ip_address, port, alias, db_path)


def remove_ip_host(ip_address: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_ip_host(ip_address, db_path)


def get_stored_ip_hosts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_stored_ip_hosts(db_path)


def update_ip_status(ip_address: str, is_online: bool, db_path: Optional[str] = None) -> bool:
    return central_db.update_ip_status(ip_address, is_online, db_path)
