# ADR-018: FREE Extraction Pipeline Progress Report

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.0.0 |
| **CC Layer** | CC-04 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-018 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-28 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-outreach-core |
| **Hub Name** | People Enrichment Hub |
| **Hub ID** | enrichment-hub |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | N/A |
| CC-02 (Hub) | [x] | People Hub, Enrichment Hub |
| CC-03 (Context) | [x] | People staging, extraction context |
| CC-04 (Process) | [x] | State extraction pipeline process |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [x] |
| M — Middle | [x] |
| O — Egress | [x] |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Variable (behavior tuning) |
| **Mutability** | [x] Configuration |

---

## Context

The FREE extraction pipeline extracts leadership contact information (CEO, CFO, HR) from company websites using zero-cost methods (httpx + selectolax + regex). This document tracks extraction progress across target states and records operational decisions.

### Target States (Revised 2026-01-28)

**Previous targets (DEPRECATED):** WV, VT, WY, AK, ND, SD, DE, MT, RI

**Current targets:** PA, OH, VA, NC, MD, KY, OK, WV, DE

---

## Decision

### Extraction Status as of 2026-01-28

| State | Companies | URLs Complete | Paid Queue | Pending | People | Status |
|-------|-----------|---------------|------------|---------|--------|--------|
| PA | 16,571 | 3,451 | 6,966 | 14,416 | 16,433 | IN PROGRESS |
| OH | 14,843 | 3,054 | 6,215 | 12,912 | 18,546 | IN PROGRESS |
| VA | 11,983 | 0 | 0 | 16,404 | 4,234 | PENDING |
| NC | 10,794 | 0 | 0 | 12,259 | 4,816 | PENDING |
| MD | 8,344 | 1,529 | 2,939 | 5,720 | 11,963 | IN PROGRESS |
| KY | 3,864 | 0 | 0 | 3,661 | 1,687 | PENDING |
| OK | 3,743 | 0 | 0 | 3,925 | 128 | PENDING |
| WV | 1,340 | 115 | 262 | 610 | 660 | IN PROGRESS |
| DE | 3,159 | 290 | 710 | 1,604 | 1,173 | IN PROGRESS |

### Summary Totals

| Metric | Value |
|--------|-------|
| **Total Companies** | 74,641 |
| **Total People Extracted** | 59,640 |
| **URLs Processed (Complete)** | 8,439 |
| **URLs in Paid Queue** | 17,174 |
| **URLs Pending** | 71,511 |
| **Total URLs** | 97,124 |

### Extraction Status Distribution

| Status | Count | Percentage |
|--------|-------|------------|
| pending | 71,511 | 73.6% |
| queued_for_paid | 17,092 | 17.6% |
| complete | 8,439 | 8.7% |
| queued_paid (legacy) | 73 | 0.1% |
| failed | 9 | 0.0% |

---

## Technical Implementation

### Connection Stability Fix (2026-01-28)

During Ohio extraction, SSL connection timeouts were encountered after ~2-3 batches. Resolution:

```python
def _refresh_connection(self):
    """Refresh the database connection."""
    try:
        self.conn.close()
    except:
        pass
    self.conn = psycopg2.connect(DATABASE_URL)

# In extraction loop - ping before each write:
try:
    cur.execute("SELECT 1")
except:
    self._refresh_connection()
    cur = self.conn.cursor()

# Commit after each URL (not batched)
self.conn.commit()
```

### Pipeline Command

```bash
# Single state extraction
doppler run -- python scripts/state_extraction_pipeline.py --state {STATE_CODE} --batch-size 500

# Available states: PA, OH, VA, NC, MD, KY, OK, WV, DE
```

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Batch commits (every 50 URLs) | Caused data loss on connection timeout |
| No connection refresh | SSL timeouts after idle periods |
| Smaller batch sizes | Slower processing, same timeout issues |
| Do Nothing | Pipeline fails on long-running extractions |

---

## Consequences

### Enables

- Reliable long-running extractions (hours)
- No data loss on connection failures
- Per-URL transaction safety
- Resumable pipeline (processes only pending URLs)

### Prevents

- Batch processing efficiency (acceptable tradeoff)
- Silent failures from SSL timeouts

---

## Execution Order

| Priority | State | Companies | Est. URLs | Status |
|----------|-------|-----------|-----------|--------|
| 1 | PA | 16,571 | 10,417 | ✅ IN PROGRESS |
| 2 | OH | 14,843 | 9,269 | ✅ IN PROGRESS |
| 3 | MD | 8,344 | 4,468 | ✅ IN PROGRESS |
| 4 | VA | 11,983 | ~7,500 | 🔜 NEXT |
| 5 | NC | 10,794 | ~6,700 | ⏳ PENDING |
| 6 | WV | 1,340 | ~800 | ✅ PARTIAL |
| 7 | DE | 3,159 | ~900 | ✅ PARTIAL |
| 8 | KY | 3,864 | ~2,400 | ⏳ PENDING |
| 9 | OK | 3,743 | ~2,300 | ⏳ PENDING |

---

## Paid Enrichment Queue

After FREE extraction completes, URLs that yield no results are queued for paid enrichment via Clay.

**Current Queue:** 17,174 URLs

| Source | Count | Notes |
|--------|-------|-------|
| PA | ~6,966 | 67% queue rate |
| OH | ~6,215 | 67% queue rate |
| MD | ~2,939 | 66% queue rate |
| WV | ~262 | 69% queue rate |
| DE | ~710 | 71% queue rate |

---

## Next Actions

1. ✅ Document current progress (this ADR)
2. ✅ Push to GitHub
3. 🔜 Run VA extraction
4. 🔜 Run NC extraction
5. 🔜 Complete WV remaining URLs
6. 🔜 Complete DE remaining URLs
7. 🔜 Run KY extraction
8. 🔜 Run OK extraction

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-28 | Initial ADR created |
| 2026-01-28 | Corrected target states from small-state pilot to actual targets |
| 2026-01-28 | Added connection stability fix for SSL timeouts |
