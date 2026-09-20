from dataclasses import dataclass

@dataclass
class TranscodeResult:
    """Result of an audio transcode operation."""
    success: bool
    output_path: str
    original_path: str
    original_bitrate: int|None = None
    target_bitrate: int | None = None
    original_size: int = 0
    new_size: int = 0
    error: str | None = None
