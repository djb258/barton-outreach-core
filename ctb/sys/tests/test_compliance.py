"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/tests
Barton ID: 04.04.17
Unique ID: CTB-C5CB0390
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
"""

"""
Basic compliance test suite for Barton Outreach Core
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_project_structure():
    """Test that essential project directories exist"""
    root = Path(__file__).parent.parent
    
    assert (root / "src").exists(), "src directory should exist"
    assert (root / "docs").exists(), "docs directory should exist"
    assert (root / "tools").exists(), "tools directory should exist"
    assert (root / "garage-mcp").exists(), "garage-mcp directory should exist"

def test_documentation_exists():
    """Test that required documentation files exist"""
    root = Path(__file__).parent.parent
    
    assert (root / "README.md").exists(), "README.md should exist"
    assert (root / "LICENSE").exists(), "LICENSE should exist"
    assert (root / "CONTRIBUTING.md").exists(), "CONTRIBUTING.md should exist"

def test_heir_compliance():
    """Test HEIR compliance files"""
    root = Path(__file__).parent.parent
    
    assert (root / "heir.doctrine.yaml").exists(), "heir.doctrine.yaml should exist"
    assert (root / ".github/workflows").exists(), "GitHub workflows should exist"

def test_package_json():
    """Test that package.json has required scripts"""
    root = Path(__file__).parent.parent
    package_json = root / "package.json"
    
    assert package_json.exists(), "package.json should exist"
    
    import json
    with open(package_json) as f:
        package = json.load(f)
    
    assert "scripts" in package, "package.json should have scripts"
    assert "dev" in package["scripts"], "Should have dev script"
    assert "build" in package["scripts"], "Should have build script"
    assert "compliance:check" in package["scripts"], "Should have compliance:check script"

def test_python_requirements():
    """Test that Python requirements file exists"""
    root = Path(__file__).parent.parent
    
    assert (root / "requirements.txt").exists(), "requirements.txt should exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])