#!/usr/bin/env python3
"""
Control Plane Orchestrator — CLI for the V1 agent governance pipeline.

Usage:
    python agents/orchestrator.py status                  # Control Panel diagnostic
    python agents/orchestrator.py route plan              # Route WORK_PACKET outbox -> inbox
    python agents/orchestrator.py route plan --approve    # Route with architectural approval
    python agents/orchestrator.py route build             # Route CHANGESET outbox -> inbox
    python agents/orchestrator.py validate <file>         # Validate a single artifact
    python agents/orchestrator.py clean                   # Clear all inbox/outbox artifacts
"""

import argparse
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from bus import (
    get_bus_state,
    get_latest_artifact,
    route_work_packet,
    route_changeset,
    validate_file,
    check_protected_paths,
    clean_all,
    FOLDERS,
)


# ---------------------------------------------------------------------------
# Status (Control Panel output)
# ---------------------------------------------------------------------------

def cmd_status():
    """Implements the Control Panel structured diagnostic report."""
    state = get_bus_state()

    # Latest artifacts
    wp_path, wp_data = get_latest_artifact(FOLDERS["work_packets"]["outbox"])
    if not wp_data:
        wp_path, wp_data = get_latest_artifact(FOLDERS["work_packets"]["inbox"])

    cs_path, cs_data = get_latest_artifact(FOLDERS["changesets"]["outbox"])
    if not cs_data:
        cs_path, cs_data = get_latest_artifact(FOLDERS["changesets"]["inbox"])

    ar_path, ar_data = get_latest_artifact(FOLDERS["audit_reports"]["outbox"])
    if not ar_data:
        ar_path, ar_data = get_latest_artifact(FOLDERS["audit_reports"]["inbox"])

    # Git state
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=10,
        )
        git_lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        uncommitted = any(not l.startswith("?") for l in git_lines)
        untracked = any(l.startswith("?") for l in git_lines)
        clean_tree = len(git_lines) == 0
    except Exception:
        uncommitted = False
        untracked = False
        clean_tree = False

    # Governance signals
    arch_elevation = False
    protected_touched = False
    scope_violation = False
    execution_error = False

    if wp_data and wp_data.get("architectural_flag"):
        arch_elevation = True
    if cs_data and cs_data.get("architectural_flag"):
        arch_elevation = True

    if cs_data and cs_data.get("modified_paths"):
        violations = check_protected_paths(cs_data["modified_paths"])
        if violations and violations[0] != "INCOMPLETE STATE: could not parse protected_assets.md":
            protected_touched = True

    if wp_data and cs_data:
        allowed = set(wp_data.get("allowed_paths", []))
        modified = set(cs_data.get("modified_paths", []))
        if modified - allowed:
            scope_violation = True

    if ar_data and ar_data.get("classification") == "FAIL_EXECUTION":
        execution_error = True

    # Ready to merge
    if not ar_data or not wp_data or not cs_data:
        ready = "INCOMPLETE STATE"
    elif (
        ar_data.get("classification") == "PASS"
        and not wp_data.get("architectural_flag")
        and not cs_data.get("architectural_flag")
        and not protected_touched
        and not scope_violation
        and clean_tree
    ):
        ready = "TRUE"
    else:
        ready = "FALSE"

    # Next action
    if ready == "INCOMPLETE STATE":
        missing = []
        if not wp_data:
            missing.append("WORK_PACKET")
        if not cs_data:
            missing.append("CHANGESET")
        if not ar_data:
            missing.append("AUDIT_REPORT")
        next_action = f"Missing artifacts: {', '.join(missing)}. Run the pipeline to generate them."
    elif ready == "TRUE":
        next_action = "All checks pass. Safe to merge."
    else:
        reasons = []
        if ar_data and ar_data.get("classification") != "PASS":
            reasons.append(f"AUDIT_REPORT classification is {ar_data.get('classification')}")
        if arch_elevation:
            reasons.append("Architectural elevation detected — requires parent-level human approval")
        if protected_touched:
            reasons.append("Protected path touched")
        if scope_violation:
            reasons.append("Scope violation detected")
        if not clean_tree:
            reasons.append("Git working tree is not clean")
        next_action = "Resolve: " + "; ".join(reasons) + "." if reasons else "Review artifacts manually."

    # Output
    yn = lambda b: "yes" if b else "no"

    print("=" * 56)
    print("  IMO-CREATOR CONTROL PANEL")
    print("=" * 56)
    print()
    print("## 1. Folder Bus State")
    print()
    print(f"  {'Location':<30s} Count")
    print(f"  {'-'*30} -----")
    for key in sorted(state.keys()):
        print(f"  {key:<30s} {state[key]}")
    print()

    print("## 2. Latest WORK_PACKET")
    print()
    if wp_data:
        print(f"  id:                 {wp_data.get('id', '?')}")
        print(f"  change_type:        {wp_data.get('change_type', '?')}")
        print(f"  architectural_flag: {wp_data.get('architectural_flag', '?')}")
        print(f"  allowed_paths:      {wp_data.get('allowed_paths', '?')}")
    else:
        print("  NO WORK_PACKET FOUND")
    print()

    print("## 3. Latest CHANGESET")
    print()
    if cs_data:
        print(f"  id:                 {cs_data.get('id', '?')}")
        print(f"  work_packet_id:     {cs_data.get('work_packet_id', '?')}")
        print(f"  modified_paths:     {cs_data.get('modified_paths', '?')}")
        print(f"  architectural_flag: {cs_data.get('architectural_flag', '?')}")
    else:
        print("  NO CHANGESET FOUND")
    print()

    print("## 4. Latest AUDIT_REPORT")
    print()
    if ar_data:
        print(f"  classification: {ar_data.get('classification', '?')}")
        print(f"  summary:        {ar_data.get('summary', '?')}")
    else:
        print("  NO AUDIT_REPORT FOUND")
    print()

    print("## 5. Governance Signals")
    print()
    print(f"  ARCHITECTURAL_ELEVATION_DETECTED:  {yn(arch_elevation)}")
    print(f"  PROTECTED_PATH_TOUCHED:            {yn(protected_touched)}")
    print(f"  SCOPE_VIOLATION_DETECTED:          {yn(scope_violation)}")
    print(f"  EXECUTION_ERROR_DETECTED:          {yn(execution_error)}")
    print()

    print("## 6. Git State")
    print()
    print(f"  Uncommitted changes:  {yn(uncommitted)}")
    print(f"  Untracked files:      {yn(untracked)}")
    print(f"  Clean working tree:   {yn(clean_tree)}")
    print()

    print(f"## 7. READY_TO_MERGE")
    print()
    print(f"  {ready}")
    print()

    print(f"## 8. NEXT REQUIRED HUMAN ACTION")
    print()
    print(f"  {next_action}")
    print()
    print("=" * 56)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

def cmd_route(step, approve=False):
    """Route artifacts between outbox and inbox."""
    if step == "plan":
        success, msg = route_work_packet(approve_architectural=approve)
    elif step == "build":
        success, msg = route_changeset()
    elif step == "audit":
        print("AUDIT_REPORT is terminal. No routing needed (human reviews from outbox).")
        return
    else:
        print(f"Unknown step: {step}. Use: plan, build, audit")
        sys.exit(1)

    if success:
        print(f"OK: {msg}")
    else:
        print(f"BLOCKED: {msg}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def cmd_validate(file_path):
    """Validate a single artifact file."""
    valid, errors = validate_file(file_path)
    if valid:
        print(f"VALID: {file_path}")
    else:
        print(f"INVALID: {file_path}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

def cmd_clean():
    """Clear all artifacts from inbox/outbox folders."""
    removed = clean_all()
    print(f"Cleaned {removed} artifact(s) from all inbox/outbox folders.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="V1 Control Plane Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status                   Control Panel diagnostic report
  route plan [--approve]   Route WORK_PACKET from outbox to inbox
  route build              Route CHANGESET from outbox to inbox
  route audit              (terminal — no routing needed)
  validate <file>          Validate a single artifact against its schema
  clean                    Remove all artifacts from inbox/outbox folders
""",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Control Panel diagnostic report")

    route_parser = subparsers.add_parser("route", help="Route artifacts between outbox/inbox")
    route_parser.add_argument("step", choices=["plan", "build", "audit"], help="Pipeline step to route")
    route_parser.add_argument("--approve", action="store_true", help="Approve architectural elevation (human override)")

    validate_parser = subparsers.add_parser("validate", help="Validate an artifact file")
    validate_parser.add_argument("file", help="Path to JSON artifact")

    subparsers.add_parser("clean", help="Clear all inbox/outbox artifacts")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "route":
        cmd_route(args.step, approve=args.approve)
    elif args.command == "validate":
        cmd_validate(args.file)
    elif args.command == "clean":
        cmd_clean()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
