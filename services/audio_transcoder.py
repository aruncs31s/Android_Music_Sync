"""
Audio Transcoder Service for high-fidelity audio downconversion.
Uses FFmpeg to transcode high-bitrate audio (e.g. 320 kbps MP3 / FLAC) to space-saving bitrates
(128 kbps, 192 kbps, 256 kbps) while strictly preserving ID3 tags and metadata (SRP / DIP).
"""
import os
import shutil
import tempfile
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Tuple, Generator
from utils import audio_metadata
from utils import get_logger
import model

logger = get_logger()



from model.transcoder import TranscodeResult


class AudioTranscoder:
    """
    Handles audio bitrate detection and downconversion with metadata preservation.
    """

    SUPPORTED_TARGET_BITRATES = [128, 192, 256, 320]

    @classmethod
    def is_ffmpeg_available(cls) -> bool:
        """Check if ffmpeg executable is available in PATH."""
        return shutil.which("ffmpeg") is not None

    @classmethod
    def detect_bitrate(cls, filepath: str) -> int |None:
        """
        Extract numeric audio bitrate in kbps.
        Returns integer kbps (e.g. 320, 256, 128) or 999 for lossless FLAC/WAV.
        """
        if not os.path.exists(filepath):
            return None

        ext = os.path.splitext(filepath)[1].lower()
        if ext in (".flac", ".wav", ".alac"):
            # Lossless formats are effectively higher quality than any MP3
            return 999

        try:
            meta = audio_metadata.extract_audio_metadata(filepath)
            raw_br = meta.get("bitrate") or ""
            if isinstance(raw_br, str):
                digits = "".join(ch for ch in raw_br if ch.isdigit())
                if digits:
                    return int(digits)
            elif isinstance(raw_br, (int, float)):
                return int(raw_br)
        except Exception as e:
            logger.debug(f"[AudioTranscoder] Metadata extraction note for {filepath}: {e}")

        # Fallback to ffprobe if available
        if shutil.which("ffprobe"):
            try:
                out = subprocess.check_output(
                    [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=bit_rate",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        filepath
                    ],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=3.0
                ).strip()
                if out.isdigit():
                    return int(out) // 1000
            except Exception:
                pass

        return None

    @classmethod
    def needs_downconversion(cls, input_path: str, target_bitrate_kbps: Optional[int]) -> bool:
        """
        Determine whether downconversion is warranted:
        - target_bitrate_kbps must be specified and > 0.
        - Source bitrate must be greater than target_bitrate_kbps (or lossless).
        """
        if not target_bitrate_kbps or target_bitrate_kbps <= 0:
            return False

        current_br = cls.detect_bitrate(input_path)
        if current_br is None:
            # Cannot determine bitrate — if target is 128 or 192, allow transcode
            return target_bitrate_kbps <= 192

        # Lossless or strictly higher bitrate warrants downconversion
        return current_br > target_bitrate_kbps

    @classmethod
    def transcode_audio(
        cls,
        input_path: str,
        target_bitrate_kbps: int,
        output_path: str |None = None
    ) -> model.TranscodeResult:
        """
        Transcode an audio file to target bitrate MP3 using ffmpeg.
        Preserves all metadata (-map_metadata 0).
        """
        if not os.path.exists(input_path):
            return model.TranscodeResult(
                success=False,
                output_path="",
                original_path=input_path,
                error=f"Input file not found: {input_path}"
            )

        if not cls.is_ffmpeg_available():
            return model.TranscodeResult(
                success=False,
                output_path=input_path,
                original_path=input_path,
                error="ffmpeg executable not found in PATH"
            )

        orig_size = os.path.getsize(input_path)
        orig_br = cls.detect_bitrate(input_path)

        # Determine output path
        created_temp = False
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            output_path = tmp.name
            tmp.close()
            created_temp = True

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vn",
            "-map_metadata", "0",
            "-c:a", "libmp3lame",
            "-b:a", f"{int(target_bitrate_kbps)}k",
            output_path
        ]

        logger.info(f"[AudioTranscoder] Downconverting '{os.path.basename(input_path)}' ({orig_br or 'unknown'} kbps -> {target_bitrate_kbps} kbps)...")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60.0)
            if res.returncode != 0:
                if created_temp and os.path.exists(output_path):
                    os.remove(output_path)
                logger.error(f"[AudioTranscoder] ffmpeg error: {res.stderr}")
                return TranscodeResult(
                    success=False,
                    output_path="",
                    original_path=input_path,
                    original_bitrate=orig_br,
                    target_bitrate=target_bitrate_kbps,
                    original_size=orig_size,
                    error=res.stderr.strip() or "ffmpeg transcode failed"
                )

            new_size = os.path.getsize(output_path)
            logger.info(f"[AudioTranscoder] Complete: {orig_size} bytes -> {new_size} bytes ({round(new_size/1024/1024, 2)} MB)")
            return TranscodeResult(
                success=True,
                output_path=output_path,
                original_path=input_path,
                original_bitrate=orig_br,
                target_bitrate=target_bitrate_kbps,
                original_size=orig_size,
                new_size=new_size
            )
        except Exception as e:
            if created_temp and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            logger.error(f"[AudioTranscoder] Transcode exception: {e}")
            return TranscodeResult(
                success=False,
                output_path="",
                original_path=input_path,
                original_bitrate=orig_br,
                target_bitrate=target_bitrate_kbps,
                original_size=orig_size,
                error=str(e)
            )

    @classmethod
    @contextmanager
    def managed_transcode(
        cls,
        input_path: str,
        target_bitrate_kbps: Optional[int]
    ) -> Generator[Tuple[str, bool], None, None]:
        """
        Context manager that yields (filepath_to_send, was_transcoded).
        If downconversion was performed, automatically deletes the temporary file upon exit.
        """
        if not target_bitrate_kbps or not cls.needs_downconversion(input_path, target_bitrate_kbps):
            # No transcoding needed — use original directly
            yield input_path, False
            return

        result = cls.transcode_audio(input_path, target_bitrate_kbps)
        if not result.success:
            logger.warning(f"[AudioTranscoder] Downconversion failed ({result.error}), falling back to original file.")
            yield input_path, False
            return

        temp_path = result.output_path
        try:
            yield temp_path, True
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"[AudioTranscoder] Cleaned up temporary transcode file: {temp_path}")
                except Exception as e:
                    logger.warning(f"[AudioTranscoder] Failed to remove temp file {temp_path}: {e}")
