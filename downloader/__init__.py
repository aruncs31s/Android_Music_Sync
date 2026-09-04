"""
Downloader package for retrieving songs from Spotify links, Telegram Deezload bot, or search queries.
All downloaded files are saved into songs/download/ directory by default.
"""

from .manager import DownloadManager

__all__ = ["DownloadManager"]
