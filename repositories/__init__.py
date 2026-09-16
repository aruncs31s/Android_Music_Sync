"""
Repositories package initializing and exporting Repository singletons.
"""
from repositories.song_repository import SongRepository
from repositories.playlist_repository import PlaylistRepository
from repositories.hide_list_repository import HideListRepository
from repositories.device_repository import DeviceRepository
from repositories.deleted_song_repository import DeletedSongRepository

# Export singleton instances
song_repo = SongRepository()
playlist_repo = PlaylistRepository()
hide_repo = HideListRepository()
device_repo = DeviceRepository()
deleted_repo = DeletedSongRepository()

__all__ = [
    "SongRepository",
    "PlaylistRepository",
    "HideListRepository",
    "DeviceRepository",
    "DeletedSongRepository",
    "song_repo",
    "playlist_repo",
    "hide_repo",
    "device_repo",
    "deleted_repo",
]
