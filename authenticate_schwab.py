#!/usr/bin/env python3
"""
Schwab OAuth Authentication for TradeAssist

This script authenticates with Schwab API using your configured redirect URI
and saves tokens for the TradeAssist application.
"""

import json
import time
import webbrowser
import requests
import secrets
import base64
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode
from dotenv import load_dotenv

def main():
    """Run Schwab OAuth authentication flow."""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    client_id = os.getenv('SCHWAB_CLIENT_ID')
    client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
    callback_url = os.getenv('SCHWAB_REDIRECT_URI', 'http://127.0.0.1')
    
    if not client_id or not client_secret:
        print("❌ Error: SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET must be set in .env file")
        return
    
    print("🚀 Schwab OAuth Authentication for TradeAssist")
    print("=" * 50)
    print(f"📋 Client ID: {client_id}")
    print(f"🔄 Callback URL: {callback_url}")
    print()
    
    print("Manual authentication process:")
    print("1. I'll open a browser with the Schwab login URL")
    print("2. Log into your Schwab account")
    print("3. Authorize the application")
    print("4. You'll be redirected to a page that won't load (this is normal)")
    print("5. Copy the ENTIRE URL from your browser's address bar")
    print("6. Paste it here when prompted")
    print()
    
    input("Press Enter to open the authorization URL...")
    
    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Build the authorization URL manually
        auth_params = {
            'client_id': client_id,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'state': state,
            'scope': 'readonly'  # Basic scope for market data
        }
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(auth_params)}"
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
        
        if 'code' not in query_params:
            raise ValueError("No authorization code found in callback URL")
        
        if 'state' not in query_params or query_params['state'][0] != state:
            raise ValueError("State parameter mismatch - possible security issue")
        
        auth_code = query_params['code'][0]
        print(f"\nExtracted authorization code: {auth_code[:10]}...")
        
        # Exchange authorization code for access token
        token_url = "https://api.schwabapi.com/v1/oauth/token"
        
        # Prepare credentials for Basic Auth
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': callback_url
        }
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print("Exchanging authorization code for access token...")
        response = requests.post(token_url, data=token_data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.status_code} - {response.text}")
        
        raw_token = response.json()
        
        # Convert to format expected by schwab-package
        current_time = int(time.time())
        expires_in = raw_token.get('expires_in', 1800)
        
        # Create token in the format schwab-package expects
        token_data = {
            "access_token": raw_token["access_token"],
            "refresh_token": raw_token["refresh_token"],
            "id_token": raw_token.get("id_token", ""),
            "token_type": raw_token.get("token_type", "Bearer"),
            "scope": raw_token.get("scope", "api"),
            "expires_in": expires_in,
            "expires_at": current_time + expires_in,
            "creation_timestamp": current_time
        }
        
        # Save token in the same location TradeAssist expects
        token_file = Path("data") / "schwab_tokens.json"
        token_file.parent.mkdir(exist_ok=True)
        
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"\n✅ Authentication successful!")
        print(f"💾 Token saved to: {token_file}")
        print()
        print("🎉 You can now start TradeAssist with:")
        print("   python run.py")
        print()
        print("The system will now be able to connect to real Schwab API for market data streaming!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n📋 Troubleshooting:")
        print("1. Make sure you copied the complete callback URL")
        print("2. Verify your API credentials are correct")
        print("3. Check that your app is approved and active")
        print("4. Ensure the callback URL exactly matches your Schwab app config")
        return False

if __name__ == "__main__":
    main()