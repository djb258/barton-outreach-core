"""
Enrichment Agents - Barton Outreach Core

Tiered enrichment agents for cost-optimized data enrichment.

Tier 0: FREE/Near-Free ($0.00 - $0.005)
- direct_scraper: Direct HTTP scraping (FREE)
- google_cse: Google Custom Search ($0.005 after free tier)

Tier 1: Cheap ($0.20)
- firecrawl: Web scraping API
- serpapi: Google search API

Tier 2: Mid-Cost ($1.50)
- clearbit: Company enrichment
- abacus: AI-powered enrichment

Tier 3: Expensive ($3.00)
- peopledatalabs: Premium enrichment
- rocketreach: Contact finder
- apify: Web automation

Barton Doctrine ID: 04.04.02.04.enrichment.agents
"""

from . import tier0

__all__ = ['tier0']
