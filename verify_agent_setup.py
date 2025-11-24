#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive verification script for all agent setups.
Checks environment variables, packages, scripts, and API connections.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.05.04
Unique ID: CTB-VERIFY-AGENTS
Enforcement: ORBT
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment_variables():
    """Check if all API keys are set."""
    print("\n" + "="*80)
    print("ENVIRONMENT VARIABLES CHECK")
    print("="*80 + "\n")
    
    keys = {
        "ANTHROPIC_API_KEY": "Claude",
        "GOOGLE_API_KEY": "Gemini",
        "OPENAI_API_KEY": "Codex"
    }
    
    all_set = True
    for key, name in keys.items():
        value = os.getenv(key)
        if value:
            masked = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
            print(f"[OK] {name:10} - {key:25} is set ({masked})")
        else:
            print(f"[MISSING] {name:10} - {key:25} not set")
            all_set = False
    
    print()
    return all_set

def check_python_packages():
    """Check if all required packages are installed."""
    print("="*80)
    print("PYTHON PACKAGES CHECK")
    print("="*80 + "\n")
    
    packages = {
        "anthropic": "Claude",
        "google.generativeai": "Gemini",
        "openai": "Codex"
    }
    
    all_installed = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"[OK] {name:10} - {package:25} installed")
        except ImportError:
            print(f"[MISSING] {name:10} - {package:25} not installed")
            all_installed = False
    
    print()
    return all_installed

def check_cli_scripts():
    """Check if CLI scripts exist."""
    print("="*80)
    print("CLI SCRIPTS CHECK")
    print("="*80 + "\n")
    
    if sys.platform == "win32":
        scripts_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
    else:
        scripts_dir = Path.home() / ".local" / "bin"
    
    scripts = {
        "claude.py": "Claude",
        "gemini.py": "Gemini",
        "codex.py": "Codex"
    }
    
    all_exist = True
    for script, name in scripts.items():
        script_path = scripts_dir / script
        if script_path.exists():
            print(f"[OK] {name:10} - {script:25} exists")
        else:
            print(f"[MISSING] {name:10} - {script:25} not found at {script_path}")
            all_exist = False
    
    print(f"\nScripts directory: {scripts_dir}")
    print()
    return all_exist

def check_path():
    """Check if scripts directory is in PATH."""
    print("="*80)
    print("PATH CHECK")
    print("="*80 + "\n")
    
    if sys.platform == "win32":
        scripts_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
    else:
        scripts_dir = Path.home() / ".local" / "bin"
    
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    scripts_str = str(scripts_dir)
    
    if scripts_str in path_dirs:
        print(f"[OK] Scripts directory in PATH")
        print(f"     {scripts_dir}")
    else:
        print(f"[WARNING] Scripts directory not in PATH")
        print(f"     {scripts_dir}")
        print(f"\nTo add to PATH (PowerShell):")
        print(f'     $env:PATH += ";{scripts_dir}"')
        print(f"\nOr permanently:")
        print(f'     [Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User")')
    
    print()
    return scripts_str in path_dirs

def test_api_connections():
    """Test actual API connections."""
    print("="*80)
    print("API CONNECTION TESTS")
    print("="*80 + "\n")
    
    results = {}
    
    # Test Claude
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=20,
                messages=[{"role": "user", "content": "Say 'Claude OK'"}]
            )
            print("[OK] Claude - API connection successful")
            print(f"     Response: {message.content[0].text[:50]}...")
            results["Claude"] = True
        except Exception as e:
            print(f"[ERROR] Claude - API connection failed: {e}")
            results["Claude"] = False
    else:
        print("[SKIP] Claude - API key not set")
        results["Claude"] = None
    
    # Test Gemini
    if os.getenv("GOOGLE_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Say 'Gemini OK'")
            print("[OK] Gemini - API connection successful")
            print(f"     Response: {response.text[:50]}...")
            results["Gemini"] = True
        except Exception as e:
            print(f"[ERROR] Gemini - API connection failed: {e}")
            results["Gemini"] = False
    else:
        print("[SKIP] Gemini - API key not set")
        results["Gemini"] = None
    
    # Test Codex
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Say 'Codex OK'"}],
                max_tokens=20
            )
            print("[OK] Codex - API connection successful")
            print(f"     Response: {response.choices[0].message.content[:50]}...")
            results["Codex"] = True
        except Exception as e:
            print(f"[ERROR] Codex - API connection failed: {e}")
            results["Codex"] = False
    else:
        print("[SKIP] Codex - API key not set")
        results["Codex"] = None
    
    print()
    return results

def main():
    """Run all verification checks."""
    print("\n" + "="*80)
    print("AGENT SETUP VERIFICATION")
    print("="*80)
    print("\nVerifying all agent setups (Cursor, Claude, Gemini, Codex)...")
    
    env_ok = check_environment_variables()
    packages_ok = check_python_packages()
    scripts_ok = check_cli_scripts()
    path_ok = check_path()
    
    api_results = test_api_connections()
    
    # Summary
    print("="*80)
    print("VERIFICATION SUMMARY")
    print("="*80 + "\n")
    
    print("Setup Components:")
    print(f"  Environment Variables: {'[OK]' if env_ok else '[MISSING]'}")
    print(f"  Python Packages:       {'[OK]' if packages_ok else '[MISSING]'}")
    print(f"  CLI Scripts:           {'[OK]' if scripts_ok else '[MISSING]'}")
    print(f"  PATH Configuration:    {'[OK]' if path_ok else '[WARNING]'}")
    
    print("\nAPI Connections:")
    for agent, result in api_results.items():
        if result is True:
            print(f"  {agent:10} - [OK] Connected")
        elif result is False:
            print(f"  {agent:10} - [ERROR] Connection failed")
        else:
            print(f"  {agent:10} - [SKIP] API key not set")
    
    print()
    
    # Recommendations
    if not env_ok:
        print("="*80)
        print("RECOMMENDATIONS")
        print("="*80 + "\n")
        print("1. Set missing environment variables:")
        print("   PowerShell (permanent):")
        print('   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key", "User")')
        print('   [System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key", "User")')
        print('   [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key", "User")')
        print("\n2. Restart your terminal after setting variables")
        print("\n3. Get API keys from:")
        print("   Claude:  https://console.anthropic.com/settings/keys")
        print("   Gemini:  https://makersuite.google.com/app/apikey")
        print("   Codex:   https://platform.openai.com/api-keys")
    
    if not path_ok:
        print("\n4. Add scripts to PATH (see PATH CHECK section above)")
    
    print("\n" + "="*80 + "\n")
    
    # Final status
    all_ready = env_ok and packages_ok and scripts_ok and all(r for r in api_results.values() if r is not None)
    
    if all_ready:
        print("✅ ALL AGENTS READY TO USE!")
        print("\nYou can now use:")
        print("  - claude 'your prompt'")
        print("  - gemini 'your prompt'")
        print("  - codex 'your prompt'")
        print("  - Cursor (built-in IDE)")
    else:
        print("[WARNING] SETUP INCOMPLETE")
        print("\nPlease complete the missing steps above.")
    
    print()

if __name__ == "__main__":
    main()

