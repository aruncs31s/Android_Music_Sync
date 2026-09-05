from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from typing import Any, Iterable

try:
    import colorlog

    has_colorlog = True
except ImportError:
    has_colorlog = False


DEFAULT_TEXT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

STANDARD_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


@dataclass
class LoggerConfig:
    name: str = "music-sync"
    level: int | str = logging.INFO
    enable_console: bool = True
    enable_file: bool = True
    file_path: str = "logs/app.log"
    file_mode: str = "a"
    rotate: bool = True
    max_bytes: int = 1_048_576
    backup_count: int = 3
    use_json: bool = False
    text_format: str = DEFAULT_TEXT_FORMAT
    date_format: str = DEFAULT_DATE_FORMAT
    include_fields: list[str] = field(
        default_factory=lambda: ["timestamp", "level", "logger", "message", "extra"]
    )
    allowed_extra_keys: list[str] | None = None
    propagate: bool = False
    use_color: bool = True


class JsonLogFormatter(logging.Formatter):
    def __init__(
        self,
        include_fields: Iterable[str],
        date_format: str,
        allowed_extra_keys: list[str] | None = None,
    ):
        super().__init__(datefmt=date_format)
        self.include_fields = list(include_fields)
        self.allowed_extra_keys = set(allowed_extra_keys or [])

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {}

        if "timestamp" in self.include_fields:
            payload["timestamp"] = self.formatTime(record, self.datefmt)
        if "level" in self.include_fields:
            payload["level"] = record.levelname
        if "logger" in self.include_fields:
            payload["logger"] = record.name
        if "message" in self.include_fields:
            payload["message"] = record.getMessage()
        if "module" in self.include_fields:
            payload["module"] = record.module
        if "function" in self.include_fields:
            payload["function"] = record.funcName
        if "line" in self.include_fields:
            payload["line"] = record.lineno
        if "thread" in self.include_fields:
            payload["thread"] = record.threadName
        if "process" in self.include_fields:
            payload["process"] = record.process

        if "extra" in self.include_fields:
            extra = {
                key: value
                for key, value in record.__dict__.items()
                if key not in STANDARD_RECORD_KEYS
            }
            if self.allowed_extra_keys:
                extra = {
                    key: value
                    for key, value in extra.items()
                    if key in self.allowed_extra_keys
                }
            payload["extra"] = extra

        if record.exc_info and "exception" in self.include_fields:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class SingletonLogger:
    _instance: SingletonLogger | None = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> SingletonLogger:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._logger = None
                    cls._instance._lock = threading.Lock()
                    cls._instance._config = LoggerConfig()
        return cls._instance

    def configure(self, config: LoggerConfig) -> logging.Logger:
        with self._lock:
            self._config = config
            self._logger = self._build_logger(config)
            self._initialized = True
            return self._logger

    def get_logger(self) -> logging.Logger:
        with self._lock:
            if not self._initialized or self._logger is None:
                self._logger = self._build_logger(self._config)
                self._initialized = True
            return self._logger

    def _build_logger(self, config: LoggerConfig) -> logging.Logger:
        logger = logging.getLogger(config.name)
        logger.setLevel(_resolve_level(config.level))
        logger.propagate = config.propagate

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass

        formatter: logging.Formatter
        if config.use_json:
            formatter = JsonLogFormatter(
                include_fields=config.include_fields,
                date_format=config.date_format,
                allowed_extra_keys=config.allowed_extra_keys,
            )
        else:
            formatter = logging.Formatter(config.text_format, config.date_format)

        if config.enable_console:
            console_handler = logging.StreamHandler()
            if config.use_color and has_colorlog and not config.use_json:
                console_handler.setFormatter(
                    colorlog.ColoredFormatter(
                        fmt="%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(levelname)-8s%(reset)s | %(name)s | %(message)s",
                        datefmt=config.date_format,
                        log_colors={
                            "DEBUG": "cyan",
                            "INFO": "green",
                            "WARNING": "yellow",
                            "ERROR": "red",
                            "CRITICAL": "red,bg_white",
                        },
                        secondary_log_colors={},
                        style="%",
                    )
                )
            else:
                console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if config.enable_file:
            file_handler = self._create_file_handler(config)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def _create_file_handler(config: LoggerConfig) -> logging.Handler:
        directory = os.path.dirname(config.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if config.rotate:
            return RotatingFileHandler(
                filename=config.file_path,
                mode=config.file_mode,
                maxBytes=config.max_bytes,
                backupCount=config.backup_count,
                encoding="utf-8",
            )

        return logging.FileHandler(
            filename=config.file_path,
            mode=config.file_mode,
            encoding="utf-8",
        )


def _resolve_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    resolved = logging.getLevelName(level.upper())
    if isinstance(resolved, int):
        return resolved
    raise ValueError(f"Invalid log level: {level}")


def configure_logger(config: LoggerConfig) -> logging.Logger:
    return SingletonLogger().configure(config)


def get_logger() -> logging.Logger:
    return SingletonLogger().get_logger()
