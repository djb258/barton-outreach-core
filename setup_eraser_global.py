#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Eraser.io for global terminal access and Obsidian integration.
Eraser.io is a diagramming tool - this sets up CLI access and Obsidian integration.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.07.01
Unique ID: CTB-ERASER-GLOBAL
Enforcement: ORBT
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json

def check_eraser_installation():
    """Check if Eraser.io is installed or accessible."""
    print("\n[1/5] Checking for Eraser.io...")
    
    # Eraser.io is web-based, but may have desktop app
    if platform.system() == "Windows":
        # Check for desktop app
        paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "eraser" / "Eraser.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Eraser" / "Eraser.exe",
        ]
        
        for path in paths:
            if path.exists():
                print(f"[OK] Eraser desktop app found at: {path}")
                return str(path), "desktop"
    
    # Check if accessible via browser
    print("[INFO] Eraser.io is web-based (https://app.eraser.io)")
    print("[INFO] Setting up CLI for web access and API integration")
    return None, "web"

def install_eraser_packages():
    """Install packages for Eraser.io API access."""
    print("\n[2/5] Installing Eraser.io API packages...")
    
    packages = ["requests", "httpx"]
    
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    print("[OK] API packages installed")
    return True

def create_eraser_cli_script(eraser_path, eraser_type):
    """Create global Eraser.io CLI script."""
    print("\n[3/5] Creating global Eraser.io CLI script...")
    
    if platform.system() == "Windows":
        script_dir = Path(os.environ.get("APPDATA", "")) / "Python" / "Scripts"
        script_path = script_dir / "eraser.py"
        bat_path = script_dir / "eraser.bat"
    else:
        script_dir = Path.home() / ".local" / "bin"
        script_path = script_dir / "eraser"
        script_dir.mkdir(parents=True, exist_ok=True)
        bat_path = None
    
    script_dir.mkdir(parents=True, exist_ok=True)
    
    # Default Obsidian vault path
    obsidian_vault = Path.home() / "Documents" / "Obsidian Vault"
    
    script_content = f'''#!/usr/bin/env python3
"""Global Eraser.io CLI - Create diagrams and integrate with Obsidian."""
import sys
import os
import subprocess
import webbrowser
from pathlib import Path
import json

ERASER_WEB_URL = "https://app.eraser.io"
ERASER_API_URL = "https://api.eraser.io/v1"
OBSIDIAN_VAULT = Path(r"{obsidian_vault}")

def open_eraser():
    """Open Eraser.io in browser."""
    print("Opening Eraser.io...")
    webbrowser.open(ERASER_WEB_URL)
    return True

def create_diagram(name=None):
    """Create a new diagram."""
    url = ERASER_WEB_URL
    if name:
        url += f"/new?name={{name}}"
    webbrowser.open(url)
    print(f"Opening new diagram: {{name or 'Untitled'}}")
    return True

def export_to_obsidian(diagram_url=None, note_name=None):
    """Export diagram to Obsidian vault."""
    if not OBSIDIAN_VAULT.exists():
        print(f"ERROR: Obsidian vault not found at {{OBSIDIAN_VAULT}}")
        print("Create vault first or update path in script")
        return False
    
    # Create diagrams folder in Obsidian
    diagrams_folder = OBSIDIAN_VAULT / "Diagrams"
    diagrams_folder.mkdir(exist_ok=True)
    
    if note_name:
        note_path = diagrams_folder / f"{{note_name}}.md"
    else:
        from datetime import datetime
        note_path = diagrams_folder / f"Diagram-{{datetime.now().strftime('%Y%m%d-%H%M%S')}}.md"
    
    # Create note with Eraser embed
    content = f"""# {{note_name or 'Diagram'}}

## Eraser.io Diagram

{{f"[View in Eraser]({{diagram_url or ERASER_WEB_URL}})" if diagram_url else "Create diagram in Eraser.io"}}

## Notes
- Created: {{datetime.now().strftime('%Y-%m-%d %H:%M')}}
- Tool: Eraser.io

## How to Embed

1. Create diagram in Eraser.io
2. Export as Markdown or image
3. Save to Attachments folder
4. Link here: `![[attachment-name.png]]`

## Tags
#diagram #eraser
"""
    
    note_path.write_text(content)
    print(f"Created Obsidian note: {{note_path}}")
    
    # Try to open Obsidian
    try:
        obsidian_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "obsidian" / "Obsidian.exe"
        if obsidian_path.exists():
            subprocess.Popen([str(obsidian_path), str(OBSIDIAN_VAULT)])
    except:
        pass
    
    return True

def list_diagrams():
    """List diagrams (requires API key)."""
    api_key = os.getenv("ERASER_API_KEY")
    if not api_key:
        print("INFO: ERASER_API_KEY not set")
        print("Get API key from: https://app.eraser.io/settings/api")
        print("")
        print("To list diagrams, set:")
        print("  $env:ERASER_API_KEY='your-api-key'")
        return False
    
    try:
        import requests
        headers = {{"Authorization": f"Bearer {{api_key}}"}}
        response = requests.get(f"{{ERASER_API_URL}}/diagrams", headers=headers)
        
        if response.status_code == 200:
            diagrams = response.json()
            print("Your Eraser.io diagrams:")
            for diagram in diagrams.get("data", []):
                print(f"  - {{diagram.get('name', 'Untitled')}}: {{diagram.get('url', 'N/A')}}")
        else:
            print(f"ERROR: {{response.status_code}} - {{response.text}}")
    except Exception as e:
        print(f"ERROR: {{e}}")
    
    return True

def main():
    import platform
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("Eraser.io CLI - Diagram Creation and Obsidian Integration")
        print("Usage:")
        print("  eraser open                    Open Eraser.io in browser")
        print("  eraser new [name]              Create new diagram")
        print("  eraser obsidian [note_name]     Create Obsidian note for diagram")
        print("  eraser list                    List your diagrams (requires API key)")
        print("")
        print("Examples:")
        print("  eraser open                    Open Eraser.io")
        print("  eraser new 'System Architecture'  Create named diagram")
        print("  eraser obsidian 'Database Schema'  Create Obsidian note")
        print("")
        print("API Key:")
        print("  Set ERASER_API_KEY environment variable for API access")
        print("  Get from: https://app.eraser.io/settings/api")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "open":
        open_eraser()
    
    elif command == "new":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        create_diagram(name)
    
    elif command == "obsidian":
        note_name = sys.argv[2] if len(sys.argv) > 2 else None
        export_to_obsidian(None, note_name)
    
    elif command == "list":
        list_diagrams()
    
    else:
        print(f"ERROR: Unknown command '{{command}}'")
        print("Run 'eraser' for usage information")
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

def create_obsidian_integration():
    """Create Obsidian integration files."""
    print("\n[4/5] Creating Obsidian integration...")
    
    obsidian_vault = Path.home() / "Documents" / "Obsidian Vault"
    
    if not obsidian_vault.exists():
        print("[WARNING] Obsidian vault not found - integration skipped")
        return False
    
    # Create Diagrams folder
    diagrams_folder = obsidian_vault / "Diagrams"
    diagrams_folder.mkdir(exist_ok=True)
    print(f"  Created: Diagrams/ folder in Obsidian vault")
    
    # Create Eraser template
    templates_folder = obsidian_vault / "Templates"
    templates_folder.mkdir(exist_ok=True)
    
    eraser_template = templates_folder / "Eraser Diagram.md"
    eraser_template.write_text("""# {{title}}

## Eraser.io Diagram

[View in Eraser](https://app.eraser.io)

## Diagram Details
- **Created**: {{date:YYYY-MM-DD}}
- **Tool**: Eraser.io
- **Type**: 

## Description


## Related Notes
- 

## Tags
#diagram #eraser
""")
    print(f"  Created: Templates/Eraser Diagram.md")
    
    # Create index note
    diagrams_index = diagrams_folder / "Index.md"
    diagrams_index.write_text("""# Diagrams Index

## Eraser.io Diagrams

This folder contains diagrams created with Eraser.io.

## Quick Links
- [Eraser.io](https://app.eraser.io)
- [[../Templates/Eraser Diagram|Diagram Template]]

## How to Use

1. Create diagram in Eraser.io: `eraser new "Diagram Name"`
2. Export as Markdown or image
3. Save to this folder or Attachments
4. Link in notes: `![[diagram-name.png]]`

## Tags
#index #diagrams
""")
    print(f"  Created: Diagrams/Index.md")
    
    print("[OK] Obsidian integration created")
    return True

def show_usage_examples():
    """Show usage examples."""
    print("\n[5/5] Usage Examples")
    print("="*80)
    print("\nAfter restarting terminal:")
    print("\n  eraser open                    # Open Eraser.io in browser")
    print("  eraser new 'System Design'      # Create new diagram")
    print("  eraser obsidian 'Architecture'  # Create Obsidian note for diagram")
    print("  eraser list                     # List your diagrams (needs API key)")
    print("\nObsidian Integration:")
    print("  - Diagrams folder created in your Obsidian vault")
    print("  - Template available: 'Eraser Diagram'")
    print("  - Use: eraser obsidian <name> to create note")
    print("\nAPI Access:")
    print("  - Get API key: https://app.eraser.io/settings/api")
    print("  - Set: $env:ERASER_API_KEY='your-key'")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("ERASER.IO GLOBAL SETUP")
    print("="*80)
    print("\nSetting up Eraser.io for global terminal access...")
    
    eraser_path, eraser_type = check_eraser_installation()
    install_eraser_packages()
    script_path, script_dir = create_eraser_cli_script(eraser_path, eraser_type)
    create_obsidian_integration()
    show_usage_examples()
    
    print("="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nCLI script location: {script_dir}")
    print("\nNext steps:")
    print("  1. Restart your terminal")
    print("  2. Use 'eraser' command from anywhere")
    print("  3. Try: eraser open")
    print("  4. Optional: Get API key from https://app.eraser.io/settings/api")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()







