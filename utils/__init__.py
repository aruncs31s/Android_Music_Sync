"""
Utils package for Antigravity Music Manager.
Provides SingletonLogger and logging utilities.
"""

from utils.singleton_logger import LoggerConfig, configure_logger, get_logger
from utils.string import normalize_string
from utils.time import format_ts

__all__ = [
    "get_logger",
    "configure_logger",
    "LoggerConfig",
    "normalize_string",
    "format_ts",
]
