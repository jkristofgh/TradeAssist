#!/usr/bin/env python3
"""
Manual authentication script for Schwab API when callback URL has no port.

This script handles the OAuth flow manually by building the authorization URL
and handling the token exchange directly. It saves the token in the correct
schwab-py format from the start.
"""

import base64
import json
import secrets
import time
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests


def manual_auth():
    """Manual authentication flow."""
    print("Manual Schwab Authentication")
    print("=" * 40)

    api_key = input("Enter your Schwab API Key: ").strip()
    app_secret = input("Enter your Schwab App Secret: ").strip()
    callback_url = "https://127.0.0.1:3000/callback"  # Your registered URL without port

    print(f"\nUsing callback URL: {callback_url}")
    print("\nManual authentication process:")
    print("1. I'll open a browser with the Schwab login URL")
    print("2. Log into your Schwab account")
    print("3. Authorize the application")
    print("4. You'll be redirected to a page that won't load (this is normal)")
    print("5. Copy the ENTIRE URL from your browser's address bar")
    print("6. Paste it here when prompted")

    input("\nPress Enter to open the authorization URL...")

    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)

        # Build the authorization URL manually
        auth_params = {
            "client_id": api_key,
            "redirect_uri": callback_url,
            "response_type": "code",
            "state": state,
            "scope": "readonly",  # Basic scope for market data
        }

        auth_url = (
            f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(auth_params)}"
        )
        print(f"\nOpening: {auth_url}")

        # Open browser
        webbrowser.open(auth_url)

        print("\nAfter authorizing in the browser:")
        callback_response = input("Paste the complete callback URL here: ").strip()

        if not callback_response.startswith(callback_url):
            raise ValueError(f"Callback URL should start with {callback_url}")

        # Parse the authorization code from the callback URL
        parsed_url = urlparse(callback_response)
        query_params = parse_qs(parsed_url.query)

        if "code" not in query_params:
            raise ValueError("No authorization code found in callback URL")

        if "state" not in query_params or query_params["state"][0] != state:
            raise ValueError("State parameter mismatch - possible security issue")

        auth_code = query_params["code"][0]
        print(f"\nExtracted authorization code: {auth_code[:10]}...")

        # Exchange authorization code for access token
        token_url = "https://api.schwabapi.com/v1/oauth/token"

        # Prepare credentials for Basic Auth
        credentials = f"{api_key}:{app_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": callback_url,
        }

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        print("Exchanging authorization code for access token...")
        response = requests.post(token_url, data=token_data, headers=headers)

        if response.status_code != 200:
            raise ValueError(
                f"Token exchange failed: {response.status_code} - {response.text}"
            )

        raw_token = response.json()

        # Convert to schwab-py format immediately
        current_time = int(time.time())
        expires_in = raw_token.get("expires_in", 1800)

        # Create token in the format schwab-py expects
        schwab_token = {
            "token": {
                "access_token": raw_token["access_token"],
                "refresh_token": raw_token["refresh_token"],
                "id_token": raw_token.get("id_token", ""),
                "token_type": raw_token.get("token_type", "Bearer"),
                "scope": raw_token.get("scope", "api"),
                "expires_in": expires_in,
                "expires_at": current_time + expires_in,
            },
            "creation_timestamp": current_time,
        }

        # Save token in schwab-py format
        token_file = Path("schwab_tokens.json")
        with open(token_file, "w") as f:
            json.dump(schwab_token, f, indent=2)

        print(f"\n✅ Authentication successful!")
        print(f"Token saved to {token_file} in schwab-py format")

        # Create client with the token and test it
        try:
            from schwab.auth import client_from_token_file

            client = client_from_token_file(
                api_key=api_key, app_secret=app_secret, token_path=str(token_file)
            )

            # Test the client
            accounts_response = client.get_account_numbers()
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                account_count = len(accounts_data) if accounts_data else 0
                print(f"✅ Test successful! Found {account_count} account(s).")
            else:
                print(
                    f"✅ Token saved successfully, but account test returned status {accounts_response.status_code}"
                )
                print(
                    "This might be normal if you don't have trading accounts linked or need additional permissions."
                )

        except Exception as e:
            print(f"⚠️  Token saved but test failed: {e}")
            print("This might be normal if you don't have trading accounts linked.")

        return True

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you copied the complete callback URL")
        print("2. Verify your API credentials are correct")
        print("3. Check that your app is approved and active")
        print("4. Ensure the callback URL exactly matches your Schwab app config")
        return False


def check_existing_token():
    """Check if there's already a valid token."""
    token_file = Path("schwab_tokens.json")
    if token_file.exists():
        print(f"Found existing token file: {token_file}")
        choice = input("Do you want to use the existing token? (y/n): ").strip().lower()
        if choice == "y":
            return True
    return False


def main():
    """Main entry point."""
    print("Schwab API Manual Authentication")
    print("=" * 40)
    print("This script works with callback URLs that don't have port numbers.")
    print("Registered callback URL: https://127.0.0.1")
    print("It automatically saves tokens in the correct schwab-py format.")
    print()

    if check_existing_token():
        print(
            "Using existing token. If API calls fail, delete schwab_tokens.json and re-run this script."
        )
        return

    success = manual_auth()
    if success:
        print("\n🎉 Authentication complete! You can now run examples/basic_usage.py")
        print("No token conversion needed - it's already in the correct format!")
    else:
        print(
            "\n💡 If this continues to fail, consider updating your callback URL to include :8080"
        )


if __name__ == "__main__":
    main()
