#!/usr/bin/env python3
"""OAuth helper script for Monzo authentication.

Run this script to get your initial access and refresh tokens.
You'll need to:
1. Register an app at https://developers.monzo.com
2. Set MONZO_CLIENT_ID and MONZO_CLIENT_SECRET in your .env file
3. Run this script and follow the prompts
"""

import http.server
import os
import socket
import socketserver
import urllib.parse
import webbrowser
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load existing env vars
load_dotenv()

CLIENT_ID = os.getenv("MONZO_CLIENT_ID")
CLIENT_SECRET = os.getenv("MONZO_CLIENT_SECRET")
PORT = int(os.getenv("MONZO_AUTH_PORT", "8080"))
REDIRECT_URI = f"http://localhost:{PORT}/callback"
AUTH_URL = "https://auth.monzo.com"
API_URL = "https://api.monzo.com"


class ReusableTCPServer(socketserver.TCPServer):
    """TCP server that allows port reuse to avoid TIME_WAIT issues."""
    allow_reuse_address = True


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler to catch the OAuth callback."""

    auth_code: str | None = None

    def do_GET(self):
        """Handle the OAuth callback."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Success!</h1>"
                b"<p>You can close this window and return to the terminal.</p>"
                b"<p>Don't forget to approve the login in your Monzo app!</p>"
                b"</body></html>"
            )
        else:
            error = params.get("error", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {error}</h1></body></html>".encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def get_auth_url() -> str:
    """Build the authorization URL."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": "monzo_mcp_auth",
    }
    return f"{AUTH_URL}/?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(auth_code: str) -> dict:
    """Exchange the authorization code for access and refresh tokens."""
    response = httpx.post(
        f"{API_URL}/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
        },
    )
    response.raise_for_status()
    return response.json()


def update_env_file(access_token: str, refresh_token: str) -> None:
    """Update the .env file with the new tokens."""
    env_path = Path(__file__).parent.parent / ".env"

    # Read existing content or start fresh
    if env_path.exists():
        content = env_path.read_text()
        lines = content.splitlines()
    else:
        # Copy from .env.example
        example_path = Path(__file__).parent.parent / ".env.example"
        if example_path.exists():
            content = example_path.read_text()
            lines = content.splitlines()
        else:
            lines = [
                f"MONZO_CLIENT_ID={CLIENT_ID}",
                f"MONZO_CLIENT_SECRET={CLIENT_SECRET}",
                "MONZO_ACCESS_TOKEN=",
                "MONZO_REFRESH_TOKEN=",
            ]

    # Update token lines
    new_lines = []
    access_set = False
    refresh_set = False

    for line in lines:
        if line.startswith("MONZO_ACCESS_TOKEN="):
            new_lines.append(f"MONZO_ACCESS_TOKEN={access_token}")
            access_set = True
        elif line.startswith("MONZO_REFRESH_TOKEN="):
            new_lines.append(f"MONZO_REFRESH_TOKEN={refresh_token}")
            refresh_set = True
        else:
            new_lines.append(line)

    # Add if not present
    if not access_set:
        new_lines.append(f"MONZO_ACCESS_TOKEN={access_token}")
    if not refresh_set:
        new_lines.append(f"MONZO_REFRESH_TOKEN={refresh_token}")

    env_path.write_text("\n".join(new_lines) + "\n")
    print(f"\nTokens saved to {env_path}")


def main():
    """Run the OAuth flow."""
    print("Monzo MCP Authentication")
    print("=" * 40)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("\nError: Missing credentials!")
        print("1. Go to https://developers.monzo.com")
        print("2. Create a new OAuth client")
        print(f"3. Set the redirect URL to EXACTLY: {REDIRECT_URI}")
        print("4. Set confidentiality to: Confidential")
        print("5. Copy your Client ID and Client Secret")
        print("6. Create a .env file with:")
        print("   MONZO_CLIENT_ID=your_client_id")
        print("   MONZO_CLIENT_SECRET=your_client_secret")
        print("7. Run this script again")
        return

    # Start local server to catch callback
    try:
        server = ReusableTCPServer(("localhost", PORT), OAuthCallbackHandler)
    except OSError as e:
        print(f"\nError: Could not start server on port {PORT}: {e}")
        print("Try setting MONZO_AUTH_PORT to a different port in your .env file")
        print("(and update the redirect URL in your Monzo developer app to match)")
        return

    # Build and display auth URL
    auth_url = get_auth_url()
    print(f"\nRedirect URL configured: {REDIRECT_URI}")
    print("(Make sure this EXACTLY matches your Monzo developer app settings)")
    print(f"\n>>> Auth URL: {auth_url}")
    print("\nOpening browser...")
    webbrowser.open(auth_url)

    # Wait for callback
    print("\nWaiting for authorization...")
    print("(Approve the request in your Monzo app when prompted)")
    server.handle_request()

    if not OAuthCallbackHandler.auth_code:
        print("\nError: No authorization code received")
        return

    print("\nExchanging code for tokens...")
    try:
        tokens = exchange_code_for_tokens(OAuthCallbackHandler.auth_code)
    except httpx.HTTPStatusError as e:
        print(f"\nError getting tokens: {e.response.text}")
        return

    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token", "")

    print("\nSuccess! Tokens received.")
    print("\nIMPORTANT: Open your Monzo app and approve the login request!")
    print("You have 5 minutes to approve before the token becomes restricted.")

    update_env_file(access_token, refresh_token)

    print("\nYou're all set! You can now run the MCP server.")


if __name__ == "__main__":
    main()
