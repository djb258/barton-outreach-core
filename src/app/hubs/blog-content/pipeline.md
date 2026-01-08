# Blog Sub-Hub — Signal Pipeline

**Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Status:** Implemented

---

## Overview

The Blog Sub-Hub is a **read-only signal emitter** that processes external news content and converts it into structured BIT (Buyer Intent Tool) signals.

### Altitude & Role

| Property | Value |
|----------|-------|
| Altitude | 10,000 → 5,000 ft |
| Function | Convert external news content into structured BIT signals |
| Identity | Downstream only |
| Failure Mode | DROP or QUEUE — never rescue |

---

## Core Doctrine (Hard Rules)

| Rule | Status |
|------|--------|
| ❌ Never mint a company | ENFORCED |
| ❌ Never trigger enrichment | ENFORCED |
| ❌ Never mutate Company Lifecycle | ENFORCED |
| ❌ No retries, no fuzzy rescue | ENFORCED |
| ✅ company_sov_id MUST exist before emitting | ENFORCED |
| ✅ All outputs must be deterministic + logged | ENFORCED |
| ✅ LLMs are classifiers only, never decision authorities | ENFORCED |

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BLOG SUB-HUB PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │   INGEST     │────▶│    PARSE     │────▶│   EXTRACT    │                │
│   │  (Input)     │     │  (Middle)    │     │  (Middle)    │                │
│   │              │     │              │     │              │                │
│   │ • NewsAPI    │     │ • Strip HTML │     │ • spaCy NER  │                │
│   │ • RSS        │     │ • Clean text │     │ • Regex      │                │
│   │ • SEC 8-K    │     │ • Normalize  │     │ • Domains    │                │
│   │ • PR Wire    │     │              │     │ • Money      │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│          │                    │                    │                        │
│          ▼                    ▼                    ▼                        │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                      CLASSIFY EVENT                       │             │
│   │                        (Middle)                           │             │
│   │                                                           │             │
│   │   Priority Order:                                         │             │
│   │   1. SEC 8-K Item Codes (HARD RULE)                      │             │
│   │   2. Keyword Patterns (DETERMINISTIC)                     │             │
│   │   3. LLM Tiebreaker (AMBIGUOUS ONLY)                     │             │
│   └──────────────────────────────────────────────────────────┘             │
│                              │                                              │
│                              ▼                                              │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                     MATCH COMPANY                         │             │
│   │                       (Middle)                            │             │
│   │                                                           │             │
│   │   Priority Order:                                         │             │
│   │   1. Exact Domain Match                                   │             │
│   │   2. Exact Normalized Name                                │             │
│   │   3. PostgreSQL FTS                                       │             │
│   │   4. rapidfuzz (≥0.90 threshold)                         │             │
│   │                                                           │             │
│   │   FAIL CLOSED: No match → QUEUE for Identity Resolution  │             │
│   └──────────────────────────────────────────────────────────┘             │
│                              │                                              │
│          ┌───────────────────┼───────────────────┐                         │
│          ▼                   ▼                   ▼                         │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐                   │
│   │  MATCHED   │      │  QUEUED    │      │  DROPPED   │                   │
│   │            │      │            │      │            │                   │
│   │ Continue   │      │ Identity   │      │ Log AIR    │                   │
│   │ Pipeline   │      │ Resolution │      │ TERMINAL   │                   │
│   └────────────┘      └────────────┘      └────────────┘                   │
│          │                                                                  │
│          ▼                                                                  │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                    VALIDATE SIGNAL                        │             │
│   │                       (Middle)                            │             │
│   │                                                           │             │
│   │   Gates (ALL must pass):                                  │             │
│   │   1. company_sov_id exists                                │             │
│   │   2. event_type is allowed                                │             │
│   │   3. confidence ≥ 0.75                                    │             │
│   │   4. source is declared                                   │             │
│   │   5. signal is not duplicate (30-day window)             │             │
│   └──────────────────────────────────────────────────────────┘             │
│                              │                                              │
│                              ▼                                              │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                    EMIT BIT SIGNAL                        │             │
│   │                       (Output)                            │             │
│   │                                                           │             │
│   │   • Send to BIT Engine                                    │             │
│   │   • Write AIR Log Entry                                   │             │
│   │   • Track Cost Attribution                                │             │
│   │   • Return EMITTED terminal state                         │             │
│   └──────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
hubs/blog-content/
├── __init__.py              # Main entry point
├── blog_node_spoke.py       # Pipeline orchestrator
├── pipeline.md              # This document
├── PRD.md                   # Product Requirements
├── ADR.md                   # Architecture Decision Record
├── hub.manifest.yaml        # Hub configuration
└── imo/
    ├── __init__.py
    ├── input/
    │   ├── __init__.py
    │   └── ingest_article.py    # Stage 1: Article ingestion
    ├── middle/
    │   ├── __init__.py
    │   ├── parse_content.py     # Stage 2: Content parsing
    │   ├── extract_entities.py  # Stage 3: Entity extraction
    │   ├── classify_event.py    # Stage 4: Event classification
    │   ├── match_company.py     # Stage 5: Company matching
    │   └── validate_signal.py   # Stage 6: Signal validation
    └── output/
        ├── __init__.py
        └── emit_bit_signal.py   # Stage 7: Signal emission
```

---

## Event Types (Locked)

| Event Type | BIT Impact | Description |
|------------|------------|-------------|
| FUNDING_EVENT | +15.0 | Funding rounds, investments |
| ACQUISITION | +12.0 | M&A activity |
| LEADERSHIP_CHANGE | +8.0 | Executive appointments/departures |
| EXPANSION | +7.0 | New offices, market entry |
| PRODUCT_LAUNCH | +5.0 | New products/services |
| PARTNERSHIP | +5.0 | Strategic partnerships |
| LAYOFF | -3.0 | Workforce reductions |
| NEGATIVE_NEWS | -5.0 | Lawsuits, scandals, regulatory issues |

---

## Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| BLOG-000 | Kill Switch | Pipeline killed by switch |
| BLOG-001 | Ingest/Parse | Article parsing failed |
| BLOG-002 | Extract | NER extraction failed |
| BLOG-003 | Classify | Low confidence / classification failed |
| BLOG-004 | Match | Company not matched |
| BLOG-201 | Emit | BIT Engine unavailable |
| BLOG-202 | Validate | Invalid company_id |
| BLOG-203 | Validate | Duplicate signal |
| BLOG-204 | Emit | Emission error |
| BLOG-301 | Match | Company fuzzy match below threshold |
| BLOG-999 | Any | Unhandled exception |

---

## Kill Switches

| Switch | Scope | Effect |
|--------|-------|--------|
| KILL_BLOG_SUBHUB | ALL | Stops all pipeline processing |
| KILL_FUNDING_DETECTION | FUNDING_EVENT | Blocks funding signal emission |
| KILL_MA_DETECTION | ACQUISITION | Blocks M&A signal emission |
| KILL_LEADERSHIP_DETECTION | LEADERSHIP_CHANGE | Blocks leadership signal emission |
| KILL_BLOG_SIGNALS | EMISSION | Stops signal emission (validates only) |

---

## Terminal States

| State | Meaning | Action |
|-------|---------|--------|
| EMITTED | Signal sent to BIT Engine | Success path |
| QUEUED | Company not found | Route to Identity Resolution |
| DROPPED | Validation failed | Log and discard |

---

## Tools & Dependencies

### Ingestion (Pluggable)

| Tool | Purpose | Source Type |
|------|---------|-------------|
| NewsAPI | News aggregation | General news |
| RSS | Feed parsing | Company blogs, PR |
| SEC EDGAR | 8-K filings | Material events |

### Entity Extraction

| Tool | Purpose | Priority |
|------|---------|----------|
| spaCy (en_core_web_lg) | NER | Primary |
| Regex patterns | Fallback/enhancement | Secondary |

### Company Matching

| Method | Threshold | Priority |
|--------|-----------|----------|
| Exact domain | N/A | 1 |
| Exact normalized name | N/A | 2 |
| PostgreSQL FTS | Single match | 3 |
| rapidfuzz | ≥0.90 | 4 |

### Event Classification

| Method | When Used |
|--------|-----------|
| SEC 8-K codes | Always (if SEC source) |
| Keyword patterns | Primary classifier |
| LLM tiebreaker | Ambiguous cases only |

---

## Usage Example

```python
from hubs.blog_content import run

# Process an article
result = await run({
    'title': 'Acme Corp Raises $50M Series B',
    'content': 'Acme Corporation announced today that it has raised...',
    'source': 'newsapi',
    'source_url': 'https://example.com/news/acme-funding',
    'published_at': '2024-01-15T10:30:00Z'
})

# Check result
print(f"Terminal State: {result.terminal_state}")  # EMITTED
print(f"Company: {result.company_sov_id}")
print(f"Event: {result.event_type}")
print(f"Processing Time: {result.processing_time_ms}ms")
```

---

## Observability

Every pipeline run logs:

| Field | Description |
|-------|-------------|
| correlation_id | Unique trace ID |
| article_id | Article identifier |
| source | Input source |
| matched_company_sov_id | Matched company (if any) |
| event_type | Classified event (if any) |
| confidence | Classification confidence |
| terminal_state | Final state |
| processing_time_ms | Total processing time |
| llm_cost | Cost attribution (if LLM used) |

---

## Explicit Non-Goals

| Non-Goal | Reason |
|----------|--------|
| Content generation | Read-only signal emitter |
| Blog writing | Not a content system |
| Lead scoring | BIT handles scoring |
| Enrichment | Company Hub responsibility |
| Identity creation | Company Hub responsibility |

---

## Related Documentation

- [PRD.md](./PRD.md) - Product Requirements
- [ADR.md](./ADR.md) - Architecture Decision Record
- [hub.manifest.yaml](./hub.manifest.yaml) - Hub Configuration
- [BIT Doctrine](../../doctrine/ple/BIT_DOCTRINE.md) - Buyer Intent Tool
- [Company Hub](../company/README.md) - Company Master Data
