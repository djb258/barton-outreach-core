#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Obsidian for global terminal access.
Creates CLI commands to open vaults, create notes, and manage Obsidian from terminal.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.06.02
Unique ID: CTB-OBSIDIAN-GLOBAL
Enforcement: ORBT
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime

def find_obsidian_executable():
    """Find Obsidian executable path."""
    print("\n[1/4] Finding Obsidian installation...")
    
    if platform.system() == "Windows":
        paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "obsidian" / "Obsidian.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Obsidian" / "Obsidian.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Obsidian" / "Obsidian.exe",
        ]
        
        for path in paths:
            if path.exists():
                print(f"[OK] Found at: {path}")
                return str(path)
    else:
        # Unix-like systems
        try:
            result = subprocess.run(["which", "obsidian"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Found at: {result.stdout.strip()}")
                return result.stdout.strip()
        except:
            pass
        
        # Check common locations
        common_paths = [
            "/usr/bin/obsidian",
            "/usr/local/bin/obsidian",
            Path.home() / ".local" / "bin" / "obsidian",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                print(f"[OK] Found at: {path}")
                return str(path)
    
    print("[ERROR] Obsidian not found")
    return None

def create_obsidian_cli_script(obsidian_path):
    """Create global Obsidian CLI script."""
    print("\n[2/4] Creating global Obsidian CLI script...")
    
    if platform.system() == "Windows":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "obsidian.py"
        bat_path = script_dir / "obsidian.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "obsidian"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    # Default vault path
    default_vault = Path.home() / "Documents" / "Obsidian Vault"
    
    script_content = f'''#!/usr/bin/env python3
"""Global Obsidian CLI - Open vaults and manage notes from terminal."""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

OBSIDIAN_PATH = r"{obsidian_path}"
DEFAULT_VAULT = Path(r"{default_vault}")

def open_vault(vault_path=None):
    """Open Obsidian vault."""
    if vault_path is None:
        vault_path = DEFAULT_VAULT
    else:
        vault_path = Path(vault_path).expanduser().resolve()
    
    if not vault_path.exists():
        print(f"ERROR: Vault not found at {{vault_path}}")
        print("Create vault first or specify correct path")
        return False
    
    if platform.system() == "Windows":
        subprocess.Popen([OBSIDIAN_PATH, str(vault_path)])
    else:
        subprocess.Popen([OBSIDIAN_PATH, str(vault_path)])
    
    print(f"Opening vault: {{vault_path}}")
    return True

def create_note(note_name, vault_path=None, folder="00-Inbox"):
    """Create a new note in vault."""
    if vault_path is None:
        vault_path = DEFAULT_VAULT
    else:
        vault_path = Path(vault_path).expanduser().resolve()
    
    if not vault_path.exists():
        print(f"ERROR: Vault not found at {{vault_path}}")
        return False
    
    # Ensure folder exists
    folder_path = vault_path / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Create note
    note_path = folder_path / f"{{note_name}}.md"
    if note_path.exists():
        print(f"Note already exists: {{note_path}}")
    else:
        note_path.write_text(f"# {{note_name}}\\n\\n")
        print(f"Created note: {{note_path}}")
    
    # Open in Obsidian
    open_vault(vault_path)
    
    # Try to open the specific note (Obsidian may not support this directly)
    return True

def create_daily_note(vault_path=None):
    """Create today's daily note."""
    today = datetime.now().strftime("%Y-%m-%d")
    folder = "01-Daily"
    return create_note(today, vault_path, folder)

def list_vaults():
    """List available vaults."""
    docs = Path.home() / "Documents"
    vaults = []
    
    for item in docs.iterdir():
        if item.is_dir() and ("obsidian" in item.name.lower() or "vault" in item.name.lower()):
            vaults.append(item)
    
    if vaults:
        print("Available vaults:")
        for vault in vaults:
            print(f"  - {{vault}}")
    else:
        print("No vaults found in Documents folder")
        print(f"Default vault: {{DEFAULT_VAULT}}")
    
    return vaults

def main():
    import platform
    
    if len(sys.argv) < 2:
        print("Obsidian CLI - Terminal Access to Obsidian")
        print("Usage:")
        print("  obsidian open [vault_path]     Open vault (default: Documents/Obsidian Vault)")
        print("  obsidian new <name> [folder]  Create new note")
        print("  obsidian daily                 Create today's daily note")
        print("  obsidian list                  List available vaults")
        print("  obsidian vault                 Open default vault")
        print("")
        print("Examples:")
        print("  obsidian vault                 Open default vault")
        print("  obsidian new 'Meeting Notes'   Create note in Inbox")
        print("  obsidian new 'Project' Projects Create note in Projects folder")
        print("  obsidian daily                 Create today's daily note")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "open" or command == "vault":
        vault_path = sys.argv[2] if len(sys.argv) > 2 else None
        open_vault(vault_path)
    
    elif command == "new":
        if len(sys.argv) < 3:
            print("ERROR: Note name required")
            print("Usage: obsidian new <note_name> [folder]")
            sys.exit(1)
        note_name = sys.argv[2]
        folder = sys.argv[3] if len(sys.argv) > 3 else "00-Inbox"
        create_note(note_name, None, folder)
    
    elif command == "daily":
        create_daily_note()
    
    elif command == "list":
        list_vaults()
    
    else:
        print(f"ERROR: Unknown command '{{command}}'")
        print("Run 'obsidian' for usage information")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(script_path, 0o755)
    
    if bat_path:
        with open(bat_path, 'w') as f:
            f.write(f'@python "{script_path}" %*\n')
    
    print(f"[OK] CLI script created: {script_path}")
    if bat_path:
        print(f"[OK] Batch file created: {bat_path}")
    
    return script_path, script_dir

def add_to_path(script_dir):
    """Add scripts directory to PATH if not already there."""
    print("\n[3/4] Checking PATH configuration...")
    
    if platform.system() == "Windows":
        current_path = os.environ.get("PATH", "")
        scripts_str = str(script_dir)
        
        if scripts_str in current_path:
            print("[OK] Scripts directory already in PATH")
            return True
        
        # Add to user PATH
        user_path = os.environ.get("Path", "")
        if scripts_str not in user_path:
            new_path = f"{user_path};{scripts_str}"
            os.environ["Path"] = new_path
            # Also set permanently
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                current_value = winreg.QueryValueEx(key, "Path")[0]
                if scripts_str not in current_value:
                    new_value = f"{current_value};{scripts_str}"
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_value)
                winreg.CloseKey(key)
                print(f"[OK] Added to PATH permanently")
                print(f"     Restart terminal to use 'obsidian' command directly")
            except Exception as e:
                print(f"[WARNING] Could not update PATH permanently: {e}")
                print(f"     Add manually: {scripts_str}")
        else:
            print("[OK] Already in user PATH")
    else:
        print("[INFO] Add to PATH manually:")
        print(f"     export PATH=\"$PATH:{script_dir}\"")
    
    return True

def create_usage_examples():
    """Show usage examples."""
    print("\n[4/4] Usage Examples")
    print("="*80)
    print("\nAfter restarting terminal, you can use:")
    print("\n  obsidian vault              # Open default vault")
    print("  obsidian open               # Open default vault")
    print("  obsidian open /path/to/vault # Open specific vault")
    print("  obsidian new 'Note Name'     # Create note in Inbox")
    print("  obsidian new 'Project' Projects # Create note in Projects folder")
    print("  obsidian daily              # Create today's daily note")
    print("  obsidian list               # List available vaults")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("OBSIDIAN GLOBAL SETUP")
    print("="*80)
    print("\nSetting up Obsidian for global terminal access...")
    
    obsidian_path = find_obsidian_executable()
    if not obsidian_path:
        print("\n[ERROR] Obsidian not found. Please install Obsidian first.")
        print("Download from: https://obsidian.md/download")
        return
    
    script_path, script_dir = create_obsidian_cli_script(obsidian_path)
    add_to_path(script_dir)
    create_usage_examples()
    
    print("="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nCLI script location: {script_dir}")
    print("\nNext steps:")
    print("  1. Restart your terminal")
    print("  2. Use 'obsidian' command from anywhere")
    print("  3. Try: obsidian vault")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

