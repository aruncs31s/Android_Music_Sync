"""
Utils package for Antigravity Music Manager.
Provides SingletonLogger and logging utilities.
"""
from utils.singleton_logger import get_logger, configure_logger, LoggerConfig

__all__ = ["get_logger", "configure_logger", "LoggerConfig"]
