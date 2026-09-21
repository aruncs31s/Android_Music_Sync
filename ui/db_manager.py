"""
Web UI Database Manager Module.
Delegates to centralized database database/db.db (database.db_manager).
Shared by Web UI and TUI modules.
"""
from typing import List, Dict, Any, Optional, Set
import database.db_manager as central_db
from model.song import RestoredSongRecord, SongRecord


def get_ui_db_path() -> str:
    return central_db.get_central_db_path()


def get_connection(db_path: Optional[str] = None):
    return central_db.get_connection(db_path)


def add_hidden_file(filepath: str, filename: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_hidden_file(filepath, filename, db_path)


def remove_hidden_file(filepath: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_hidden_file(filepath, db_path)


def get_all_hidden_records(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_hidden_records(db_path)


def get_hidden_paths_set(db_path: Optional[str] = None) -> Set[str]:
    return central_db.get_hidden_paths_set(db_path)


def add_synced_file(filepath: str, filename: str, device_serial: str, remote_dir: str = "", db_path: Optional[str] = None) -> bool:
    return central_db.add_synced_file(filepath, filename, device_serial, remote_dir, db_path)


def get_all_synced_records(device_serial: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_all_synced_records(device_serial, db_path)


def remove_synced_file(device_serial: str, filename: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_synced_file(device_serial, filename, db_path)



def create_playlist(name: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return central_db.create_playlist(name, db_path)


def delete_playlist(playlist_id: int, db_path: Optional[str] = None) -> bool:
    return central_db.delete_playlist(playlist_id, db_path)


def get_playlists(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_playlists(db_path)


def add_track_to_playlist(
    playlist_id: int,
    filepath: str,
    status: str = "present",
    original_path: Optional[str] = None,
    readable_name: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    db_path: Optional[str] = None
) -> bool:
    return central_db.add_track_to_playlist(
        playlist_id, filepath, status, original_path, readable_name, title, artist, album, db_path
    )


def remove_track_from_playlist(playlist_id: int, filepath: str, db_path: Optional[str] = None) -> bool:
    return central_db.remove_track_from_playlist(playlist_id, filepath, db_path)


def get_playlist_tracks(playlist_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_playlist_tracks(playlist_id, db_path)


def resolve_playlist_track(
    playlist_id: int,
    original_path: str,
    resolved_filepath: str,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    track_id: Optional[int] = None,
    db_path: Optional[str] = None
) -> bool:
    return central_db.resolve_playlist_track(
        playlist_id, original_path, resolved_filepath, title, artist, album, track_id, db_path
    )


def get_playlist_absent_tracks(playlist_id: Optional[int] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_playlist_absent_tracks(playlist_id, db_path)


def get_stored_ip_hosts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_stored_ip_hosts(db_path)


def add_ip_host(ip_address: str, port: int = 5000, alias: str | None = None, song_count: int = 0, db_path: Optional[str] = None) -> bool:
    return central_db.add_ip_host(ip_address, port, alias, song_count, db_path)


save_ip_host = add_ip_host


def remove_ip_host(ip_address: str, db_path: str | None = None) -> bool:
    return central_db.remove_ip_host(ip_address, db_path)


def update_ip_status(ip_address: str, is_online: bool, song_count: Optional[int] = None, db_path: str | None = None) -> bool:
    return central_db.update_ip_status(ip_address, is_online, song_count, db_path)


def add_deleted_song(record: SongRecord, db_path: Optional[str] = None) -> bool:
    return central_db.add_deleted_song(record, db_path)


def get_deleted_songs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_deleted_songs(db_path)


def remove_deleted_song(record_id: int, db_path: Optional[str] = None) -> bool:
    return central_db.remove_deleted_song(record_id, db_path)


def clear_deleted_songs(db_path: Optional[str] = None) -> bool:
    return central_db.clear_deleted_songs(db_path)


def save_local_songs(songs: list[RestoredSongRecord], purge_missing: bool = True, db_path: Optional[str] = None) -> int:
    return central_db.save_local_songs(songs, purge_missing, db_path)


def get_stored_local_songs(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    return central_db.get_stored_local_songs(db_path)


def get_local_songs_count(db_path: Optional[str] = None) -> int:
    return central_db.get_local_songs_count(db_path)


def delete_stored_local_song(filepath: str, db_path: Optional[str] = None) -> bool:
    return central_db.delete_stored_local_song(filepath, db_path)


def delete_stored_local_songs_batch(filepaths: List[str], db_path: Optional[str] = None) -> int:
    return central_db.delete_stored_local_songs_batch(filepaths, db_path)
