"""
Signal Sweep — Field Monitor Bridge for Blog Sub-Hub
=====================================================
Reads field_monitor.field_state changes for blog content URLs
and bridges detected content changes into the blog pipeline
for re-processing.

Components:
    - url_seeder: Seeds blog URLs from vendor.blog into field_monitor
    - change_bridge: Reads detected changes and bridges to ingest_article
    - parser_templates: Parser function definitions for blog content

Kill switches:
    - KILL_SIGNAL_SWEEP: Stops all signal sweep processing
    - KILL_BLOG_URL_SEED: Stops URL seeding
    - KILL_FUNDING_DETECTION: Reused from blog pipeline
"""

from .url_seeder import seed_blog_urls, SeedResult
from .change_bridge import scan_blog_changes, BlogChange, BlogSweepResult
from .parser_templates import BLOG_PARSERS

__all__ = [
    'seed_blog_urls',
    'SeedResult',
    'scan_blog_changes',
    'BlogChange',
    'BlogSweepResult',
    'BLOG_PARSERS',
]
