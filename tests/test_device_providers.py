"""
Unit tests for Device Providers and DeviceProviderRegistry.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from device_providers.base import DeviceProvider, PushResult, DeleteResult
from device_providers.local_provider import LocalDeviceProvider
from device_providers.adb_provider import AdbDeviceProvider
from device_providers.over_ip_provider import OverIpDeviceProvider
from device_providers.registry import DeviceProviderRegistry


class TestDeviceProviders(unittest.TestCase):

    def test_registry_resolution(self):
        p_local = DeviceProviderRegistry.get_provider("local")
        self.assertIsInstance(p_local, LocalDeviceProvider)

        p_adb1 = DeviceProviderRegistry.get_provider("adb_SERIAL123")
        self.assertIsInstance(p_adb1, AdbDeviceProvider)
        self.assertEqual(p_adb1.serial, "SERIAL123")

        p_adb2 = DeviceProviderRegistry.get_provider("adb:XYZ987")
        self.assertIsInstance(p_adb2, AdbDeviceProvider)
        self.assertEqual(p_adb2.serial, "XYZ987")

        p_ip1 = DeviceProviderRegistry.get_provider("ip_192.168.1.100")
        self.assertIsInstance(p_ip1, OverIpDeviceProvider)
        self.assertEqual(p_ip1.ip, "192.168.1.100")

        p_ip2 = DeviceProviderRegistry.get_provider("ip:192.168.1.101")
        self.assertIsInstance(p_ip2, OverIpDeviceProvider)
        self.assertEqual(p_ip2.ip, "192.168.1.101")

        p_none = DeviceProviderRegistry.get_provider(None)
        self.assertIsInstance(p_none, LocalDeviceProvider)

    def test_custom_provider_registration_ocp(self):
        class MockMtpProvider(DeviceProvider):
            def get_device_info(self):
                return {"device_id": self.device_id, "type": "mtp"}
            def get_songs(self, force_refresh=False, progress_cb=None):
                return []
            def push_song(self, local_filepath, remote_dir=None, filename=None):
                return PushResult(success=True, filepath=local_filepath)
            def delete_song(self, filepath_or_id, filename=None):
                return DeleteResult(success=True, filepath_or_id=filepath_or_id)
            def stream_song(self, filepath_or_id, range_header=None):
                return None

        DeviceProviderRegistry.register_provider_factory("mtp_", lambda did: MockMtpProvider(did))
        p = DeviceProviderRegistry.get_provider("mtp_DEVICE01")
        self.assertIsInstance(p, MockMtpProvider)
        self.assertEqual(p.get_device_info()["type"], "mtp")

    @patch("over_ip.client.get_remote_songs")
    def test_over_ip_provider_get_songs(self, mock_get_songs):
        mock_get_songs.return_value = [{"title": "Remote Track", "artist": "Remote Band"}]
        provider = OverIpDeviceProvider("ip_192.168.1.50")
        songs = provider.get_songs(force_refresh=True)
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0]["title"], "Remote Track")

    @patch("over_ip.client.upload_song_to_peer", return_value=True)
    def test_over_ip_provider_push_song(self, mock_upload):
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(b"FAKE_AUDIO")
        tmp.close()

        try:
            provider = OverIpDeviceProvider("ip_192.168.1.50")
            res = provider.push_song(tmp.name)
            self.assertTrue(res.success)
            mock_upload.assert_called_once()
        finally:
            os.remove(tmp.name)


if __name__ == "__main__":
    unittest.main()
