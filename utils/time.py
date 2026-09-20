import datetime
from typing import Optional, Union, Any


def format_ts(ts_val: Any, default: str = "") -> str:
    """Format Unix timestamp in seconds to 'YYYY-MM-DD HH:MM:SS' format."""
    if not ts_val or str(ts_val).strip() in ("NULL", "None", ""):
        return default
    try:
        ts = float(ts_val)
        if ts <= 0:
            return default
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return default


def format_duration(duration_val: Optional[Union[int, float, str]], is_ms: bool = False) -> str:
    """
    Format duration to 'MM:SS' or 'HH:MM:SS' format.
    Accepts duration in seconds or milliseconds (when is_ms=True).
    """
    if not duration_val or str(duration_val).strip() in ("NULL", "None", ""):
        return "00:00"
    try:
        val = float(duration_val)
        total_seconds = int(val // 1000) if is_ms else int(val)
        if total_seconds <= 0:
            return "00:00"

        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "00:00"


def format_size(bytes_val: Optional[Union[int, float, str]]) -> str:
    """Format size in bytes to human-readable string (B, KB, MB, GB)."""
    if not bytes_val or str(bytes_val).strip() in ("NULL", "None", ""):
        return "0 B"
    try:
        b = float(bytes_val)
        if b <= 0:
            return "0 B"
        if b < 1024:
            return f"{int(b)} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        else:
            return f"{b / (1024 * 1024 * 1024):.2f} GB"
    except (ValueError, TypeError):
        return "0 B"
