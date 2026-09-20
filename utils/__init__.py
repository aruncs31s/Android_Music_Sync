"""
Utils package for Antigravity Music Manager.
Provides SingletonLogger and logging utilities.
"""

from utils.singleton_logger import LoggerConfig, configure_logger, get_logger
from utils.string import normalize_string, clean_string_for_matching, sanitize_filename
from utils.time import format_ts, format_duration, format_size

__all__ = [
    "get_logger",
    "configure_logger",
    "LoggerConfig",
    "normalize_string",
    "clean_string_for_matching",
    "sanitize_filename",
    "format_ts",
    "format_duration",
    "format_size",
]
