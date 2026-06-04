"""Tests for the local HTTP OAuth callback server."""

import threading
import time

import pytest
import requests

from getjobber_cli.auth.callback_server import OAuthCallbackHandler, OAuthCallbackServer
from getjobber_cli.constants import CALLBACK_PATH


def _find_free_port():
    """Pick a free port to avoid clashing with anything on 8888."""
    import socket

    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def server():
    """Yield a started callback server on an ephemeral port."""
    port = _find_free_port()
    srv = OAuthCallbackServer(host="localhost", port=port)
    srv.start()
    # Give the thread a moment to actually start
    time.sleep(0.05)
    yield srv, port
    srv.stop()


class TestCallbackServerLifecycle:
    def test_server_starts_on_expected_port(self, server):
        srv, port = server
        assert srv.server is not None
        # Should respond on its port
        resp = requests.get(f"http://localhost:{port}{CALLBACK_PATH}?code=abc&state=s", timeout=2)
        assert resp.status_code == 200

    def test_server_stops_cleanly(self):
        port = _find_free_port()
        srv = OAuthCallbackServer(host="localhost", port=port)
        srv.start()
        time.sleep(0.05)
        srv.stop()
        assert srv.server is None
        assert srv.server_thread is None


class TestCallbackHandler:
    def test_captures_code_and_state(self, server):
        srv, port = server
        # Send a callback in a thread
        def post_callback():
            requests.get(
                f"http://localhost:{port}{CALLBACK_PATH}?code=ABC123&state=mystate",
                timeout=2,
            )

        t = threading.Thread(target=post_callback)
        t.start()
        result = srv.wait_for_callback(timeout=5)
        t.join()
        assert result["authorization_code"] == "ABC123"
        assert result["state"] == "mystate"
        assert result["error"] is None

    def test_returns_success_html(self, server):
        srv, port = server
        resp = requests.get(
            f"http://localhost:{port}{CALLBACK_PATH}?code=abc&state=s",
            timeout=2,
        )
        assert resp.status_code == 200
        # Stylized HTML — just look for "Authentication Successful" header
        assert "Authentication Successful" in resp.text

    def test_returns_error_html_for_error_callback(self, server):
        srv, port = server
        resp = requests.get(
            f"http://localhost:{port}{CALLBACK_PATH}"
            "?error=access_denied&error_description=user+denied",
            timeout=2,
        )
        assert resp.status_code == 200
        assert "Authentication Failed" in resp.text

    def test_404_for_other_paths(self, server):
        srv, port = server
        resp = requests.get(f"http://localhost:{port}/bogus", timeout=2)
        assert resp.status_code == 404

    def test_missing_code_returns_none_in_result(self, server):
        srv, port = server

        def post_callback():
            requests.get(
                f"http://localhost:{port}{CALLBACK_PATH}?state=onlystate",
                timeout=2,
            )

        t = threading.Thread(target=post_callback)
        t.start()
        result = srv.wait_for_callback(timeout=5)
        t.join()
        assert result["authorization_code"] is None
        assert result["state"] == "onlystate"


class TestWaitForCallbackTimeout:
    def test_timeout_returns_error_dict(self):
        port = _find_free_port()
        srv = OAuthCallbackServer(host="localhost", port=port)
        srv.start()
        try:
            result = srv.wait_for_callback(timeout=0)
            assert result["error"] == "timeout"
            assert "Callback timeout" in result["error_description"]
        finally:
            srv.stop()


class TestLogMessageSuppressed:
    """Log messages should be suppressed to keep test output clean."""

    def test_log_message_does_nothing(self):
        # Construct a minimal handler-like stub by overriding __init__
        handler = OAuthCallbackHandler.__new__(OAuthCallbackHandler)
        # Should not raise even with placeholder args
        handler.log_message("%s", "anything")
