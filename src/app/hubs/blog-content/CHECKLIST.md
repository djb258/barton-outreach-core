# Blog Content — IMO Compliance Checklist

**Hub**: Blog Content (04.04.05)
**Doctrine**: Spine-First Architecture v1.1
**IMO Gate**: `blog_imo.py`
**Last Updated**: 2026-01-08

---

## 0. Spine-First Gate (DOCTRINE LOCK)

### Spine Enforcement

- [x] `ENFORCE_OUTREACH_SPINE_ONLY = True` assertion present
- [x] All operations key off `outreach_id` from spine
- [x] NEVER references `sovereign_id` directly
- [x] NEVER mints `outreach_id` (spine does that)
- [x] Reads from `outreach.outreach` spine table only

### Upstream Gate

- [x] Checks Company Target `execution_status = 'ready'` before processing
- [x] Halts if upstream hub not PASS
- [x] Does NOT proceed on upstream FAIL

---

## 1. IMO Input Stage (I)

### Input Validation

- [x] Validates `outreach_id` provided
- [x] Validates `outreach_id` exists in spine
- [x] Validates domain exists in spine record
- [x] Check idempotency: if already PASS/FAIL, exit immediately

---

## 2. IMO Middle Stage (M)

### M1 — Content Processing

- [x] Accepts optional content payload for processing
- [x] No-content case handled gracefully (PASS with no signal)

### M2 — Event Classification

- [x] 8 event types with locked BIT impacts:
  - FUNDING_EVENT (+15.0)
  - ACQUISITION (+12.0)
  - LEADERSHIP_CHANGE (+8.0)
  - EXPANSION (+7.0)
  - PRODUCT_LAUNCH (+5.0)
  - PARTNERSHIP (+5.0)
  - LAYOFF (-3.0)
  - NEGATIVE_NEWS (-5.0)

### M3 — Keyword Classification

- [x] Hard rules applied FIRST (deterministic)
- [x] Confidence based on keyword match density
- [x] UNKNOWN event type for no matches

---

## 3. IMO Output Stage (O)

### PASS Output

- [x] Write to `outreach.blog`
- [x] `blog_id` generated (UUID)
- [x] `outreach_id` foreign key set
- [x] `context_summary` populated (if content provided)
- [x] `source_type` populated
- [x] `source_url` populated
- [x] `context_timestamp` set
- [x] `created_at` timestamp set

### FAIL Output

- [x] Write to `outreach.blog_errors`
- [x] `failure_code` populated (BLOG-XXX)
- [x] `blocking_reason` populated
- [x] `pipeline_stage` = 'blog_imo'
- [x] `retry_allowed = FALSE`
- [x] Execution STOPS (terminal)

---

## 4. Write Hygiene (HARD LAW)

### Allowed Writes

- [x] `outreach.blog` (PASS)
- [x] `outreach.blog_errors` (FAIL)

### Forbidden Writes

- [x] **NO** writes to `marketing.*` tables
- [x] **NO** writes to `cl.*` tables
- [x] **NO** writes to `intake.*` tables
- [x] **NO** writes upstream
- [x] **NO** writes to `outreach.outreach` (spine)

---

## 5. Tool Registry Compliance

### Tier 0 (FREE) — ALLOWED

- [x] TOOL-LOCAL-001: KeywordClassifier (local regex)

### Forbidden Tools

- [x] No paid tools in this hub
- [x] No enrichment triggers
- [x] No API calls that incur cost

---

## 6. Forbidden Patterns (DOCTRINE LOCK)

The following are **permanently forbidden** in Blog Content:

- [x] **NO** company minting
- [x] **NO** outreach_id minting
- [x] **NO** enrichment triggers
- [x] **NO** paid API calls
- [x] **NO** retry/backoff logic
- [x] **NO** hold queues
- [x] **NO** rescue patterns
- [x] **NO** upstream data modification

---

## 7. Error Codes (v1.0)

| Code | Stage | Description |
|------|-------|-------------|
| `BLOG-I-NO-OUTREACH` | I | No outreach_id provided |
| `BLOG-I-NOT-FOUND` | I | outreach_id not found in spine |
| `BLOG-I-NO-DOMAIN` | I | No domain in spine record |
| `BLOG-I-UPSTREAM-FAIL` | I | Company Target not PASS |
| `BLOG-I-ALREADY-PROCESSED` | I | Idempotent skip (already done) |
| `BLOG-M-NO-CONTENT` | M | No content to process |
| `BLOG-M-CLASSIFY-FAIL` | M | Event classification failed |
| `BLOG-M-NO-EVENT` | M | No actionable event detected |
| `BLOG-O-WRITE-FAIL` | O | Failed to write to Neon |

---

## 8. Logging (MANDATORY)

Every IMO run MUST log:

- [x] `outreach_id`
- [x] IMO stage transitions (I → M → O)
- [x] Tool IDs used
- [x] PASS or FAIL outcome
- [x] Duration in milliseconds
- [x] Error details (if FAIL)
- [x] Event type (if PASS)

---

## 9. CI Guard Compliance

The following guards run on every PR touching `hubs/blog-content/**`:

- [x] Guard 1: No `sovereign_id` references
- [x] Guard 2: No CL table references
- [x] Guard 3: No `marketing.*` writes
- [x] Guard 4: No enrichment triggers
- [x] Guard 5: Spine guard assertion present
- [x] Guard 6: No retry logic
- [x] Guard 7: Doctrine lock comment present
- [x] Guard 8: No context view writes
- [x] Guard 9: No company minting
- [x] Guard 10: No outreach_id minting
- [x] Guard 11: No social metrics fields (SCOPE LOCK)
- [x] Guard 12: Scope guard assertion present
- [x] Guard 13: Error persistence assertion present
- [x] Guard 14: blog_errors references present
- [x] Guard 15: Print statement check (no bypass)

See: `.github/workflows/blog_imo_guard.yml`

---

## 10. Terminal Failure Doctrine

> **FAIL is FOREVER. There are no retries.**

- [x] Failed records go to `outreach.blog_errors`
- [x] `retry_allowed = FALSE` on all errors
- [x] Failed records do NOT proceed downstream
- [x] Resolution requires human intervention + new `outreach_id`

---

## 11. Signal-Only Compliance

### What Blog Content DOES

- [x] Provides timing signals from news/content
- [x] Classifies events with BIT impacts
- [x] Writes context to `outreach.blog`

### What Blog Content DOES NOT DO

- [x] Does NOT mint companies
- [x] Does NOT trigger enrichment
- [x] Does NOT trigger paid API calls
- [x] Does NOT modify upstream data
- [x] Does NOT mint outreach_id

---

## 12. Waterfall Position

Blog Content is the **4th (LAST)** sub-hub in the waterfall:

| Order | Hub | Required State |
|-------|-----|----------------|
| 1 | Company Target | `execution_status = 'ready'` |
| 2 | DOL Filings | (optional) |
| 3 | People Intelligence | (optional) |
| **4** | **Blog Content** | **LAST — context finalization** |

---

## 13. Scope Lock Compliance (DOCTRINE LOCK)

> **The Blog Sub-Hub records *where* a company publishes, not *how large* the audience is.**

### Scope Guard

- [x] `DISALLOW_SOCIAL_METRICS = True` assertion present
- [x] Forbidden fields list defined in code

### Company-Level Only

- [x] Operates exclusively at company level
- [x] Social platforms = presence verification only
- [x] NO audience metrics (followers, subscribers)
- [x] NO engagement metrics (likes, views, comments)
- [x] NO sentiment analysis
- [x] NO people-level social data

---

## 14. Error Handling Discipline (DOCTRINE LOCK)

> **Errors are first-class outputs, not hidden logging.**

### Error Persistence Guard

- [x] `ENFORCE_ERROR_PERSISTENCE = True` assertion present
- [x] `BlogPipelineError` exception class exists
- [x] Central error handler `_write_error()` exists

### Error Table Compliance

- [x] `outreach.blog_errors` table exists in Neon
- [x] All required columns present:
  - [x] `error_id` (UUID, PK)
  - [x] `outreach_id` (UUID, FK)
  - [x] `pipeline_stage` (VARCHAR)
  - [x] `failure_code` (VARCHAR)
  - [x] `blocking_reason` (TEXT)
  - [x] `severity` (VARCHAR)
  - [x] `retry_allowed` (BOOLEAN, FALSE)
  - [x] `process_id` (UUID)
  - [x] `raw_input` (JSONB)
  - [x] `stack_trace` (TEXT)
  - [x] `created_at` (TIMESTAMPTZ)

### Error Output

- [x] Every failure persists to `outreach.blog_errors`
- [x] `error_persisted` field in result tracks persistence
- [x] `process_id` captured for traceability
- [x] No silent failures

### Forced Failure Test

- [x] `run_forced_failure_test()` function exists
- [x] Test passes with all assertions green

---

## Prime Directive (v1.1)

```
+===============================================================================+
|                     BLOG CONTENT IMO — PRIME DIRECTIVE                        |
|                                                                               |
|   1. outreach_id is the ONLY identity                                         |
|   2. Upstream gate MUST be checked (CT ready)                                 |
|   3. Signal-only: NO enrichment, NO minting, NO spend                         |
|   4. FAIL is terminal (no retries)                                            |
|   5. All writes to outreach.blog or outreach.blog_errors only                 |
|   6. Company-level only: NO social metrics                                    |
|   7. Errors are first-class outputs: NO silent failures                       |
|                                                                               |
+===============================================================================+
```

---

## Compliance Rule

**All boxes MUST be checked for this hub to ship.**

---

**Last Updated**: 2026-01-08
**Hub**: Blog Content (04.04.05)
**Doctrine Version**: Spine-First Architecture v1.1
**Status**: PRODUCTION LOCKED
