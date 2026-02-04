# Hunter DOL Slot Filling Potential Analysis
**Date**: 2026-02-04
**Analysis Type**: READ-ONLY
**Join Path**: `people.company_slot` → `outreach.outreach` → `enrichment.hunter_contact`

---

## Executive Summary

**We can fill 78,809 slots (49.74%) for 27,568 Hunter DOL companies using existing Hunter contact data.**

### Key Findings

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Hunter DOL Companies** | 54,155 | Source: `outreach.company_target` where `source = 'hunter_dol_intake'` |
| **Companies with Hunter Contacts** | 54,155 (100%) | All have matching contacts in `enrichment.hunter_contact` |
| **Total Hunter Contacts Available** | 305,695 | Contacts across all Hunter DOL domains |
| **Companies with Fillable Slots** | 27,568 (50.9%) | Companies with at least 1 slot matchable to criteria |
| **Total Slots Fillable** | 78,809 of 158,436 (49.74%) | Across CEO, CFO, HR slots |

---

## Slot-by-Slot Breakdown

### 1. CEO Slots

| Metric | Value |
|--------|-------|
| **Companies with Fillable CEO Slots** | 25,426 |
| **Unfilled CEO Slots Matchable** | 25,426 |
| **Unique Hunter Contacts Available** | 83,258 |
| **Total Contact Matches** | 83,258 |

**Matching Criteria:**
- Department: `Executive`, `Management`
- OR Title patterns: `%ceo%`, `%chief executive%`, `%president%`, `%owner%`, `%founder%`

**Coverage**: 46.9% of Hunter DOL companies have a CEO slot that can be filled

---

### 2. CFO Slots

| Metric | Value |
|--------|-------|
| **Companies with Fillable CFO Slots** | 27,310 |
| **Unfilled CFO Slots Matchable** | 27,310 |
| **Unique Hunter Contacts Available** | 100,980 |
| **Total Contact Matches** | 100,980 |

**Matching Criteria:**
- Department: `Finance`, `Executive`, `Management`, `Operations & logistics`
- OR Title patterns: `%cfo%`, `%chief financial%`, `%controller%`, `%finance director%`, `%vp finance%`, `%treasurer%`, `%accounting%`

**Coverage**: 50.4% of Hunter DOL companies have a CFO slot that can be filled

---

### 3. HR Slots (Excluding Recruiters)

| Metric | Value |
|--------|-------|
| **Companies with Fillable HR Slots** | 26,073 |
| **Unfilled HR Slots Matchable** | 26,073 |
| **Unique Hunter Contacts Available** | 90,998 |
| **Total Contact Matches** | 90,998 |

**Matching Criteria:**
- Department: `HR`, `Executive`, `Management`, `Operations & logistics`
- OR Title patterns: `%human resource%`, `%hr director%`, `%hr manager%`, `%benefit%`, `%payroll%`, `%chro%`, `%chief people%`
- **EXCLUDING**: `%recruit%`, `%talent acquisition%`, `%staffing%`

**Coverage**: 48.1% of Hunter DOL companies have an HR slot that can be filled

---

## Department Distribution

Top departments available in Hunter contact data for Hunter DOL companies:

| Rank | Department | Unique Contacts | Companies Covered |
|------|------------|-----------------|-------------------|
| 1 | Management | 40,085 | 16,692 |
| 2 | Executive | 38,743 | 18,762 |
| 3 | Support | 35,771 | 25,377 |
| 4 | Sales | 21,662 | 10,949 |
| 5 | Operations & logistics | 13,753 | 8,542 |
| 6 | Finance | 11,394 | 6,872 |
| 7 | IT / Engineering | 9,561 | 6,158 |
| 8 | Education | 7,637 | 3,959 |
| 9 | Writing & communication | 6,620 | 4,386 |
| 10 | Marketing | 6,505 | 4,477 |
| 11 | HR | 5,376 | 4,118 |
| 12 | Medical & health | 4,972 | 2,507 |
| 13 | Legal | 4,226 | 1,853 |
| 14 | Arts & design | 3,834 | 2,226 |

---

## Key Insights

### 1. High Domain Coverage
- **100% of Hunter DOL companies have matching contacts** in `enrichment.hunter_contact`
- This represents 305,695 total contacts across 54,155 domains
- Average: 5.6 contacts per company

### 2. Balanced Slot Fill Potential
- CEO: 25,426 slots (46.9% coverage)
- CFO: 27,310 slots (50.4% coverage) - **HIGHEST**
- HR: 26,073 slots (48.1% coverage)

CFO slots have the highest fill potential due to broader department matching (Finance, Executive, Management, Operations).

### 3. Nearly Half of All Slots Fillable
- **49.74% of all unfilled Hunter DOL slots** (78,809 / 158,436) can be filled using existing Hunter data
- This represents **50.9% of Hunter DOL companies** (27,568 / 54,155) with at least 1 fillable slot

### 4. Quality Over Quantity
- Average 3.3 matching contacts per fillable CEO slot
- Average 3.7 matching contacts per fillable CFO slot
- Average 3.5 matching contacts per fillable HR slot

This provides multiple candidate options for each slot, enabling quality selection.

---

## Remaining Gap Analysis

### Companies Without Fillable Slots
- **26,587 companies (49.1%)** have no slots fillable using current criteria
- These companies have Hunter contacts, but they don't match CEO/CFO/HR criteria
- Likely reasons:
  - Contacts are in non-executive departments (Sales, Support, IT, etc.)
  - Title patterns don't match executive/leadership roles
  - Missing department/title data

### Unfilled Slots After Hunter Fill
- **79,627 slots (50.26%)** will remain unfilled after using Hunter data
- Breakdown by slot type:
  - CEO: ~28,729 slots (assuming 1 per company × 54,155 - 25,426)
  - CFO: ~26,845 slots
  - HR: ~28,082 slots (excluding recruiters)

---

## Recommended Next Steps

### 1. Immediate Actions
1. **Execute Hunter-based slot filling** for the 78,809 matchable slots
2. **Prioritize CFO slots** (27,310 fillable) - highest coverage
3. **Use department + title matching** as primary criteria
4. **Implement confidence scoring** for multiple candidate matches

### 2. Quality Assurance
1. **Verify email addresses** before slot assignment
2. **Validate titles** against slot type (CEO/CFO/HR)
3. **Check for stale contacts** (last verified date)
4. **Score candidates** when multiple matches exist per slot

### 3. Gap Filling Strategy
For the remaining 79,627 unfilled slots:
1. **Expand title pattern matching** (e.g., VP Finance → CFO)
2. **Cross-department matching** (e.g., Operations → HR)
3. **Use external enrichment** (Apollo, ZoomInfo, etc.)
4. **Pattern-based email generation** where domain + pattern is known

---

## Technical Details

### Database Query Join Path
```sql
FROM people.company_slot cs
JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.source = 'hunter_dol_intake'
  AND cs.is_filled = false
```

### Schema Mapping
- `people.company_slot.slot_id` = Primary key for slots
- `outreach.company_target.source` = `'hunter_dol_intake'`
- `outreach.outreach.domain` = Join key to Hunter contacts
- `enrichment.hunter_contact.id` = Primary key for contacts
- `enrichment.hunter_contact.job_title` = Title matching field
- `enrichment.hunter_contact.department` = Department matching field

### Execution Environment
- **Database**: Neon PostgreSQL (serverless)
- **Analysis Type**: READ-ONLY (no data modifications)
- **Script**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\hunter_dol_slot_analysis.py`

---

## Appendix: Raw Query Results

### Query 1: Domain Overlap
```
metric: Domain Overlap
company_count: 54,155
unique_domains: 54,155
matching_hunter_domains: 54,155
total_contacts_available: 305,695
```

### Query 2: CEO Slot Potential
```
slot_type: CEO Slots
companies_with_fillable_slots: 25,426
unfilled_slots: 25,426
unique_contacts_available: 83,258
total_contact_matches: 83,258
```

### Query 3: CFO Slot Potential
```
slot_type: CFO Slots
companies_with_fillable_slots: 27,310
unfilled_slots: 27,310
unique_contacts_available: 100,980
total_contact_matches: 100,980
```

### Query 4: HR Slot Potential
```
slot_type: HR Slots
companies_with_fillable_slots: 26,073
unfilled_slots: 26,073
unique_contacts_available: 90,998
total_contact_matches: 90,998
```

### Query 5: Overall Summary
```
metric: OVERALL SUMMARY
companies_with_fillable_slots: 27,568
total_slots_fillable: 78,809
ceo_slots_fillable: 25,426
cfo_slots_fillable: 27,310
hr_slots_fillable: 26,073
pct_of_total_unfilled: 49.74%
```

---

**Analysis Completed**: 2026-02-04
**Analyst**: Claude (Database Expert)
**Status**: ✓ COMPLETE (READ-ONLY)
