# Tier 0 Enrichment Setup Guide

## Overview

Tier 0 is the FREE/near-free enrichment layer that runs BEFORE any paid APIs.

**Goal:** Handle 70-90% of enrichment requests at near-zero cost.

**Cost Comparison:**
| Tier | Cost per Lookup | 48K Companies Cost |
|------|----------------|-------------------|
| Tier 0 (FREE) | $0.00 - $0.005 | $0 - $240 |
| Tier 1 (Paid) | $0.20 | $9,600 |
| Tier 2 (Mid) | $1.50 | $72,000 |
| Tier 3 (Premium) | $3.00 | $144,000 |

---

## Tier 0 Agents

### 1. Direct Scraper (FREE - $0.00)

**What it does:**
- Scrapes company websites directly using HTTP requests
- Extracts emails, LinkedIn URLs, phone numbers
- Guesses website URLs from company names (company.com)
- Checks common contact page paths (/contact, /about, etc.)

**Requirements:**
- Python packages: `requests`, `beautifulsoup4`
- No API keys needed!

**Install:**
```bash
pip install requests beautifulsoup4
```

**Success rate:** ~30-50% (depends on whether website exists)

---

### 2. Google Custom Search ($0.005 after free tier)

**What it does:**
- Uses Google's search API to find company websites
- 100 queries/day FREE
- After that: $5 per 1,000 queries = $0.005 each
- 40X cheaper than SerpAPI!

**Requirements:**
1. Google Cloud account
2. Custom Search API enabled
3. Programmable Search Engine created

**Setup Steps:**

#### Step 1: Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Custom Search API":
   - APIs & Services → Library
   - Search "Custom Search API"
   - Click Enable
4. Create credentials:
   - APIs & Services → Credentials
   - Create Credentials → API Key
   - Copy the key

#### Step 2: Create Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create new search engine
3. Sites to search: Enter `*.com` (or leave blank for whole web)
4. Name: "Company Website Finder"
5. Create
6. Copy the Search Engine ID (CX)

#### Step 3: Configure .env

Add to your `.env` file:

```bash
# Google Custom Search API
GOOGLE_CSE_API_KEY=AIzaSyB...your-key-here
GOOGLE_CSE_CX=a1b2c3d4e5f...your-cx-here
```

**Success rate:** ~60-80%

---

## Cost Projection

**Scenario: 48,000 companies to enrich**

### Without Tier 0 (Current):
- All companies go to Tier 1 (Firecrawl/SerpAPI)
- 48,000 × $0.20 = **$9,600**

### With Tier 0 (Optimized):
| Tier | Success Rate | Companies | Cost Each | Total |
|------|-------------|-----------|-----------|-------|
| Tier 0 | 80% | 38,400 | $0.005 | $192 |
| Tier 1 | 15% | 7,200 | $0.20 | $1,440 |
| Tier 2 | 4% | 1,920 | $1.50 | $2,880 |
| Tier 3 | 1% | 480 | $3.00 | $1,440 |
| **Total** | 100% | 48,000 | - | **$5,952** |

**Savings: $3,648 (38% reduction)**

---

## Testing

### Quick Test (5 companies):

```bash
cd barton-outreach-core
python ctb/sys/enrichment/test_enrichment.py --max 5
```

### Expected Output:

```
============================================================
ENRICHMENT SYSTEM TEST
============================================================

[TIER 0] Free enrichment agents loaded (direct_scrape, google_cse)

TEST 1: Direct Firecrawl API Test
...

TEST 3: Enrichment Queue Processing (max=5)

[1/5] Company Name
  [TIER 0] Attempting FREE enrichment ($0.00-$0.005)...
  [Tier0] Trying direct scrape (FREE)...
  [DirectScrape SUCCESS] Found data from guessed website
  [TIER 0 SUCCESS] Enriched with direct_scrape for $0.000

============================================================
ENRICHMENT TEST SUMMARY
============================================================
Companies processed: 5
Successful enrichments: 4

TIER BREAKDOWN:
- Tier 0 (free): 3 companies ($0.015)
- Tier 1 (paid): 1 company ($0.20)

Total cost: $0.215
============================================================
```

---

## Troubleshooting

### "Tier 0 agents not available"

Install dependencies:
```bash
pip install requests beautifulsoup4
```

### "Google CSE not configured"

1. Check `.env` has correct keys
2. Verify API key is enabled in Google Cloud Console
3. Verify CSE ID is correct

### "Direct scrape always fails"

This is expected for companies without websites. The scraper:
1. First checks if `website` field exists
2. Then guesses URLs from company name
3. Many companies simply don't have websites

The scraper failing is fine - it falls through to Google CSE, then Tier 1.

### Rate limit errors

The rate limiter should handle this automatically. If you see frequent rate limits:
1. Check circuit breaker status: `python rate_limiter.py`
2. Reduce `global_limit` in rate_limiter.py
3. Add delays between companies in queue processor

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ENRICHMENT WATERFALL                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 0: FREE ($0.00 - $0.005)                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Direct Scraper   │→ │ Google CSE       │                 │
│  │ $0.00            │  │ $0.005           │                 │
│  └──────────────────┘  └──────────────────┘                 │
│  Target: 80% success rate                                   │
└─────────────────────────────────────────────────────────────┘
                            │ (if Tier 0 fails)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: PAID ($0.20)                                       │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Firecrawl        │→ │ SerpAPI          │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            │ (if Tier 1 fails)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: MID-COST ($1.50)                                   │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Clearbit         │→ │ Abacus.ai        │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            │ (if Tier 2 fails)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: PREMIUM ($3.00)                                    │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ RocketReach      │→ │ People Data Labs │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Files

| File | Purpose |
|------|---------|
| `agents/tier0/__init__.py` | Tier 0 module exports |
| `agents/tier0/direct_scraper.py` | FREE HTTP scraping |
| `agents/tier0/google_cse_agent.py` | Google Custom Search |
| `enrichment_waterfall.py` | Main orchestrator (calls Tier 0 first) |
| `rate_limiter.py` | Rate limiting (includes Tier 0 limits) |
| `.env` | API keys (GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX) |

---

## Next Steps

1. **Set up Google CSE** (follow steps above)
2. **Test with 10 companies**: `python test_enrichment.py --max 10`
3. **Check Tier 0 success rate** - should be 70-90%
4. **Process full queue** when ready

---

**Last Updated:** 2025-11-25
**Barton Doctrine ID:** 04.04.02.04.enrichment.tier0
