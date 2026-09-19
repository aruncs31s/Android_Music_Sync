import os
import sys
import unittest
import tempfile

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database.db_manager as db_manager
from unittest.mock import patch
from ui.server import app


class TestPlaylists(unittest.TestCase):
    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)

        # Monkeypatch central_db path for testing
        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path

        self.app_client = app.test_client()
        self.app_client.testing = True

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    def test_database_playlist_crud(self):
        # 1. Create playlist
        pl = db_manager.create_playlist("Workout Mix", db_path=self.tmp_db_path)
        self.assertIsNotNone(pl)
        self.assertEqual(pl["name"], "Workout Mix")

        # 2. Get playlists
        playlists = db_manager.get_playlists(db_path=self.tmp_db_path)
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]["name"], "Workout Mix")
        self.assertEqual(playlists[0]["track_count"], 0)

        # 3. Add tracks
        success1 = db_manager.add_track_to_playlist(pl["id"], "/music/song1.mp3", db_path=self.tmp_db_path)
        success2 = db_manager.add_track_to_playlist(pl["id"], "/music/song2.mp3", db_path=self.tmp_db_path)
        self.assertTrue(success1)
        self.assertTrue(success2)

        tracks = db_manager.get_playlist_tracks(pl["id"], db_path=self.tmp_db_path)
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0]["filepath"], "/music/song1.mp3")

        # 4. Remove track
        rem_success = db_manager.remove_track_from_playlist(pl["id"], "/music/song1.mp3", db_path=self.tmp_db_path)
        self.assertTrue(rem_success)

        tracks_after = db_manager.get_playlist_tracks(pl["id"], db_path=self.tmp_db_path)
        self.assertEqual(len(tracks_after), 1)
        self.assertEqual(tracks_after[0]["filepath"], "/music/song2.mp3")

        # 5. Delete playlist
        del_success = db_manager.delete_playlist(pl["id"], db_path=self.tmp_db_path)
        self.assertTrue(del_success)
        self.assertEqual(len(db_manager.get_playlists(db_path=self.tmp_db_path)), 0)

    @patch("over_ip.song_scanner.scan_songs_from_paths", return_value=[])
    def test_playlist_api_endpoints(self, _mock_scan):
        # Create via API
        res = self.app_client.post("/api/playlists/create", json={"name": "Roadtrip Hits"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        pl_id = data["playlist"]["id"]

        # List via API
        res = self.app_client.get("/api/playlists")
        self.assertEqual(res.status_code, 200)
        pls = res.get_json()
        self.assertEqual(len(pls), 1)
        self.assertEqual(pls[0]["name"], "Roadtrip Hits")

        # Add track via API
        res = self.app_client.post(f"/api/playlists/{pl_id}/add-track", json={"filepath": "/tmp/track.mp3"})
        self.assertEqual(res.status_code, 200)

        # Get tracks via API
        res = self.app_client.get(f"/api/playlists/{pl_id}/tracks")
        self.assertEqual(res.status_code, 200)
        tracks = res.get_json()
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["filepath"], "/tmp/track.mp3")

        # Delete playlist via API
        res = self.app_client.post("/api/playlists/delete", json={"playlist_id": pl_id})
        self.assertEqual(res.status_code, 200)

        # Verify list empty
        res = self.app_client.get("/api/playlists")
        self.assertEqual(len(res.get_json()), 0)


if __name__ == "__main__":
    unittest.main()
