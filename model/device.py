from dataclasses import dataclass
from typing import Optional
from model.base import DictLikeRecord
from model.enums import DeviceType


@dataclass
class DeviceRecord(DictLikeRecord):
    """Model representing a connected device (Local, ADB, or Over-IP)."""
    serial: str
    description: str = ""
    device_type: str = DeviceType.ADB.value
    is_online: bool = True
    last_seen: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = 5000
