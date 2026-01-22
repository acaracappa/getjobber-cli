"""OAuth 2.0 authentication flow for GetJobber."""

import secrets
import urllib.parse
import webbrowser
from typing import Optional

import requests
from requests_oauthlib import OAuth2Session

from getjobber_cli.auth.callback_server import OAuthCallbackServer
from getjobber_cli.constants import (
    CALLBACK_HOST,
    CALLBACK_PORT,
    CALLBACK_TIMEOUT,
    DEFAULT_REDIRECT_URI,
    OAUTH_AUTHORIZE_URL,
    OAUTH_TOKEN_URL,
)
from getjobber_cli.utils.errors import OAuthError


class OAuthFlow:
    """Manages OAuth 2.0 authorization flow."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = DEFAULT_REDIRECT_URI):
        """Initialize OAuth flow.

        Args:
            client_id: OAuth client ID.
            client_secret: OAuth client secret.
            redirect_uri: Redirect URI for callback.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state: Optional[str] = None

    def generate_auth_url(self) -> str:
        """Generate authorization URL with state parameter.

        Returns:
            Authorization URL for user to visit.
        """
        # Generate random state for CSRF protection
        self.state = secrets.token_urlsafe(32)

        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": self.state,
        }

        auth_url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        return auth_url

    def open_browser(self, auth_url: str) -> bool:
        """Open system browser to authorization URL.

        Args:
            auth_url: Authorization URL to open.

        Returns:
            True if browser opened successfully, False otherwise.
        """
        try:
            return webbrowser.open(auth_url)
        except Exception:
            return False

    def start_callback_server(self) -> OAuthCallbackServer:
        """Start local callback server.

        Returns:
            OAuthCallbackServer instance.
        """
        server = OAuthCallbackServer(host=CALLBACK_HOST, port=CALLBACK_PORT)
        server.start()
        return server

    def exchange_code_for_token(self, authorization_code: str) -> dict:
        """Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from callback.

        Returns:
            Token response with access_token, refresh_token, expires_in, etc.

        Raises:
            OAuthError: If token exchange fails.
        """
        token_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(
                OAUTH_TOKEN_URL,
                data=token_data,
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error_description", "Token exchange failed")
                raise OAuthError(error_message, error_code=error_data.get("error"))

            token_response = response.json()
            return token_response

        except requests.exceptions.RequestException as e:
            raise OAuthError(f"Network error during token exchange: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token.

        Returns:
            Token response with new access_token and expires_in.

        Raises:
            OAuthError: If token refresh fails.
        """
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(
                OAUTH_TOKEN_URL,
                data=token_data,
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error_description", "Token refresh failed")
                raise OAuthError(error_message, error_code=error_data.get("error"))

            token_response = response.json()
            return token_response

        except requests.exceptions.RequestException as e:
            raise OAuthError(f"Network error during token refresh: {str(e)}")

    def handle_authorization(self) -> dict:
        """Handle complete authorization flow.

        Returns:
            Token response with access_token, refresh_token, expires_in, etc.

        Raises:
            OAuthError: If authorization flow fails.
        """
        # Generate auth URL
        auth_url = self.generate_auth_url()

        # Start callback server
        callback_server = self.start_callback_server()

        try:
            # Open browser
            browser_opened = self.open_browser(auth_url)
            if not browser_opened:
                # If browser doesn't open automatically, show URL
                print(f"\nPlease visit this URL to authorize:\n{auth_url}\n")

            print(f"Waiting for authorization... (timeout in {CALLBACK_TIMEOUT}s)")

            # Wait for callback
            callback_result = callback_server.wait_for_callback(timeout=CALLBACK_TIMEOUT)

            # Check for errors
            if callback_result.get("error"):
                error = callback_result["error"]
                if error == "timeout":
                    raise OAuthError("Authorization timeout. Please try again.")
                error_description = callback_result.get("error_description", "Unknown error")
                raise OAuthError(error_description, error_code=error)

            # Validate state parameter
            received_state = callback_result.get("state")
            if received_state != self.state:
                raise OAuthError("State mismatch. Possible CSRF attack.")

            # Get authorization code
            authorization_code = callback_result.get("authorization_code")
            if not authorization_code:
                raise OAuthError("No authorization code received")

            # Exchange code for token
            token_response = self.exchange_code_for_token(authorization_code)
            return token_response

        finally:
            # Always stop the callback server
            callback_server.stop()
