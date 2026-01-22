"""Authentication commands for GetJobber CLI."""

import typer
from datetime import datetime

from getjobber_cli.auth.oauth import OAuthFlow
from getjobber_cli.auth.token_manager import get_token_manager
from getjobber_cli.utils.config import get_config
from getjobber_cli.utils.errors import ConfigurationError, OAuthError
from getjobber_cli.utils.formatters import print_error, print_info, print_success


def login():
    """Authenticate with GetJobber using OAuth 2.0."""
    try:
        # Get configuration
        config = get_config()

        # Check if OAuth credentials are configured
        if not config.is_configured():
            print_error("OAuth credentials not configured.")
            print_info("Please configure your OAuth credentials first:")
            print_info("  getjobber-cli config set client_id YOUR_CLIENT_ID")
            print_info("  getjobber-cli config set client_secret YOUR_CLIENT_SECRET")
            print_info("\nFor setup instructions, visit the documentation.")
            raise typer.Exit(1)

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")

        # Initialize OAuth flow
        oauth_flow = OAuthFlow(client_id=client_id, client_secret=client_secret)

        print_info("Starting OAuth authentication flow...")
        print_info("Your browser will open to authorize the application.")

        # Handle authorization
        token_response = oauth_flow.handle_authorization()

        # Store tokens
        token_manager = get_token_manager()
        token_manager.store_tokens(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            expires_in=token_response.get("expires_in", 3600),
            token_type=token_response.get("token_type", "Bearer"),
        )

        print_success("Successfully authenticated with GetJobber!")

        # Show expiry information
        expiry_time = token_manager.get_expiry_time()
        if expiry_time:
            expiry_datetime = datetime.fromtimestamp(expiry_time)
            print_info(f"Token expires at: {expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    except ConfigurationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except OAuthError as e:
        print_error(f"Authentication failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def logout():
    """Clear stored authentication credentials."""
    try:
        token_manager = get_token_manager()

        # Check if authenticated
        if not token_manager.is_authenticated():
            print_info("Not currently authenticated.")
            raise typer.Exit(0)

        # Confirm logout
        confirm = typer.confirm("Are you sure you want to logout?")
        if not confirm:
            print_info("Logout cancelled.")
            raise typer.Exit(0)

        # Clear tokens
        token_manager.clear_tokens()
        print_success("Successfully logged out.")

    except Exception as e:
        print_error(f"Error during logout: {str(e)}")
        raise typer.Exit(1)


def status():
    """Show authentication status."""
    try:
        token_manager = get_token_manager()
        config = get_config()

        print_info("Authentication Status\n")

        # Check configuration
        if config.is_configured():
            client_id = config.get("client_id")
            masked_id = f"{client_id[:8]}...{client_id[-4:]}" if len(client_id) > 12 else client_id
            print_info(f"Client ID: {masked_id}")
        else:
            print_error("OAuth credentials not configured")

        # Check authentication
        if token_manager.is_authenticated():
            print_success("Status: Authenticated")

            # Show expiry
            expiry_time = token_manager.get_expiry_time()
            if expiry_time:
                expiry_datetime = datetime.fromtimestamp(expiry_time)
                current_time = datetime.now()
                time_remaining = expiry_datetime - current_time

                print_info(f"Token expires: {expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                print_info(f"Time remaining: {str(time_remaining).split('.')[0]}")
        else:
            print_error("Status: Not authenticated")
            print_info("Run 'getjobber-cli login' to authenticate")

    except Exception as e:
        print_error(f"Error checking status: {str(e)}")
        raise typer.Exit(1)


def refresh():
    """Manually refresh access token."""
    try:
        token_manager = get_token_manager()
        config = get_config()

        # Check if authenticated
        token_data = token_manager.get_tokens()
        if not token_data:
            print_error("Not authenticated. Please login first.")
            raise typer.Exit(1)

        # Get refresh token
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            print_error("No refresh token available. Please login again.")
            raise typer.Exit(1)

        # Get OAuth credentials
        if not config.is_configured():
            print_error("OAuth credentials not configured.")
            raise typer.Exit(1)

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")

        # Refresh token
        print_info("Refreshing access token...")
        oauth_flow = OAuthFlow(client_id=client_id, client_secret=client_secret)
        token_response = oauth_flow.refresh_access_token(refresh_token)

        # Store new tokens
        token_manager.store_tokens(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token", refresh_token),
            expires_in=token_response.get("expires_in", 3600),
            token_type=token_response.get("token_type", "Bearer"),
        )

        print_success("Access token refreshed successfully!")

        # Show expiry information
        expiry_time = token_manager.get_expiry_time()
        if expiry_time:
            expiry_datetime = datetime.fromtimestamp(expiry_time)
            print_info(f"Token expires at: {expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    except OAuthError as e:
        print_error(f"Token refresh failed: {str(e)}")
        print_info("Please login again: getjobber-cli login")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Error refreshing token: {str(e)}")
        raise typer.Exit(1)
