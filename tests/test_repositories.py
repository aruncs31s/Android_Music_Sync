import os
import sys
import unittest
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config_manager
import database.db_manager as db_manager
import redis_cache
from repositories import song_repo, playlist_repo, hide_repo, device_repo


class TestRepositories(unittest.TestCase):

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)

        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path

        # Clear test cache keys
        self.cfg = config_manager.load_config()
        self.redis_cfg = self.cfg.get("redis")
        if self.redis_cfg:
            redis_cache.delete_cache_pattern(self.redis_cfg, "cache:*")

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        if self.redis_cfg:
            redis_cache.delete_cache_pattern(self.redis_cfg, "cache:*")
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    def test_playlist_repository_crud_and_invalidation(self):
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

    def test_redis_disabled_fallback(self):
        # Test fallback when redis is disabled in config
        disabled_cfg = {"enabled": False}
        redis_cache.set_json(disabled_cfg, "cache:test:key", {"data": 123})
        res = redis_cache.get_json(disabled_cfg, "cache:test:key")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
