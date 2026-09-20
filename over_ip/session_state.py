"""
In-memory desktop playback session state.
Updated by the browser via POST /api/session/heartbeat.
Read by remote Android/device peers via GET /api/session/state.
"""
import threading
import time
import socket


_lock = threading.Lock()
_state = {
    "device_id": "",
    "device_name": socket.gethostname(),
    "device_role": "desktop",
    "is_playing": False,
    "current_title": "",
    "current_artist": "",
    "current_filepath": "",
    "position_ms": 0,
    "duration_ms": 0,
    "queue_size": 0,
    "repeat_mode": "off",
    "is_shuffled": False,
    "last_updated": 0.0,
}


def get_state() -> dict:
    """Return a copy of the current session state."""
    with _lock:
        return dict(_state)


def update_state(**kwargs) -> None:
    """Update session state fields from keyword arguments."""
    with _lock:
        for key, value in kwargs.items():
            if key in _state:
                _state[key] = value
        _state["last_updated"] = time.time()


def is_stale(max_age_seconds: float = 15.0) -> bool:
    """Return True if the browser hasn't sent a heartbeat recently."""
    with _lock:
        age = time.time() - _state["last_updated"]
    return age > max_age_seconds
