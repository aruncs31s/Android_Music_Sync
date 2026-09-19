"""
Device Provider Registry implementing the Factory and Open/Closed Principle (OCP).
Allows resolving the appropriate DeviceProvider for any device_id string,
and dynamically registering new provider types without modifying existing code.
"""
from typing import Dict, Type, Optional, Callable
from device_providers.base import DeviceProvider
from device_providers.local_provider import LocalDeviceProvider
from device_providers.adb_provider import AdbDeviceProvider
from device_providers.over_ip_provider import OverIpDeviceProvider


class DeviceProviderRegistry:
    """Registry that resolves device_id to the appropriate DeviceProvider subclass."""

    _custom_factories: Dict[str, Callable[[str], DeviceProvider]] = {}

    @classmethod
    def register_provider_factory(cls, prefix: str, factory: Callable[[str], DeviceProvider]):
        """Register a new device provider factory by its device_id prefix (OCP)."""
        cls._custom_factories[prefix.lower()] = factory

    @classmethod
    def get_provider(cls, device_id: Optional[str]) -> DeviceProvider:
        """
        Factory method returning the concrete DeviceProvider for the given device_id (LSP).
        Default is LocalDeviceProvider if device_id is empty or 'local'.
        """
        if not device_id or device_id.lower() == "local":
            return LocalDeviceProvider()

        clean_id = device_id.strip()

        # Check custom registered factories
        for prefix, factory in cls._custom_factories.items():
            if clean_id.lower().startswith(prefix):
                return factory(clean_id)

        # ADB Device
        if clean_id.startswith("adb_") or clean_id.startswith("adb:"):
            return AdbDeviceProvider(clean_id)

        # Over-IP Peer
        if clean_id.startswith("ip_") or clean_id.startswith("ip:") or clean_id.startswith("http://") or clean_id.startswith("https://"):
            return OverIpDeviceProvider(clean_id)

        # Fallback to local if unknown format
        return LocalDeviceProvider(clean_id)
