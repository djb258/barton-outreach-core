# OUTREACH ID DIAGNOSTIC MODEL
## Pressure Test Results & Redesign

**Generated:** 2026-01-20
**Total outreach_ids:** 74,173

---

## 1. CHECKBOX MODEL CRITIQUE

The current binary `complete/incomplete` model has critical flaws:

| Problem | Impact |
|---------|--------|
| **No Explanation** | "incomplete" tells you nothing about WHY |
| **Conflates States** | "not started" vs "failed" vs "waiting" all = incomplete |
| **Blocks Valid Outreach** | Missing DOL shouldn't block if we have email+people |
| **Error Orphans** | 74k+ errors sit in tables with no visibility in main view |

### Current Reality (discovered via diagnostic view):
```
By CT Status:
  PASS: 58,554 (79%)
  WAITING: 15,619 (21%)

By People Status:
  WAITING: 74,173 (100%)  ← THE REAL BOTTLENECK

Top Bottlenecks:
  [PEOPLE] PROCESSING: 58,554
  [COMPANY_TARGET] PROCESSING: 15,619

Total Outreach Ready: 0
```

**The checkbox model hid the fact that ZERO outreach_ids have verified people contacts.**

---

## 2. STATUS-BASED DIAGNOSTIC MODEL

### ENUM States (per sub-hub)

| Status | Meaning | Action |
|--------|---------|--------|
| `PASS` | Data present, valid, ready for use | None - proceed |
| `NOT_REQUIRED` | This sub-hub not needed for this outreach_id | None - skip |
| `WAITING` | Queued, processing, or awaiting upstream | Monitor |
| `BLOCKED` | Failed with known error code (diagnosable) | Fix error |
| `MISSING` | No data and no error (needs investigation) | Investigate |

### Status Logic per Sub-Hub

**Company Target:**
```sql
CASE 
    WHEN imo_completed_at IS NOT NULL THEN 'PASS'
    WHEN execution_status = 'failed' THEN 'BLOCKED'
    WHEN execution_status IN ('pending', 'ready') THEN 'WAITING'
    ELSE 'MISSING'
END
```

**DOL:**
```sql
CASE 
    WHEN dol.ein IS NOT NULL THEN 'PASS'
    WHEN error.failure_code = 'NO_MATCH' THEN 'NOT_REQUIRED'  -- No 5500 = not a plan sponsor
    WHEN error.failure_code IS NOT NULL THEN 'BLOCKED'
    ELSE 'WAITING'
END
```

**People:**
```sql
CASE 
    WHEN COUNT(verified_email) > 0 THEN 'PASS'
    WHEN COUNT(people) > 0 THEN 'WAITING'  -- Has people but unverified
    WHEN error.failure_code IS NOT NULL THEN 'BLOCKED'
    ELSE 'WAITING'
END
```

**Blog:**
```sql
CASE 
    WHEN COUNT(blog_signals) > 0 THEN 'PASS'
    WHEN error.failure_code IS NOT NULL THEN 'BLOCKED'
    ELSE 'NOT_REQUIRED'  -- Blog is enrichment only
END
```

---

## 3. OUTREACH ELIGIBILITY RULES

### Hard Requirements (must be PASS to send email)

| Sub-Hub | Requirement | Reason |
|---------|-------------|--------|
| Company Target | PASS | Need validated email method |
| People | PASS | Need at least 1 verified contact |

### Soft Requirements (enhance but don't block)

| Sub-Hub | Acceptable States | Reason |
|---------|-------------------|--------|
| DOL | PASS, NOT_REQUIRED, WAITING | Retirement plan data enriches messaging |
| Blog | PASS, NOT_REQUIRED | Signal data enriches timing |

### Eligibility Formula
```sql
outreach_ready = (ct_status = 'PASS' AND people_status = 'PASS')
```

---

## 4. DIAGNOSTIC VIEW: `v_outreach_diagnostic`

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `outreach_id` | UUID | Primary identifier |
| `domain` | TEXT | Company domain |
| `sovereign_id` | UUID | Identity link |
| `ct_status` | ENUM | Company Target status |
| `dol_status` | ENUM | DOL status |
| `people_status` | ENUM | People status |
| `blog_status` | ENUM | Blog status |
| `ct_error` | TEXT | Error code if BLOCKED |
| `dol_error` | TEXT | Error code if BLOCKED |
| `people_error` | TEXT | Error code if BLOCKED |
| `blog_error` | TEXT | Error code if BLOCKED |
| `people_count` | INT | Total people records |
| `people_verified` | INT | Verified email count |
| `blog_signals` | INT | Blog signal count |
| `outreach_ready` | BOOLEAN | Ready to send email |
| `bottleneck_hub` | TEXT | First blocking sub-hub |
| `bottleneck_reason` | TEXT | Why it's blocked |
| `created_at` | TIMESTAMP | Record creation |
| `last_activity_at` | TIMESTAMP | Last update |

### Key Queries

**Find all blocked outreach_ids with their reason:**
```sql
SELECT outreach_id, domain, bottleneck_hub, bottleneck_reason
FROM outreach.v_outreach_diagnostic
WHERE outreach_ready = false
ORDER BY bottleneck_hub, bottleneck_reason;
```

**Count by bottleneck:**
```sql
SELECT bottleneck_hub, bottleneck_reason, COUNT(*)
FROM outreach.v_outreach_diagnostic
WHERE bottleneck_hub IS NOT NULL
GROUP BY 1, 2
ORDER BY COUNT(*) DESC;
```

**Find outreach_ids ready except for one sub-hub:**
```sql
SELECT * FROM outreach.v_outreach_diagnostic
WHERE ct_status = 'PASS'
  AND people_status = 'WAITING'  -- Only waiting on people
ORDER BY domain;
```

---

## 5. CURRENT STATE (After People Promotion)

**Promotion Date:** 2026-01-20
**Promoted:** 546 people via `cl.company_identity_bridge`

```
Total: 74,173 outreach_ids

┌─────────────────────────────────────────────────────────┐
│ COMPANY TARGET                                          │
│   PASS: 58,554 (79%)                                    │
│   WAITING: 15,619 (21%)                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ DOL                                                     │
│   PASS: 6,512 (9%)                                      │
│   NOT_REQUIRED: 55,636 (75%) ← NO_MATCH = no 5500 filing│
│   BLOCKED: 11,914 (16%) ← NO_STATE errors               │
│   WAITING: 111                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PEOPLE (AFTER BRIDGE PROMOTION)                         │
│   PASS: 395 (0.5%) ← 546 people → 395 unique companies  │
│   WAITING: 73,778 (99.5%)                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ BLOG                                                    │
│   PASS: 74,173 (100%)                                   │
└─────────────────────────────────────────────────────────┘

OUTREACH READY: 362 (0.5%)  ← Up from 0!
```

### Bottleneck Distribution (Not Ready)
| Bottleneck | Reason | Count |
|------------|--------|-------|
| PEOPLE | PROCESSING | 58,192 |
| COMPANY_TARGET | PROCESSING | 15,619 |

---

## 6. CRITICAL FINDING: ID FORMAT MISMATCH (RESOLVED)

**The People pipeline was blocked due to incompatible ID formats.**

```
people_master.company_unique_id:  04.04.01.99.00624.624  (DOL-style)
company_target.company_unique_id: 9e969c59-1cf7-4a1e-8495-a275627621e7  (UUID)

Initial Overlap: 0 companies could be matched
```

### Solution: cl.company_identity_bridge

The bridge table `cl.company_identity_bridge` (71,820 records) maps:
- `source_company_id` (DOL-style) → `company_sov_id` (UUID)

**Bridge Linkage Results:**
| Metric | Count |
|--------|-------|
| People in people_master | 30,808 |
| People linkable via bridge | 29,904 |
| With verified email | 546 |
| Unique companies with verified contacts | 395 |

### Promotion Script

Created `scripts/promote_people_via_bridge.py` to:
1. Join people_master → bridge → outreach via sovereign_id
2. Insert verified contacts into outreach.people
3. Result: **546 people promoted → 362 outreach_ids now ready**

### Data Inventory (Updated)
| Table | Records | ID Format |
|-------|---------|-----------|
| intake.people_raw_intake | 120,045 | DOL-style |
| people.people_master | 30,808 | DOL-style |
| cl.company_identity_bridge | 71,820 | DOL-style → UUID |
| outreach.people | **546** | UUID (via bridge) |
| outreach.company_target | 74,173 | UUID |

### Root Cause (for reference)
The company identity systems used different ID schemes:
- **DOL/People domain**: `04.04.01.XX.XXXXX.XXX` format
- **Outreach domain**: UUID format

The bridge table `cl.company_identity_bridge` resolved this mismatch.

---

## 7. ACTION ITEMS

### ✅ COMPLETED: ID Format Mismatch Fixed
- [x] Discovered `cl.company_identity_bridge` exists with 71,820 mappings
- [x] Created `scripts/promote_people_via_bridge.py`
- [x] Promoted 546 people with verified emails
- [x] **362 outreach_ids now ready for email** (up from 0)

### NEXT PRIORITY: Scale People Promotion
To increase ready outreach_ids, need more verified people:
1. **Verify remaining 29,358 people** (in bridge but unverified email)
2. **Run email verification pipeline** on people_master emails
3. **Re-run promotion script** after verification

### Secondary (Error Cleanup)
| Error Code | Count | Fix |
|------------|-------|-----|
| NO_STATE | 11,900 | GooglePlaces lookup (~$178) |
| CT-M-NO-MX | 6,848 | Periodic MX re-check |
| NO_MATCH | 55,636 | Mark NOT_REQUIRED (no 5500 filing) |

---

## 7. MODEL GUARANTEES

✅ **Every outreach_id is visible** - No hidden failures  
✅ **One row = one diagnosis** - No join required for status  
✅ **Scales to 77k+** - View uses indexed columns  
✅ **No new tables** - Just a view over existing data  
✅ **No external tools** - Pure SQL logic  
✅ **Preserves identity** - sovereign_id linkage maintained  
✅ **Explains bottlenecks** - bottleneck_hub + bottleneck_reason  

---

## View Definition

The view `outreach.v_outreach_diagnostic` has been created. See [create_diagnostic_view.py](../scripts/create_diagnostic_view.py) for the full SQL.
