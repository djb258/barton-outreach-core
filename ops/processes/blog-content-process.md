# Process Declaration: Blog Content Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-04 (Process) |
| **Process Doctrine** | `templates/doctrine/PROCESS_DOCTRINE.md` |

---

## Process Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-BLOG-001 |
| **Doctrine ID** | 04.04.05 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
blog-content-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `crawl` | News/blog crawl | `blog-content-crawl-20260129-a1b2c3d4` |
| `detect` | Event detection | `blog-content-detect-20260129-b2c3d4e5` |
| `match` | Company matching | `blog-content-match-20260129-c3d4e5f6` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_BLOG_NEWS_SUBHUB.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | outreach.outreach | Operational spine identifier |
| `company_sov_id` | CL | Company identity for matching |
| `news_feed_data` | External RSS/APIs | Raw news feed content |
| `funding_alerts` | External providers | Funding event notifications |
| `content_webhooks` | External services | Real-time content webhooks |

---

## Variables Produced

_Reference: `docs/prd/PRD_BLOG_NEWS_SUBHUB.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `blog_url` | outreach.blog | Discovered blog URL |
| `rss_feed_url` | outreach.blog | RSS feed URL |
| `signal_count` | outreach.blog | Number of signals detected |
| `FUNDING_EVENT_signal` | BIT Engine | Signal emission (+15.0) |
| `ACQUISITION_signal` | BIT Engine | Signal emission (+12.0) |
| `LEADERSHIP_CHANGE_signal` | BIT Engine | Signal emission (+8.0) |
| `LAYOFF_signal` | BIT Engine | Signal emission (-3.0) |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_BLOG_NEWS_SUBHUB.md` |
| **PRD Version** | 3.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive news feeds, funding alerts, content webhooks |
| **COMPUTE** | M (Middle) | Event detection, company matching, sentiment analysis |
| **GOVERN** | O (Egress) | Emit FUNDING_EVENT, ACQUISITION, LEADERSHIP_CHANGE signals |

---

## Execution Flow

```
1. CAPTURE: Ingest news feeds and funding alerts
   ↓
2. COMPUTE: Detect event type (funding, acquisition, etc.)
   ↓
3. COMPUTE: Match article to company via entity extraction
   ↓
4. COMPUTE: Classify sentiment (positive/negative impact)
   ↓
5. GOVERN: Write to outreach.blog
   ↓
6. GOVERN: Emit appropriate signal to BIT Engine
```

---

## Signal Emissions

| Signal | Impact | Dedup Key | Window |
|--------|--------|-----------|--------|
| `FUNDING_EVENT` | +15.0 | `(company_id, article_id)` | 30 days |
| `ACQUISITION` | +12.0 | `(company_id, article_id)` | 30 days |
| `LEADERSHIP_CHANGE` | +8.0 | `(company_id, article_id)` | 30 days |
| `EXPANSION` | +7.0 | `(company_id, article_id)` | 30 days |
| `PRODUCT_LAUNCH` | +5.0 | `(company_id, article_id)` | 30 days |
| `PARTNERSHIP` | +5.0 | `(company_id, article_id)` | 30 days |
| `LAYOFF` | -3.0 | `(company_id, article_id)` | 30 days |
| `NEGATIVE_NEWS` | -5.0 | `(company_id, article_id)` | 30 days |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `BLOG-001` | LOW | RSS feed unavailable |
| `BLOG-002` | MEDIUM | Event detection confidence < 0.5 |
| `BLOG-003` | HIGH | Company matching failed |
| `BLOG-101` | LOW | Article parse error |
| `BLOG-201` | MEDIUM | Entity extraction failed |

---

## Authority Constraints

| Can Do | Cannot Do |
|--------|-----------|
| Emit timing signals | Mint companies |
| Modulate BIT scores | Revive companies |
| Read company_sov_id | Trigger enrichment |
| Read lifecycle_state | Mutate lifecycle |

---

## Correlation ID Enforcement

- `correlation_id` generated at article ingest (one per article)
- Included in all signal emissions
- Stored in `outreach.blog_errors` for tracing

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_BLOG_NEWS_SUBHUB.md` |
| **Tables READ** | `cl.company_identity`, `outreach.outreach` |
| **Tables WRITTEN** | `outreach.blog`, `blog.pressure_signals`, `outreach.bit_signals`, `outreach.blog_errors` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
