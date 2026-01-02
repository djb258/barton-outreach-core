#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Gemini with OAuth/account-based authentication (no API key needed).
Uses Google account credentials instead of API key.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.05
Unique ID: CTB-GEMINI-OAUTH
Enforcement: ORBT
"""

import os
import sys
import subprocess
from pathlib import Path

def install_google_auth_packages():
    """Install packages needed for OAuth authentication."""
    print("\n[1/3] Installing Google OAuth packages...")
    
    packages = [
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-generativeai"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    print("[OK] OAuth packages installed")
    return True

def create_gemini_oauth_script():
    """Create Gemini CLI script with OAuth authentication."""
    print("\n[2/3] Creating Gemini OAuth CLI script...")
    
    if sys.platform == "win32":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "gemini-oauth.py"
        bat_path = script_dir / "gemini-oauth.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "gemini-oauth"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    script_content = '''#!/usr/bin/env python3
"""Gemini CLI with OAuth authentication - uses Google account login."""
import sys
import os
from pathlib import Path
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

# OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/generative-language']

# Token storage
TOKEN_DIR = Path.home() / ".gemini_oauth"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"

def get_credentials():
    """Get OAuth credentials, prompting for login if needed."""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        
        if not creds:
            # Check for credentials file
            if not CREDENTIALS_FILE.exists():
                print("ERROR: OAuth credentials file not found")
                print(f"Expected at: {CREDENTIALS_FILE}")
                print("")
                print("To set up OAuth:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download credentials.json")
                print(f"4. Save to: {CREDENTIALS_FILE}")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        TOKEN_DIR.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def main():
    if len(sys.argv) < 2:
        print("Gemini OAuth CLI - Google Account Authentication")
        print("Usage: gemini-oauth <prompt>")
        print("Example: gemini-oauth 'Explain machine learning'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        # Get OAuth credentials
        creds = get_credentials()
        
        # Configure Gemini with OAuth
        genai.configure(credentials=creds)
        
        # Use model
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    if sys.platform != "Windows":
        os.chmod(script_path, 0o755)
    
    if bat_path:
        with open(bat_path, 'w') as f:
            f.write(f'@python "{script_path}" %*\n')
    
    print(f"[OK] OAuth script created: {script_path}")
    print(f"[INFO] Credentials file needed at: {TOKEN_DIR / 'credentials.json'}")
    
    return script_path, TOKEN_DIR

def show_oauth_setup_instructions():
    """Show instructions for OAuth setup."""
    print("\n[3/3] OAuth Setup Instructions")
    print("="*80)
    print("\nTo use Gemini with your Google account (no API key needed):")
    print("\n1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/apis/credentials")
    print("\n2. Create OAuth 2.0 Client ID:")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Application type: 'Desktop app'")
    print("   - Name: 'Gemini CLI'")
    print("   - Click 'Create'")
    print("\n3. Download credentials:")
    print("   - Click download icon next to your OAuth client")
    print("   - Save as 'credentials.json'")
    print(f"   - Move to: {Path.home() / '.gemini_oauth' / 'credentials.json'}")
    print("\n4. First run will open browser for Google login")
    print("   - Authorize the application")
    print("   - Token will be saved for future use")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("GEMINI OAUTH SETUP")
    print("="*80)
    print("\nSetting up Gemini with Google account authentication...")
    
    install_google_auth_packages()
    script_path, token_dir = create_gemini_oauth_script()
    show_oauth_setup_instructions()
    
    print("="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nOAuth script: {script_path}")
    print(f"Credentials location: {token_dir}")
    print("\nNext steps:")
    print("  1. Follow OAuth setup instructions above")
    print("  2. Download credentials.json to the token directory")
    print("  3. Run: gemini-oauth 'your prompt'")
    print("  4. First run will prompt for Google login")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()







