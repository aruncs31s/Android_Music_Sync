import os
import sys
import unittest
import tempfile
import sqlite3
import zipfile
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import utils.android.poweramp.poweramp_importer as poweramp_importer
from ui.server import app
import database.db_manager as db_manager


class TestPowerampImporter(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db", dir=self.tmp_dir)
        os.close(self.tmp_db_fd)

        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path

        self.app_client = app.test_client()
        self.app_client.testing = True

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        if os.path.exists(self.tmp_dir):
            import shutil
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _create_sample_poweramp_db(self, db_path: str):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE playlists (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                keep_list_pos INTEGER,
                keep_track_pos INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE tracks (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER,
                path TEXT NOT NULL,
                readable_name TEXT,
                file_type INTEGER,
                cue_offset_ms INTEGER,
                rating INTEGER DEFAULT 0,
                played_at INTEGER,
                played_fully_at INTEGER,
                played_times INTEGER,
                last_pos INTEGER,
                export_type INTEGER,
                preset_id INTEGER,
                total_played_times INTEGER
            )
        """)

        # Add playlists
        c.execute("INSERT INTO playlists (_id, name) VALUES (1, 'Favorites')")
        c.execute("INSERT INTO playlists (_id, name) VALUES (2, 'Gym Mix')")

        # Add tracks
        # Track 1 in Favorites: exact match
        c.execute("""
            INSERT INTO tracks (playlist_id, path, readable_name, rating)
            VALUES (1, 'primary/Music/Rock/Song1.mp3', 'Song One (320kbps)', 5)
        """)
        # Track 2 in Favorites: absent song
        c.execute("""
            INSERT INTO tracks (playlist_id, path, readable_name, rating)
            VALUES (1, 'primary/Music/Pop/MissingSong.flac', 'Missing Song [FLAC]', 0)
        """)
        # Track 3 in Gym Mix: clean match
        c.execute("""
            INSERT INTO tracks (playlist_id, path, readable_name, rating)
            VALUES (2, 'SDCard/EDM/BeastMode_Track.mp3', 'Beast Mode Track', 4)
        """)

        conn.commit()
        conn.close()

    def test_clean_string_for_matching(self):
        self.assertEqual(
            poweramp_importer.clean_string_for_matching("Pazham Thamizhppaattizhayum (128).mp3"),
            "pazham thamizhppaattizhayum"
        )
        self.assertEqual(
            poweramp_importer.clean_string_for_matching("Song_Name - Artist [FLAC].flac"),
            "song name artist"
        )
        self.assertEqual(
            poweramp_importer.clean_string_for_matching("Track (Official Video) [320 kbps]"),
            "track"
        )
        self.assertEqual(poweramp_importer.clean_string_for_matching(None), "")

    def test_extract_database_direct_sqlite(self):
        sample_db = os.path.join(self.tmp_dir, "sample.db")
        self._create_sample_poweramp_db(sample_db)

        db_path, temp_dir = poweramp_importer.extract_database_from_source(sample_db)
        self.assertEqual(db_path, sample_db)
        self.assertIsNone(temp_dir)

    def test_extract_database_directory(self):
        sub_dir = os.path.join(self.tmp_dir, "backup_folder")
        os.makedirs(sub_dir, exist_ok=True)
        lists_export = os.path.join(sub_dir, "lists-export")
        self._create_sample_poweramp_db(lists_export)

        db_path, temp_dir = poweramp_importer.extract_database_from_source(sub_dir)
        self.assertEqual(db_path, lists_export)
        self.assertIsNone(temp_dir)

    def test_extract_database_extensionless_zip(self):
        # Create a zip archive with NO extension
        zip_path = os.path.join(self.tmp_dir, "poweramp-backup-noext")
        lists_export = os.path.join(self.tmp_dir, "lists-export-tmp")
        self._create_sample_poweramp_db(lists_export)

        with zipfile.ZipFile(zip_path, "w") as z:
            z.write(lists_export, arcname="lists-export")

        db_path, temp_dir = poweramp_importer.extract_database_from_source(zip_path)
        self.assertTrue(os.path.exists(db_path))
        self.assertIsNotNone(temp_dir)
        self.assertTrue(db_path.endswith("lists-export"))

        # Clean up
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_import_poweramp_backup(self):
        sample_db = os.path.join(self.tmp_dir, "lists-export")
        self._create_sample_poweramp_db(sample_db)

        local_songs = [
            {
                "filepath": "/Users/test/Music/Song1.mp3",
                "filename": "Song1.mp3",
                "title": "Song One",
                "artist": "Artist A",
                "album": "Album A"
            },
            {
                "filepath": "/Users/test/Music/Beast Mode Track.mp3",
                "filename": "Beast Mode Track.mp3",
                "title": "Beast Mode Track",
                "artist": "DJ Gym",
                "album": "Workout"
            }
        ]

        report = poweramp_importer.import_poweramp_backup(
            sample_db,
            sync_to_library=True,
            local_songs=local_songs
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_playlists"], 2)
        self.assertEqual(report["total_tracks"], 3)
        self.assertEqual(report["matched_tracks_count"], 2)
        self.assertEqual(report["absent_tracks_count"], 1)
        self.assertEqual(report["liked_tracks_synced"], 2)  # Song1 (rating 5) and BeastMode (rating 4)

        absent = report["absent_songs"]
        self.assertEqual(len(absent), 1)
        self.assertEqual(absent[0]["playlist_name"], "Favorites")
        self.assertEqual(absent[0]["filename"], "MissingSong.flac")

    def test_api_poweramp_import_and_export(self):
        sample_db = os.path.join(self.tmp_dir, "lists-export")
        self._create_sample_poweramp_db(sample_db)

        # 1. Test POST /api/poweramp/import with file_path
        res = self.app_client.post("/api/poweramp/import", json={"file_path": sample_db})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_playlists"], 2)

        # 2. Test GET /api/poweramp/export-absent
        export_res = self.app_client.get("/api/poweramp/export-absent")
        self.assertEqual(export_res.status_code, 200)
        self.assertIn("POWERAMP PLAYLIST IMPORT - ABSENT SONGS REPORT", export_res.text)
        self.assertIn("MissingSong.flac", export_res.text)


if __name__ == "__main__":
    unittest.main()
