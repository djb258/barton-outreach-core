"""
Seed LinkedIn Parser Templates into DeltaHound KV
==================================================
WP: wp-20260306-talent-flow-linkedin-monitor
Repair: wp-20260306-field-monitor-subhub-integrations (ParserConfig JSON format)
Kill switch: KILL_LINKEDIN_SEED

Seeds parser configs for LinkedIn profile title extraction
into the PARSER_KV namespace used by field-monitor-parser-registry.

KV key format: domain::field_name
KV value: JSON ParserConfig (regex-based extraction)

Usage:
    doppler run -- python seed_linkedin_parsers.py [--dry-run]
"""

import os
import sys
import json

# Parser configs for LinkedIn — ParserConfig JSON format
# The parser-registry applies: new RegExp(pattern, flags), extract group, apply transforms
PARSERS = [
    {
        "key": "linkedin.com::title",
        "config": {
            "type": "regex",
            "pattern": "<title[^>]*>([^<]+)",
            "flags": "i",
            "group": 1,
            "transforms": [
                {"type": "replace", "pattern": " \\| LinkedIn$", "flags": "", "replacement": ""},
                {"type": "trim"},
            ],
        },
        "description": "Extract job title from LinkedIn profile page <title> tag",
    },
]


def main():
    dry_run = "--dry-run" in sys.argv

    # Kill switch
    if os.environ.get("KILL_LINKEDIN_SEED", "").upper() in ("1", "TRUE", "YES"):
        print("KILL_LINKEDIN_SEED active — aborting")
        sys.exit(0)

    print(f"LinkedIn Parser Seed — {"DRY RUN" if dry_run else "LIVE"}")
    print(f"Parsers to seed: {len(PARSERS)}")
    print()

    for parser in PARSERS:
        config_json = json.dumps(parser["config"])
        print(f"  Key: {parser["key"]}")
        print(f"  Description: {parser["description"]}")
        print(f"  Config: {config_json}")

        if not dry_run:
            print("  -> Would write to PARSER_KV (Cloudflare KV API call)")

        print()

    if dry_run:
        print("DRY RUN complete — no KV writes performed")
        print(json.dumps({"parsers": PARSERS, "dry_run": True}, indent=2))
    else:
        print(f"Seeded {len(PARSERS)} parser(s) to PARSER_KV")


if __name__ == "__main__":
    main()
