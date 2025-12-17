#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup OpenAI Codex API for global terminal access.
Installs CLI tools and configures environment variables.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.02
Unique ID: CTB-CODEX-GLOBAL
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

def install_openai_package():
    """Install OpenAI package globally."""
    print("\n[1/4] Installing OpenAI package...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", 
            "openai"
        ])
        print("[OK] OpenAI package installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install: {e}")
        return False

def create_codex_cli_script():
    """Create a global CLI script for Codex/OpenAI."""
    print("\n[2/4] Creating global Codex CLI script...")
    
    # Determine script location based on OS
    if platform.system() == "Windows":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "codex.py"
        bat_path = script_dir / "codex.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "codex"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Python script
    script_content = '''#!/usr/bin/env python3
"""Global Codex CLI - Access OpenAI Codex from any terminal."""
import sys
import os
from openai import OpenAI

# Load API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    print("Get your API key from: https://platform.openai.com/api-keys")
    sys.exit(1)

client = OpenAI(api_key=api_key)

def main():
    if len(sys.argv) < 2:
        print("Codex CLI - OpenAI Code Generation")
        print("Usage: codex <prompt>")
        print("Example: codex 'Write a Python function to sort a list'")
        print("")
        print("Models available:")
        print("  - gpt-4 (default)")
        print("  - gpt-4-turbo")
        print("  - gpt-3.5-turbo")
        print("  - code-davinci-002 (legacy Codex)")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    # Check for model flag
    model = "gpt-4"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
            # Remove model args from prompt
            prompt = " ".join([arg for arg in sys.argv[1:] if arg != "--model" and sys.argv[sys.argv.index(arg) - 1] != "--model" or sys.argv.index(arg) <= idx])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant. Provide clear, concise code with explanations when helpful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        print(response.choices[0].message.content)
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
    print("OPENAI API KEY SETUP")
    print("="*80)
    print("\n1. Get your API key from:")
    print("   https://platform.openai.com/api-keys")
    print("\n2. Set environment variable:")
    
    if platform.system() == "Windows":
        print("\n   For PowerShell (current session):")
        print('   $env:OPENAI_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (PowerShell):")
        print('   [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")')
        print("\n   Or add to System Properties > Environment Variables")
    else:
        print("\n   For current session:")
        print('   export OPENAI_API_KEY="your-api-key-here"')
        print("\n   For permanent setup (add to ~/.bashrc or ~/.zshrc):")
        print('   echo \'export OPENAI_API_KEY="your-api-key-here"\' >> ~/.bashrc')
        print('   source ~/.bashrc')
    
    print("\n" + "="*80 + "\n")
    
    # Check if already set
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"[OK] API key found in environment: {api_key[:10]}...")
        return True
    else:
        print("[INFO] API key not set - follow instructions above")
        return False

def create_test_script():
    """Create a test script to verify setup."""
    print("\n[4/4] Creating test script...")
    
    test_script = Path("test_codex.py")
    
    test_content = '''#!/usr/bin/env python3
"""Test OpenAI Codex API connection."""
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Say 'Hello from Codex!' in one sentence."}
        ],
        max_tokens=50
    )
    print("SUCCESS!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    print(f"[OK] Test script created: {test_script}")
    print("   Run: python test_codex.py")

def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*80)
    print("USAGE EXAMPLES")
    print("="*80)
    print("\n1. Basic code generation:")
    print("   codex 'Write a Python function to calculate fibonacci'")
    print("\n2. Code explanation:")
    print("   codex 'Explain this SQL query: SELECT * FROM users'")
    print("\n3. Code refactoring:")
    print("   codex 'Refactor this function to use async/await'")
    print("\n4. Different models:")
    print("   codex --model gpt-4-turbo 'Generate a REST API endpoint'")
    print("   codex --model gpt-3.5-turbo 'Simple function'")
    print("\n5. In Python scripts:")
    print("   from openai import OpenAI")
    print("   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))")
    print("   response = client.chat.completions.create(")
    print("       model='gpt-4',")
    print("       messages=[{'role': 'user', 'content': 'Your prompt'}]")
    print("   )")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("CODEX GLOBAL SETUP")
    print("="*80)
    print("\nSetting up OpenAI Codex API for global terminal access...")
    
    if not check_python_version():
        return
    
    if not install_openai_package():
        return
    
    script_path, script_dir = create_codex_cli_script()
    
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
    print("  3. Test: python test_codex.py")
    print("  4. Use globally: codex 'your prompt'")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

