#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Obsidian for knowledge management and note-taking.
Creates vault structure and initial configuration.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.06.01
Unique ID: CTB-OBSIDIAN-SETUP
Enforcement: ORBT
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json

def check_obsidian_installed():
    """Check if Obsidian is installed."""
    print("\n[1/5] Checking for Obsidian installation...")
    
    if platform.system() == "Windows":
        # Check common installation paths
        paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "obsidian" / "Obsidian.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Obsidian" / "Obsidian.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Obsidian" / "Obsidian.exe",
        ]
        
        for path in paths:
            if path.exists():
                print(f"[OK] Obsidian found at: {path}")
                return str(path)
        
        print("[MISSING] Obsidian not found")
        return None
    else:
        # Unix-like systems
        try:
            result = subprocess.run(["which", "obsidian"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Obsidian found at: {result.stdout.strip()}")
                return result.stdout.strip()
        except:
            pass
        
        print("[MISSING] Obsidian not found")
        return None

def create_vault_structure(vault_path):
    """Create Obsidian vault structure."""
    print("\n[2/5] Creating vault structure...")
    
    vault = Path(vault_path)
    vault.mkdir(parents=True, exist_ok=True)
    
    # Create standard Obsidian directories
    directories = [
        "00-Inbox",
        "01-Daily",
        "02-Projects",
        "03-Areas",
        "04-Resources",
        "05-Archive",
        "Attachments",
        "Templates"
    ]
    
    for dir_name in directories:
        (vault / dir_name).mkdir(exist_ok=True)
        print(f"  Created: {dir_name}/")
    
    print(f"[OK] Vault structure created at: {vault}")
    return vault

def create_config_file(vault_path):
    """Create Obsidian configuration file."""
    print("\n[3/5] Creating Obsidian configuration...")
    
    config = {
        "newFileLocation": "folder",
        "newFileFolderPath": "00-Inbox",
        "attachmentFolderPath": "Attachments",
        "useMarkdownLinks": True,
        "alwaysUpdateLinks": True,
        "newLinkFormat": "shortest",
        "useTab": False,
        "tabSize": 2,
        "showLineNumber": True,
        "spellcheck": True,
        "foldHeading": True,
        "foldIndent": True,
        "showFrontmatter": True,
        "strictLineBreaks": False,
        "showIndentGuide": True,
        "showInlineTitle": True,
        "readableLineLength": True,
        "defaultViewMode": "source",
        "alwaysShowHeaders": True,
        "showUnsupportedFiles": True,
        "livePreview": True,
        "vimMode": False,
        "spellcheckLanguages": ["en-US"],
        "communityPluginSortOrder": "release",
        "promptDelete": True,
        "deleteFile": "trash",
        "newFileLocation": "folder",
        "newFileFolderPath": "00-Inbox"
    }
    
    config_path = Path(vault_path) / ".obsidian" / "app.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"[OK] Configuration created: {config_path}")
    return config_path

def create_initial_notes(vault_path):
    """Create initial notes and templates."""
    print("\n[4/5] Creating initial notes...")
    
    vault = Path(vault_path)
    
    # Welcome note
    welcome = vault / "Welcome.md"
    welcome.write_text("""# Welcome to Your Obsidian Vault

This is your personal knowledge base and note-taking system.

## Quick Start

- **Daily Notes**: Use `01-Daily/` for daily journaling
- **Projects**: Track active projects in `02-Projects/`
- **Areas**: Ongoing responsibilities in `03-Areas/`
- **Resources**: Reference materials in `04-Resources/`
- **Inbox**: Quick capture in `00-Inbox/`

## Tips

- Use `[[links]]` to connect notes
- Create templates in `Templates/`
- Use tags: `#tag` for categorization
- Search with `Ctrl+Shift+F`

## Keyboard Shortcuts

- `Ctrl+N`: New note
- `Ctrl+O`: Open quick switcher
- `Ctrl+P`: Command palette
- `Ctrl+E`: Toggle edit/preview
- `Ctrl+Shift+F`: Search in all files

Happy note-taking!
""")
    print("  Created: Welcome.md")
    
    # Daily note template
    daily_template = vault / "Templates" / "Daily Note.md"
    daily_template.write_text("""# {{date:YYYY-MM-DD}} - Daily Note

## Today's Focus
- 

## Tasks
- [ ] 
- [ ] 
- [ ] 

## Notes
- 

## Meetings
- 

## Tomorrow
- 

## Tags
#daily
""")
    print("  Created: Templates/Daily Note.md")
    
    # Project template
    project_template = vault / "Templates" / "Project.md"
    project_template.write_text("""# {{title}}

## Overview
- **Status**: 
- **Start Date**: 
- **Target Date**: 
- **Owner**: 

## Goals
- 

## Tasks
- [ ] 
- [ ] 
- [ ] 

## Notes
- 

## Resources
- 

## Tags
#project
""")
    print("  Created: Templates/Project.md")
    
    # Index note
    index = vault / "Index.md"
    index.write_text("""# Vault Index

## Quick Links
- [[Welcome]]
- [[Daily Notes|01-Daily/]]
- [[Projects|02-Projects/]]
- [[Areas|03-Areas/]]
- [[Resources|04-Resources/]]

## Recent Notes
(Use Obsidian's graph view to explore connections)

## Tags
#index
""")
    print("  Created: Index.md")
    
    print("[OK] Initial notes created")

def create_shortcut_script(vault_path, obsidian_path):
    """Create shortcut script to open vault."""
    print("\n[5/5] Creating shortcut script...")
    
    if platform.system() == "Windows":
        script_path = Path.home() / "Desktop" / "Open Obsidian Vault.bat"
        script_content = f'''@echo off
cd /d "{vault_path}"
start "" "{obsidian_path}" "{vault_path}"
'''
        script_path.write_text(script_content)
        print(f"[OK] Desktop shortcut created: {script_path}")
    else:
        script_path = Path.home() / ".local" / "bin" / "obsidian-vault"
        script_content = f'''#!/bin/bash
cd "{vault_path}"
{obsidian_path} "{vault_path}" &
'''
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        print(f"[OK] Script created: {script_path}")
    
    return script_path

def show_installation_instructions():
    """Show instructions if Obsidian is not installed."""
    print("\n" + "="*80)
    print("OBSIDIAN INSTALLATION INSTRUCTIONS")
    print("="*80)
    print("\nObsidian is not installed. Please install it:")
    print("\n1. Download Obsidian:")
    print("   https://obsidian.md/download")
    print("\n2. Install:")
    print("   - Windows: Run the installer")
    print("   - Mac: Drag to Applications")
    print("   - Linux: Use your package manager")
    print("\n3. After installation, run this script again")
    print("\n" + "="*80 + "\n")

def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("OBSIDIAN SETUP")
    print("="*80)
    print("\nSetting up Obsidian vault and configuration...")
    
    # Check if Obsidian is installed
    obsidian_path = check_obsidian_installed()
    
    if not obsidian_path:
        show_installation_instructions()
        return
    
    # Create vault in user's Documents
    vault_path = Path.home() / "Documents" / "Obsidian Vault"
    
    # Create structure
    vault = create_vault_structure(vault_path)
    
    # Create config
    create_config_file(vault_path)
    
    # Create initial notes
    create_initial_notes(vault_path)
    
    # Create shortcut
    create_shortcut_script(vault_path, obsidian_path)
    
    print("\n" + "="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    print(f"\nVault Location: {vault_path}")
    print("\nTo open your vault:")
    print(f"  1. Open Obsidian")
    print(f"  2. Click 'Open folder as vault'")
    print(f"  3. Select: {vault_path}")
    print(f"\nOr use the desktop shortcut: 'Open Obsidian Vault.bat'")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

