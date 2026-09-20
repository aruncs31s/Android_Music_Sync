import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import services.sync_checker as sync_checker
from ui.server import app


class TestSyncChecker(unittest.TestCase):

    def setUp(self):
        self.tmp_song = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.tmp_song.write(b"ID3" + b"\x00" * 1024)
        self.tmp_song.close()
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.tmp_song.name):
            os.remove(self.tmp_song.name)

    def test_normalize_str(self):
        self.assertEqual(sync_checker.normalize_str("Vidyasagar - Song (Remix)"), "vidyasagarsongremix")
        self.assertEqual(sync_checker.normalize_str(""), "")

    def test_calculate_similarity_score(self):
        local_song = {
            "title": "Mareez - E - Ishq",
            "artist": "Sharib Toshi",
            "filename": "Mareez - E - Ishq.mp3"
        }
        exact_dev_song = {
            "title": "Mareez - E - Ishq",
            "artist": "Sharib Toshi",
            "filename": "Mareez - E - Ishq.mp3"
        }
        similar_dev_song = {
            "title": "Mareez - E - Ishq (Remix)",
            "artist": "Sharib Toshi",
            "filename": "Mareez - E - Ishq (Remix).mp3"
        }
        different_song = {
            "title": "Something Completely Different",
            "artist": "Unknown",
            "filename": "diff.mp3"
        }

        # Exact match returns 100
        self.assertEqual(sync_checker.calculate_similarity_score(local_song, exact_dev_song), 100)

        # Similar song returns high match
        sim_score = sync_checker.calculate_similarity_score(local_song, similar_dev_song)
        self.assertGreaterEqual(sim_score, 70)

        # Different song returns lower score
        diff_score = sync_checker.calculate_similarity_score(local_song, different_song)
        self.assertLess(diff_score, 50)

    @patch("services.sync_checker.song_repo.get_all_songs", return_value=[])
    @patch("services.sync_checker.device_repo.get_device_songs")
    def test_check_song_on_device_exact_and_similar(self, mock_get_songs, _mock_all_songs):
        mock_get_songs.return_value = {
            "device_id": "adb_TESTSERIAL",
            "device_name": "Android ADB: TestTablet",
            "device_type": "ADB USB/Wi-Fi",
            "songs": [
                {
                    "_id": "101",
                    "title": os.path.splitext(os.path.basename(self.tmp_song.name))[0],
                    "artist": "Artist A",
                    "_display_name": os.path.basename(self.tmp_song.name),
                    "_data": f"/storage/emulated/0/Music/{os.path.basename(self.tmp_song.name)}",
                    "duration_formatted": "04:30",
                    "bitrate_kbps": "320",
                    "size_formatted": "10 MB"
                },
                {
                    "_id": "102",
                    "title": os.path.splitext(os.path.basename(self.tmp_song.name))[0] + " (Acoustic)",
                    "artist": "Artist A",
                    "_display_name": "Similar Song.mp3",
                    "_data": "/storage/emulated/0/Music/Similar Song.mp3",
                    "duration_formatted": "04:15",
                    "bitrate_kbps": "128",
                    "size_formatted": "4 MB"
                }
            ]
        }

        res = sync_checker.check_song_on_device(self.tmp_song.name, "adb_TESTSERIAL")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["exact_match"]["found"])
        self.assertEqual(res["exact_match"]["device_song"]["id"], "101")
        self.assertGreaterEqual(len(res["similar_songs"]), 1)
        self.assertEqual(res["similar_songs"][0]["id"], "102")

    def test_api_check_song_endpoint_validation(self):
        # Missing parameters
        res = self.client.get("/api/sync/check-song")
        self.assertEqual(res.status_code, 400)

        # File not found
        res = self.client.get("/api/sync/check-song?filepath=/nonexistent/song.mp3&device_id=adb_123")
        self.assertEqual(res.status_code, 404)

    @patch("services.sync_checker.song_repo.get_all_songs", return_value=[])
    @patch("services.sync_checker.device_repo.get_device_songs")
    def test_api_check_song_endpoint_success(self, mock_get_songs, _mock_all_songs):
        mock_get_songs.return_value = {
            "device_id": "adb_123",
            "device_name": "ADB Device",
            "songs": []
        }
        res = self.client.get(f"/api/sync/check-song?filepath={self.tmp_song.name}&device_id=adb_123")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertFalse(data["exact_match"]["found"])


if __name__ == "__main__":
    unittest.main()
