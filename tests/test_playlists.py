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

    @patch("over_ip.song_scanner.scan_songs_from_paths", return_value=[])
    def test_absent_track_status_persistence_and_resolution(self, _mock_scan):
        """Verify absent tracks are stored permanently in SQLite and can be resolved."""
        # 1. Create playlist
        pl = db_manager.create_playlist("Chill Vibes", db_path=self.tmp_db_path)
        pl_id = pl["id"]

        # 2. Add 1 present and 1 absent track
        db_manager.add_track_to_playlist(
            pl_id,
            filepath="/local/music/PresentSong.mp3",
            status="present",
            title="Present Song",
            db_path=self.tmp_db_path
        )
        db_manager.add_track_to_playlist(
            pl_id,
            filepath="/android/storage/RareMissing.flac",
            status="absent",
            original_path="/android/storage/RareMissing.flac",
            readable_name="Rare Missing Track",
            title="Rare Missing Track",
            db_path=self.tmp_db_path
        )

        # 3. Check playlist counts: track_count=2, present_count=1, absent_count=1
        pls = db_manager.get_playlists(db_path=self.tmp_db_path)
        self.assertEqual(len(pls), 1)
        self.assertEqual(pls[0]["track_count"], 2)
        self.assertEqual(pls[0]["present_count"], 1)
        self.assertEqual(pls[0]["absent_count"], 1)

        # 4. Check absent tracks query
        absent_tracks = db_manager.get_playlist_absent_tracks(pl_id, db_path=self.tmp_db_path)
        self.assertEqual(len(absent_tracks), 1)
        self.assertEqual(absent_tracks[0]["status"], "absent")
        self.assertEqual(absent_tracks[0]["original_path"], "/android/storage/RareMissing.flac")

        # 5. Resolve absent track
        resolved = db_manager.resolve_playlist_track(
            playlist_id=pl_id,
            original_path="/android/storage/RareMissing.flac",
            resolved_filepath="/local/music/FoundRareMissing.flac",
            title="Rare Missing Track (Found)",
            db_path=self.tmp_db_path
        )
        self.assertTrue(resolved)

        # 6. Verify counts updated: absent_count=0, present_count=2
        pls_after = db_manager.get_playlists(db_path=self.tmp_db_path)
        self.assertEqual(pls_after[0]["absent_count"], 0)
        self.assertEqual(pls_after[0]["present_count"], 2)

        # 7. Verify tracks list shows status='present' and updated filepath
        tracks_after = db_manager.get_playlist_tracks(pl_id, db_path=self.tmp_db_path)
        resolved_t = next(t for t in tracks_after if t["title"] == "Rare Missing Track (Found)")
        self.assertEqual(resolved_t["status"], "present")
        self.assertEqual(resolved_t["filepath"], "/local/music/FoundRareMissing.flac")

    @patch("over_ip.song_scanner.scan_songs_from_paths", return_value=[])
    def test_absent_api_and_resolution(self, _mock_scan):
        """Verify GET /api/playlists/<id>/absent and POST /api/playlists/<id>/resolve endpoints."""
        # Create playlist
        res = self.app_client.post("/api/playlists/create", json={"name": "Electronic Drive"})
        pl_id = res.get_json()["playlist"]["id"]

        # Insert absent track into DB
        db_manager.add_track_to_playlist(
            pl_id,
            filepath="/sdcard/Music/SynthWave.mp3",
            status="absent",
            original_path="/sdcard/Music/SynthWave.mp3",
            readable_name="Synth Wave Intro",
            title="Synth Wave Intro",
            db_path=self.tmp_db_path
        )

        # Check /api/playlists/<id>/absent
        res = self.app_client.get(f"/api/playlists/{pl_id}/absent")
        self.assertEqual(res.status_code, 200)
        absent_data = res.get_json()
        self.assertEqual(len(absent_data), 1)
        self.assertEqual(absent_data[0]["status"], "absent")
        self.assertEqual(absent_data[0]["title"], "Synth Wave Intro")

        # Check /api/playlists/absent-all
        res_all = self.app_client.get("/api/playlists/absent-all")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(len(res_all.get_json()), 1)

        # Resolve via API
        res_resolve = self.app_client.post(f"/api/playlists/{pl_id}/resolve", json={
            "original_path": "/sdcard/Music/SynthWave.mp3",
            "resolved_filepath": "/home/music/SynthWave_hq.mp3",
            "title": "Synth Wave Intro (HQ)"
        })
        self.assertEqual(res_resolve.status_code, 200)
        self.assertEqual(res_resolve.get_json()["status"], "success")

        # Verify absent list is now 0
        res_absent_after = self.app_client.get(f"/api/playlists/{pl_id}/absent")
        self.assertEqual(len(res_absent_after.get_json()), 0)

        # Verify tracks list has resolved track
        res_tracks = self.app_client.get(f"/api/playlists/{pl_id}/tracks")
        tracks = res_tracks.get_json()
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["status"], "present")
        self.assertEqual(tracks[0]["filepath"], os.path.abspath("/home/music/SynthWave_hq.mp3"))

    @patch("over_ip.song_scanner.scan_songs_from_paths", return_value=[])
    def test_poweramp_status_refresh_persistence(self, _mock_scan):
        """Verify that absent songs survive page refresh even if in-memory report is None."""
        import ui.server as ui_server

        # 1. Create playlist with absent track
        pl = db_manager.create_playlist("Gym Bangers", db_path=self.tmp_db_path)
        db_manager.add_track_to_playlist(
            pl["id"],
            filepath="/storage/TrackUnmatched.mp3",
            status="absent",
            original_path="/storage/TrackUnmatched.mp3",
            readable_name="Unmatched Track",
            title="Unmatched Track",
            db_path=self.tmp_db_path
        )

        # 2. Simulate refresh: clear in-memory variable
        ui_server._last_poweramp_report = None

        # 3. GET /api/poweramp/status should still return report from persistent SQLite!
        res = self.app_client.get("/api/poweramp/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["has_report"])
        self.assertIsNotNone(data["report"])
        self.assertEqual(data["report"]["absent_tracks_count"], 1)
        self.assertEqual(data["report"]["absent_songs"][0]["readable_name"], "Unmatched Track")


if __name__ == "__main__":
    unittest.main()
