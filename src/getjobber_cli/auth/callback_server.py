"""Local HTTP server for OAuth callback handling."""

import http.server
import socketserver
import threading
import urllib.parse
from typing import Optional

from getjobber_cli.constants import CALLBACK_HOST, CALLBACK_PATH, CALLBACK_PORT, CALLBACK_TIMEOUT


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    # Class variables to store callback data
    authorization_code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    received_event = threading.Event()

    def do_GET(self):
        """Handle GET request to callback endpoint."""
        # Parse the query parameters
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == CALLBACK_PATH:
            query_params = urllib.parse.parse_qs(parsed_path.query)

            # Extract authorization code, state, and error
            OAuthCallbackHandler.authorization_code = query_params.get("code", [None])[0]
            OAuthCallbackHandler.state = query_params.get("state", [None])[0]
            OAuthCallbackHandler.error = query_params.get("error", [None])[0]

            # Send response to browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if OAuthCallbackHandler.error:
                error_description = query_params.get("error_description", ["Unknown error"])[0]
                html_content = f"""
                <html>
                <head>
                    <title>Authentication Failed</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                        }}
                        h1 {{ color: #e74c3c; margin-top: 0; }}
                        p {{ color: #555; line-height: 1.6; }}
                        .error {{ color: #e74c3c; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Authentication Failed</h1>
                        <p class="error">{error_description}</p>
                        <p>You can close this window and return to the terminal.</p>
                    </div>
                </body>
                </html>
                """
            else:
                html_content = """
                <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }
                        .container {
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                        }
                        h1 { color: #27ae60; margin-top: 0; }
                        p { color: #555; line-height: 1.6; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✅ Authentication Successful!</h1>
                        <p>You have successfully authenticated with GetJobber.</p>
                        <p>You can close this window and return to the terminal.</p>
                    </div>
                </body>
                </html>
                """

            self.wfile.write(html_content.encode())

            # Signal that callback was received
            OAuthCallbackHandler.received_event.set()
        else:
            # Handle other paths
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress server log messages."""
        pass


class OAuthCallbackServer:
    """Local HTTP server for handling OAuth callbacks."""

    def __init__(self, host: str = CALLBACK_HOST, port: int = CALLBACK_PORT):
        """Initialize the callback server.

        Args:
            host: Host to bind the server to.
            port: Port to bind the server to.
        """
        self.host = host
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the callback server in a background thread."""
        # Reset class variables
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.state = None
        OAuthCallbackHandler.error = None
        OAuthCallbackHandler.received_event.clear()

        # Create server
        self.server = socketserver.TCPServer((self.host, self.port), OAuthCallbackHandler)

        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def wait_for_callback(self, timeout: int = CALLBACK_TIMEOUT) -> dict:
        """Wait for OAuth callback.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            Dictionary with authorization_code, state, and error.
        """
        # Wait for callback with timeout
        received = OAuthCallbackHandler.received_event.wait(timeout)

        if not received:
            return {"error": "timeout", "error_description": "Callback timeout exceeded"}

        return {
            "authorization_code": OAuthCallbackHandler.authorization_code,
            "state": OAuthCallbackHandler.state,
            "error": OAuthCallbackHandler.error,
        }

    def stop(self) -> None:
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.server_thread:
            self.server_thread.join(timeout=1)
            self.server_thread = None
