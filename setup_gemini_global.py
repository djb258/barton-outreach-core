#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Google Gemini API for global terminal access.
Installs CLI tools and configures environment variables.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.01
Unique ID: CTB-GEMINI-GLOBAL
Enforcement: ORBT
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[ERROR] Python 3.8+ required")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_gemini_package():
    """Install Google Generative AI package globally."""
    print("\n[1/4] Installing Google Generative AI package...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", 
            "google-generativeai", "google-ai-generativelanguage"
        ])
        print("[OK] Google Generative AI package installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install: {e}")
        return False

def create_gemini_cli_script():
    """Create a global CLI script for Gemini."""
    print("\n[2/4] Creating global Gemini CLI script...")
    
    # Determine script location based on OS
    if platform.system() == "Windows":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "gemini.py"
        bat_path = script_dir / "gemini.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "gemini"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Python script
    script_content = '''#!/usr/bin/env python3
"""Global Gemini CLI - Access Google Gemini from any terminal."""
import sys
import os
import google.generativeai as genai

# Load API key from environment
api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not set")
    print("Get your API key from: https://makersuite.google.com/app/apikey")
    sys.exit(1)

genai.configure(api_key=api_key)

def main():
    if len(sys.argv) < 2:
        print("Gemini CLI - Google Generative AI")
        print("Usage: gemini <prompt>")
        print("Example: gemini 'Explain quantum computing'")
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
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix
    if platform.system() != "Windows":
        os.chmod(script_path, 0o755)
    
    # Create batch file for Windows
    if bat_path:
        with open(bat_path, 'w') as f:
            f.write(f'@python "{script_path}" %*\n')
    
    print(f"[OK] CLI script created: {script_path}")
    if bat_path:
        print(f"[OK] Batch file created: {bat_path}")
    
    return script_path, script_dir

def setup_environment_variables():
    """Guide user to set up API key."""
    print("\n[3/4] Setting up environment variables...")
    
    print("\n" + "="*80)
    print("GEMINI API KEY SETUP")
    print("="*80)
    print("\n1. Get your API key from:")
    print("   https://makersuite.google.com/app/apikey")
    print("\n2. Set environment variable:")
    
    if platform.system() == "Windows":
        print("\n   For PowerShell (current session):")
        print('   $env:GOOGLE_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (PowerShell):")
        print('   [System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-api-key-here", "User")')
        print("\n   Or add to System Properties > Environment Variables")
    else:
        print("\n   For current session:")
        print('   export GOOGLE_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (add to ~/.bashrc or ~/.zshrc):")
        print('   echo \'export GOOGLE_API_KEY="your-api-key-here"\' >> ~/.bashrc')
        print('   source ~/.bashrc')
    
    print("\n" + "="*80 + "\n")
    
    # Check if already set
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"[OK] API key found in environment: {api_key[:10]}...")
        return True
    else:
        print("[INFO] API key not set - follow instructions above")
        return False

def create_test_script():
    """Create a test script to verify setup."""
    print("\n[4/4] Creating test script...")
    
    test_script = Path("test_gemini.py")
    
    test_content = '''#!/usr/bin/env python3
"""Test Gemini API connection."""
import os
import google.generativeai as genai

api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY not set")
    exit(1)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say 'Hello from Gemini!' in one sentence.")
    print("SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print(f"[OK] Test script created: {test_script}")
    print("   Run: python test_gemini.py")

def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*80)
    print("USAGE EXAMPLES")
    print("="*80)
    print("\n1. Basic query:")
    print("   gemini 'What is machine learning?'")
    print("\n2. Code generation:")
    print("   gemini 'Write a Python function to calculate fibonacci'")
    print("\n3. Analysis:")
    print("   gemini 'Analyze this SQL query: SELECT * FROM users'")
    print("\n4. In Python scripts:")
    print("   import google.generativeai as genai")
    print("   genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))")
    print("   model = genai.GenerativeModel('gemini-pro')")
    print("   response = model.generate_content('Your prompt')")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("GEMINI GLOBAL SETUP")
    print("="*80)
    print("\nSetting up Google Gemini API for global terminal access...")
    
    if not check_python_version():
        return
    
    if not install_gemini_package():
        return
    
    script_path, script_dir = create_gemini_cli_script()
    
    has_key = setup_environment_variables()
    
    create_test_script()
    
    show_usage_examples()
    
    print("="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nCLI script location: {script_dir}")
    print("\nNext steps:")
    print("  1. Add API key to environment (see instructions above)")
    print("  2. Add script directory to PATH:")
    if platform.system() == "Windows":
        print(f"     $env:PATH += \";{script_dir}\"")
    else:
        print(f"     export PATH=\"$PATH:{script_dir}\"")
    print("  3. Test: python test_gemini.py")
    print("  4. Use globally: gemini 'your prompt'")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

