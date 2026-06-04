"""Tests for OAuth 2.0 authentication flow."""

import urllib.parse

import pytest
import requests
import responses

from getjobber_cli.auth.oauth import OAuthFlow
from getjobber_cli.constants import OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL
from getjobber_cli.utils.errors import OAuthError


@pytest.fixture
def oauth_flow():
    return OAuthFlow(client_id="cid", client_secret="csec")


class TestGenerateAuthURL:
    def test_includes_required_params(self, oauth_flow):
        url = oauth_flow.generate_auth_url()
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        assert url.startswith(OAUTH_AUTHORIZE_URL)
        assert params["client_id"] == ["cid"]
        assert params["response_type"] == ["code"]
        assert "state" in params
        assert "redirect_uri" in params

    def test_sets_state_attribute(self, oauth_flow):
        oauth_flow.generate_auth_url()
        assert oauth_flow.state is not None
        assert len(oauth_flow.state) > 16

    def test_generates_unique_state_each_call(self, oauth_flow):
        oauth_flow.generate_auth_url()
        s1 = oauth_flow.state
        oauth_flow.generate_auth_url()
        s2 = oauth_flow.state
        assert s1 != s2


class TestExchangeCodeForToken:
    @responses.activate
    def test_success(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            json={
                "access_token": "at",
                "refresh_token": "rt",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            status=200,
        )
        result = oauth_flow.exchange_code_for_token("auth_code_123")
        assert result["access_token"] == "at"
        assert result["refresh_token"] == "rt"

    @responses.activate
    def test_invalid_code_raises_oauth_error(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            json={"error": "invalid_grant", "error_description": "bad code"},
            status=400,
        )
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.exchange_code_for_token("bad_code")
        assert "bad code" in str(exc_info.value)
        assert exc_info.value.error_code == "invalid_grant"

    @responses.activate
    def test_error_response_with_empty_body(self, oauth_flow):
        responses.add(responses.POST, OAUTH_TOKEN_URL, body="", status=500)
        with pytest.raises(OAuthError):
            oauth_flow.exchange_code_for_token("code")

    @responses.activate
    def test_network_error(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            body=requests.exceptions.ConnectionError("network down"),
        )
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.exchange_code_for_token("code")
        assert "Network error" in str(exc_info.value)


class TestRefreshAccessToken:
    @responses.activate
    def test_success(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            json={
                "access_token": "new_at",
                "refresh_token": "new_rt",
                "expires_in": 3600,
            },
            status=200,
        )
        result = oauth_flow.refresh_access_token("old_rt")
        assert result["access_token"] == "new_at"

    @responses.activate
    def test_invalid_refresh_token(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            json={"error": "invalid_grant", "error_description": "expired"},
            status=401,
        )
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.refresh_access_token("expired_rt")
        assert exc_info.value.error_code == "invalid_grant"

    @responses.activate
    def test_network_error(self, oauth_flow):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            body=requests.exceptions.ConnectionError("oops"),
        )
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.refresh_access_token("rt")
        assert "Network error" in str(exc_info.value)


class TestOpenBrowser:
    def test_returns_false_on_exception(self, oauth_flow, monkeypatch):
        def raise_exc(url):
            raise Exception("no browser")

        monkeypatch.setattr("webbrowser.open", raise_exc)
        assert oauth_flow.open_browser("http://x") is False

    def test_returns_true_on_success(self, oauth_flow, monkeypatch):
        monkeypatch.setattr("webbrowser.open", lambda url: True)
        assert oauth_flow.open_browser("http://x") is True


class TestHandleAuthorization:
    @responses.activate
    def test_state_mismatch_raises(self, oauth_flow, monkeypatch):
        # Stub out the callback server so it returns a wrong state
        class FakeServer:
            def start(self):
                pass

            def wait_for_callback(self, timeout):
                return {
                    "authorization_code": "code",
                    "state": "wrong",
                    "error": None,
                }

            def stop(self):
                pass

        monkeypatch.setattr(oauth_flow, "start_callback_server", lambda: FakeServer())
        monkeypatch.setattr(oauth_flow, "open_browser", lambda url: True)

        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.handle_authorization()
        assert "State mismatch" in str(exc_info.value)

    @responses.activate
    def test_timeout_raises(self, oauth_flow, monkeypatch):
        class FakeServer:
            def start(self):
                pass

            def wait_for_callback(self, timeout):
                return {"error": "timeout", "error_description": "timed out"}

            def stop(self):
                pass

        monkeypatch.setattr(oauth_flow, "start_callback_server", lambda: FakeServer())
        monkeypatch.setattr(oauth_flow, "open_browser", lambda url: True)
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.handle_authorization()
        assert "timeout" in str(exc_info.value).lower()

    @responses.activate
    def test_missing_code_raises(self, oauth_flow, monkeypatch):
        # Make state match but omit authorization_code
        original = oauth_flow.generate_auth_url

        def stub_auth():
            url = original()
            return url

        class FakeServer:
            def start(self):
                pass

            def wait_for_callback(self, timeout):
                return {
                    "authorization_code": None,
                    "state": oauth_flow.state,
                    "error": None,
                }

            def stop(self):
                pass

        monkeypatch.setattr(oauth_flow, "start_callback_server", lambda: FakeServer())
        monkeypatch.setattr(oauth_flow, "open_browser", lambda url: True)
        with pytest.raises(OAuthError) as exc_info:
            oauth_flow.handle_authorization()
        assert "authorization code" in str(exc_info.value).lower()

    @responses.activate
    def test_happy_path(self, oauth_flow, monkeypatch):
        responses.add(
            responses.POST,
            OAUTH_TOKEN_URL,
            json={"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
            status=200,
        )

        class FakeServer:
            def start(self):
                pass

            def wait_for_callback(self, timeout):
                return {
                    "authorization_code": "good_code",
                    "state": oauth_flow.state,
                    "error": None,
                }

            def stop(self):
                pass

        monkeypatch.setattr(oauth_flow, "start_callback_server", lambda: FakeServer())
        monkeypatch.setattr(oauth_flow, "open_browser", lambda url: True)

        result = oauth_flow.handle_authorization()
        assert result["access_token"] == "at"
