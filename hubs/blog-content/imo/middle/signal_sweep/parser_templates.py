"""
Parser Templates — Blog content hash parser definitions
========================================================
WP: wp-20260306-signal-sweep-blog-monitor
Repair: wp-20260306-field-monitor-subhub-integrations (ParserConfig JSON format)

Defines parser configs for blog content monitoring
via the DeltaHound parser-registry KV store.

The parser-registry applies regex extraction with transforms.
KV values are JSON ParserConfig objects:
    {"type": "regex", "pattern": "...", "flags": "...", "group": N, "transforms": [...]}
"""

# Generic blog content hash parser config
# Extracts <article> body content for change detection.
# The extracted text changes when the article body changes,
# which triggers the signal sweep bridge.
BLOG_CONTENT_HASH_CONFIG = {
    "type": "regex",
    "pattern": "<article[^>]*>([\\s\\S]{50,}?)</article>",
    "flags": "i",
    "group": 1,
    "transforms": [
        {"type": "replace", "pattern": "<[^>]+>", "flags": "g", "replacement": " "},
        {"type": "replace", "pattern": "\\s+", "flags": "g", "replacement": " "},
        {"type": "trim"},
    ],
}

# Fallback: extract from <main> if no <article> tag
BLOG_MAIN_HASH_CONFIG = {
    "type": "regex",
    "pattern": "<main[^>]*>([\\s\\S]{50,}?)</main>",
    "flags": "i",
    "group": 1,
    "transforms": [
        {"type": "replace", "pattern": "<[^>]+>", "flags": "g", "replacement": " "},
        {"type": "replace", "pattern": "\\s+", "flags": "g", "replacement": " "},
        {"type": "trim"},
    ],
}

# Parser definitions for PARSER_KV seeding
# Key format: domain::field_name
# These are generic — specific domain overrides can be added per-site
BLOG_PARSERS = [
    {
        "key_pattern": "*::content_hash",
        "config": BLOG_CONTENT_HASH_CONFIG,
        "description": "Generic blog content hash — extracts <article> body text for change detection",
        "is_default": True,
    },
    {
        "key_pattern": "*::content_hash_fallback",
        "config": BLOG_MAIN_HASH_CONFIG,
        "description": "Fallback blog content hash — extracts <main> body text if <article> absent",
        "is_default": False,
    },
]
