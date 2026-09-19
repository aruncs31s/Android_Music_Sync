import unittest
import json
import os
import io
from unittest.mock import patch, MagicMock
from ui.server import app
from services.audio_transcoder import TranscodeResult


class TestUiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_transcode_endpoint_missing_params(self):
        res = self.client.post('/api/song/transcode', json={})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("error", data)

    def test_transcode_endpoint_file_not_found(self):
        res = self.client.post('/api/song/transcode', json={
            "filepath": "/tmp/non_existent_audio_xyz_123.mp3",
            "target_bitrate": 192
        })
        self.assertEqual(res.status_code, 404)

    @patch("services.audio_transcoder.AudioTranscoder.transcode_audio")
    @patch("repositories.song_repo.invalidate_all_song_caches")
    @patch("os.path.exists", return_value=True)
    def test_transcode_endpoint_success(self, mock_exists, mock_invalidate, mock_transcode):
        mock_transcode.return_value = TranscodeResult(
            success=True,
            output_path="/tmp/test_192k.mp3",
            original_path="/tmp/test.mp3",
            target_bitrate=192
        )
        res = self.client.post('/api/song/transcode', json={
            "filepath": "/tmp/test.mp3",
            "target_bitrate": 192,
            "replace_original": False
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["output_path"], "/tmp/test_192k.mp3")

    @patch("repositories.device_repo.push_song_to_device")
    def test_upload_to_device_endpoint(self, mock_push_song):
        mock_push_song.return_value = {
            "status": "success",
            "message": "Uploaded successfully"
        }

        data = {
            'target_bitrate': 'original',
            'files': (io.BytesIO(b"fake audio data"), "test.mp3")
        }
        res = self.client.post(
            '/api/devices/ip_192.168.1.50/upload',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 200)
        resp_data = json.loads(res.data)
        self.assertEqual(resp_data["status"], "success")
        self.assertEqual(resp_data["uploaded"], 1)

    @patch("services.stream_service.StreamService.stream_remote_peer")
    def test_stream_over_ip_proxy_routing(self, mock_stream_remote):
        from flask import Response
        mock_stream_remote.return_value = Response("audio stream", status=200, mimetype="audio/mpeg")

        res = self.client.get('/api/song/stream?filepath=/sdcard/Music/test.mp3&device_id=ip_192.168.1.75')
        self.assertEqual(res.status_code, 200)
        mock_stream_remote.assert_called_once_with('ip_192.168.1.75', '/sdcard/Music/test.mp3', range_header=None)


if __name__ == '__main__':
    unittest.main()
