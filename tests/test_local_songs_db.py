import unittest
import os
import tempfile
import database.db_manager as db_mgr
from over_ip.song_scanner import scan_songs_from_paths
from unittest.mock import patch


class TestLocalSongsDb(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_music.db")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_save_and_retrieve_local_songs(self):
        songs = [
            {
                "filepath": "/music/track1.mp3",
                "filename": "track1.mp3",
                "title": "Track One",
                "artist": "Artist Alpha",
                "album": "Album Alpha",
                "size": 5000000,
                "size_formatted": "5.0 MB",
                "mtime": 1000.0,
                "bitrate_kbps": "320 kbps",
                "bitrate_val": 320
            },
            {
                "filepath": "/music/track2.mp3",
                "filename": "track2.mp3",
                "title": "Track Two",
                "artist": "Artist Beta",
                "album": "Album Beta",
                "size": 3000000,
                "size_formatted": "3.0 MB",
                "mtime": 2000.0,
                "bitrate_kbps": "192 kbps",
                "bitrate_val": 192
            }
        ]

        saved = db_mgr.save_local_songs(songs, purge_missing=False, db_path=self.db_path)
        self.assertEqual(saved, 2)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 2)

        stored = db_mgr.get_stored_local_songs(self.db_path)
        self.assertEqual(len(stored), 2)
        # Should be ordered by mtime descending (track2 has mtime 2000 > track1 1000)
        self.assertEqual(stored[0]["filepath"], "/music/track2.mp3")
        self.assertEqual(stored[0]["title"], "Track Two")
        self.assertEqual(stored[1]["filepath"], "/music/track1.mp3")

    def test_delete_and_batch_delete(self):
        songs = [
            {"filepath": f"/music/song_{i}.mp3", "filename": f"song_{i}.mp3", "title": f"Song {i}", "mtime": float(i)}
            for i in range(5)
        ]
        db_mgr.save_local_songs(songs, purge_missing=False, db_path=self.db_path)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 5)

        # Single delete
        db_mgr.delete_stored_local_song("/music/song_0.mp3", self.db_path)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 4)

        # Batch delete
        del_count = db_mgr.delete_stored_local_songs_batch(["/music/song_1.mp3", "/music/song_2.mp3"], self.db_path)
        self.assertEqual(del_count, 2)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 2)

    def test_purge_missing_on_rescan(self):
        songs1 = [
            {"filepath": "/music/a.mp3", "filename": "a.mp3", "title": "A", "mtime": 100.0},
            {"filepath": "/music/b.mp3", "filename": "b.mp3", "title": "B", "mtime": 200.0}
        ]
        db_mgr.save_local_songs(songs1, purge_missing=False, db_path=self.db_path)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 2)

        # Rescan where b.mp3 is gone, only a.mp3 remains
        songs2 = [
            {"filepath": "/music/a.mp3", "filename": "a.mp3", "title": "A", "mtime": 100.0}
        ]
        db_mgr.save_local_songs(songs2, purge_missing=True, db_path=self.db_path)
        self.assertEqual(db_mgr.get_local_songs_count(self.db_path), 1)
        remaining = db_mgr.get_stored_local_songs(self.db_path)
        self.assertEqual(remaining[0]["filepath"], "/music/a.mp3")

    def test_incremental_scanner_reuses_metadata_when_mtime_matches(self):
        # Create a real audio file
        test_file = os.path.join(self.tmp_dir.name, "sample.mp3")
        with open(test_file, "wb") as f:
            f.write(b"ID3\x03\x00\x00\x00\x00\x00#dummy_audio_bytes_1234567890")

        st = os.stat(test_file)
        cached_metadata = {
            test_file: {
                "filepath": test_file,
                "filename": "sample.mp3",
                "title": "Cached Title Fast",
                "artist": "Cached Artist Fast",
                "album": "Cached Album Fast",
                "size": st.st_size,
                "size_formatted": "1 KB",
                "mtime": st.st_mtime,
                "mtime_str": "2026-01-01 00:00:00",
                "bitrate_kbps": "320 kbps",
                "bitrate_val": 320
            }
        }

        # Patch mutagen to fail if called, verifying mutagen is NOT invoked when cached
        with patch("audio_metadata.extract_audio_metadata", side_effect=RuntimeError("Mutagen should not be called!")):
            scanned = scan_songs_from_paths(
                [self.tmp_dir.name],
                existing_metadata_map=cached_metadata
            )
            self.assertEqual(len(scanned), 1)
            self.assertEqual(scanned[0]["title"], "Cached Title Fast")
            self.assertEqual(scanned[0]["artist"], "Cached Artist Fast")


if __name__ == "__main__":
    unittest.main()
