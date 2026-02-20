# PRD: Blog/News Sub-Hub v3.0

**Status:** Planned
**Version:** 3.0 (Constitutional Compliance)
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-29
**Doctrine:** IMO-Creator Constitutional Doctrine
**Barton ID Range:** `04.04.05.XX.XXXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |
| **Doctrine ID** | 04.04.05 |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0 |
| **Waterfall Order** | 5 |
| **Classification** | Optional |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms external news content and blog signals (CONSTANTS) into structured business event signals for buyer intent detection (VARIABLES) through CAPTURE (news and blog ingestion), COMPUTE (entity extraction, event detection, company matching), and GOVERN (signal emission with idempotency and confidence filtering)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | External news content → Structured business event signals |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `news_content_signals` | External Sources | News articles and press releases |
| `blog_content` | External Sources | Company blog content |
| `rss_feeds` | External Sources | RSS feed content |
| `outreach_id` | Outreach Spine | Operational identifier for FK linkage |
| `company_domain` | Company Target | Domain for company matching |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `funding_event_signal` | BIT Engine | Funding round detection signal |
| `acquisition_signal` | BIT Engine | M&A activity signal |
| `leadership_change_signal` | BIT Engine | Leadership change signal |
| `layoff_signal` | BIT Engine | Workforce reduction signal (negative) |
| `content_signal_count` | Outreach Blog table | Count of detected signals |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| News Ingestion | **CAPTURE** | I (Ingress) | Ingest news articles and blog content |
| Entity Extraction | **COMPUTE** | M (Middle) | Extract companies, people, events from content |
| Event Detection | **COMPUTE** | M (Middle) | Classify events (funding, M&A, leadership) |
| Company Matching | **COMPUTE** | M (Middle) | Match extracted entities to Company Hub records |
| Signal Emission | **GOVERN** | O (Egress) | Emit idempotent signals with confidence filtering |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | News ingestion, entity extraction, event detection, company matching, signal emission |
| **OUT OF SCOPE** | Company identity creation (Company Target owns), BIT scoring (BIT Engine owns), people management (People owns), DOL data (DOL owns) |

---

## Sub-Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       BLOG/NEWS SUB-HUB OWNERSHIP                             ║
║                                                                               ║
║   This sub-hub OWNS:                                                          ║
║   ├── Company news article ingestion                                         ║
║   ├── Blog post and press release monitoring                                 ║
║   ├── Funding event detection                                                ║
║   ├── M&A activity tracking                                                  ║
║   ├── Leadership change detection                                            ║
║   ├── Layoff/workforce signal detection                                      ║
║   └── Sentiment analysis and signal emission                                 ║
║                                                                               ║
║   This sub-hub DOES NOT OWN:                                                  ║
║   ├── Company identity creation (company_id, domain)                         ║
║   ├── Email pattern discovery or generation                                  ║
║   ├── People lifecycle management or slot assignment                         ║
║   ├── BIT Engine scoring or decision making                                  ║
║   ├── Outreach decisions (who gets messaged, when, how)                      ║
║   └── DOL filing ingestion                                                   ║
║                                                                               ║
║   This sub-hub EMITS SIGNALS to Company Hub. It NEVER makes decisions.       ║
║                                                                               ║
║   PREREQUISITE: company_id MUST exist before signal emission.                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Correlation ID Doctrine

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Every article ingested into the Blog/News Sub-Hub receives a correlation_id║
║   (UUID v4) at ingest time. This ID propagates through:                      ║
║                                                                               ║
║   1. Article parsing                                                          ║
║   2. Entity extraction                                                        ║
║   3. Company matching                                                         ║
║   4. Event classification                                                     ║
║   5. Signal emission to BIT Engine                                           ║
║   6. Error logging                                                            ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every article ingest MUST generate or receive correlation_id            ║
║   2. Every signal emitted to BIT Engine MUST include correlation_id          ║
║   3. Every error logged MUST include correlation_id                          ║
║   4. correlation_id MUST NOT be modified after initial generation            ║
║   5. Articles reprocessed use original correlation_id (idempotency)          ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Signal Idempotency Doctrine

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       SIGNAL IDEMPOTENCY ENFORCEMENT                          ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Blog/News Sub-Hub MUST ensure signals are not duplicated.                  ║
║                                                                               ║
║   DEDUPLICATION RULES:                                                        ║
║   ├── Key: (company_id, signal_type, article_id)                             ║
║   ├── Window: 30 days (news events are time-sensitive)                       ║
║   └── Hash: SHA-256 of key fields for fast lookup                            ║
║                                                                               ║
║   DUPLICATE HANDLING:                                                         ║
║   ├── Same article reprocessed → Skip signal emission                        ║
║   ├── Same event from different source → Emit if confidence higher           ║
║   └── Similar event (fuzzy) → Log for human review                           ║
║                                                                               ║
║   DEDUPLICATION FLOW:                                                         ║
║   1. Generate signal_key hash                                                 ║
║   2. Check signal_cache for existing key (30-day window)                     ║
║   3. If exists and same source: SKIP                                         ║
║   4. If exists and different source: Compare confidence, emit if higher      ║
║   5. If not exists: Emit signal and cache key                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Blog Sub-Hub Live Metrics (2026-02-13 VERIFIED)

> **Standard View**: See `docs/DATABASE_OVERVIEW_TEMPLATE.md` for the complete Database Overview format.

| Metric | Count | % of 94,129 |
|--------|-------|-------------|
| **Blog Coverage** | 93,596 | 99.4% |
| **Companies with Sitemap** | 31,679 | 33.7% |
| **Companies with Source URLs** | 40,381 | 42.9% |
| **Company LinkedIn** | 45,057 | 47.9% |
| Domain Reachable | 52,870 | 85.4% of checked |
| Domain Unreachable | 9,047 | 14.6% of checked |

### Source URL Types (vendor.blog, source_table = 'company.company_source_urls')

| Source Type | Count | Purpose |
|-------------|-------|---------|
| `about_page` | 26,662 | Company About Us pages |
| `press_page` | 14,377 | News/Press/Announcements |
| `leadership_page` | 12,602 | Executive bios |
| `team_page` | 8,896 | Staff listings |
| `careers_page` | 16,262 | Job postings |
| `contact_page` | 25,213 | Contact info |
| **Total URLs** | **104,012** | **36,142 companies** |

> **Phase 3 Note (2026-02-20)**: Source URL data migrated from `company.company_source_urls` to `vendor.blog`. Spine-linked URLs remain in `outreach.source_urls`.

### Data Sources

| Metric | Source Table |
|--------|-------------|
| Blog Coverage | `outreach.blog` |
| Sitemaps | `vendor.blog` (`source_table = 'outreach.sitemap_discovery'`, `has_sitemap = TRUE`) |
| Source URLs | `vendor.blog` (`source_table = 'company.company_source_urls'`) or `outreach.source_urls` (spine-linked) |
| Company LinkedIn | `cl.company_identity.linkedin_company_url` |
| Domain Health | `vendor.blog` (`source_table = 'outreach.sitemap_discovery'`, `domain_reachable`) |

---

## 1. Purpose

The Blog/News Sub-Hub monitors external news sources, company blogs, and press releases to detect business events that signal buyer intent. It processes unstructured content and emits structured signals to the BIT Engine.

### Core Functions

1. **News Ingestion** - Crawl and ingest company news articles
2. **Event Detection** - Identify funding, M&A, leadership changes
3. **Sentiment Analysis** - Analyze content for positive/negative signals
4. **Entity Matching** - Match articles to Company Hub records
5. **Signal Emission** - Emit intent signals to BIT Engine
6. **Competitor Intel** - Track competitor mentions and movements

### Company-First Doctrine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   IF company cannot be matched to company_id:                          │
│       Queue article for Company Identity resolution.                    │
│       DO NOT emit signals without valid company anchor.                 │
│                                                                         │
│   Blog/News Sub-Hub NEVER creates company identity.                    │
│   Blog/News Sub-Hub requests identity creation from Company Hub.        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Sources

### Primary Sources

| Source | Type | Frequency |
|--------|------|-----------|
| Company Blogs | RSS/Crawl | Daily |
| Press Releases | PR Newswire, GlobeNewswire | Real-time |
| News APIs | NewsAPI, Bing News | Hourly |
| LinkedIn News | Company page posts | Daily |
| SEC Filings | 8-K, press releases | Real-time |

### Content Types

| Type | Signal Potential | Priority |
|------|-----------------|----------|
| Funding Announcements | Very High (+15) | 1 |
| M&A Announcements | Very High (+12) | 1 |
| Leadership Changes | High (+8) | 2 |
| Product Launches | Medium (+5) | 3 |
| Layoff Announcements | Negative (-3) | 2 |
| Expansion News | High (+7) | 2 |
| Partnership Announcements | Medium (+5) | 3 |

---

## 3. Tooling Declarations

### News Ingestion Tools

| Tool | Purpose | Rate Limit | Cost Tier | Cache Policy |
|------|---------|------------|-----------|--------------|
| NewsAPI | News article search | 100 req/day (free) | $0-$449/mo | 1 hour |
| Bing News Search | News aggregation | 1000 req/mo (free) | $7/1K transactions | 1 hour |
| PR Newswire API | Press releases | Per contract | Enterprise | No cache |
| GlobeNewswire | Press releases | Per contract | Enterprise | No cache |
| SEC EDGAR API | 8-K filings | No limit (public) | Free | 24 hours |
| Firecrawl | Company blog crawl | 500 pages/mo | $19-$99/mo | 24 hours |

### NLP/Entity Extraction Tools

| Tool | Purpose | Rate Limit | Cost Tier | Cache Policy |
|------|---------|------------|-----------|--------------|
| spaCy (en_core_web_lg) | NER extraction | Local | Free | N/A |
| OpenAI GPT-4 | Event classification | 10K TPM | $0.03/1K tokens | 1 hour |
| Anthropic Claude | Event classification | 100K TPM | $0.008/1K tokens | 1 hour |
| LangChain | Pipeline orchestration | N/A | Free | N/A |

### Entity Matching Tools

| Tool | Purpose | Rate Limit | Cost Tier | Cache Policy |
|------|---------|------------|-----------|--------------|
| rapidfuzz | Fuzzy company matching | Local | Free | N/A |
| PostgreSQL FTS | Full-text search | N/A | DB cost | N/A |
| Company Hub API | Domain/name lookup | Internal | Free | 5 minutes |

### Rate Limit Policy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RATE LIMIT POLICY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NewsAPI (Free Tier):                                                      │
│   ├── 100 requests/day                                                      │
│   ├── Backoff: Exponential (1s → 2s → 4s → 8s)                             │
│   └── Fallback: Switch to Bing News Search                                 │
│                                                                             │
│   OpenAI/Anthropic:                                                         │
│   ├── Rate limit: Token-based (TPM)                                         │
│   ├── Backoff: Exponential with jitter                                     │
│   └── Fallback: Queue for retry with 60s delay                             │
│                                                                             │
│   Firecrawl:                                                                 │
│   ├── 500 pages/month (Hobby)                                               │
│   ├── Priority: High-value company blogs only                              │
│   └── Fallback: BeautifulSoup direct crawl                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Owned Processes

### Blog Node Spoke (Planned)

**Status:** PLANNED
**Purpose:** Process news articles and emit signals to BIT Engine

#### Process Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BLOG NODE PROCESS FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

    NEWS SOURCES                           BLOG SUB-HUB
    (External)                             (Signal Emitter)

    ┌───────────────────┐                  ┌───────────────────┐
    │ News APIs         │                  │ Blog Node Spoke   │
    │                   │    Raw Article   │                   │
    │ • NewsAPI         ├─────────────────►│ 1. Parse content  │
    │ • PR Newswire     │                  │ 2. Extract entities│
    │ • Company blogs   │                  │ 3. Match to company│
    │ • SEC filings     │                  │ 4. Classify event │
    └───────────────────┘                  └─────────┬─────────┘
                                                     │
                                                     │ company_id found?
                                                     │
                              ┌───────────────────────┴───────────────────────┐
                              │ YES                                      NO   │
                              ▼                                              ▼
                    ┌───────────────────┐                    ┌───────────────────┐
                    │ Classify Event    │                    │ Queue for         │
                    │                   │                    │ Identity          │
                    │ • Funding?        │                    │ Resolution        │
                    │ • M&A?            │                    │                   │
                    │ • Leadership?     │                    │ Request company   │
                    │ • Layoff?         │                    │ creation from Hub │
                    └─────────┬─────────┘                    └───────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Emit Signal       │
                    │                   │
                    │ • FUNDING_EVENT   │
                    │ • ACQUISITION     │
                    │ • LEADERSHIP_CHG  │
                    │ • LAYOFF          │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ BIT ENGINE        │
                    │ (Company Hub)     │
                    │                   │
                    │ Aggregate signals │
                    │ Calculate score   │
                    └───────────────────┘
```

#### Input Contract: NewsArticle

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlation_id` | string (UUID v4) | Yes | **Pipeline trace ID - generated at ingest** |
| `article_id` | string | Yes | Unique article identifier |
| `title` | string | Yes | Article headline |
| `content` | string | Yes | Full article text |
| `source` | string | Yes | News source (NewsAPI, PR Newswire) |
| `published_at` | datetime | Yes | Publication timestamp |
| `url` | string | Yes | Source URL |
| `company_mentions` | List[str] | No | Extracted company names |
| `domain_mentions` | List[str] | No | Extracted domains |
| `ingested_at` | datetime | Yes | When article was ingested |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | string (UUID v4) | **Same as input - propagated unchanged** |
| `status` | ResultStatus | SUCCESS, FAILED, SKIPPED |
| `event_type` | EventType | FUNDING, ACQUISITION, etc. |
| `company_id` | string | Matched company |
| `confidence` | float | Event detection confidence (0.0-1.0) |
| `signals_emitted` | List[Dict] | Signals sent to BIT Engine |
| `processing_time_ms` | int | Time to process article |
| `failure_reason` | string | Null if success, error code if failed |

---

## 4. Signal Emission

### Signal Types

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| `FUNDING_EVENT` | `SignalType.FUNDING_EVENT` | +15.0 | Funding round announced |
| `ACQUISITION` | `SignalType.ACQUISITION` | +12.0 | M&A activity detected |
| `LEADERSHIP_CHANGE` | `SignalType.LEADERSHIP_CHANGE` | +8.0 | C-suite change announced |
| `EXPANSION` | `SignalType.EXPANSION` | +7.0 | New office/market expansion |
| `PRODUCT_LAUNCH` | `SignalType.PRODUCT_LAUNCH` | +5.0 | New product announced |
| `PARTNERSHIP` | `SignalType.PARTNERSHIP` | +5.0 | Partnership announced |
| `LAYOFF` | `SignalType.LAYOFF` | -3.0 | Workforce reduction |
| `NEGATIVE_NEWS` | `SignalType.NEGATIVE_NEWS` | -5.0 | Legal issues, scandals |

### Signal Emission Code (Planned)

```python
class BlogNodeSpoke(Spoke):
    """
    Blog/News Node - Processes news and emits signals.

    ONLY emits signals. NEVER makes outreach decisions.
    """

    def _send_signal(
        self,
        correlation_id: str,  # REQUIRED - propagated from article ingest
        signal_type: SignalType,
        company_id: str,
        article_id: str,
        impact: float,
        confidence: float,
        metadata: Dict = None
    ):
        """
        Core signal emission with deduplication.

        IDEMPOTENCY: Uses (company_id, signal_type, article_id) as dedup key.
        WINDOW: 30 days (news events are time-sensitive).
        """
        # Generate deduplication key
        dedup_key = f"{company_id}:{signal_type.value}:{article_id}"

        # Check deduplication (30-day window for news events)
        existing = self.signal_cache.get(dedup_key, window_days=30)
        if existing:
            # Same article already processed - skip
            if existing['source'] == 'blog_node':
                logger.info(
                    f"Signal dedup: skipping duplicate",
                    extra={
                        'correlation_id': correlation_id,
                        'dedup_key': dedup_key,
                        'original_correlation_id': existing['correlation_id']
                    }
                )
                return
            # Different source with lower confidence - skip
            if existing['confidence'] >= confidence:
                logger.info(f"Signal dedup: existing signal has higher confidence")
                return

        # Emit signal to BIT Engine
        self.bit_engine.create_signal(
            correlation_id=correlation_id,  # REQUIRED
            signal_type=signal_type,
            company_id=company_id,
            source_spoke='blog_node',
            impact=impact,
            metadata={
                **(metadata or {}),
                'confidence': confidence,
                'detected_at': datetime.now().isoformat()
            }
        )

        # Cache for deduplication
        self.signal_cache.set(dedup_key, {
            'correlation_id': correlation_id,
            'source': 'blog_node',
            'confidence': confidence,
            'emitted_at': datetime.now().isoformat()
        }, ttl_days=30)

    def _emit_funding_signal(
        self,
        correlation_id: str,  # REQUIRED
        company_id: str,
        article: NewsArticle,
        funding_details: FundingDetails
    ):
        """Emit funding event signal to BIT Engine"""
        self._send_signal(
            correlation_id=correlation_id,
            signal_type=SignalType.FUNDING_EVENT,
            company_id=company_id,
            article_id=article.article_id,
            impact=15.0,
            confidence=funding_details.confidence,
            metadata={
                'article_id': article.article_id,
                'funding_amount': funding_details.amount,
                'funding_round': funding_details.round,  # Series A, B, etc.
                'lead_investor': funding_details.lead_investor,
                'source_url': article.url
            }
        )

    def _emit_acquisition_signal(
        self,
        correlation_id: str,  # REQUIRED
        company_id: str,
        article: NewsArticle,
        acquisition_details: AcquisitionDetails
    ):
        """Emit acquisition signal to BIT Engine"""
        self._send_signal(
            correlation_id=correlation_id,
            signal_type=SignalType.ACQUISITION,
            company_id=company_id,
            article_id=article.article_id,
            impact=12.0,
            confidence=acquisition_details.confidence,
            metadata={
                'article_id': article.article_id,
                'acquisition_type': acquisition_details.type,  # acquired, acquiring
                'target_company': acquisition_details.target,
                'deal_value': acquisition_details.value,
                'source_url': article.url
            }
        )

    def _emit_leadership_change_signal(
        self,
        correlation_id: str,  # REQUIRED
        company_id: str,
        article: NewsArticle,
        leadership_details: LeadershipChange
    ):
        """Emit leadership change signal to BIT Engine"""
        self._send_signal(
            correlation_id=correlation_id,
            signal_type=SignalType.LEADERSHIP_CHANGE,
            company_id=company_id,
            article_id=article.article_id,
            impact=8.0,
            confidence=leadership_details.confidence,
            metadata={
                'article_id': article.article_id,
                'person_name': leadership_details.person_name,
                'new_title': leadership_details.new_title,
                'previous_title': leadership_details.previous_title,
                'change_type': leadership_details.change_type,  # hired, promoted, departed
                'source_url': article.url
            }
        )

    def _emit_layoff_signal(
        self,
        correlation_id: str,  # REQUIRED
        company_id: str,
        article: NewsArticle,
        layoff_details: LayoffDetails
    ):
        """Emit layoff signal to BIT Engine (negative impact)"""
        self._send_signal(
            correlation_id=correlation_id,
            signal_type=SignalType.LAYOFF,
            company_id=company_id,
            article_id=article.article_id,
            impact=-3.0,  # Negative impact
            confidence=layoff_details.confidence,
            metadata={
                'article_id': article.article_id,
                'headcount_affected': layoff_details.headcount,
                'percentage': layoff_details.percentage,
                'reason': layoff_details.reason,
                'source_url': article.url
            }
        )
```

---

## 5. Event Detection

### Event Classification Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT CLASSIFICATION PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────┘

    Raw Article
         │
         ▼
┌─────────────────────┐
│ 1. TEXT EXTRACTION  │
│                     │
│ • Strip HTML        │
│ • Normalize text    │
│ • Extract title     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 2. ENTITY EXTRACTION│
│                     │
│ • Company names     │
│ • Person names      │
│ • Dollar amounts    │
│ • Dates             │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 3. EVENT DETECTION  │
│                     │
│ • Funding keywords  │
│ • M&A keywords      │
│ • Leadership keywords│
│ • Layoff keywords   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 4. CONFIDENCE SCORE │
│                     │
│ • Keyword density   │
│ • Entity quality    │
│ • Source reliability│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 5. SIGNAL EMISSION  │
│ (if confidence > threshold)│
└─────────────────────┘
```

### Event Keyword Patterns

#### Funding Events

```python
FUNDING_KEYWORDS = [
    'raised', 'funding', 'series a', 'series b', 'series c',
    'seed round', 'venture capital', 'investment round',
    'led by', 'participated in', 'million in funding',
    'billion in funding', 'closes', 'announces funding'
]

FUNDING_ENTITIES = [
    'amount',           # $X million, $X billion
    'round_type',       # Series A, seed, growth
    'lead_investor',    # Led by XYZ Capital
    'participating'     # With participation from
]
```

#### M&A Events

```python
MA_KEYWORDS = [
    'acquired', 'acquisition', 'merger', 'merged with',
    'buys', 'purchased', 'deal', 'transaction',
    'to acquire', 'acquisition of', 'merger agreement',
    'combined company', 'will acquire'
]

MA_ENTITIES = [
    'target_company',   # Company being acquired
    'acquirer',         # Company doing the acquiring
    'deal_value',       # Transaction value
    'deal_type'         # Acquisition, merger, spin-off
]
```

#### Leadership Changes

```python
LEADERSHIP_KEYWORDS = [
    'appointed', 'named', 'promoted', 'joins',
    'steps down', 'departs', 'resigned', 'retiring',
    'new ceo', 'new cfo', 'new cto', 'new coo',
    'chief executive', 'chief financial', 'chief technology'
]

LEADERSHIP_ENTITIES = [
    'person_name',      # Executive name
    'new_title',        # New position
    'previous_title',   # Previous position
    'previous_company'  # Where they came from
]
```

#### Layoff Events

```python
LAYOFF_KEYWORDS = [
    'layoff', 'layoffs', 'workforce reduction',
    'cutting jobs', 'job cuts', 'downsizing',
    'restructuring', 'letting go', 'eliminating',
    'reducing headcount', 'staff reduction'
]

LAYOFF_ENTITIES = [
    'headcount',        # Number affected
    'percentage',       # Percentage of workforce
    'departments',      # Affected departments
    'reason'            # Why (cost cutting, restructuring)
]
```

---

## 6. Entity Matching

### Matching Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY MATCHING                                    │
└─────────────────────────────────────────────────────────────────────────────┘

1. Extract company mentions from article
   └── NER (Named Entity Recognition)
   └── Pattern matching (Inc., LLC, Corp., etc.)

2. Normalize company names
   └── Remove legal suffixes (Inc., LLC)
   └── Lowercase and strip
   └── Remove punctuation

3. Query Company Hub
   └── Exact match: company_name
   └── Domain match: Extract domain from article URL or content
   └── Fuzzy match: Similarity score >= 0.90

4. Result:
   ├── company_id found → Proceed to event classification
   └── company_id NOT found → Queue for identity creation

5. No-Match Queue
   └── Store unmatched articles with:
       • Extracted company name
       • Article URL
       • Source domain
       • Source: 'blog_news'
```

### Matching Implementation (Planned)

```python
def match_company(self, article: NewsArticle) -> Optional[str]:
    """
    Match article to Company Hub record.

    Returns company_id if found, None otherwise.
    """
    # Try domain match first (most reliable)
    for domain in article.domain_mentions:
        company_id = self.company_hub.lookup_by_domain(domain)
        if company_id:
            return company_id

    # Try exact name match
    for company_name in article.company_mentions:
        normalized = self._normalize_company_name(company_name)
        company_id = self.company_hub.lookup_by_name(normalized)
        if company_id:
            return company_id

    # Try fuzzy match (with high threshold)
    for company_name in article.company_mentions:
        company_id = self.company_hub.fuzzy_lookup(
            company_name,
            threshold=0.90
        )
        if company_id:
            return company_id

    # No match - queue for identity creation
    self._queue_for_identity(article)
    return None
```

---

## 8. Failure Modes (Standardized)

### Detection Failures

| Failure | Error Code | Severity | Local Emit | Global Emit | Recovery |
|---------|------------|----------|------------|-------------|----------|
| Article parsing error | BLOG-001 | WARN | `blog_parsing_errors` | `shq_error_log` | Skip, queue for review |
| NER extraction failed | BLOG-002 | WARN | `blog_ner_failures` | `shq_error_log` | Fall back to keywords |
| Low confidence event | BLOG-003 | INFO | `blog_low_confidence` | — | Queue for human review |
| Company not matched | BLOG-004 | INFO | `blog_unmatched` | — | Queue for Company Hub |
| No events detected | — | DEBUG | — | — | Normal behavior |

### Processing Failures

| Failure | Error Code | Severity | Local Emit | Global Emit | Recovery |
|---------|------------|----------|------------|-------------|----------|
| NewsAPI rate limit | BLOG-101 | WARN | `blog_rate_limits` | `shq_error_log` | Exponential backoff |
| Source unavailable | BLOG-102 | WARN | `blog_source_failures` | `shq_error_log` | Queue for next cycle |
| Database connection | BLOG-103 | ERROR | `blog_db_errors` | `shq_error_log` | Retry with backoff, alert |
| LLM API timeout | BLOG-104 | WARN | `blog_llm_timeouts` | `shq_error_log` | Retry 3x, then skip |
| LLM API error | BLOG-105 | ERROR | `blog_llm_errors` | `shq_error_log` | Fall back to keywords |

### Signal Emission Failures

| Failure | Error Code | Severity | Local Emit | Global Emit | Recovery |
|---------|------------|----------|------------|-------------|----------|
| BIT Engine unavailable | BLOG-201 | ERROR | `blog_bit_failures` | `shq_error_log` | Queue signal for retry |
| Invalid company_id | BLOG-202 | WARN | `blog_invalid_company` | `shq_error_log` | Skip, investigate |
| Duplicate signal detected | BLOG-203 | DEBUG | — | — | Normal dedup behavior |
| Signal emission timeout | BLOG-204 | WARN | `blog_signal_timeouts` | `shq_error_log` | Retry 3x |

### Two-Layer Error Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TWO-LAYER ERROR MODEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: LOCAL (Blog Sub-Hub owned)                                       │
│   ├── Table: blog_processing_errors                                         │
│   ├── Owner: Blog/News Sub-Hub                                              │
│   ├── Purpose: Operational remediation                                      │
│   └── Fields: correlation_id, article_id, error_code, timestamp             │
│                                                                             │
│   LAYER 2: GLOBAL (System-wide visibility)                                  │
│   ├── Table: shq_error_log (public schema)                                  │
│   ├── Owner: Platform team                                                  │
│   ├── Purpose: Trend analysis, alerting                                     │
│   └── Fields: correlation_id, component='blog_subhub', error_code, severity │
│                                                                             │
│   ERROR FLOW:                                                               │
│   1. Error occurs during article processing                                 │
│   2. Log to local table (blog_processing_errors)                           │
│   3. If severity >= WARN: Also emit to shq_error_log                       │
│   4. Include correlation_id in BOTH logs                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Code Standards

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR CODE CONVENTIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Format: BLOG-{CATEGORY}{NUMBER}                                           │
│                                                                             │
│   Categories:                                                               │
│   ├── 0XX: Detection/Parsing errors                                         │
│   ├── 1XX: Processing/API errors                                            │
│   ├── 2XX: Signal emission errors                                           │
│   └── 3XX: Matching/Identity errors                                         │
│                                                                             │
│   Examples:                                                                 │
│   ├── BLOG-001: Article parsing failed                                      │
│   ├── BLOG-101: NewsAPI rate limit exceeded                                 │
│   ├── BLOG-201: BIT Engine unavailable                                      │
│   └── BLOG-301: Company fuzzy match below threshold                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Kill Switches

### Sub-Hub Level

```python
# Blog/News Sub-Hub Kill Switch
if os.environ.get('KILL_BLOG_SUBHUB', 'false').lower() == 'true':
    logger.warning("Blog/News Sub-Hub killed by configuration")
    return SpokeResult(
        status=ResultStatus.SKIPPED,
        failure_reason='killed_by_config'
    )
```

### Process-Level Kill Switches

| Switch | Scope | Effect |
|--------|-------|--------|
| `KILL_BLOG_SUBHUB` | All news processing | Stops entire sub-hub |
| `KILL_FUNDING_DETECTION` | Funding events | Stops funding detection |
| `KILL_MA_DETECTION` | M&A events | Stops M&A detection |
| `KILL_LEADERSHIP_DETECTION` | Leadership changes | Stops leadership detection |
| `KILL_BLOG_SIGNALS` | Signal emission | Stops signals to BIT Engine |

---

## 10. Observability

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `blog.articles.processed` | Counter | Total articles processed |
| `blog.articles.matched` | Counter | Articles matched to company |
| `blog.events.detected` | Counter | Events detected |
| `blog.events.type.{type}` | Counter | Events by type |
| `blog.signals.emitted` | Counter | Signals sent to BIT Engine |
| `blog.confidence.avg` | Gauge | Average event confidence |

### Logging

```python
# Standard log format for Blog/News Sub-Hub
logger.info(
    "Article processed",
    extra={
        'sub_hub': 'blog_news',
        'article_id': article.article_id,
        'source': article.source,
        'company_id': company_id,
        'event_type': event_type,
        'confidence': confidence
    }
)
```

---

## 11. Integration with Company Hub

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BLOG/NEWS → COMPANY HUB DATA FLOW                      │
└─────────────────────────────────────────────────────────────────────────────┘

    NEWS SOURCES                             COMPANY HUB
    (External)                               (Internal)

    ┌───────────────────┐                    ┌───────────────────┐
    │ NewsAPI           │                    │ Company Master    │
    │ PR Newswire       │                    │                   │
    │ Company blogs     │   Domain/Name      │ • company_id      │
    │ SEC filings       ├───────────────────►│ • domain          │
    │                   │      Query         │ • company_name    │
    └───────────────────┘                    └─────────┬─────────┘
                                                       │
                                                       │ company_id
                                                       │
                                             ┌─────────▼─────────┐
                                             │ Blog Sub-Hub      │
                                             │                   │
                                             │ • Parse article   │
                                             │ • Detect events   │
                                             │ • Emit signals    │
                                             └─────────┬─────────┘
                                                       │
                                                       │ SIGNALS
                                                       │ • FUNDING_EVENT
                                                       │ • ACQUISITION
                                                       │ • LEADERSHIP_CHANGE
                                                       │ • LAYOFF
                                                       │
                                             ┌─────────▼─────────┐
                                             │ BIT ENGINE        │
                                             │ (Company Hub)     │
                                             │                   │
                                             │ News signals      │
                                             │ contribute +15 to │
                                             │ -5 to BIT score   │
                                             └───────────────────┘
```

---

## 12. Configuration (Planned)

### Sub-Hub Configuration

```python
{
    'blog_subhub': {
        'enabled': False,               # PLANNED - not yet implemented
        'sources': {
            'newsapi': {
                'enabled': True,
                'api_key': 'env:NEWSAPI_KEY',
                'rate_limit': 100       # requests/day
            },
            'pr_newswire': {
                'enabled': True,
                'crawl_frequency': 3600  # seconds
            },
            'company_blogs': {
                'enabled': True,
                'crawl_frequency': 86400 # daily
            }
        },
        'detection': {
            'min_confidence': 0.75,     # Min confidence to emit signal
            'review_threshold': 0.50    # Queue for review if below
        },
        'matching': {
            'exact_match': True,
            'fuzzy_match': True,
            'fuzzy_threshold': 0.90
        }
    }
}
```

### Signal Configuration

```python
{
    'signals': {
        'FUNDING_EVENT': {
            'enabled': True,
            'impact': 15.0
        },
        'ACQUISITION': {
            'enabled': True,
            'impact': 12.0
        },
        'LEADERSHIP_CHANGE': {
            'enabled': True,
            'impact': 8.0
        },
        'LAYOFF': {
            'enabled': True,
            'impact': -3.0
        }
    }
}
```

---

## 13. Implementation Roadmap

### Phase 1: Foundation (Planned)

- [ ] Create `blog_node_spoke.py` base structure
- [ ] Implement NewsAPI integration
- [ ] Build basic keyword-based event detection
- [ ] Add company matching via domain lookup

### Phase 2: Enhanced Detection (Planned)

- [ ] Implement NER for entity extraction
- [ ] Add funding event detection with amount extraction
- [ ] Add M&A detection with target/acquirer identification
- [ ] Add leadership change detection

### Phase 3: Intelligence (Planned)

- [ ] Add sentiment analysis
- [ ] Implement confidence scoring model
- [ ] Add competitor intelligence tracking
- [ ] Build article deduplication

### Phase 4: Scale (Planned)

- [ ] Add PR Newswire integration
- [ ] Add SEC 8-K filing integration
- [ ] Implement company blog RSS crawling
- [ ] Build real-time processing pipeline

---

## 14. Promotion States

### Burn-In Mode vs Steady-State Mode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROMOTION STATE DEFINITIONS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BURN-IN MODE (Initial Deployment)                                         │
│   ├── Duration: First 30 days of production                                 │
│   ├── Thresholds: Higher confidence required (0.85 vs 0.75)                 │
│   ├── Kill switches: More sensitive (3 errors → kill)                      │
│   ├── Alerting: Immediate on any ERROR severity                            │
│   └── Review: All signals queued for human verification                     │
│                                                                             │
│   STEADY-STATE MODE (After Validation)                                      │
│   ├── Promotion: After passing all gates below                              │
│   ├── Thresholds: Standard confidence (0.75)                                │
│   ├── Kill switches: Standard sensitivity (10 errors → kill)               │
│   ├── Alerting: Standard alerting rules                                    │
│   └── Review: Only low-confidence signals reviewed                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Promotion Gates (Burn-In → Steady-State)

| Gate | Criteria | Measurement |
|------|----------|-------------|
| G1 | ≥100 articles processed without critical error | `blog.articles.processed >= 100 AND blog.errors.critical == 0` |
| G2 | Company match rate ≥ 60% | `blog.articles.matched / blog.articles.processed >= 0.60` |
| G3 | Signal confidence mean ≥ 0.80 | `AVG(confidence) >= 0.80` |
| G4 | No BIT Engine emission failures in 7 days | `blog_bit_failures.count(7d) == 0` |
| G5 | Human review approval rate ≥ 90% | `blog.signals.approved / blog.signals.reviewed >= 0.90` |
| G6 | All API integrations stable (99% uptime) | `blog.api.uptime >= 0.99` |
| G7 | Deduplication working (≤ 1% duplicate signals) | `blog.signals.duplicates / blog.signals.emitted <= 0.01` |
| G8 | False positive rate ≤ 5% | `blog.signals.false_positive / blog.signals.emitted <= 0.05` |

### State Transition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE TRANSITION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐                              ┌───────────────┐
    │   BURN-IN     │    All gates G1-G8 pass     │  STEADY-STATE │
    │               │─────────────────────────────►│               │
    │  (30 days)    │                              │  (Ongoing)    │
    └───────────────┘                              └───────────────┘
           │                                              │
           │  Critical failure                            │  Regression detected
           │  or gate regression                         │  (fails G1-G8)
           │                                              │
           ▼                                              ▼
    ┌───────────────┐                              ┌───────────────┐
    │   SUSPENDED   │                              │   BURN-IN     │
    │               │                              │   (Reset)     │
    │  Manual fix   │                              │               │
    │  required     │                              │  Re-validate  │
    └───────────────┘                              └───────────────┘
```

---

## 15. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial Blog/News Sub-Hub PRD (PLANNED status) |
| 2.1 | 2025-12-17 | Hardened: Correlation ID, Signal Idempotency, Tooling, Failure Handling, Promotion States |
| 3.0 | 2026-02-13 | Added live metrics: blog coverage 93,596 (99.4%), sitemaps 31,679 (33.7%), source URLs 104,012 across 36,142 companies, company LinkedIn 45,057 (47.9%). Reference to Database Overview Template. |

---

*Document Version: 3.0*
*Last Updated: 2026-02-13*
*Owner: Blog/News Sub-Hub*
*Status: ACTIVE (data populated, signal detection PLANNED)*
*Doctrine: CL Parent-Child Doctrine v1.1 / Barton Doctrine*
