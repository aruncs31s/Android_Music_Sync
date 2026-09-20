"""
Stream Service for high-efficiency audio playback and Over-IP audio proxying.
Supports HTTP Range seeking (RFC 7233) for both local files and remote Over-IP companion devices (SRP).
"""
import os
import mimetypes
from typing import Optional, Tuple, Generator
from flask import Response, request
from device_providers.registry import DeviceProviderRegistry
from device_providers.over_ip_provider import OverIpDeviceProvider
from utils import get_logger

logger = get_logger()


class StreamService:
    """Handles audio streaming for local files and remote peer devices."""

    @classmethod
    def stream_local_file(cls, filepath: str, range_header: Optional[str] = None) -> Response:
        """
        Stream a local file with proper HTTP 206 Partial Content and Range seeking.
        """
        filepath = os.path.abspath(filepath)
        if not os.path.isfile(filepath):
            return Response("File not found", status=404, mimetype="text/plain")

        file_size = os.path.getsize(filepath)
        content_type, _ = mimetypes.guess_type(filepath)
        content_type = content_type or "audio/mpeg"

        if not range_header or not range_header.startswith("bytes="):
            # Stream entire file
            def full_generator():
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        yield chunk

            resp = Response(full_generator(), status=200, mimetype=content_type)
            resp.headers["Content-Length"] = str(file_size)
            resp.headers["Accept-Ranges"] = "bytes"
            return resp

        # Parse byte range: "bytes=start-end"
        range_val = range_header.replace("bytes=", "").strip()
        parts = range_val.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

        if start >= file_size or start > end:
            resp = Response("", status=416, mimetype="text/plain")
            resp.headers["Content-Range"] = f"bytes */{file_size}"
            return resp

        end = min(end, file_size - 1)
        length = end - start + 1

        def partial_generator():
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk_size = min(remaining, 65536)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        resp = Response(partial_generator(), status=206, mimetype=content_type)
        resp.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        resp.headers["Content-Length"] = str(length)
        resp.headers["Accept-Ranges"] = "bytes"
        return resp

    @classmethod
    def stream_remote_peer(
        cls,
        device_id: str,
        remote_filepath: str,
        range_header: Optional[str] = None
    ) -> Response:
        """
        Proxy audio stream from remote Over-IP companion device to client browser.
        """
        provider = DeviceProviderRegistry.get_provider(device_id)
        if not isinstance(provider, OverIpDeviceProvider):
            return Response(f"Device {device_id} is not an Over-IP device", status=400, mimetype="text/plain")

        try:
            req, status_code, res_headers = provider.stream_song(remote_filepath, range_header=range_header)

            def proxy_generator():
                try:
                    for chunk in req.iter_content(chunk_size=65536):
                        if chunk:
                            yield chunk
                finally:
                    req.close()

            resp = Response(
                proxy_generator(),
                status=status_code,
                mimetype=res_headers.get("Content-Type", "audio/mpeg")
            )
            for k, v in res_headers.items():
                if k.lower() != "content-type":
                    resp.headers[k] = v

            resp.headers["Accept-Ranges"] = "bytes"
            return resp
        except Exception as e:
            logger.error(f"[StreamService] Error proxying stream from {device_id}: {e}")
            return Response(f"Stream error from device: {e}", status=502, mimetype="text/plain")
