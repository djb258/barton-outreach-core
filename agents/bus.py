"""
Message Bus — Validates and routes artifacts between agent outbox/inbox folders.

The bus is the ONLY mechanism that moves artifacts between folders.
No agent may move artifacts (per governance.md).

Routing model:
  Planner  -> work_packets/outbox  ->  work_packets/inbox  -> Builder + Auditor
  Builder  -> changesets/outbox    ->  changesets/inbox     -> Auditor
  Auditor  -> audit_reports/outbox ->  (terminal, human review)
"""

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Folder structure
FOLDERS = {
    "work_packets": {
        "inbox": REPO_ROOT / "work_packets" / "inbox",
        "outbox": REPO_ROOT / "work_packets" / "outbox",
    },
    "changesets": {
        "inbox": REPO_ROOT / "changesets" / "inbox",
        "outbox": REPO_ROOT / "changesets" / "outbox",
    },
    "audit_reports": {
        "inbox": REPO_ROOT / "audit_reports" / "inbox",
        "outbox": REPO_ROOT / "audit_reports" / "outbox",
    },
}

SCHEMAS = {
    "work_packet": REPO_ROOT / "agents" / "contracts" / "work_packet.schema.json",
    "changeset": REPO_ROOT / "agents" / "contracts" / "changeset.schema.json",
    "audit_report": REPO_ROOT / "agents" / "contracts" / "audit_report.schema.json",
}

FOLDER_SCHEMA_MAP = {
    "work_packets": "work_packet",
    "changesets": "changeset",
    "audit_reports": "audit_report",
}


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def load_schema(schema_type):
    """Load a JSON schema file."""
    path = SCHEMAS.get(schema_type)
    if not path or not path.exists():
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def validate_artifact(data, schema_type):
    """
    Validate artifact data against its schema contract.

    Checks: required fields, types, enum values, additionalProperties: false.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    schema = load_schema(schema_type)
    if not schema:
        return False, [f"Schema '{schema_type}' not found"]

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    allowed_keys = set(properties.keys())

    for field in required:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    extra = set(data.keys()) - allowed_keys
    if extra:
        errors.append(f"Extra fields not allowed: {sorted(extra)}")

    type_map = {"string": str, "boolean": bool, "array": list, "object": dict}

    for key, prop_def in properties.items():
        if key not in data:
            continue
        val = data[key]
        expected_type = prop_def.get("type")

        if expected_type in type_map and not isinstance(val, type_map[expected_type]):
            errors.append(f"Field '{key}': expected {expected_type}, got {type(val).__name__}")
            continue

        if expected_type == "string" and isinstance(val, str):
            min_len = prop_def.get("minLength", 0)
            if len(val) < min_len:
                errors.append(f"Field '{key}': must be at least {min_len} character(s)")

        if "enum" in prop_def and val not in prop_def["enum"]:
            errors.append(f"Field '{key}': '{val}' not in {prop_def['enum']}")

        if expected_type == "array" and isinstance(val, list):
            min_items = prop_def.get("minItems", 0)
            if len(val) < min_items:
                errors.append(f"Field '{key}': must have at least {min_items} item(s)")

    return len(errors) == 0, errors


def validate_file(file_path):
    """Validate a JSON artifact file. Auto-detects schema type from path."""
    path = Path(file_path)
    if not path.exists():
        return False, [f"File not found: {file_path}"]

    schema_type = None
    for folder_name, st in FOLDER_SCHEMA_MAP.items():
        if folder_name in path.parts:
            schema_type = st
            break

    if not schema_type:
        return False, [f"Cannot determine schema type from path: {file_path}"]

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    return validate_artifact(data, schema_type)


# ---------------------------------------------------------------------------
# Artifact listing
# ---------------------------------------------------------------------------

def list_artifacts(folder_path):
    """List all .json files in a folder, sorted newest first by mtime."""
    folder = Path(folder_path)
    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)


def get_latest_artifact(folder_path):
    """Get the most recent JSON artifact from a folder. Returns (path, data) or (None, None)."""
    files = list_artifacts(folder_path)
    if not files:
        return None, None
    path = files[0]
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return path, data
    except (json.JSONDecodeError, IOError):
        return path, None


# ---------------------------------------------------------------------------
# Bus state
# ---------------------------------------------------------------------------

def get_bus_state():
    """Get artifact counts for all inbox/outbox folders."""
    state = {}
    for artifact_type, paths in FOLDERS.items():
        for box_type, box_path in paths.items():
            key = f"{artifact_type}/{box_type}"
            state[key] = len(list_artifacts(box_path))
    return state


# ---------------------------------------------------------------------------
# Protected asset detection
# ---------------------------------------------------------------------------

def load_protected_paths():
    """Parse protected folders/files from protected_assets.md."""
    pa_path = REPO_ROOT / "docs" / "constitutional" / "protected_assets.md"
    if not pa_path.exists():
        return None

    protected = []
    with open(pa_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            for cell in cells:
                if cell.startswith("`") and cell.endswith("`"):
                    val = cell.strip("`").strip()
                    if val.startswith("/") or val.endswith("/") or val.endswith(".md") or val.endswith(".json") or val.endswith(".yaml"):
                        protected.append(val.strip("/"))

    return protected if protected else None


def check_protected_paths(modified_paths):
    """Check if any modified paths touch protected assets. Returns list of violations."""
    protected = load_protected_paths()
    if protected is None:
        return ["INCOMPLETE STATE: could not parse protected_assets.md"]

    violations = []
    for mp in modified_paths:
        mp_clean = mp.strip("/")
        for pf in protected:
            if mp_clean.startswith(pf) or mp_clean == pf:
                violations.append(f"{mp} touches protected: {pf}")
    return violations


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_work_packet(approve_architectural=False):
    """
    Route latest WORK_PACKET from outbox -> inbox.

    If architectural_flag is true, requires approve_architectural=True
    (human approval) to proceed.

    Returns (success, message).
    """
    outbox = FOLDERS["work_packets"]["outbox"]
    inbox = FOLDERS["work_packets"]["inbox"]

    path, data = get_latest_artifact(outbox)
    if not path:
        return False, "No WORK_PACKET found in work_packets/outbox"
    if data is None:
        return False, f"Could not parse {path.name}"

    valid, errors = validate_artifact(data, "work_packet")
    if not valid:
        return False, f"WORK_PACKET validation failed:\n  " + "\n  ".join(errors)

    if data.get("architectural_flag") and not approve_architectural:
        return False, (
            "HALT: architectural_flag is TRUE.\n"
            "This WORK_PACKET requires human approval before Builder may proceed.\n"
            "Re-run with --approve to continue."
        )

    inbox.mkdir(parents=True, exist_ok=True)
    dest = inbox / path.name
    shutil.copy2(path, dest)

    flag = " [ARCHITECTURAL - human approved]" if data.get("architectural_flag") else ""
    return True, f"Routed: {path.name} -> work_packets/inbox{flag}"


def route_changeset():
    """
    Route latest CHANGESET from outbox -> inbox.

    Cross-validates against the source WORK_PACKET:
      - work_packet_id must match
      - change_type must match
      - architectural_flag must match
      - modified_paths must be subset of allowed_paths

    Returns (success, message).
    """
    outbox = FOLDERS["changesets"]["outbox"]
    inbox = FOLDERS["changesets"]["inbox"]

    path, data = get_latest_artifact(outbox)
    if not path:
        return False, "No CHANGESET found in changesets/outbox"
    if data is None:
        return False, f"Could not parse {path.name}"

    valid, errors = validate_artifact(data, "changeset")
    if not valid:
        return False, f"CHANGESET validation failed:\n  " + "\n  ".join(errors)

    # Find matching WORK_PACKET in inbox
    wp_inbox = FOLDERS["work_packets"]["inbox"]
    wp_id = data.get("work_packet_id")
    wp_data = None

    for wp_file in list_artifacts(wp_inbox):
        try:
            with open(wp_file, "r", encoding="utf-8-sig") as f:
                candidate = json.load(f)
            if candidate.get("id") == wp_id:
                wp_data = candidate
                break
        except (json.JSONDecodeError, IOError):
            continue

    if wp_data is None:
        return False, f"No WORK_PACKET with id '{wp_id}' found in work_packets/inbox"

    # Cross-validate envelope fields
    mismatches = []
    if data.get("change_type") != wp_data.get("change_type"):
        mismatches.append(f"change_type: '{data.get('change_type')}' vs '{wp_data.get('change_type')}'")
    if data.get("architectural_flag") != wp_data.get("architectural_flag"):
        mismatches.append(f"architectural_flag: {data.get('architectural_flag')} vs {wp_data.get('architectural_flag')}")
    if data.get("doctrine_version") != wp_data.get("doctrine_version"):
        mismatches.append(f"doctrine_version: '{data.get('doctrine_version')}' vs '{wp_data.get('doctrine_version')}'")
    if mismatches:
        return False, "CHANGESET envelope mismatch with WORK_PACKET:\n  " + "\n  ".join(mismatches)

    # Check modified_paths subset of allowed_paths
    # allowed_paths entries ending with "/" are directory prefixes
    allowed = wp_data.get("allowed_paths", [])
    modified = data.get("modified_paths", [])
    outside = []
    for mp in modified:
        if not any(
            mp == ap or (ap.endswith("/") and mp.startswith(ap))
            for ap in allowed
        ):
            outside.append(mp)
    if outside:
        return False, "SCOPE VIOLATION: modified_paths outside allowed_paths:\n  " + "\n  ".join(sorted(outside))

    inbox.mkdir(parents=True, exist_ok=True)
    dest = inbox / path.name
    shutil.copy2(path, dest)

    return True, f"Routed: {path.name} -> changesets/inbox"


def clean_all():
    """Remove all JSON artifacts from all inbox/outbox folders."""
    removed = 0
    for artifact_type, paths in FOLDERS.items():
        for box_type, box_path in paths.items():
            for f in list_artifacts(box_path):
                f.unlink()
                removed += 1
    return removed
