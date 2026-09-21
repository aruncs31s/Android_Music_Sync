"""
Local Network Peer Discovery for Over-IP Synchronization.
Uses lightweight UDP broadcast on port 5005 to automatically detect
peer devices (Android companion app and Desktop instances) on the local Wi-Fi.
"""
import socket
import json
import threading
import time
from typing import List, Dict, Any, Optional

import database.db_manager as ui_db
from utils import get_logger

logger = get_logger()

DISCOVERY_PORT = 5005
MAGIC_HEADER = "AndroidMusicSync"


def is_local_address(ip: str) -> bool:
    """Check if the given IP belongs to this local machine or loopback."""
    if not ip:
        return True
    ip = ip.strip()
    if ip in ("127.0.0.1", "::1", "localhost", "0.0.0.0"):
        return True
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        if ip in local_ips:
            return True
    except Exception:
        pass
    try:
        if ip == socket.gethostbyname(socket.gethostname()):
            return True
    except Exception:
        pass
    return False


def is_self_payload(ip: str, payload: dict) -> bool:
    """Check if an incoming discovery probe or announcement originated from this machine."""
    if is_local_address(ip):
        return True
    role = payload.get("role")
    hostname = payload.get("hostname", "")
    if role == "desktop" and hostname == socket.gethostname():
        return True
    return False


def cleanup_loopback_hosts():
    """Remove any stored IP hosts that match local machine interfaces or loopback."""
    try:
        stored = ui_db.get_stored_ip_hosts()
        for h in stored:
            ip = h.get("ip_address")
            alias = h.get("alias", "")
            if ip and (is_local_address(ip) or (socket.gethostname() in alias and "Desktop" in alias)):
                logger.info(f"[Discovery] Purged loopback host from database: {ip} ({alias})")
                ui_db.remove_ip_host(ip)
    except Exception as e:
        logger.debug(f"[Discovery] Cleanup loopback error: {e}")


class PeerDiscoveryService:
    """
    Background UDP service that announces this Desktop server on the local Wi-Fi
    and listens for probes from the Android companion app.
    """
    _instance: Optional['PeerDiscoveryService'] = None
    _lock = threading.Lock()

    def __init__(self, port: int = 5000):
        self.server_port = port
        self._stop_event = threading.Event()
        self._listener_thread: Optional[threading.Thread] = None
        self._sock: Optional[socket.socket] = None

    @classmethod
    def get_instance(cls, port: int = 5000) -> 'PeerDiscoveryService':
        with cls._lock:
            if cls._instance is None:
                cls._instance = PeerDiscoveryService(port=port)
            return cls._instance

    def start(self):
        """Start listening for incoming peer discovery probes in background."""
        cleanup_loopback_hosts()
        if self._listener_thread and self._listener_thread.is_alive():
            return

        self._stop_event.clear()
        self._listener_thread = threading.Thread(
            target=self._run_listener,
            daemon=True,
            name="peer-discovery-listener"
        )
        self._listener_thread.start()
        logger.info(f"[Discovery] Peer discovery listener started on UDP port {DISCOVERY_PORT}")

        # Broadcast initial announcement on startup
        threading.Thread(target=self.broadcast_announce, daemon=True).start()

    def stop(self):
        """Stop background listener thread and close socket."""
        self._stop_event.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _run_listener(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except Exception:
                    pass
            sock.bind(("", DISCOVERY_PORT))
            sock.settimeout(1.0)
            self._sock = sock
        except Exception as e:
            logger.warning(f"[Discovery] Could not bind UDP port {DISCOVERY_PORT}: {e}")
            return

        while not self._stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                ip = addr[0]
                payload = json.loads(data.decode("utf-8", errors="ignore"))

                if payload.get("magic") != MAGIC_HEADER:
                    continue

                if is_self_payload(ip, payload):
                    continue

                cmd = payload.get("cmd")

                if cmd == "DISCOVER":
                    # Peer is searching for servers. Reply with our desktop announcement
                    reply = json.dumps({
                        "magic": MAGIC_HEADER,
                        "cmd": "ANNOUNCE",
                        "role": "desktop",
                        "hostname": socket.gethostname(),
                        "port": self.server_port
                    }).encode("utf-8")
                    sock.sendto(reply, addr)
                    logger.info(f"[Discovery] Answered discovery probe from {ip}:{addr[1]}")

                    # If sender is Android, auto-register it in our database!
                    if payload.get("role") == "android":
                        peer_port = payload.get("port", 5000)
                        hostname = payload.get("hostname", ip)
                        ui_db.save_ip_host(ip, peer_port, alias=f"{hostname} (Android)")
                        ui_db.update_ip_status(ip, True)

                elif cmd == "ANNOUNCE":
                    peer_role = payload.get("role", "unknown")
                    peer_hostname = payload.get("hostname", ip)
                    peer_port = payload.get("port", 5000)
                    logger.info(f"[Discovery] Discovered peer announcement: {peer_hostname} ({peer_role}) at {ip}:{peer_port}")
                    ui_db.save_ip_host(ip, peer_port, alias=f"{peer_hostname} ({peer_role.title()})")
                    ui_db.update_ip_status(ip, True)

            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.debug(f"[Discovery] Listener error: {e}")

    def _get_broadcast_destinations(self) -> List[str]:
        dests = ["255.255.255.255"]
        try:
            import subprocess, re
            output = subprocess.check_output(["ifconfig"], text=True)
            for b in re.findall(r"broadcast\s+(\d+\.\d+\.\d+\.\d+)", output):
                if b not in dests:
                    dests.append(b)
        except Exception:
            pass
        try:
            hosts = ui_db.get_stored_ip_hosts()
            for h in hosts:
                ip = h.get("ip_address")
                if ip and ip not in dests:
                    dests.append(ip)
        except Exception:
            pass
        return dests

    def broadcast_announce(self):
        """Send an announcement broadcast to subnet broadcasts and known peers."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)
            payload = json.dumps({
                "magic": MAGIC_HEADER,
                "cmd": "ANNOUNCE",
                "role": "desktop",
                "hostname": socket.gethostname(),
                "port": self.server_port
            }).encode("utf-8")
            for dest in self._get_broadcast_destinations():
                try:
                    sock.sendto(payload, (dest, DISCOVERY_PORT))
                except Exception:
                    pass
            sock.close()
            logger.info(f"[Discovery] Broadcasted desktop announcement on UDP :{DISCOVERY_PORT}")
        except Exception as e:
            logger.debug(f"[Discovery] Broadcast announce error: {e}")

    def broadcast_discover(self, timeout: float = 1.5) -> List[Dict[str, Any]]:
        """
        Send a discovery probe to local network and collect all responding peers.
        Auto-registers newly discovered peers into SQLite ip_hosts table.
        """
        discovered = []
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)

            probe = json.dumps({
                "magic": MAGIC_HEADER,
                "cmd": "DISCOVER",
                "role": "desktop",
                "hostname": socket.gethostname(),
                "port": self.server_port
            }).encode("utf-8")

            for dest in self._get_broadcast_destinations():
                try:
                    sock.sendto(probe, (dest, DISCOVERY_PORT))
                except Exception:
                    pass
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(2048)
                    ip = addr[0]
                    payload = json.loads(data.decode("utf-8", errors="ignore"))

                    if payload.get("magic") == MAGIC_HEADER and payload.get("cmd") == "ANNOUNCE":
                        if is_self_payload(ip, payload):
                            continue

                        peer_role = payload.get("role", "unknown")
                        peer_hostname = payload.get("hostname", ip)
                        peer_port = payload.get("port", 5000)

                        # Auto-save peer
                        ui_db.save_ip_host(ip, peer_port, alias=f"{peer_hostname} ({peer_role.title()})")
                        ui_db.update_ip_status(ip, True)

                        discovered.append({
                            "ip": ip,
                            "port": peer_port,
                            "hostname": peer_hostname,
                            "role": peer_role
                        })
                except socket.timeout:
                    break
                except Exception:
                    break

            sock.close()
        except Exception as e:
            logger.warning(f"[Discovery] Broadcast discover error: {e}")

        logger.info(f"[Discovery] Self-discovery complete: found {len(discovered)} active peer(s)")
        return discovered
