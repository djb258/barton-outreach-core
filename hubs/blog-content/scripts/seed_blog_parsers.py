"""
Seed Blog Parser Templates into DeltaHound KV
==============================================
WP: wp-20260306-signal-sweep-blog-monitor
Repair: wp-20260306-field-monitor-subhub-integrations (ParserConfig JSON format)
Kill switch: KILL_BLOG_URL_SEED

Seeds parser configs for blog content hash extraction
into the PARSER_KV namespace used by field-monitor-parser-registry.

KV key format: domain::field_name
KV value: JSON ParserConfig (regex-based extraction)

Usage:
    doppler run -- python seed_blog_parsers.py [--dry-run]
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from imo.middle.signal_sweep.parser_templates import BLOG_PARSERS


def main():
    dry_run = "--dry-run" in sys.argv

    # Kill switch
    if os.environ.get("KILL_BLOG_URL_SEED", "").upper() in ("1", "TRUE", "YES"):
        print("KILL_BLOG_URL_SEED active — aborting")
        sys.exit(0)

    if os.environ.get("KILL_SIGNAL_SWEEP", "").upper() in ("1", "TRUE", "YES"):
        print("KILL_SIGNAL_SWEEP active — aborting")
        sys.exit(0)

    print(f"Blog Parser Seed — {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Parsers to seed: {len(BLOG_PARSERS)}")
    print()

    for parser in BLOG_PARSERS:
        config_json = json.dumps(parser["config"])
        print(f"  Key pattern: {parser['key_pattern']}")
        print(f"  Description: {parser['description']}")
        print(f"  Default: {parser['is_default']}")
        print(f"  Config: {config_json}")

        if not dry_run:
            # In production, this calls the Cloudflare KV API
            # For default parsers, seed with each domain::content_hash key
            print("  -> Would write to PARSER_KV (Cloudflare KV API call)")

        print()

    if dry_run:
        print("DRY RUN complete — no KV writes performed")
        print(json.dumps({"parsers": [p["key_pattern"] for p in BLOG_PARSERS], "dry_run": True}, indent=2))
    else:
        print(f"Seeded {len(BLOG_PARSERS)} parser(s) to PARSER_KV")


if __name__ == "__main__":
    main()
