"""
Unit tests for AudioTranscoder service and downconversion logic.
"""
import os
import sys
import subprocess
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.audio_transcoder import AudioTranscoder


class TestAudioTranscoder(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="transcode_test_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_mp3(self, name: str = "test_320k.mp3", bitrate_kbps: int = 320) -> str:
        out_path = os.path.join(self.temp_dir, name)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=440:duration=1.5",
            "-metadata", "title=Synthetic Test Track",
            "-metadata", "artist=Test Artist",
            "-metadata", "album=Test Album",
            "-c:a", "libmp3lame",
            "-b:a", f"{bitrate_kbps}k",
            out_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path

    def test_ffmpeg_availability(self):
        self.assertTrue(AudioTranscoder.is_ffmpeg_available())

    def test_detect_bitrate(self):
        mp3_320 = self._create_synthetic_mp3("sine_320.mp3", bitrate_kbps=320)
        br = AudioTranscoder.detect_bitrate(mp3_320)
        self.assertIsNotNone(br)
        self.assertEqual(br, 320)

    def test_needs_downconversion(self):
        mp3_320 = self._create_synthetic_mp3("sine_320.mp3", bitrate_kbps=320)
        # Needs downconversion when target < 320
        self.assertTrue(AudioTranscoder.needs_downconversion(mp3_320, 128))
        self.assertTrue(AudioTranscoder.needs_downconversion(mp3_320, 192))
        self.assertTrue(AudioTranscoder.needs_downconversion(mp3_320, 256))

        # Does NOT need downconversion when target >= 320
        self.assertFalse(AudioTranscoder.needs_downconversion(mp3_320, 320))
        self.assertFalse(AudioTranscoder.needs_downconversion(mp3_320, 0))
        self.assertFalse(AudioTranscoder.needs_downconversion(mp3_320, None))

    def test_transcode_320k_to_128k(self):
        mp3_320 = self._create_synthetic_mp3("source_320.mp3", bitrate_kbps=320)
        orig_size = os.path.getsize(mp3_320)

        dst_path = os.path.join(self.temp_dir, "downconverted_128k.mp3")
        res = AudioTranscoder.transcode_audio(mp3_320, target_bitrate_kbps=128, output_path=dst_path)

        self.assertTrue(res.success)
        self.assertTrue(os.path.isfile(dst_path))
        self.assertEqual(res.target_bitrate, 128)
        self.assertLess(res.new_size, orig_size)

        new_br = AudioTranscoder.detect_bitrate(dst_path)
        self.assertEqual(new_br, 128)

    def test_managed_transcode_context_manager_cleans_up(self):
        mp3_320 = self._create_synthetic_mp3("source_320.mp3", bitrate_kbps=320)

        temp_created = None
        with AudioTranscoder.managed_transcode(mp3_320, target_bitrate_kbps=192) as (path, transcoded):
            self.assertTrue(transcoded)
            self.assertTrue(os.path.isfile(path))
            self.assertNotEqual(path, mp3_320)
            temp_created = path

        # Must be deleted after exiting context manager
        self.assertFalse(os.path.exists(temp_created))


if __name__ == "__main__":
    unittest.main()
