"""Tests for token storage and retrieval."""

import json
import time
from unittest.mock import patch

import keyring
import pytest

from getjobber_cli.auth.token_manager import TokenManager, get_token_manager
from getjobber_cli.constants import (
    CREDENTIALS_FILE_NAME,
    KEYRING_SERVICE_NAME,
    KEYRING_USERNAME,
    TOKEN_EXPIRY_BUFFER,
)
from getjobber_cli.utils.errors import TokenStorageError


@pytest.fixture
def token_manager_with_keyring(tmp_path):
    """Token manager with keyring available (mocked)."""
    with patch("getjobber_cli.auth.token_manager.keyring") as mock_keyring:
        # Keyring "available" -> initial call doesn't raise
        mock_keyring.get_password.return_value = None
        tm = TokenManager(config_dir=tmp_path / ".getjobber")
        tm._keyring_store = {}
        # Wire the mock to a fake store after the availability check
        def fake_set(service, user, value):
            tm._keyring_store[(service, user)] = value
        def fake_get(service, user):
            return tm._keyring_store.get((service, user))
        def fake_delete(service, user):
            if (service, user) in tm._keyring_store:
                del tm._keyring_store[(service, user)]
            else:
                raise keyring.errors.PasswordDeleteError("missing")
        mock_keyring.set_password.side_effect = fake_set
        mock_keyring.get_password.side_effect = fake_get
        mock_keyring.delete_password.side_effect = fake_delete
        # Real PasswordDeleteError class so except clause works
        mock_keyring.errors = keyring.errors
        yield tm


@pytest.fixture
def token_manager_no_keyring(tmp_path):
    """Token manager with keyring NOT available -> file fallback."""
    with patch("getjobber_cli.auth.token_manager.keyring") as mock_keyring:
        mock_keyring.get_password.side_effect = Exception("no keyring backend")
        mock_keyring.errors = keyring.errors
        tm = TokenManager(config_dir=tmp_path / ".getjobber")
        yield tm


class TestKeyringAvailability:
    def test_keyring_available(self, token_manager_with_keyring):
        assert token_manager_with_keyring.use_keyring is True

    def test_keyring_not_available(self, token_manager_no_keyring):
        assert token_manager_no_keyring.use_keyring is False


class TestStoreTokens:
    def test_keyring_storage(self, token_manager_with_keyring):
        tm = token_manager_with_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        stored = tm._keyring_store[(KEYRING_SERVICE_NAME, KEYRING_USERNAME)]
        data = json.loads(stored)
        assert data["access_token"] == "at"
        assert data["refresh_token"] == "rt"
        assert "expires_at" in data
        assert data["token_type"] == "Bearer"

    def test_file_fallback_storage(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        assert tm.credentials_file.exists()
        data = json.loads(tm.credentials_file.read_text())
        assert data["access_token"] == "at"

    def test_file_permissions_are_restrictive(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt")
        mode = tm.credentials_file.stat().st_mode & 0o777
        assert mode == 0o600

    def test_storage_error_wrapped(self, token_manager_with_keyring, monkeypatch):
        tm = token_manager_with_keyring
        monkeypatch.setattr(
            "getjobber_cli.auth.token_manager.keyring.set_password",
            lambda *args: (_ for _ in ()).throw(Exception("boom")),
        )
        with pytest.raises(TokenStorageError):
            tm.store_tokens("at", "rt")


class TestGetTokens:
    def test_returns_none_when_nothing_stored_keyring(self, token_manager_with_keyring):
        assert token_manager_with_keyring.get_tokens() is None

    def test_returns_none_when_nothing_stored_file(self, token_manager_no_keyring):
        assert token_manager_no_keyring.get_tokens() is None

    def test_round_trip_keyring(self, token_manager_with_keyring):
        tm = token_manager_with_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        data = tm.get_tokens()
        assert data["access_token"] == "at"

    def test_round_trip_file(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        data = tm.get_tokens()
        assert data["access_token"] == "at"

    def test_corrupted_json_raises(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm._ensure_config_dir()
        tm.credentials_file.write_text("not json{{{")
        with pytest.raises(TokenStorageError):
            tm.get_tokens()


class TestClearTokens:
    def test_keyring_clear(self, token_manager_with_keyring):
        tm = token_manager_with_keyring
        tm.store_tokens("at", "rt")
        tm.clear_tokens()
        assert tm.get_tokens() is None

    def test_keyring_clear_when_missing_does_not_raise(self, token_manager_with_keyring):
        tm = token_manager_with_keyring
        # Nothing stored; should swallow PasswordDeleteError
        tm.clear_tokens()

    def test_file_clear(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt")
        assert tm.credentials_file.exists()
        tm.clear_tokens()
        assert not tm.credentials_file.exists()

    def test_file_clear_when_missing_does_not_raise(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        # No file -> no-op
        tm.clear_tokens()


class TestExpiration:
    def test_is_expired_true_when_past(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        data = {"expires_at": int(time.time()) - 100}
        assert tm.is_expired(data) is True

    def test_is_expired_true_within_buffer(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        # Will expire within buffer window
        data = {"expires_at": int(time.time()) + (TOKEN_EXPIRY_BUFFER // 2)}
        assert tm.is_expired(data) is True

    def test_is_expired_false_when_future(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        data = {"expires_at": int(time.time()) + 10_000}
        assert tm.is_expired(data) is False

    def test_is_expired_missing_field(self, token_manager_no_keyring):
        # Missing field -> defaults to 0 -> definitely expired
        assert token_manager_no_keyring.is_expired({}) is True


class TestGetAccessToken:
    def test_returns_token_when_valid(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        assert tm.get_access_token() == "at"

    def test_returns_none_when_expired(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=0)
        assert tm.get_access_token() is None

    def test_returns_none_when_no_tokens(self, token_manager_no_keyring):
        assert token_manager_no_keyring.get_access_token() is None


class TestGetRefreshToken:
    def test_returns_refresh_token(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        assert tm.get_refresh_token() == "rt"

    def test_returns_none_no_tokens(self, token_manager_no_keyring):
        assert token_manager_no_keyring.get_refresh_token() is None


class TestGetExpiryTime:
    def test_returns_expiry(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        assert isinstance(tm.get_expiry_time(), int)

    def test_returns_none_no_tokens(self, token_manager_no_keyring):
        assert token_manager_no_keyring.get_expiry_time() is None


class TestIsAuthenticated:
    def test_authenticated_when_valid(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=3600)
        assert tm.is_authenticated() is True

    def test_not_authenticated_when_no_tokens(self, token_manager_no_keyring):
        assert token_manager_no_keyring.is_authenticated() is False

    def test_not_authenticated_when_expired(self, token_manager_no_keyring):
        tm = token_manager_no_keyring
        tm.store_tokens("at", "rt", expires_in=0)
        assert tm.is_authenticated() is False


class TestGetTokenManagerHelper:
    def test_returns_instance(self):
        assert isinstance(get_token_manager(), TokenManager)
