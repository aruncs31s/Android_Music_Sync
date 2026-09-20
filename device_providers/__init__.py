"""
Device Providers package for Antigravity Music Manager.
Defines clean SOLID abstractions for interacting with different storage & peer transports:
- Local filesystem
- Android ADB (USB/Wi-Fi)
- Over-IP companion peers (HTTP REST)
"""
from device_providers.base import (
    DeviceProvider,
    SongQueryable,
    SongPushable,
    SongDeletable,
    SongStreamable,
    PushResult,
    DeleteResult,
)
from device_providers.registry import DeviceProviderRegistry

__all__ = [
    "DeviceProvider",
    "SongQueryable",
    "SongPushable",
    "SongDeletable",
    "SongStreamable",
    "PushResult",
    "DeleteResult",
    "DeviceProviderRegistry",
]
