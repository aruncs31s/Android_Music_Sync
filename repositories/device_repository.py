"""
Device Repository module with Redis caching for connected ADB & Over-IP devices.
"""
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import over_ip.db as over_ip_db
from utils import get_logger

logger = get_logger()


class DeviceRepository(BaseRepository):
    """
    Repository for managing Over-IP peer hosts and ADB connected devices
    with Redis cache-awareness.
    """

    CACHE_KEY_IP_HOSTS = "cache:devices:ip_hosts"

    def get_stored_ip_hosts(self) -> List[Dict[str, Any]]:
        """
        Fetch stored Over-IP hosts.
        Checks Redis cache first; queries SQLite on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_IP_HOSTS)
        if cached is not None:
            logger.info("[DeviceRepository] Redis Cache Hit: Loaded IP hosts.")
            return cached

        hosts = ui_db.get_stored_ip_hosts()
        self._cache_set(self.CACHE_KEY_IP_HOSTS, hosts)
        return hosts

    def add_ip_host(self, ip_address: str, port: int = 5000, alias: str = "") -> bool:
        """
        Add or update an IP host entry in database/db.db and invalidate Redis cache.
        """
        success = over_ip_db.add_ip_host(ip_address, port, alias)
        if success:
            self._cache_delete(self.CACHE_KEY_IP_HOSTS)
        return success

    def update_ip_status(self, ip_address: str, is_online: bool) -> bool:
        """
        Update online status for an IP host and invalidate Redis cache.
        """
        success = over_ip_db.update_ip_status(ip_address, is_online)
        if success:
            self._cache_delete(self.CACHE_KEY_IP_HOSTS)
        return success

    def get_synced_records(self, device_serial: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch synced track records by device serial.
        """
        return ui_db.get_all_synced_records(device_serial)
