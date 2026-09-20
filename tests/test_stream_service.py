"""
Unit tests for StreamService (RFC 7233 range streaming & Over-IP proxy).
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.stream_service import StreamService


class TestStreamService(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.tmp.write(b"0123456789" * 100) # 1000 bytes
        self.tmp.close()

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_stream_local_file_full(self):
        resp = StreamService.stream_local_file(self.tmp.name)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Content-Length"), "1000")
        self.assertEqual(resp.headers.get("Accept-Ranges"), "bytes")
        data = b"".join(resp.response)
        self.assertEqual(len(data), 1000)

    def test_stream_local_file_range_partial(self):
        # Range: bytes=0-99 (first 100 bytes)
        resp = StreamService.stream_local_file(self.tmp.name, range_header="bytes=0-99")
        self.assertEqual(resp.status_code, 206)
        self.assertEqual(resp.headers.get("Content-Range"), "bytes 0-99/1000")
        self.assertEqual(resp.headers.get("Content-Length"), "100")
        data = b"".join(resp.response)
        self.assertEqual(len(data), 100)
        self.assertEqual(data, b"0123456789" * 10)

    def test_stream_local_file_not_found(self):
        resp = StreamService.stream_local_file("/tmp/nonexistent_song_123.mp3")
        self.assertEqual(resp.status_code, 404)

    @patch("device_providers.over_ip_provider.OverIpDeviceProvider.stream_song")
    def test_stream_remote_peer_proxy(self, mock_stream):
        mock_req = MagicMock()
        mock_req.iter_content.return_value = [b"STREAM_CHUNK_1", b"STREAM_CHUNK_2"]
        mock_stream.return_value = (
            mock_req,
            200,
            {"Content-Type": "audio/mpeg", "Content-Length": "28"}
        )

        resp = StreamService.stream_remote_peer("ip_192.168.1.55", "/sdcard/song.mp3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Content-Type"), "audio/mpeg")
        self.assertEqual(resp.headers.get("Content-Length"), "28")
        data = b"".join(resp.response)
        self.assertEqual(data, b"STREAM_CHUNK_1STREAM_CHUNK_2")


if __name__ == "__main__":
    unittest.main()
