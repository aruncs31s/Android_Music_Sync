"""
Download Manager coordinating song downloads to songs/download/ directory.
Supports direct Spotify/yt-dlp engine, Telegram Deezload bot automation,
and post-download ADB push & duplicate detection.
"""
import os
import sys
from typing import Optional

from . import spotify_downloader
from . import telegram_deezload
import adb_pusher

DEFAULT_DOWNLOAD_DIR = "songs/download"

class DownloadManager:
    def __init__(
        self,
        output_dir: str = DEFAULT_DOWNLOAD_DIR,
        use_telegram: bool = False,
        device_serial: Optional[str] = None,
        auto_push_adb: Optional[bool] = None
    ):
        self.output_dir = output_dir
        self.use_telegram = use_telegram
        self.device_serial = device_serial
        self.auto_push_adb = auto_push_adb
        os.makedirs(self.output_dir, exist_ok=True)

    def download(self, query_or_url: str) -> Optional[str]:
        """
        Download song from Spotify URL or query and save to output_dir (songs/download/).
        Post-download: Check ADB duplicate, ask user, verify remote folder, and push to device.
        """
        print(f"\n[DownloadManager] Starting download for: {query_or_url}", file=sys.stderr)
        print(f"[DownloadManager] Target directory: {os.path.abspath(self.output_dir)}", file=sys.stderr)

        file_path = None

        # Try Telegram Deezload if requested or if TELEGRAM_API_ID is present
        if self.use_telegram or os.getenv("TELEGRAM_API_ID"):
            if spotify_downloader.is_spotify_url(query_or_url):
                print("[DownloadManager] Attempting download via Telegram Deezload bot...", file=sys.stderr)
                file_path = telegram_deezload.download_via_deezload(query_or_url, output_dir=self.output_dir)

        # Direct engine fallback (yt-dlp)
        if not file_path:
            print("[DownloadManager] Downloading via Direct Engine (yt-dlp)...", file=sys.stderr)
            file_path = spotify_downloader.download_audio(query_or_url, output_dir=self.output_dir)

        if file_path:
            print(f"[DownloadManager] Successfully saved to: {file_path}", file=sys.stderr)
            # Post-download ADB push & duplicate check workflow
            adb_pusher.handle_post_download_adb_workflow(
                local_filepath=file_path,
                device_serial=self.device_serial,
                auto_confirm=self.auto_push_adb
            )
        else:
            print("[DownloadManager] Download failed.", file=sys.stderr)

        return file_path
