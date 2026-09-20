from enum import Enum


class TrackStatus(str, Enum):
    """Single source of truth for playlist track statuses."""
    PRESENT = "present"
    ABSENT = "absent"


class DeviceType(str, Enum):
    """Single source of truth for connected device types."""
    ADB = "adb"
    OVER_IP = "over_ip"
    LOCAL = "local"


class SyncDirection(str, Enum):
    """Direction for synchronization workflows."""
    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"
