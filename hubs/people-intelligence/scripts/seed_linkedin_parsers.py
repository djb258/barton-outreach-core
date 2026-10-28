"""
Talent Flow — LinkedIn Parser KV Seeder
========================================
Work Packet: wp-20260306-talent-flow-linkedin-monitor
ORBT: Build
CTB: hubs/people-intelligence/scripts/ (support surface)

Seeds Cloudflare KV (PARSER_KV namespace) with parser function
bodies for extracting current_title and current_company from
public LinkedIn profile HTML.

Consumed by: field-monitor-parser-registry Cloudflare Worker
KV key format: {domain}::{field_name}
KV value: JavaScript function body string

Usage:
    python seed_linkedin_parsers.py --dry-run
    python seed_linkedin_parsers.py
    python seed_linkedin_parsers.py --env production
"""

import subprocess
import json
import sys
import os


# ═══════════════════════════════════════════════════════════════
# Parser Function Bodies (JavaScript)
# ═══════════════════════════════════════════════════════════════
# The parser-registry worker wraps each as: new Function('html', fnBody)
# Extraction strategy: JSON-LD > og:title meta > HTML class fallback

PARSERS = {
    "www.linkedin.com::current_title": r"""
var ldMatch = html.match(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/i);
if (ldMatch) {
    try {
        var ld = JSON.parse(ldMatch[1]);
        if (ld.jobTitle) return ld.jobTitle;
        if (ld['@graph']) {
            for (var i = 0; i < ld['@graph'].length; i++) {
                if (ld['@graph'][i].jobTitle) return ld['@graph'][i].jobTitle;
            }
        }
    } catch(e) {}
}
var ogTitle = html.match(/<meta[^>]*property="og:title"[^>]*content="([^"]*)"[^>]*>/i);
if (ogTitle && ogTitle[1]) {
    var parts = ogTitle[1].split(' - ');
    if (parts.length >= 2) {
        var titlePart = parts.slice(1).join(' - ');
        var atIdx = titlePart.lastIndexOf(' at ');
        if (atIdx > 0) return titlePart.substring(0, atIdx).trim();
        return titlePart.trim();
    }
}
var headlineMatch = html.match(/class="[^"]*top-card-layout__headline[^"]*"[^>]*>([^<]+)/i);
if (headlineMatch) {
    var headline = headlineMatch[1].trim();
    var atIdx2 = headline.lastIndexOf(' at ');
    if (atIdx2 > 0) return headline.substring(0, atIdx2).trim();
    return headline;
}
return null;
""",

    "www.linkedin.com::current_company": r"""
var ldMatch = html.match(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/i);
if (ldMatch) {
    try {
        var ld = JSON.parse(ldMatch[1]);
        if (ld.worksFor) {
            if (typeof ld.worksFor === 'string') return ld.worksFor;
            if (ld.worksFor.name) return ld.worksFor.name;
            if (Array.isArray(ld.worksFor) && ld.worksFor[0]) {
                return ld.worksFor[0].name || ld.worksFor[0];
            }
        }
    } catch(e) {}
}
var ogTitle = html.match(/<meta[^>]*property="og:title"[^>]*content="([^"]*)"[^>]*>/i);
if (ogTitle && ogTitle[1]) {
    var parts = ogTitle[1].split(' - ');
    if (parts.length >= 2) {
        var titlePart = parts.slice(1).join(' - ');
        var atIdx = titlePart.lastIndexOf(' at ');
        if (atIdx > 0) return titlePart.substring(atIdx + 4).trim();
    }
}
var companyMatch = html.match(/class="[^"]*top-card-layout__second-subline[^"]*"[^>]*>[\s\S]*?<a[^>]*>([^<]+)/i);
if (companyMatch) return companyMatch[1].trim();
return null;
"""
}


def main():
    dry_run = "--dry-run" in sys.argv
    env = None
    for i, arg in enumerate(sys.argv):
        if arg == "--env" and i + 1 < len(sys.argv):
            env = sys.argv[i + 1]

    print(f"Talent Flow — LinkedIn Parser KV Seeder")
    print(f"Parsers: {len(PARSERS)} | Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    if dry_run:
        for key, body in PARSERS.items():
            print(f"\n  Key: {key}")
            print(f"  Body: {len(body)} chars")
        print("\nDry run complete.")
        return

    ns_id = os.environ.get("PARSER_KV_NAMESPACE_ID")
    if not ns_id:
        print("ERROR: Set PARSER_KV_NAMESPACE_ID env var")
        sys.exit(1)

    fm_root = os.environ.get(
        "FIELD_MONITOR_ROOT",
        os.path.expanduser("~/Documents/IMO-Creator/templates/snap-on/field-monitor")
    )

    ok, fail = 0, 0
    for key, body in PARSERS.items():
        cmd = ["npx", "wrangler", "kv", "key", "put", key, body.strip(),
               "--namespace-id", ns_id]
        if env:
            cmd.extend(["--env", env])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=fm_root)
        if result.returncode == 0:
            print(f"  OK: {key}")
            ok += 1
        else:
            print(f"  FAIL: {key} — {result.stderr.strip()}")
            fail += 1

    print(f"\nResults: {ok} OK, {fail} FAILED")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
