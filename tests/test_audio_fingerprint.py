import os
import sys
import shutil
import unittest
import tempfile
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils import audio_fingerprint
import database.db_manager as db_manager
import ui.stats_manager as stats_manager
from repositories.song_repository import SongRepository


class TestAudioFingerprint(unittest.TestCase):

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)

        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path

        # Create temporary dummy audio files
        self.temp_dir = tempfile.mkdtemp(prefix="audio_fp_test_")
        self.song_a = os.path.join(self.temp_dir, "song_a.mp3")
        self.song_b = os.path.join(self.temp_dir, "song_b.m4a")
        self.song_c = os.path.join(self.temp_dir, "song_c.flac")

        for path, content in [
            (self.song_a, b"FAKE_AUDIO_DATA_FOR_SONG_A"),
            (self.song_b, b"FAKE_AUDIO_DATA_FOR_SONG_B"),
            (self.song_c, b"FAKE_AUDIO_DATA_FOR_SONG_C"),
        ]:
            with open(path, "wb") as f:
                f.write(content)

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    def test_is_fpcalc_available(self):
        result = audio_fingerprint.is_fpcalc_available()
        self.assertIsInstance(result, bool)

    def test_are_fingerprints_equal(self):
        self.assertTrue(audio_fingerprint.are_fingerprints_equal("AQAA...", "AQAA..."))
        self.assertTrue(audio_fingerprint.are_fingerprints_equal("  AQAA...  ", "AQAA..."))
        self.assertFalse(audio_fingerprint.are_fingerprints_equal("AQAA...", "BBAA..."))
        self.assertFalse(audio_fingerprint.are_fingerprints_equal("", "AQAA..."))
        self.assertFalse(audio_fingerprint.are_fingerprints_equal(None, "AQAA..."))

    def test_sqlite_fingerprint_caching(self):
        st = os.stat(self.song_a)
        fsize = st.st_size
        fmtime = st.st_mtime
        test_fp = "AQAA_TEST_FINGERPRINT_12345"
        test_duration = 184.5

        # 1. Initially nothing cached
        cached = db_manager.get_cached_fingerprint(self.song_a, fsize, fmtime, db_path=self.tmp_db_path)
        self.assertIsNone(cached)

        # 2. Save fingerprint to DB
        saved = db_manager.save_cached_fingerprint(
            self.song_a, fsize, fmtime, test_duration, test_fp, db_path=self.tmp_db_path
        )
        self.assertTrue(saved)

        # 3. Retrieve matching fingerprint
        cached = db_manager.get_cached_fingerprint(self.song_a, fsize, fmtime, db_path=self.tmp_db_path)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["fingerprint"], test_fp)
        self.assertEqual(cached["duration"], test_duration)

        # 4. Check that stale mtime or size returns None (cache miss / invalidation)
        stale_mtime = db_manager.get_cached_fingerprint(self.song_a, fsize, fmtime + 10.0, db_path=self.tmp_db_path)
        self.assertIsNone(stale_mtime)

        stale_size = db_manager.get_cached_fingerprint(self.song_a, fsize + 100, fmtime, db_path=self.tmp_db_path)
        self.assertIsNone(stale_size)

        # 5. Bulk load map
        fp_map = db_manager.get_all_cached_fingerprints_map(db_path=self.tmp_db_path)
        self.assertIn(self.song_a, fp_map)
        self.assertEqual(fp_map[self.song_a]["fingerprint"], test_fp)

    @patch("utils.audio_fingerprint.is_fpcalc_available", return_value=False)
    def test_detect_duplicates_fpcalc_missing_fallback(self, mock_avail):
        # When fpcalc is missing and user requests fingerprinting,
        # it must set warning and fall back to metadata matching.
        songs = [
            {"filepath": self.song_a, "title": "Track One", "artist": "Artist X", "filename": "song_a.mp3"},
            {"filepath": self.song_b, "title": "Track One", "artist": "Artist X", "filename": "song_b.m4a"},
        ]

        result = stats_manager.detect_duplicate_songs(songs, use_fingerprint=True)
        self.assertFalse(result["fpcalc_available"])
        self.assertIsNotNone(result["warning"])
        self.assertIn("fpcalc", result["warning"].lower())
        # Found cluster via fallback metadata match
        self.assertEqual(result["cluster_count"], 1)
        self.assertEqual(result["clusters"][0]["match_type"], "title_artist")

    @patch("utils.audio_fingerprint.is_fpcalc_available", return_value=True)
    def test_detect_duplicates_acoustic_waveform_clustering(self, mock_avail):
        # Mock generate_audio_fingerprint to return identical fingerprint for song_a and song_b
        # even though their filenames and titles differ!
        def fake_fp(filepath, *args, **kwargs):
            if filepath in (self.song_a, self.song_b):
                return {"duration": 210.0, "fingerprint": "IDENTICAL_ACOUSTIC_FINGERPRINT"}
            return {"duration": 180.0, "fingerprint": "DISTINCT_FINGERPRINT_C"}

        songs = [
            {"filepath": self.song_a, "title": "Different Title A", "artist": "Artist 1", "filename": "song_a.mp3"},
            {"filepath": self.song_b, "title": "Totally Other Title B", "artist": "Artist 2", "filename": "song_b.m4a"},
            {"filepath": self.song_c, "title": "Solo Track", "artist": "Artist 3", "filename": "song_c.flac"},
        ]

        with patch("utils.audio_fingerprint.generate_audio_fingerprint", side_effect=fake_fp):
            result = stats_manager.detect_duplicate_songs(songs, use_fingerprint=True)

        self.assertTrue(result["fpcalc_available"])
        self.assertIsNone(result["warning"])
        self.assertEqual(result["cluster_count"], 1)
        cluster = result["clusters"][0]
        self.assertEqual(cluster["match_type"], "audio_fingerprint")
        self.assertEqual(cluster["count"], 2)
        cluster_paths = [s["filepath"] for s in cluster["songs"]]
        self.assertIn(self.song_a, cluster_paths)
        self.assertIn(self.song_b, cluster_paths)

    def test_song_repository_duplicate_modes(self):
        repo = SongRepository()
        dummy_songs = [
            {"filepath": self.song_a, "title": "Song", "artist": "Band", "filename": "a.mp3"},
            {"filepath": self.song_b, "title": "Song", "artist": "Band", "filename": "b.mp3"},
        ]
        with patch.object(repo, "get_all_songs", return_value=dummy_songs):
            res_tags = repo.get_duplicates(force_refresh=True, use_fingerprint=False)
            self.assertIn("clusters", res_tags)

            res_fp = repo.get_duplicates(force_refresh=True, use_fingerprint=True)
            self.assertIn("clusters", res_fp)


if __name__ == "__main__":
    unittest.main()
