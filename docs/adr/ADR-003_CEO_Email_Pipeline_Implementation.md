# ADR-003: CEO Email Pipeline Implementation (Phases 5-8)

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.0 |
| **CC Layer** | CC-04 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-003 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-14 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL (Company Lifecycle) |
| **Hub Name** | People Intelligence Sub-Hub |
| **Hub ID** | 04.04.02 |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | N/A |
| CC-02 (Hub) | [x] | People Intelligence Hub owns pipeline |
| CC-03 (Context) | [x] | Multi-slot support (CEO, CFO, HR, CTO, CMO, COO) |
| CC-04 (Process) | [x] | Email generation, verification, promotion to Neon |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I - Ingress | [x] |
| M - Middle | [x] |
| O - Egress | [x] |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Variable (implementation) |
| **Mutability** | [ ] Immutable |

---

## Context

**Problem Statement:**

The People Intelligence Hub required a production-ready pipeline to:
1. Generate emails for executives using domain patterns (first.last@domain)
2. Assign executives to company slots (CEO, CFO, HR, etc.)
3. Verify emails through external APIs (optional)
4. Promote verified contacts to Neon database

**Requirements:**
- Multi-slot support for different executive types
- Graceful handling of database transaction errors
- Support for international names with accented characters
- Skip-verification mode for bulk processing
- Audit trail via CSV exports

---

## Decision

### Implementation File

**Location:** `hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py`

### Supported Slot Types

| Slot | Seniority | Title Keywords |
|------|-----------|----------------|
| CEO | 100 | Chief Executive, President, CEO, Managing Director |
| CFO | 95 | Chief Financial, CFO, VP Finance, Finance Director |
| CTO | 90 | Chief Technology, CTO, VP Engineering |
| CMO | 85 | Chief Marketing, CMO, VP Marketing |
| COO | 85 | Chief Operating, COO, VP Operations |
| HR | 80 | Chief Human Resources, CHRO, HR Director, VP HR |

### Email Generation Pattern

Default pattern: `{first}.{last}@{domain}`

**ASCII Normalization:** Names with accented characters are normalized:
- `é` → `e`, `í` → `i`, `ñ` → `n`, etc.
- Uses Python's `unicodedata.normalize('NFKD')` + ASCII encoding

### Email Verification Providers

| Provider | API | Mode | Status |
|----------|-----|------|--------|
| MillionVerifier | REST | Single | Supported |
| EmailVerify.io | REST | Single | Default |
| Prospeo | REST | Single | Supported |

### Command Line Interface

```bash
# Full verification
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path>

# Skip verification (bulk processing)
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --skip-verification

# Specify slot type
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --slot-type HR
```

### Transaction Handling

**Problem:** PostgreSQL transaction abort killed entire batch when single record failed email format constraint.

**Solution:** Added `conn.rollback()` in exception handler to continue processing remaining records:

```python
except Exception as e:
    candidate.error = str(e)
    stats.errors.append(f"Neon write error for {candidate.full_name}: {e}")
    conn.rollback()  # Critical: allows next record to proceed
```

### Output Files

| File | Description |
|------|-------------|
| `{slot}_pipeline_audit_{timestamp}.csv` | Full audit trail |
| `{slot}_valid_emails_{timestamp}.csv` | Emails promoted to Neon |
| `{slot}_flagged_emails_{timestamp}.csv` | Verification failures |

---

## Consequences

### Positive

1. **Multi-slot flexibility** - Single pipeline handles all executive types
2. **Bulk processing** - Skip-verification mode enables high-volume ingestion
3. **Resilient transactions** - Individual failures don't abort entire batch
4. **International support** - ASCII normalization handles accented names
5. **Audit trail** - CSV exports provide full transparency

### Negative

1. **Skip-verification risk** - Unverified emails may have higher bounce rate
2. **Pattern assumption** - Assumes first.last pattern (may not match all companies)

### Mitigations

1. Email verification can be run post-hoc via separate verification pass
2. Company email patterns can be pre-populated in company_master.email_pattern

---

## Production Usage (2026-01-14)

### States Processed

| State | HR | CFO | CEO | Total to Neon |
|-------|-----|-----|-----|---------------|
| Delaware | 116 | ~700 | ~800 | ~1,600 |
| Kentucky | ~2,000 | ~1,900 | ~2,000 | ~5,900 |
| Maryland | ~3,700 | ~3,700 | ~3,700 | ~11,100 |
| North Carolina | ~6,000 | ~6,000 | ~6,100 | ~18,100 |
| Ohio | ~7,900 | ~7,900 | ~7,800 | ~23,600 |
| Pennsylvania | ~8,300 | ~8,200 | ~8,300 | ~24,800 |
| Virginia | 7,803 | 2,167 | 8,543 | ~18,500 |
| West Virginia | 672 | 114 | 645 | ~1,430 |

**Total:** ~100,000+ executives promoted to Neon

### New Companies Identified

- 2,423 companies not previously in Neon (exported for Clay pipeline enrichment)

### Skipped Records

- 4,469 people missing domain or name data (queued for enrichment)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-13 | Initial implementation with CEO slot |
| 1.1 | 2026-01-13 | Added multi-slot support, transaction rollback fix |
| 1.2 | 2026-01-14 | Added ASCII normalization for accented characters |
| 1.3 | 2026-01-14 | Production run across 8 states |

---

*Document Version: 1.0*
*Last Updated: 2026-01-14*
*Owner: People Intelligence Hub*
*Doctrine: Bicycle Wheel v1.1 / Barton Doctrine*
