import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlaylistRecord:
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[str] = None
    track_count: int = 0
    present_count: int = 0
    absent_count: int = 0


@dataclass
class PlaylistTrackRecord:
    playlist_id: int
    filepath: str
    id: Optional[int] = None
    original_path: Optional[str] = None
    filename: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    readable_name: Optional[str] = None
    status: str = "present"  # "present" or "absent"
    track_order: int = 0
    added_at: Optional[str] = None
    duration_formatted: Optional[str] = None
    size_formatted: Optional[str] = None

    def __post_init__(self):
        if not self.filename:
            self.filename = os.path.basename(self.filepath) if self.filepath else (self.readable_name or "Unknown")
        if not self.title:
            self.title = self.readable_name or self.filename
        if not self.original_path:
            self.original_path = self.filepath
