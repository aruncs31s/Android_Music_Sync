import os
import sys
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ui.server import app
from device_providers.base import DeviceProvider, DeleteResult


class MockAdbProvider(DeviceProvider):
    def __init__(self, device_id="adb:mock_device"):
        super().__init__(device_id=device_id)

    def get_device_info(self):
        return {
            "device_id": self.device_id,
            "device_name": "Android ADB: Mock Phone",
            "device_type": "ADB USB/Wi-Fi",
            "is_online": True,
        }

    def get_songs(self, force_refresh=False, progress_cb=None):
        return [
            {
                "filepath": "/storage/emulated/0/Music/SongA.mp3",
                "filename": "SongA.mp3",
                "title": "Duplicate Song",
                "artist": "Famous Artist",
                "size": 5000000,
                "bitrate_val": 320,
            },
            {
                "filepath": "/storage/emulated/0/Download/SongA_copy.mp3",
                "filename": "SongA_copy.mp3",
                "title": "Duplicate Song",
                "artist": "Famous Artist",
                "size": 4800000,
                "bitrate_val": 256,
            },
            {
                "filepath": "/storage/emulated/0/Music/UniqueSong.mp3",
                "filename": "UniqueSong.mp3",
                "title": "Unique Track",
                "artist": "Another Artist",
                "size": 3000000,
                "bitrate_val": 192,
            },
        ]

    def push_song(self, local_filepath, remote_dir=None, filename=None):
        raise NotImplementedError

    def delete_song(self, filepath_or_id, filename=None):
        return DeleteResult(success=True, filepath_or_id=filepath_or_id, message="Deleted")

    def stream_song(self, filepath_or_id, range_header=None):
        raise NotImplementedError


class TestRemoteDuplicates(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch("device_providers.registry.DeviceProviderRegistry.get_provider")
    def test_get_duplicates_for_adb_device(self, mock_get_provider):
        mock_provider = MockAdbProvider("adb:test_phone")
        mock_get_provider.return_value = mock_provider

        res = self.client.get("/api/duplicates?device_id=adb:test_phone&refresh=true")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("clusters", data)
        self.assertEqual(data.get("cluster_count"), 1)
        self.assertEqual(data.get("total_duplicates"), 1)

        cluster = data["clusters"][0]
        self.assertEqual(cluster["cluster_name"].lower(), "famous artist - duplicate song")
        self.assertEqual(cluster["count"], 2)
        paths = [s["filepath"] for s in cluster["songs"]]
        self.assertIn("/storage/emulated/0/Music/SongA.mp3", paths)
        self.assertIn("/storage/emulated/0/Download/SongA_copy.mp3", paths)

    @patch("device_providers.registry.DeviceProviderRegistry.get_provider")
    def test_get_duplicates_remote_with_fingerprint_notice(self, mock_get_provider):
        mock_provider = MockAdbProvider("adb:test_phone")
        mock_get_provider.return_value = mock_provider

        res = self.client.get("/api/duplicates?device_id=adb:test_phone&fingerprint=true&refresh=true")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("warning", data)
        self.assertIn("Remote device", data["warning"])

    @patch("repositories.device_repo.delete_device_songs_batch")
    def test_batch_delete_remote_duplicates(self, mock_delete_batch):
        mock_delete_batch.return_value = {
            "status": "success",
            "deleted_count": 1,
            "failed": [],
            "message": "Deleted 1 files from adb:test_phone",
        }

        res = self.client.post(
            "/api/songs/delete-batch",
            json={
                "filepaths": ["/storage/emulated/0/Download/SongA_copy.mp3"],
                "device_id": "adb:test_phone",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("deleted_count"), 1)
        mock_delete_batch.assert_called_once_with(
            device_id="adb:test_phone",
            filepaths=["/storage/emulated/0/Download/SongA_copy.mp3"],
        )


if __name__ == "__main__":
    unittest.main()
