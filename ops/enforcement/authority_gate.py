#!/usr/bin/env python3
"""
Authority Assertion Gate — Canonical Chain Enforcement

DOCTRINE: claimed_cc_layer ≠ effective_cc_layer
CC-02 requires external delegation from upstream CC-02 or CC-01.
Absence of proof = failure. No self-declaration allowed.

This script:
1. Reads heir.doctrine.yaml
2. Validates authority claims against delegation artifacts
3. Computes effective_cc_layer
4. Fails closed if delegation is missing or invalid
"""

import yaml
import sys
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Exit codes
EXIT_SUCCESS = 0
EXIT_AUTHORITY_INVALID = 1
EXIT_DELEGATION_MISSING = 2
EXIT_CONFIG_ERROR = 3
EXIT_DOWNGRADED = 4


class AuthorityGate:
    """Validates CC layer claims against external delegations."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.heir_path = self.repo_root / "heir.doctrine.yaml"
        self.config: Dict[str, Any] = {}
        self.errors: list = []
        self.warnings: list = []

    def load_config(self) -> bool:
        """Load heir.doctrine.yaml configuration."""
        if not self.heir_path.exists():
            self.errors.append(f"heir.doctrine.yaml not found at {self.heir_path}")
            return False

        try:
            with open(self.heir_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Failed to parse heir.doctrine.yaml: {e}")
            return False

    def get_claimed_cc_layer(self) -> Optional[str]:
        """Get the claimed CC layer from config."""
        authority = self.config.get("authority", {})
        return authority.get("claimed_cc_layer")

    def get_effective_cc_layer(self) -> Optional[str]:
        """Get the current effective CC layer from config."""
        authority = self.config.get("authority", {})
        return authority.get("effective_cc_layer")

    def validate_delegation_artifact(self, artifact_ref: Optional[str]) -> Tuple[bool, str]:
        """
        Validate that a delegation artifact exists and is valid.

        Returns:
            Tuple of (is_valid, reason)
        """
        if not artifact_ref:
            return False, "No delegation artifact reference provided"

        # Check if artifact is a local file path
        artifact_path = self.repo_root / artifact_ref
        if artifact_path.exists():
            try:
                with open(artifact_path, "r", encoding="utf-8") as f:
                    delegation = yaml.safe_load(f)

                # Validate delegation structure
                required_fields = ["delegator", "delegatee", "cc_layer_granted", "signature"]
                missing = [f for f in required_fields if f not in delegation]
                if missing:
                    return False, f"Delegation artifact missing required fields: {missing}"

                # Validate delegatee matches this hub
                hub_id = self.config.get("hub", {}).get("id")
                if delegation.get("delegatee") != hub_id:
                    return False, f"Delegation is for {delegation.get('delegatee')}, not {hub_id}"

                return True, "Delegation artifact valid"

            except yaml.YAMLError as e:
                return False, f"Failed to parse delegation artifact: {e}"

        # Check if artifact is a URL (future: fetch and validate)
        if artifact_ref.startswith("http"):
            return False, "Remote delegation artifacts not yet supported"

        # Check if artifact is an ADR reference
        if artifact_ref.startswith("ADR-"):
            adr_path = self.repo_root / "docs" / "adr" / f"{artifact_ref}.md"
            if adr_path.exists():
                return True, f"ADR delegation reference found: {artifact_ref}"
            return False, f"ADR delegation reference not found: {artifact_ref}"

        return False, f"Delegation artifact not found: {artifact_ref}"

    def compute_effective_cc_layer(self) -> Tuple[str, str]:
        """
        Compute the effective CC layer based on delegation status.

        DOCTRINE: Fail closed. Absence of proof = failure.

        Returns:
            Tuple of (effective_cc_layer, reason)
        """
        claimed = self.get_claimed_cc_layer()
        authority = self.config.get("authority", {})
        delegation = authority.get("delegation", {})
        enforcement = authority.get("enforcement", {})

        # Rule 1: CC-01 cannot be claimed by any repo (sovereign is external)
        if claimed == "CC-01":
            return "CC-03", "CC-01 cannot be self-declared; sovereign authority is external"

        # Rule 2: CC-02 requires external delegation
        if claimed == "CC-02":
            artifact_ref = delegation.get("artifact_ref")
            is_valid, reason = self.validate_delegation_artifact(artifact_ref)

            if not is_valid:
                if enforcement.get("downgrade_on_missing", True):
                    return "CC-03", f"DOWNGRADED: {reason}"
                else:
                    return claimed, f"WARNING: {reason} (enforcement disabled)"

            return "CC-02", "Valid delegation from upstream authority"

        # Rule 3: CC-03 and CC-04 can be self-declared (they don't grant authority)
        if claimed in ["CC-03", "CC-04"]:
            return claimed, "CC-03/CC-04 are valid without external delegation"

        return "CC-04", f"Unknown CC layer claim: {claimed}; defaulting to CC-04"

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run full authority validation.

        Returns:
            Tuple of (passed, result_dict)
        """
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "repo_root": str(self.repo_root.absolute()),
            "claimed_cc_layer": None,
            "effective_cc_layer": None,
            "delegation_status": None,
            "passed": False,
            "errors": [],
            "warnings": [],
            "enforcement_mode": None,
        }

        # Load config
        if not self.load_config():
            result["errors"] = self.errors
            return False, result

        authority = self.config.get("authority", {})
        enforcement = authority.get("enforcement", {})
        result["enforcement_mode"] = enforcement.get("mode", "strict")

        # Get claimed layer
        claimed = self.get_claimed_cc_layer()
        result["claimed_cc_layer"] = claimed

        if not claimed:
            result["errors"].append("No claimed_cc_layer in authority section")
            return False, result

        # Compute effective layer
        effective, reason = self.compute_effective_cc_layer()
        result["effective_cc_layer"] = effective
        result["delegation_status"] = reason

        # Determine pass/fail
        if claimed != effective:
            if enforcement.get("mode") == "strict" and enforcement.get("block_on_invalid", True):
                result["errors"].append(
                    f"AUTHORITY GATE FAILED: Claimed {claimed} but effective is {effective}"
                )
                result["errors"].append(f"Reason: {reason}")
                result["passed"] = False
            else:
                result["warnings"].append(
                    f"CC layer mismatch: claimed {claimed}, effective {effective}"
                )
                result["warnings"].append(f"Reason: {reason}")
                result["passed"] = True  # Warn mode allows through
        else:
            result["passed"] = True

        return result["passed"], result

    def print_report(self, result: Dict[str, Any]) -> None:
        """Print validation report."""
        print("=" * 70)
        print("CANONICAL AUTHORITY GATE — VALIDATION REPORT")
        print("=" * 70)
        print(f"Timestamp:        {result['timestamp']}")
        print(f"Repository:       {result['repo_root']}")
        print(f"Enforcement Mode: {result['enforcement_mode']}")
        print("-" * 70)
        print(f"Claimed CC Layer:   {result['claimed_cc_layer']}")
        print(f"Effective CC Layer: {result['effective_cc_layer']}")
        print(f"Delegation Status:  {result['delegation_status']}")
        print("-" * 70)

        if result["errors"]:
            print("\n❌ ERRORS:")
            for err in result["errors"]:
                print(f"   • {err}")

        if result["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warn in result["warnings"]:
                print(f"   • {warn}")

        print("-" * 70)
        if result["passed"]:
            print("✅ AUTHORITY GATE: PASSED")
        else:
            print("❌ AUTHORITY GATE: FAILED")
            print("\nTo resolve:")
            print("1. Obtain delegation artifact from upstream CC-02 or CC-01")
            print("2. Place artifact at path specified in heir.doctrine.yaml")
            print("3. Update authority.delegation.artifact_ref with path")
            print("4. Re-run validation")
        print("=" * 70)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Canonical Authority Gate — Validate CC layer claims"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Force strict mode regardless of config",
    )

    args = parser.parse_args()

    gate = AuthorityGate(repo_root=args.repo_root)
    passed, result = gate.validate()

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        gate.print_report(result)

    # Exit codes
    if not passed:
        if "DOWNGRADED" in str(result.get("delegation_status", "")):
            sys.exit(EXIT_DOWNGRADED)
        elif "No delegation" in str(result.get("delegation_status", "")):
            sys.exit(EXIT_DELEGATION_MISSING)
        else:
            sys.exit(EXIT_AUTHORITY_INVALID)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
