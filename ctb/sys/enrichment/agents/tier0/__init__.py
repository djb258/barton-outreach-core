"""
Tier 0 Enrichment Agents - FREE/Near-Free
Cost: $0.00 - $0.005 per lookup

These agents run FIRST before any paid APIs.
Target: Handle 70-90% of enrichment requests at near-zero cost.

Agents:
- direct_scraper: Direct HTTP scraping with BeautifulSoup (FREE)
- google_cse: Google Custom Search API ($0.005 after 100/day free)

Barton Doctrine ID: 04.04.02.04.enrichment.agents.tier0
"""

from .direct_scraper import enrich_with_direct_scrape
from .google_cse_agent import enrich_with_google_cse

__all__ = [
    'enrich_with_direct_scrape',
    'enrich_with_google_cse'
]
