#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Anthropic Claude API for global terminal access.
Installs CLI tools and configures environment variables.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.03
Unique ID: CTB-CLAUDE-GLOBAL
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

def install_anthropic_package():
    """Install Anthropic package globally."""
    print("\n[1/4] Installing Anthropic package...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", 
            "anthropic"
        ])
        print("[OK] Anthropic package installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install: {e}")
        return False

def create_claude_cli_script():
    """Create a global CLI script for Claude."""
    print("\n[2/4] Creating global Claude CLI script...")
    
    # Determine script location based on OS
    if platform.system() == "Windows":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "claude.py"
        bat_path = script_dir / "claude.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "claude"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Python script
    script_content = '''#!/usr/bin/env python3
"""Global Claude CLI - Access Anthropic Claude from any terminal."""
import sys
import os
from anthropic import Anthropic

# Load API key from environment
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    print("Get your API key from: https://console.anthropic.com/settings/keys")
    sys.exit(1)

client = Anthropic(api_key=api_key)

def main():
    if len(sys.argv) < 2:
        print("Claude CLI - Anthropic Claude AI")
        print("Usage: claude <prompt>")
        print("Example: claude 'Explain machine learning'")
        print("")
        print("Models available:")
        print("  - claude-3-5-sonnet-20241022 (default)")
        print("  - claude-3-5-haiku-20241022")
        print("  - claude-3-opus-20240229")
        print("  - claude-3-sonnet-20240229")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    # Check for model flag
    model = "claude-3-5-sonnet-20241022"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
            # Remove model args from prompt
            prompt_parts = []
            skip_next = False
            for i, arg in enumerate(sys.argv[1:], 1):
                if skip_next:
                    skip_next = False
                    continue
                if arg == "--model":
                    skip_next = True
                    continue
                if i > idx + 1:
                    prompt_parts.append(arg)
            prompt = " ".join(prompt_parts) if prompt_parts else prompt
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        print(message.content[0].text)
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
    print("ANTHROPIC API KEY SETUP")
    print("="*80)
    print("\n1. Get your API key from:")
    print("   https://console.anthropic.com/settings/keys")
    print("\n2. Set environment variable:")
    
    if platform.system() == "Windows":
        print("\n   For PowerShell (current session):")
        print('   $env:ANTHROPIC_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (PowerShell):")
        print('   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-api-key-here", "User")')
        print("\n   Or add to System Properties > Environment Variables")
    else:
        print("\n   For current session:")
        print('   export ANTHROPIC_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (add to ~/.bashrc or ~/.zshrc):")
        print('   echo \'export ANTHROPIC_API_KEY="your-api-key-here"\' >> ~/.bashrc')
        print('   source ~/.bashrc')
    
    print("\n" + "="*80 + "\n")
    
    # Check if already set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"[OK] API key found in environment: {api_key[:10]}...")
        return True
    else:
        print("[INFO] API key not set - follow instructions above")
        return False

def create_test_script():
    """Create a test script to verify setup."""
    print("\n[4/4] Creating test script...")
    
    test_script = Path("test_claude.py")
    
    test_content = '''#!/usr/bin/env python3
"""Test Anthropic Claude API connection."""
import os
from anthropic import Anthropic

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    exit(1)

try:
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[
            {"role": "user", "content": "Say 'Hello from Claude!' in one sentence."}
        ]
    )
    print("SUCCESS!")
    print(f"Response: {message.content[0].text}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print(f"[OK] Test script created: {test_script}")
    print("   Run: python test_claude.py")

def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*80)
    print("USAGE EXAMPLES")
    print("="*80)
    print("\n1. Basic query:")
    print("   claude 'What is machine learning?'")
    print("\n2. Code generation:")
    print("   claude 'Write a Python function to calculate fibonacci'")
    print("\n3. Analysis:")
    print("   claude 'Analyze this SQL query: SELECT * FROM users'")
    print("\n4. Different models:")
    print("   claude --model claude-3-5-haiku-20241022 'Quick question'")
    print("   claude --model claude-3-opus-20240229 'Complex analysis'")
    print("\n5. In Python scripts:")
    print("   from anthropic import Anthropic")
    print("   client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))")
    print("   message = client.messages.create(")
    print("       model='claude-3-5-sonnet-20241022',")
    print("       max_tokens=4096,")
    print("       messages=[{'role': 'user', 'content': 'Your prompt'}]")
    print("   )")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("CLAUDE GLOBAL SETUP")
    print("="*80)
    print("\nSetting up Anthropic Claude API for global terminal access...")
    
    if not check_python_version():
        return
    
    if not install_anthropic_package():
        return
    
    script_path, script_dir = create_claude_cli_script()
    
    has_key = setup_environment_variables()
    
    create_test_script()
    
    show_usage_examples()
    
    print("="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nCLI script location: {script_dir}")
    print("\nNext steps:")
    print("  1. Add API key to environment (see instructions above)")
    print("  2. Script directory already in PATH (from Gemini/Codex setup)")
    print("  3. Test: python test_claude.py")
    print("  4. Use globally: claude 'your prompt'")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

