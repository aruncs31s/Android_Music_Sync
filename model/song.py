import os
from dataclasses import dataclass

from model.base import DictLikeRecord


@dataclass
class SongRecord(DictLikeRecord):
    filepath: str
    filename: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    bitrate_kbps: int | None = None
    sample_rate_hz: int | None = None
    codec: str | None = None
    size_bytes: int | None = None
    file_created_at: str | None = None
    file_modified_at: str | None = None
    tmp_path: str | None = None

    def __post_init__(self):
        # Ensure that the filepath is absolute
        self.filepath = os.path.abspath(self.filepath)
        self.filename = os.path.basename(self.filepath)


@dataclass
class RestoredSongRecord(SongRecord):
    duration_sec: float | None = None
    duration_formatted: str | None = None
    size_formatted: str | None = None
    bitrate_val: int | None = None
    channels: str | None = None
    searchable_text: str | None = None

    def __post_init__(self):
        super().__post_init__()
