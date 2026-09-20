"""
Server-Sent Events (SSE) manager for real-time session command delivery.
When a remote Android device sends a session command (play/pause/seek/transfer),
we push an SSE event to any subscribed browser clients.
"""
import queue
import threading
import json
from utils import get_logger

logger = get_logger()

# Per-client event queues. Key = unique client ID string
_clients: dict[str, queue.Queue] = {}
_lock = threading.Lock()


def register_client(client_id: str) -> queue.Queue:
    """Register a new SSE client and return its event queue."""
    q: queue.Queue = queue.Queue(maxsize=50)
    with _lock:
        _clients[client_id] = q
    logger.info(f"[SessionSSE] Client connected: {client_id}")
    return q


def unregister_client(client_id: str) -> None:
    """Remove a disconnected SSE client."""
    with _lock:
        _clients.pop(client_id, None)
    logger.info(f"[SessionSSE] Client disconnected: {client_id}")


def push_event(event_type: str, data: dict) -> int:
    """
    Push an SSE event to all connected browser clients.
    Returns the number of clients that received it.
    """
    payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    dead_clients = []
    count = 0
    with _lock:
        for client_id, q in _clients.items():
            try:
                q.put_nowait(payload)
                count += 1
            except queue.Full:
                dead_clients.append(client_id)
    for c in dead_clients:
        unregister_client(c)
    logger.debug(f"[SessionSSE] Pushed '{event_type}' to {count} client(s)")
    return count


def sse_stream(client_id: str):
    """Generator that yields SSE events for a specific client. Use with Flask Response."""
    q = register_client(client_id)
    try:
        # Send a keep-alive comment immediately
        yield ": connected\n\n"
        while True:
            try:
                event = q.get(timeout=20)
                yield event
            except queue.Empty:
                # Heartbeat keep-alive comment
                yield ": keep-alive\n\n"
    finally:
        unregister_client(client_id)
