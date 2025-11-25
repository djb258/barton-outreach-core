#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update agent authentication to support account-based login.
For Gemini: OAuth with Google account
For Claude: Check if using web interface or alternative auth

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.06
Unique ID: CTB-UPDATE-AUTH
Enforcement: ORBT
"""

import os
import sys
from pathlib import Path

def update_gemini_for_oauth():
    """Update Gemini script to try OAuth if API key not available."""
    print("\n[1/2] Updating Gemini for OAuth authentication...")
    
    script_path = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts" / "gemini.py"
    
    if not script_path.exists():
        print(f"[ERROR] gemini.py not found at {script_path}")
        return False
    
    # Read current script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check if already has OAuth support
    if "google.auth" in content or "OAuth" in content:
        print("[INFO] Gemini script already has OAuth support")
        return True
    
    # Create OAuth version
    oauth_content = '''#!/usr/bin/env python3
"""Global Gemini CLI - Uses API key or OAuth (Google account login)."""
import sys
import os
from pathlib import Path

# Try API key first
api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

if not api_key:
    # Try OAuth authentication
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        import google.generativeai as genai
        
        TOKEN_DIR = Path.home() / ".gemini_oauth"
        TOKEN_FILE = TOKEN_DIR / "token.json"
        CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"
        SCOPES = ['https://www.googleapis.com/auth/generative-language']
        
        creds = None
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except:
                pass
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif CREDENTIALS_FILE.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
                TOKEN_DIR.mkdir(exist_ok=True)
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            else:
                print("ERROR: No API key or OAuth credentials found")
                print("Option 1: Set GOOGLE_API_KEY environment variable")
                print("Option 2: Set up OAuth:")
                print(f"  - Download credentials.json from Google Cloud Console")
                print(f"  - Save to: {CREDENTIALS_FILE}")
                sys.exit(1)
        
        genai.configure(credentials=creds)
        use_oauth = True
    except ImportError:
        print("ERROR: GOOGLE_API_KEY not set and OAuth packages not installed")
        print("Install: pip install google-auth google-auth-oauthlib")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: OAuth authentication failed: {e}")
        sys.exit(1)
else:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    use_oauth = False

def main():
    if len(sys.argv) < 2:
        print("Gemini CLI - Google Generative AI")
        print("Usage: gemini <prompt>")
        print("Example: gemini 'Explain quantum computing'")
        if not api_key:
            print("")
            print("Authentication: Using OAuth (Google account login)")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    # Backup original
    backup_path = script_path.with_suffix('.py.backup')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    # Write updated version
    with open(script_path, 'w') as f:
        f.write(oauth_content)
    
    print(f"[OK] Gemini script updated with OAuth support")
    print(f"[OK] Backup saved to: {backup_path}")
    return True

def check_claude_alternatives():
    """Check for Claude alternative authentication methods."""
    print("\n[2/2] Checking Claude authentication options...")
    
    print("\nClaude Authentication Options:")
    print("="*80)
    print("\n1. API Key (Standard):")
    print("   - Get from: https://console.anthropic.com/settings/keys")
    print("   - Set: ANTHROPIC_API_KEY environment variable")
    print("\n2. Web Interface:")
    print("   - Use Claude at: https://claude.ai")
    print("   - No CLI needed - use browser interface")
    print("\n3. Cursor Integration:")
    print("   - Cursor IDE has built-in Claude support")
    print("   - Use chat panel or Cmd/Ctrl + K")
    print("\n" + "="*80)
    
    print("\n[INFO] Claude can be used via:")
    print("   - Web interface: https://claude.ai (no API key needed)")
    print("   - Cursor IDE: Built-in Claude support (no API key needed)")
    print("   - CLI: Requires ANTHROPIC_API_KEY")
    
    return True

def main():
    """Main update function."""
    print("\n" + "="*80)
    print("AGENT AUTHENTICATION UPDATE")
    print("="*80)
    print("\nUpdating agents for account-based authentication...")
    
    gemini_updated = update_gemini_for_oauth()
    claude_checked = check_claude_alternatives()
    
    print("\n" + "="*80)
    print("UPDATE SUMMARY")
    print("="*80)
    
    if gemini_updated:
        print("\n[OK] Gemini updated to support OAuth (Google account login)")
        print("   - Will try API key first")
        print("   - Falls back to OAuth if no API key")
        print("   - First OAuth run will prompt for Google login")
    
    print("\n📝 Next Steps:")
    print("   1. For Gemini OAuth:")
    print("      - Go to: https://console.cloud.google.com/apis/credentials")
    print("      - Create OAuth 2.0 Client ID (Desktop app)")
    print("      - Download credentials.json")
    print("      - Save to: ~/.gemini_oauth/credentials.json")
    print("   2. For Claude:")
    print("      - Use web interface: https://claude.ai")
    print("      - Or set ANTHROPIC_API_KEY if you have one")
    print("      - Or use Cursor's built-in Claude")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

