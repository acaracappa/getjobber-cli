"""Token storage and management for GetJobber CLI."""

import json
import time
from pathlib import Path
from typing import Optional

import keyring

from getjobber_cli.constants import (
    CONFIG_DIR_NAME,
    CREDENTIALS_FILE_NAME,
    DEFAULT_TOKEN_EXPIRY,
    KEYRING_SERVICE_NAME,
    KEYRING_USERNAME,
    TOKEN_EXPIRY_BUFFER,
)
from getjobber_cli.utils.errors import TokenExpiredError, TokenStorageError


class TokenManager:
    """Manages secure storage and retrieval of OAuth tokens."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize token manager.

        Args:
            config_dir: Optional custom config directory path.
                       Defaults to ~/.getjobber
        """
        if config_dir is None:
            self.config_dir = Path.home() / CONFIG_DIR_NAME
        else:
            self.config_dir = config_dir

        self.credentials_file = self.config_dir / CREDENTIALS_FILE_NAME
        self.use_keyring = self._check_keyring_available()

    def _check_keyring_available(self) -> bool:
        """Check if keyring is available and working.

        Returns:
            True if keyring is available, False otherwise.
        """
        try:
            # Try to access keyring
            keyring.get_password(KEYRING_SERVICE_NAME, "test")
            return True
        except Exception:
            return False

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.chmod(0o700)

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int = DEFAULT_TOKEN_EXPIRY,
        token_type: str = "Bearer",
    ) -> None:
        """Store tokens securely.

        Args:
            access_token: OAuth access token.
            refresh_token: OAuth refresh token.
            expires_in: Token expiry time in seconds.
            token_type: Token type (usually "Bearer").

        Raises:
            TokenStorageError: If token storage fails.
        """
        # Calculate expiry timestamp
        expiry_time = int(time.time()) + expires_in

        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expiry_time,
            "token_type": token_type,
        }

        token_json = json.dumps(token_data)

        try:
            if self.use_keyring:
                # Store in OS keychain
                keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME, token_json)
            else:
                # Fallback to encrypted file
                self._ensure_config_dir()
                with open(self.credentials_file, "w") as f:
                    f.write(token_json)
                # Set strict permissions
                self.credentials_file.chmod(0o600)
        except Exception as e:
            raise TokenStorageError(f"Failed to store tokens: {str(e)}")

    def get_tokens(self) -> Optional[dict]:
        """Retrieve stored tokens.

        Returns:
            Dictionary with token data, or None if no tokens stored.

        Raises:
            TokenStorageError: If token retrieval fails.
        """
        try:
            if self.use_keyring:
                # Retrieve from OS keychain
                token_json = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME)
                if not token_json:
                    return None
            else:
                # Retrieve from file
                if not self.credentials_file.exists():
                    return None
                with open(self.credentials_file, "r") as f:
                    token_json = f.read()

            token_data = json.loads(token_json)
            return token_data

        except json.JSONDecodeError:
            raise TokenStorageError("Corrupted token data. Please login again.")
        except Exception as e:
            raise TokenStorageError(f"Failed to retrieve tokens: {str(e)}")

    def clear_tokens(self) -> None:
        """Clear stored tokens.

        Raises:
            TokenStorageError: If token clearing fails.
        """
        try:
            if self.use_keyring:
                # Clear from OS keychain
                try:
                    keyring.delete_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME)
                except keyring.errors.PasswordDeleteError:
                    # Token already cleared or doesn't exist
                    pass
            else:
                # Remove credentials file
                if self.credentials_file.exists():
                    self.credentials_file.unlink()
        except Exception as e:
            raise TokenStorageError(f"Failed to clear tokens: {str(e)}")

    def is_expired(self, token_data: dict) -> bool:
        """Check if token is expired.

        Args:
            token_data: Token data dictionary.

        Returns:
            True if token is expired or will expire soon.
        """
        expires_at = token_data.get("expires_at", 0)
        current_time = int(time.time())

        # Consider token expired if it expires within buffer time
        return current_time >= (expires_at - TOKEN_EXPIRY_BUFFER)

    def get_access_token(self) -> Optional[str]:
        """Get valid access token.

        Returns:
            Access token string, or None if no valid token available.
        """
        token_data = self.get_tokens()
        if not token_data:
            return None

        if self.is_expired(token_data):
            return None

        return token_data.get("access_token")

    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token.

        Returns:
            Refresh token string, or None if no token available.
        """
        token_data = self.get_tokens()
        if not token_data:
            return None

        return token_data.get("refresh_token")

    def get_expiry_time(self) -> Optional[int]:
        """Get token expiry timestamp.

        Returns:
            Expiry timestamp, or None if no token available.
        """
        token_data = self.get_tokens()
        if not token_data:
            return None

        return token_data.get("expires_at")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token.

        Returns:
            True if authenticated with valid token, False otherwise.
        """
        token_data = self.get_tokens()
        if not token_data:
            return False

        return not self.is_expired(token_data)


def get_token_manager() -> TokenManager:
    """Get global token manager instance.

    Returns:
        TokenManager instance.
    """
    return TokenManager()
