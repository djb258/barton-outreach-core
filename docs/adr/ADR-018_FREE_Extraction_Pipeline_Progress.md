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
| PA | 16,571 | 3,451 | 6,966 | 14,416 | 16,433 | COMPLETE |
| OH | 14,843 | 9,269 | 6,215 | 0 | 18,546 | COMPLETE |
| VA | 11,983 | 500 | 280 | ~15,900 | 5,052 | IN PROGRESS |
| NC | 10,794 | 0 | 0 | 12,259 | 4,816 | PENDING |
| MD | 8,344 | 4,468 | 2,939 | 0 | 11,963 | COMPLETE |
| KY | 3,864 | 1,521 | 996 | 0 | 3,516 | COMPLETE |
| OK | 3,743 | 1,706 | 1,210 | 0 | 1,340 | COMPLETE |
| WV | 1,340 | 456 | 262 | 0 | 660 | COMPLETE |
| DE | 3,159 | 472 | 841 | 0 | 1,322 | COMPLETE |

### Summary Totals (Updated 2026-01-28)

| Metric | Value |
|--------|-------|
| **Total Companies** | 74,641 |
| **Total People in people_master** | 74,005 |
| **Free Extracted** | 47,706 |
| **People in Staging (pending)** | 77,399 |
| **People in Staging (promoted)** | 47,706 |
| **Paid Enrichment Queue** | ~19,930 |

### Slot Coverage (Updated 2026-02-07 VERIFIED)

| Slot Type | Filled | Total | Coverage |
|-----------|--------|-------|----------|
| CEO | 62,289 | 95,004 | 65.6% |
| CFO | 57,327 | 95,004 | 60.3% |
| HR | 58,141 | 95,004 | 61.2% |

**Note:** Previous counts used incorrect denominator (49,924). Correct denominator is 95,004 sovereign eligible companies.

### Extraction Status Distribution

| Status | Count | Percentage |
|--------|-------|------------|
| pending | ~28,000 | ~29% |
| queued_for_paid | ~19,930 | ~20% |
| complete | ~49,000 | ~50% |

---

## Technical Implementation

### Barton ID Sequence Fix (2026-01-28)

The `_generate_person_doctrine_id()` function was using `zfill(5)` which truncates at 100,000 IDs. Fixed to support constraint's 1-6 digit allowance:

```python
# BEFORE (broken at 100k):
seg5 = str(sequence).zfill(5)  # "100000" = 6 digits, format mismatch

# AFTER (supports up to 999,999):
seg5 = str(sequence)  # No zfill - constraint allows 1-6 digits

# Constraint: ^04\.04\.02\.[0-9]{2}\.[0-9]{1,6}\.[0-9]{3}$
```

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
- IDs up to 999,999 (previous limit was 99,999)

### Prevents

- Batch processing efficiency (acceptable tradeoff)
- Silent failures from SSL timeouts

---

## Execution Order

| Priority | State | Companies | URLs | Status |
|----------|-------|-----------|------|--------|
| 1 | PA | 16,571 | 3,451 | ✅ COMPLETE |
| 2 | OH | 14,843 | 9,269 | ✅ COMPLETE |
| 3 | MD | 8,344 | 4,468 | ✅ COMPLETE |
| 4 | VA | 11,983 | 500 | 🔄 IN PROGRESS |
| 5 | NC | 10,794 | 0 | ⏳ PENDING |
| 6 | WV | 1,340 | 456 | ✅ COMPLETE |
| 7 | DE | 3,159 | 472 | ✅ COMPLETE |
| 8 | KY | 3,864 | 1,521 | ✅ COMPLETE |
| 9 | OK | 3,743 | 1,706 | ✅ COMPLETE |

---

## Paid Enrichment Queue

After FREE extraction completes, URLs that yield no results are queued for paid enrichment via Clay.

**Current Queue:** ~19,930 URLs

| Source | Count | Notes |
|--------|-------|-------|
| PA | ~6,966 | 67% queue rate |
| OH | ~6,215 | 67% queue rate |
| MD | ~2,939 | 66% queue rate |
| VA | ~280 | In progress |
| KY | ~996 | 65% queue rate |
| OK | ~1,210 | 71% queue rate |
| WV | ~262 | 69% queue rate |
| DE | ~841 | 71% queue rate |

---

## Staging Backlog

**77,399 people pending in staging** - extracted but awaiting promotion to `people_master`.

These are blocked by:
1. ~~Barton ID sequence limit at 100,000~~ **FIXED**
2. Need to re-run assign_staged phase

To clear backlog:
```bash
doppler run -- python scripts/state_extraction_pipeline.py --state ALL --batch-size 1
# This runs only the assign_staged phase for all pending staged people
```

---

## Next Actions

1. ✅ Document current progress (this ADR)
2. ✅ Fix Barton ID sequence constraint
3. 🔜 Re-run assign_staged to clear 77k staging backlog
4. 🔜 Continue VA extraction
5. 🔜 Run NC extraction

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-28 | Initial ADR created |
| 2026-01-28 | Corrected target states from small-state pilot to actual targets |
| 2026-01-28 | Added connection stability fix for SSL timeouts |
| 2026-01-28 | Fixed Barton ID sequence limit (was 99,999, now 999,999) |
| 2026-01-28 | Parallel extraction completed WV, KY, DE, OK |
| 2026-02-07 | Updated slot coverage with correct denominators (95,004 vs 49,924) |
