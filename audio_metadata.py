"""
Audio Metadata Extractor Module.

Extracts technical audio properties (Bit Rate, Sample Rate, Channels, Codec, Duration, File Size)
using mutagen with ffprobe fallback.
"""
import os
import sys
import subprocess
from typing import Dict, Any, Optional

METADATA_CACHE: Dict[str, Dict[str, Any]] = {}


def extract_audio_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extract technical metadata from local audio file.
    Returns dictionary with bitrate, sample_rate, channels, codec, duration, size.
    """
    if not filepath or not os.path.exists(filepath):
        return {
            "bitrate": "Unknown",
            "sample_rate": "Unknown",
            "channels": "Unknown",
            "codec": "Unknown",
            "duration": "00:00",
            "size": "0 B"
        }

    abs_path = os.path.abspath(filepath)
    if abs_path in METADATA_CACHE:
        return METADATA_CACHE[abs_path]

    meta = {
        "bitrate": "Unknown",
        "sample_rate": "Unknown",
        "channels": "2 ch (Stereo)",
        "codec": os.path.splitext(filepath)[1].replace(".", "").upper(),
        "duration": "00:00",
        "size": "0 B"
    }

    # Size
    try:
        size_bytes = os.path.getsize(abs_path)
        size_mb = size_bytes / (1024 * 1024)
        meta["size"] = f"{size_mb:.1f} MB"
    except OSError:
        pass

    # Try mutagen first
    try:
        import mutagen
        audio = mutagen.File(abs_path)
        if audio and hasattr(audio, "info") and audio.info:
            info = audio.info

            # Bitrate
            bitrate_bps = getattr(info, "bitrate", None)
            if bitrate_bps and bitrate_bps > 0:
                bitrate_kbps = bitrate_bps // 1000
                meta["bitrate"] = f"{bitrate_kbps} kbps"

            # Sample Rate
            sr = getattr(info, "sample_rate", None)
            if sr and sr > 0:
                sr_khz = sr / 1000.0
                meta["sample_rate"] = f"{sr_khz:.1f} kHz ({sr} Hz)"

            # Channels
            ch = getattr(info, "channels", None)
            if ch:
                if ch == 1:
                    meta["channels"] = "1 ch (Mono)"
                elif ch == 2:
                    meta["channels"] = "2 ch (Stereo)"
                else:
                    meta["channels"] = f"{ch} channels"

            # Duration
            length_sec = getattr(info, "length", None)
            if length_sec:
                mins = int(length_sec) // 60
                secs = int(length_sec) % 60
                meta["duration"] = f"{mins:02d}:{secs:02d}"

            METADATA_CACHE[abs_path] = meta
            return meta
    except Exception:
        pass

    # Fallback to ffprobe
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_name,sample_rate,channels,bit_rate:format=duration,size",
            "-of", "default=noprint_wrappers=1:nokey=1", abs_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        if len(lines) >= 4:
            meta["codec"] = lines[0].upper()
            try:
                sr = int(lines[1])
                meta["sample_rate"] = f"{sr / 1000.0:.1f} kHz ({sr} Hz)"
            except ValueError:
                pass
            try:
                ch = int(lines[2])
                meta["channels"] = "Mono" if ch == 1 else "Stereo"
            except ValueError:
                pass
            try:
                br = int(lines[3]) // 1000
                meta["bitrate"] = f"{br} kbps"
            except ValueError:
                pass
    except Exception:
        pass

    METADATA_CACHE[abs_path] = meta
    return meta
