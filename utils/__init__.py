"""
Utils package for Antigravity Music Manager.
Provides SingletonLogger and logging utilities.
"""

from utils.singleton_logger import LoggerConfig, configure_logger, get_logger
from utils.string import normalize_string, clean_string_for_matching, sanitize_filename
from utils.time import format_ts, format_duration, format_size
import utils.config_manager as config_manager
import utils.fuzzy_matcher as fuzzy_matcher
import utils.audio_metadata as audio_metadata
import utils.audio_fingerprint as audio_fingerprint

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
    "config_manager",
    "fuzzy_matcher",
    "audio_metadata",
    "audio_fingerprint",
]

