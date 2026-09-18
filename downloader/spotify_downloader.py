"""
Spotify & Search Query Direct Audio Downloader powered by yt-dlp.
Downloads high quality audio and embeds metadata into songs/download/ directory.
"""
import os
import re
import subprocess
import shutil
from typing import Optional, Dict, Any

from utils import get_logger
logger = get_logger()

SPOTIFY_URL_REGEX = re.compile(r"https?://(?:open\.)?spotify\.(?:com|link)/(?:track|album|playlist|artist)/[a-zA-Z0-9]+")

def is_spotify_url(text: str) -> bool:
    """Check if text is a Spotify track/album/playlist URL."""
    return bool(SPOTIFY_URL_REGEX.search(text))

def download_audio(query_or_url: str, output_dir: str = "songs/download") -> Optional[str]:
    """
    Download audio from Spotify URL or search query using yt-dlp.
    Saves file to output_dir (default: songs/download/).
    Returns path of downloaded file or None on failure.
    """
    if not shutil.which("yt-dlp"):
        raise RuntimeError("yt-dlp is required for downloading audio. Please install yt-dlp.")

    os.makedirs(output_dir, exist_ok=True)

    # Output template: songs/download/%(title)s.%(ext)s
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", output_template,
        "--no-playlist",
        "--embed-thumbnail",
        "--add-metadata",
        "--no-overwrites"
    ]

    if is_spotify_url(query_or_url):
        logger.info(f"[SpotifyDownloader] Detected Spotify link: {query_or_url}")
        cmd.append(query_or_url)
    else:
        # Search query fallback (ytsearch)
        logger.info(f"[SpotifyDownloader] Searching and downloading audio for: {query_or_url}")
        cmd.append(f"ytsearch1:{query_or_url}")

    logger.info(f"[SpotifyDownloader] Downloading to: {os.path.abspath(output_dir)} ...")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse output line for file path
        output_lines = res.stdout.splitlines()
        downloaded_file = None

        for line in output_lines:
            if "[ExtractAudio] Destination:" in line:
                downloaded_file = line.split("[ExtractAudio] Destination:", 1)[1].strip()
            elif "[download]" in line and "has already been downloaded" in line:
                file_part = line.split("[download]", 1)[1].split("has already been downloaded")[0].strip()
                downloaded_file = file_part

        if not downloaded_file:
            # Fallback: scan output_dir for most recently modified file
            files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith((".mp3", ".m4a", ".flac", ".ogg"))]
            if files:
                downloaded_file = max(files, key=os.path.getmtime)

        if downloaded_file and os.path.exists(downloaded_file):
            logger.info(f"[SpotifyDownloader] Download complete: {downloaded_file}")
            return os.path.abspath(downloaded_file)

        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"[SpotifyDownloader] Error during audio download: {e.stderr or e.stdout}")
        return None
