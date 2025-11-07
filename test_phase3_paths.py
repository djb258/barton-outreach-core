#!/usr/bin/env python3
"""
Quick test to verify Phase 3 path resolution works correctly
Tests that moved scripts can find the .env file from new locations
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Test the path resolution logic used in moved scripts
def test_project_root_detection(script_path):
    """Test project root detection from a given script location"""
    test_file = Path(script_path).resolve()
    project_root = test_file.parent

    # Simulate the detection logic
    while not (project_root / ".git").exists() and project_root != project_root.parent:
        project_root = project_root.parent

    env_path = project_root / ".env"

    return {
        "script": script_path,
        "project_root": str(project_root),
        "env_path": str(env_path),
        "env_exists": env_path.exists()
    }

# Test all moved scripts
test_scripts = [
    "ctb/data/scripts/check_companies.py",
    "ctb/data/scripts/check_db_schema.py",
    "ctb/data/scripts/check_pipeline_events.py",
    "ctb/data/scripts/create_db_views.py",
    "ctb/sys/scripts/trigger_enrichment.py",
]

print("\n" + "="*80)
print("PHASE 3 PATH RESOLUTION TEST")
print("="*80 + "\n")

all_passed = True

for script in test_scripts:
    result = test_project_root_detection(script)
    status = "✅ PASS" if result["env_exists"] else "❌ FAIL"

    print(f"{status} {script}")
    print(f"     Project Root: {result['project_root']}")
    print(f"     Env Path: {result['env_path']}")
    print(f"     Env Exists: {result['env_exists']}")
    print()

    if not result["env_exists"]:
        all_passed = False

print("="*80)
if all_passed:
    print("✅ ALL TESTS PASSED - Path resolution working correctly!")
else:
    print("❌ SOME TESTS FAILED - Check .env file location")
    print("Expected: .env (at project root)")
print("="*80 + "\n")

sys.exit(0 if all_passed else 1)
