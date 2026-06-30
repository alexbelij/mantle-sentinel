"""Tests for sentinel/plugins/webhook.py"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from sentinel.plugins.webhook import WebhookNotifier

# ---------------------------------------------------------------------------
# Minimal local HTTP server to capture POST requests
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    received: list[dict] = []
    statuses: list[int] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Handler.received.append(json.loads(body))
        status = _Handler.statuses.pop(0) if _Handler.statuses else 200
        self.send_response(status)
        self.end_headers()

    def log_message(self, *_: object) -> None:
        pass  # suppress output


@pytest.fixture()
def local_server():
    _Handler.received.clear()
    _Handler.statuses.clear()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    t = Thread(target=server.handle_request, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}", _Handler
    server.server_close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_notify_sync_delivers_payload(local_server):
    url, handler = local_server
    wh = WebhookNotifier(url=url)
    ok = wh.notify_sync({"window_id": "w1", "drift_score": 0.9})
    assert ok is True
    assert len(handler.received) == 1
    assert handler.received[0]["window_id"] == "w1"


def test_notify_sync_includes_secret_header(local_server):
    url, handler = local_server

    class _SecretHandler(BaseHTTPRequestHandler):
        header_value: str | None = None
        def do_POST(self) -> None:  # noqa: N802
            _SecretHandler.header_value = self.headers.get("X-Sentinel-Secret")
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            self.send_response(200)
            self.end_headers()
        def log_message(self, *_: object) -> None:
            pass

    server2 = HTTPServer(("127.0.0.1", 0), _SecretHandler)
    port2 = server2.server_address[1]
    t2 = Thread(target=server2.handle_request, daemon=True)
    t2.start()
    wh = WebhookNotifier(
        url=f"http://127.0.0.1:{port2}",
        secret_header="X-Sentinel-Secret",
        secret_value="tok123",
    )
    wh.notify_sync({"x": 1})
    t2.join(timeout=2)
    server2.server_close()
    assert _SecretHandler.header_value == "tok123"


def test_notify_async_delivers(local_server):
    import time
    url, handler = local_server
    wh = WebhookNotifier(url=url, timeout=5)
    wh.notify({"window_id": "async-1"})
    # Give background thread time to fire
    for _ in range(20):
        if handler.received:
            break
        time.sleep(0.1)
    assert len(handler.received) == 1


def test_notify_sync_returns_false_on_connection_error():
    wh = WebhookNotifier(url="http://127.0.0.1:1", timeout=1, max_retries=1)
    result = wh.notify_sync({"x": 1})
    assert result is False
