"""
Configuration Manager for loading and saving settings from config.json.
"""
import os
import json
import sys
from typing import Dict, Any

DEFAULT_CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "local_sync_folder": "/home/aruncs/Music",
    "remote_adb_folder": "/storage/emulated/0/Music/ADB",
    "download_folder": "songs/download",
    "default_device_serial": None,
    "use_telegram": False,
    "auto_push_adb": False,
    "audio_extensions": [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"],
    "redis": {
        "enabled": True,
        "host": "localhost",
        "port": 8998,
        "db": 0,
        "password": "greenIsBest",
        "ttl_seconds": 3600
    }
}


def get_default_config_path() -> str:
    """Get absolute path to config.json in project root."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DEFAULT_CONFIG_FILENAME)


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    If file doesn't exist, create it with default values.
    """
    if not config_path:
        config_path = get_default_config_path()

    if not os.path.exists(config_path):
        print(f"[ConfigManager] Configuration file not found. Creating default: {config_path}", file=sys.stderr)
        save_config(DEFAULT_CONFIG, config_path)
        return dict(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        merged_config = dict(DEFAULT_CONFIG)
        merged_config.update(data)
        return merged_config
    except Exception as e:
        print(f"[ConfigManager] Error reading config from {config_path}: {e}. Using defaults.", file=sys.stderr)
        return dict(DEFAULT_CONFIG)


def save_config(config_data: Dict[str, Any], config_path: str = None):
    """Save configuration dictionary to JSON file."""
    if not config_path:
        config_path = get_default_config_path()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"[ConfigManager] Error writing config to {config_path}: {e}", file=sys.stderr)


def get_local_sync_folders(cfg: Dict[str, Any]) -> list[str]:
    """
    Return local_sync_folder as a list of valid directory paths.
    Supports both a single string path or a list of string paths in config.json.
    """
    val = cfg.get("local_sync_folder", "/home/aruncs/Music")
    if isinstance(val, list):
        return [os.path.expanduser(p) for p in val if p]
    elif isinstance(val, str):
        return [os.path.expanduser(val)]
    return ["/home/aruncs/Music"]

