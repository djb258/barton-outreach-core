"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/api
Barton ID: 04.04.12
Unique ID: CTB-270C5815
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
"""

import json, hashlib

OMIT = {"timestamp_last_touched", "_created_at_ms", "blueprint_version_hash"}

def _scrub(o):
    if isinstance(o, dict):
        return {k: _scrub(v) for k, v in sorted(o.items()) if k not in OMIT}
    if isinstance(o, list):
        return [_scrub(v) for v in o]
    return o

def canonicalize(ssot: dict) -> str:
    return json.dumps(_scrub(ssot), separators=(",", ":"), sort_keys=True)

def stamp_version_hash(ssot: dict) -> dict:
    canon = canonicalize(ssot)
    h = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    ssot = dict(ssot)
    doctrine = dict(ssot.get("doctrine") or {})
    doctrine["blueprint_version_hash"] = h
    ssot["doctrine"] = doctrine
    return ssot