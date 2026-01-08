# PRD: Blog Content Sub-Hub v3.0

**Status:** PRODUCTION LOCKED
**Version:** 3.0 (Spine-First Architecture)
**Last Updated:** 2026-01-08
**Doctrine:** Spine-First Architecture v1.1
**Waterfall Position:** 4th (LAST)
**IMO Gate:** `hubs/blog-content/imo/blog_imo.py`

---

## Sub-Hub Ownership Statement

```
+===============================================================================+
|                       BLOG CONTENT SUB-HUB OWNERSHIP                          |
|                                                                               |
|   This sub-hub OWNS:                                                          |
|   +-- Company timing signals from news/content                                |
|   +-- Event classification (8 locked types)                                   |
|   +-- BIT impact modulation                                                   |
|   +-- Context finalization (last hub in waterfall)                            |
|                                                                               |
|   This sub-hub DOES NOT OWN:                                                  |
|   +-- Company identity (outreach_id comes from spine)                         |
|   +-- Email patterns or enrichment                                            |
|   +-- People lifecycle or slot assignment                                     |
|   +-- Audience metrics or social engagement data                              |
|                                                                               |
|   IDENTITY: outreach_id is the ONLY identity. sovereign_id is hidden.         |
|   SCOPE: Company-level only. Records WHERE a company publishes, not HOW LARGE.|
|                                                                               |
+===============================================================================+
```

---

## Doctrine Guards (LOCKED)

```python
# Spine Guard - sub-hubs don't see sovereign_id
ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True

# Scope Guard - no social metrics
DISALLOW_SOCIAL_METRICS = True
assert DISALLOW_SOCIAL_METRICS is True

# Error Guard - no silent failures
ENFORCE_ERROR_PERSISTENCE = True
assert ENFORCE_ERROR_PERSISTENCE is True
```

---

## 1. Purpose

Provide **timing signals** from news, funding events, and content sources. BIT modulation only - cannot mint, revive, or trigger enrichment. FINAL hub in waterfall - context is finalized after this hub.

### Core Functions

1. **Event Classification** - Classify content into 8 locked event types
2. **BIT Impact** - Emit signals with fixed impact values (+15.0 to -5.0)
3. **Context Finalization** - Last hub, context finalized after PASS

### Scope Lock

> **The Blog Sub-Hub records *where* a company publishes, not *how large* the audience is.**

Social platforms (LinkedIn, Twitter, etc.) are treated as company-owned distribution surfaces for presence verification only. NO audience metrics, engagement metrics, or sentiment analysis.

---

## 2. Waterfall Position

| Order | Hub | Gate Requirement |
|-------|-----|------------------|
| 0 | Outreach Spine | Mints outreach_id |
| 1 | Company Target | **execution_status = 'ready'** |
| 2 | DOL Filings | (optional) |
| 3 | People Intelligence | (optional) |
| **4** | **Blog Content** | **LAST - context finalization** |

---

## 3. IMO Structure

### Input Stage (I)

| Check | Error Code | Action |
|-------|------------|--------|
| outreach_id provided | BLOG-I-NO-OUTREACH | FAIL |
| outreach_id in spine | BLOG-I-NOT-FOUND | FAIL |
| Domain exists | BLOG-I-NO-DOMAIN | FAIL |
| CT PASS (ready) | BLOG-I-UPSTREAM-FAIL | FAIL |
| Not already processed | BLOG-I-ALREADY-PROCESSED | SKIP |

### Middle Stage (M)

| Check | Error Code | Action |
|-------|------------|--------|
| Content processing | BLOG-M-CLASSIFY-FAIL | FAIL |
| Event classification | BLOG-M-NO-EVENT | WARN |

### Output Stage (O)

| Outcome | Table | Action |
|---------|-------|--------|
| PASS | outreach.blog | Write blog record |
| FAIL | outreach.blog_errors | Write error record |

---

## 4. Event Types (LOCKED)

| Event Type | BIT Impact | Description |
|------------|------------|-------------|
| FUNDING_EVENT | +15.0 | Funding round, Series A/B/C |
| ACQUISITION | +12.0 | M&A activity |
| LEADERSHIP_CHANGE | +8.0 | CEO/CFO/CTO changes |
| EXPANSION | +7.0 | New office, market entry |
| PRODUCT_LAUNCH | +5.0 | New product/service |
| PARTNERSHIP | +5.0 | Strategic partnership |
| LAYOFF | -3.0 | Workforce reduction |
| NEGATIVE_NEWS | -5.0 | Lawsuit, scandal |
| UNKNOWN | 0.0 | No event detected |

---

## 5. Data Model

### outreach.blog (PASS)

| Column | Type | Description |
|--------|------|-------------|
| blog_id | UUID | Primary key |
| outreach_id | UUID | FK to spine |
| context_summary | TEXT | Article summary |
| source_type | TEXT | manual, newsapi, rss |
| source_url | TEXT | Original URL |
| context_timestamp | TIMESTAMPTZ | Article date |
| created_at | TIMESTAMPTZ | Record created |

### outreach.blog_errors (FAIL)

| Column | Type | Description |
|--------|------|-------------|
| error_id | UUID | Primary key |
| outreach_id | UUID | FK to spine |
| pipeline_stage | VARCHAR | ingest, classify, write |
| failure_code | VARCHAR | BLOG-I-xxx, BLOG-M-xxx, BLOG-O-xxx |
| blocking_reason | TEXT | Human-readable |
| severity | VARCHAR | INFO, WARN, ERROR, FATAL |
| retry_allowed | BOOLEAN | ALWAYS FALSE |
| process_id | UUID | Traceability |
| raw_input | JSONB | Original payload |
| stack_trace | TEXT | Exception trace |
| created_at | TIMESTAMPTZ | Error recorded |

---

## 6. Forbidden Patterns (HARD LAW)

| Category | Forbidden |
|----------|-----------|
| Identity | NO company minting, NO outreach_id minting |
| Enrichment | NO enrichment triggers, NO paid API calls |
| Retry | NO retry logic, NO backoff, NO rescue patterns |
| Upstream | NO upstream data modification |
| Social Metrics | NO followers, engagement, likes, views, sentiment |

---

## 7. CI Guards (15 Total)

| Guard | Check |
|-------|-------|
| 1 | No sovereign_id references |
| 2 | No CL table references |
| 3 | No marketing.* writes |
| 4 | No enrichment triggers |
| 5 | Spine guard assertion present |
| 6 | No retry logic |
| 7 | Doctrine lock comment present |
| 8 | No context view writes |
| 9 | No company minting |
| 10 | No outreach_id minting |
| 11 | No social metrics fields |
| 12 | Scope guard assertion present |
| 13 | Error persistence assertion present |
| 14 | blog_errors references present |
| 15 | Print statement check |

See: `.github/workflows/blog_imo_guard.yml`

---

## 8. Error Handling

### Doctrine

> **Errors are first-class outputs, not hidden logging.**

Every failure MUST be persisted to `outreach.blog_errors`. The `error_persisted` field in BlogIMOResult tracks whether persistence succeeded.

### Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| BLOG-I-NO-OUTREACH | ingest | No outreach_id provided |
| BLOG-I-NOT-FOUND | ingest | outreach_id not in spine |
| BLOG-I-NO-DOMAIN | ingest | No domain in spine |
| BLOG-I-UPSTREAM-FAIL | ingest | CT not PASS (ready) |
| BLOG-I-ALREADY-PROCESSED | ingest | Idempotent skip (not persisted) |
| BLOG-M-CLASSIFY-FAIL | classify | Classification failed |
| BLOG-O-WRITE-FAIL | write | Neon write failed |

---

## 9. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| IMO Gate | DONE | `blog_imo.py` |
| CI Guard | DONE | `blog_imo_guard.yml` |
| Spine Guard | DONE | `ENFORCE_OUTREACH_SPINE_ONLY` |
| Scope Guard | DONE | `DISALLOW_SOCIAL_METRICS` |
| Error Guard | DONE | `ENFORCE_ERROR_PERSISTENCE` |
| Neon Tables | DONE | outreach.blog, outreach.blog_errors |
| Checklist | DONE | All items checked |
| Production Verification | DONE | PRODUCTION_VERIFICATION.md |
| Error Verification | DONE | ERROR_HANDLING_VERIFICATION.md |

---

## 10. Verification Tests

### Replay Test

- Run Blog IMO twice on 10 records
- Assert: Same row count, zero duplicates, zero new errors

### Forced Failure Test

- Inject outreach_id with CT != ready
- Assert: Error persisted to blog_errors with correct stage/code

---

## 11. ADR References

| ADR | Decision |
|-----|----------|
| ADR-BLOG-001 | Signal-only hub, no authority |
| ADR-BLOG-002 | Error discipline enforcement |
| ADR-BLOG-003 | Scope lock (company-level only) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial PRD (PLANNED) |
| 2.1 | 2025-12-17 | Hardened: Correlation ID, Signal Idempotency |
| 3.0 | 2026-01-08 | **PRODUCTION LOCKED**: Spine-First Architecture, IMO Gate, Error Discipline, Scope Lock |

---

**Document Version:** 3.0
**Last Updated:** 2026-01-08
**Owner:** Blog Content Sub-Hub
**Status:** PRODUCTION LOCKED
**Doctrine:** Spine-First Architecture v1.1
