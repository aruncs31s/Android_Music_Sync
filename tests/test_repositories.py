import os
import sys
import shutil
import unittest
import tempfile
import time
import threading
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config_manager
import database.db_manager as db_manager
import redis_cache
import repositories.deleted_song_repository as deleted_song_repository
from repositories import song_repo, playlist_repo, hide_repo, device_repo, deleted_repo


class TestRepositories(unittest.TestCase):

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)

        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path

        # Redirect the repo-local trash folder to a temp dir for the test.
        self.trash_dir = tempfile.mkdtemp(prefix="trash_test_")
        self.orig_trash_root = deleted_song_repository.TRASH_ROOT
        deleted_song_repository.TRASH_ROOT = self.trash_dir

        # Clear test cache keys
        self.cfg = config_manager.load_config()
        self.redis_cfg = self.cfg.get("redis")
        if self.redis_cfg:
            redis_cache.delete_cache_pattern(self.redis_cfg, "cache:*")

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        deleted_song_repository.TRASH_ROOT = self.orig_trash_root
        shutil.rmtree(self.trash_dir, ignore_errors=True)
        if self.redis_cfg:
            redis_cache.delete_cache_pattern(self.redis_cfg, "cache:*")
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    @patch("over_ip.song_scanner.scan_songs_from_paths", return_value=[])
    def test_playlist_repository_crud_and_invalidation(self, _mock_scan):
        # 1. Initially empty
        pls = playlist_repo.get_playlists()
        self.assertEqual(len(pls), 0)

        # 2. Create playlist
        pl_name = "Repo Test Playlist"
        created = playlist_repo.create_playlist(pl_name)
        self.assertIsNotNone(created)

        pls_after_create = playlist_repo.get_playlists()
        self.assertEqual(len(pls_after_create), 1)
        self.assertEqual(pls_after_create[0]["name"], pl_name)

        pl_id = created["id"]

        # 3. Add & get tracks
        added = playlist_repo.add_track_to_playlist(pl_id, "/tmp/sample_song.mp3")
        self.assertTrue(added)

        tracks = playlist_repo.get_playlist_tracks(pl_id)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["filepath"], "/tmp/sample_song.mp3")

        # 4. Remove track
        removed = playlist_repo.remove_track_from_playlist(pl_id, "/tmp/sample_song.mp3")
        self.assertTrue(removed)

        tracks_after_remove = playlist_repo.get_playlist_tracks(pl_id)
        self.assertEqual(len(tracks_after_remove), 0)

        # 5. Delete playlist
        deleted = playlist_repo.delete_playlist(pl_id)
        self.assertTrue(deleted)
        self.assertEqual(len(playlist_repo.get_playlists()), 0)

    def test_hide_list_repository(self):
        test_path = "/tmp/test_hidden_song.mp3"
        hide_repo.hide_file(test_path)

        records = hide_repo.get_all_hidden_records()
        self.assertTrue(any(r["filepath"] == test_path for r in records))

        hide_repo.unhide_file(test_path)
        records_after = hide_repo.get_all_hidden_records()
        self.assertFalse(any(r["filepath"] == test_path for r in records_after))

    def test_device_repository(self):
        ip = "192.168.1.199"
        device_repo.add_ip_host(ip, 5000, "Test Peer")

        hosts = device_repo.get_stored_ip_hosts()
        self.assertTrue(any(h["ip_address"] == ip for h in hosts))

    @patch("repositories.song_repo.get_all_songs", return_value=[])
    def test_device_songs_and_parser(self, _mock_songs):
        # 1. Test local device songs
        local_data = device_repo.get_device_songs("local")
        self.assertEqual(local_data["device_id"], "local")
        self.assertEqual(local_data["device_type"], "Local Storage")
        self.assertIn("songs", local_data)

        # 2. Test song parser with date_added, date_modified, and bitrate
        import song_parser
        raw_adb_line = "Row: 0 _id=101, _display_name=TestTrack.mp3, title=Test Track, artist=Robots, album=Cyber, duration=240000, _size=9600000, _data=/sdcard/Music/TestTrack.mp3, date_added=1693500000, date_modified=1693600000, bitrate=320000"
        parsed = song_parser.parse_song_line(raw_adb_line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["title"], "Test Track")
        self.assertEqual(parsed["artist"], "Robots")
        self.assertEqual(parsed["bitrate_val"], 320)
        self.assertEqual(parsed["bitrate_kbps"], "320 kbps")
        self.assertEqual(parsed["mtime"], 1693600000.0)
        self.assertNotEqual(parsed["mtime_str"], "Unknown")
        self.assertEqual(parsed["ctime"], 1693500000.0)
        self.assertNotEqual(parsed["ctime_str"], "Unknown")
        self.assertEqual(parsed["filepath"], "/sdcard/Music/TestTrack.mp3")

    def test_redis_disabled_fallback(self):
        # Test fallback when redis is disabled in config
        disabled_cfg = {"enabled": False}
        redis_cache.set_json(disabled_cfg, "cache:test:key", {"data": 123})
        res = redis_cache.get_json(disabled_cfg, "cache:test:key")
        self.assertIsNone(res)

    def _make_audio_file(self, name="trash_test_song.mp3", content=b"ID3fakeaudiodata0123456789"):
        d = tempfile.mkdtemp(prefix="music_src_")
        path = os.path.join(d, name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_delete_song_moves_to_trash_and_records_metadata(self):
        path = self._make_audio_file()
        expected_size = os.path.getsize(path)

        result = song_repo.delete_song(path)
        self.assertEqual(result.get("status"), "success")
        self.assertFalse(os.path.exists(path))

        records = deleted_repo.get_deleted_songs()
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["filepath"], os.path.abspath(path))
        self.assertEqual(rec["filename"], "trash_test_song.mp3")
        self.assertEqual(rec["size_bytes"], expected_size)
        self.assertTrue(rec["file_created_at"])
        self.assertTrue(rec["file_modified_at"])
        self.assertTrue(rec["deleted_at"])
        self.assertTrue(os.path.isfile(rec["tmp_path"]))
        self.assertTrue(rec["tmp_path"].startswith(self.trash_dir))
        # Optional metadata columns must exist even when extractor yields nothing.
        for key in ("bitrate_kbps", "sample_rate_hz", "codec"):
            self.assertIn(key, rec)

    def test_restore_deleted_song(self):
        path = self._make_audio_file("restore_me.mp3")
        with open(path, "rb") as f:
            orig_bytes = f.read()

        song_repo.delete_song(path)
        records = deleted_repo.get_deleted_songs()
        self.assertEqual(len(records), 1)
        rec = records[0]

        res = deleted_repo.restore_deleted_song(rec["id"])
        self.assertEqual(res.get("status"), "success")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), orig_bytes)
        self.assertFalse(os.path.isfile(rec["tmp_path"]))
        self.assertEqual(len(deleted_repo.get_deleted_songs()), 0)

    def test_clear_deleted_history(self):
        p1 = self._make_audio_file("clear_one.mp3")
        p2 = self._make_audio_file("clear_two.mp3")
        song_repo.delete_song(p1)
        song_repo.delete_song(p2)

        records = deleted_repo.get_deleted_songs()
        self.assertEqual(len(records), 2)
        tmp_paths = [r["tmp_path"] for r in records]

        res = deleted_repo.clear_deleted_history()
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("removed"), 2)
        self.assertEqual(len(deleted_repo.get_deleted_songs()), 0)
        for tp in tmp_paths:
            self.assertFalse(os.path.isfile(tp))

    def test_delete_nonexistent_song_returns_error(self):
        result = song_repo.delete_song("/tmp/does_not_exist_12345.mp3")
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("code"), 404)
        self.assertEqual(len(deleted_repo.get_deleted_songs()), 0)

    def test_restore_missing_record_returns_404(self):
        res = deleted_repo.restore_deleted_song(999999)
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("code"), 404)

    def test_delete_songs_batch(self):
        p1 = self._make_audio_file("batch_one.mp3")
        p2 = self._make_audio_file("batch_two.mp3")
        p3 = self._make_audio_file("batch_three.mp3")

        res = song_repo.delete_songs_batch([p1, p2, "/tmp/missing_fake.mp3"])
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("deleted_count"), 2)
        self.assertEqual(len(res.get("failed", [])), 1)

        self.assertFalse(os.path.exists(p1))
        self.assertFalse(os.path.exists(p2))
        self.assertTrue(os.path.exists(p3))

        records = deleted_repo.get_deleted_songs()
        self.assertEqual(len(records), 2)

        # Clean up p3
        song_repo.delete_song(p3)

    def test_device_repo_batch_delete_local(self):
        p1 = self._make_audio_file("dev_batch_one.mp3")
        p2 = self._make_audio_file("dev_batch_two.mp3")

        res = device_repo.delete_device_songs_batch("local", [p1, p2])
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("deleted_count"), 2)
        self.assertFalse(os.path.exists(p1))
        self.assertFalse(os.path.exists(p2))

    def test_concurrent_get_all_songs_does_not_return_empty(self):
        """
        Verify that concurrent calls to get_all_songs serialize on _scan_lock,
        broadcast progress to all active listeners, and never return an empty list
        when a scan is actively running.
        """
        song_repo.invalidate_all_song_caches()
        mock_songs = [
            {"_id": 1, "title": "Song A", "artist": "Artist A", "filepath": "/fake/a.mp3"},
            {"_id": 2, "title": "Song B", "artist": "Artist B", "filepath": "/fake/b.mp3"},
        ]
        scan_call_count = 0
        scan_lock = threading.Lock()

        def slow_scan(folders, audio_exts, progress_cb=None):
            nonlocal scan_call_count
            with scan_lock:
                scan_call_count += 1
            if progress_cb:
                progress_cb("[SCAN] file 1")
                time.sleep(0.05)
                progress_cb("[SCAN] file 2")
                time.sleep(0.05)
            return list(mock_songs)

        results = {}
        progress_logs = {"thread1": [], "thread2": [], "thread3": []}

        def worker(thread_id, force_refresh, delay=0.0):
            if delay:
                time.sleep(delay)
            cb = lambda msg: progress_logs[thread_id].append(msg)
            res = song_repo.get_all_songs(force_refresh=force_refresh, progress_cb=cb)
            results[thread_id] = res

        with patch("over_ip.song_scanner.scan_songs_from_paths", side_effect=slow_scan):
            t1 = threading.Thread(target=worker, args=("thread1", False, 0.0))
            t2 = threading.Thread(target=worker, args=("thread2", False, 0.02))
            t3 = threading.Thread(target=worker, args=("thread3", True, 0.04))

            t1.start()
            t2.start()
            t3.start()

            t1.join()
            t2.join()
            t3.join()

        # All threads must receive the songs — NONE should receive []
        self.assertEqual(len(results["thread1"]), 2)
        self.assertEqual(len(results["thread2"]), 2)
        self.assertEqual(len(results["thread3"]), 2)

        # scan_songs_from_paths should have run only once
        self.assertEqual(scan_call_count, 1)

        # Listeners registered while scan was active should receive progress messages
        self.assertTrue(len(progress_logs["thread1"]) > 0)
        self.assertTrue(len(progress_logs["thread2"]) > 0)

    def test_cache_reuse_within_grace_period(self):
        """
        Verify that a force_refresh=True call immediately following a scan
        reuses the newly scanned data without triggering a second disk scan.
        """
        song_repo.invalidate_all_song_caches()
        mock_songs = [{"_id": 1, "title": "Song 1", "filepath": "/fake/1.mp3"}]
        scan_call_count = 0

        def quick_scan(folders, audio_exts, progress_cb=None):
            nonlocal scan_call_count
            scan_call_count += 1
            return list(mock_songs)

        with patch("over_ip.song_scanner.scan_songs_from_paths", side_effect=quick_scan):
            # First scan
            res1 = song_repo.get_all_songs(force_refresh=True)
            self.assertEqual(len(res1), 1)
            self.assertEqual(scan_call_count, 1)

            # Immediate second call with force_refresh within 5 seconds
            res2 = song_repo.get_all_songs(force_refresh=True)
            self.assertEqual(len(res2), 1)
            # Should NOT have invoked quick_scan again
            self.assertEqual(scan_call_count, 1)

            # Invalidate cache
            song_repo.invalidate_all_song_caches()

            # Now force_refresh must trigger a fresh scan
            res3 = song_repo.get_all_songs(force_refresh=True)
            self.assertEqual(len(res3), 1)
            self.assertEqual(scan_call_count, 2)


if __name__ == "__main__":
    unittest.main()
