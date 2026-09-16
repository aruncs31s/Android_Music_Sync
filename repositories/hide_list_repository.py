"""
Hide List Repository module with Redis caching and SQLite fallback.
"""
from typing import List, Dict, Any

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import hide_list_db
from utils import get_logger

logger = get_logger()


class HideListRepository(BaseRepository):
    """
    Repository for managing hidden files in database/db.db with Redis caching.
    """

    CACHE_KEY_HIDDEN = "cache:hidden:all"

    def get_all_hidden_records(self) -> List[Dict[str, Any]]:
        """
        Fetch all hidden file records.
        Checks Redis cache first; queries SQLite database on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_HIDDEN)
        if cached is not None:
            logger.info("[HideListRepository] Redis Cache Hit: Loaded hidden files.")
            return cached

        records = ui_db.get_all_hidden_records()
        self._cache_set(self.CACHE_KEY_HIDDEN, records)
        return records

    def hide_file(self, filepath: str) -> bool:
        """
        Hide a file path in SQLite database and clear Redis hide list cache.
        """
        ui_db.add_hidden_file(filepath)
        hide_list_db.add_hidden_file(filepath)
        self._cache_delete(self.CACHE_KEY_HIDDEN)
        self._cache_delete("cache:songs:all")
        self._cache_delete("cache:songs:duplicates")
        return True

    def unhide_file(self, filepath: str) -> bool:
        """
        Unhide a file path in SQLite database and clear Redis hide list cache.
        """
        ui_db.remove_hidden_file(filepath)
        hide_list_db.remove_hidden_file(filepath)
        self._cache_delete(self.CACHE_KEY_HIDDEN)
        self._cache_delete("cache:songs:all")
        self._cache_delete("cache:songs:duplicates")
        return True
