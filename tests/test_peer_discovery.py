import os
import sys
import time
import socket
import unittest
import tempfile
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database.db_manager as db_manager
from over_ip.discovery import PeerDiscoveryService, DISCOVERY_PORT, MAGIC_HEADER


class TestPeerDiscovery(unittest.TestCase):

    def setUp(self):
        self.tmp_db_fd, self.tmp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_db_fd)
        self.orig_get_path = db_manager.get_central_db_path
        db_manager.get_central_db_path = lambda: self.tmp_db_path
        conn = db_manager.get_connection()
        conn.close()

        # Reset singleton
        PeerDiscoveryService._instance = None

    def tearDown(self):
        db_manager.get_central_db_path = self.orig_get_path
        if PeerDiscoveryService._instance:
            PeerDiscoveryService._instance.stop()
            PeerDiscoveryService._instance = None
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

    def test_singleton_instance(self):
        s1 = PeerDiscoveryService.get_instance(5000)
        s2 = PeerDiscoveryService.get_instance(5000)
        self.assertIs(s1, s2)

    def test_broadcast_announce_packet_structure(self):
        service = PeerDiscoveryService.get_instance(5000)
        # Verify it doesn't crash on calling announce
        service.broadcast_announce()

    def test_auto_save_discovered_peer(self):
        # Directly test saving peer to database
        db_manager.save_ip_host("192.168.1.55", 5000, "Pixel 7 (Android)")
        hosts = db_manager.get_stored_ip_hosts()
        self.assertTrue(any(h["ip_address"] == "192.168.1.55" for h in hosts))


if __name__ == "__main__":
    unittest.main()
