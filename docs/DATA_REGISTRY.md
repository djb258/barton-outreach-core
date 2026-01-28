# Data Registry — Sub-Hub Reference

**Generated**: 2026-01-23  
**Purpose**: Single source of truth for where data lives across all sub-hubs.  
**Usage**: Reference this document FIRST before searching for data.

---

## Quick Lookup by Data Type

### URLs / Domains
| Location | Column | Records | Coverage | Notes |
|----------|--------|---------|----------|-------|
| `outreach.outreach` | `domain` | **46,494** | **100%** | Master domain list (commercial only) |
| `outreach.blog` | `source_url` | ~46K | **0%** ❌ | NEEDS POPULATION |
| `company.company_master` | `website_url` | 74,641 | ~98% | Full URLs |
| `company.company_source_urls` | `source_url` | 97,124 | 100% | Crawl source URLs |
| `cl.company_domains` | `domain` | 51,910 | 100% | CL domain registry |
| `dol.ein_urls` | `url` | **119,409** | 100% | ✅ **DOL EIN→URL discovery** |

### EIN / DOL Data
| Location | Column | Records | Coverage | Notes |
|----------|--------|---------|----------|-------|
| `dol.ein_urls` | `ein` | **119,409** | 100% | ✅ **EIN→URL mapping (FREE)** |
| `outreach.dol` | `ein` | 13,829 | 100% | Outreach-linked EINs |
| `company.company_master` | `ein` | 74,641 | ~27% | Matched EINs |
| `dol.form_5500` | `sponsor_dfe_ein` | 230,482 | 100% | Large filers |
| `dol.form_5500_sf` | `sf_spons_ein` | 760,652 | 100% | Small filers |

### Email / Contact Data
| Location | Column | Records | Coverage | Notes |
|----------|--------|---------|----------|-------|
| `people.people_master` | `email` | 26,299 | 95.9% verified | Primary contacts |
| `outreach.people` | `email` | 426 | 100% | Active outreach contacts |
| `people.company_slot` | `person_unique_id` | 153,444 | 17.5% filled | Slot assignments |
| `intake.people_raw_intake` | `email` | 120,045 | Staging | Raw intake data |

### Company Identifiers
| Location | Column | Records | Notes |
|----------|--------|---------|-------|
| `outreach.outreach` | `outreach_id` | **46,494** | **MASTER LIST** (commercial companies) |
| `outreach.outreach_excluded` | `outreach_id` | 1,210 | Non-commercial exclusions |
| `cl.company_identity` | `sovereign_company_id` | 51,910 | Authority registry |
| `company.company_master` | `company_unique_id` | 74,641 | Company master ID |

---

## Schema Quick Reference

| Schema | Purpose | Key Tables | Master ID | Total Rows |
|--------|---------|------------|-----------|------------|
| `outreach` | Outreach spine & coordination | outreach, blog, dol, company_target | `outreach_id` | 344K |
| `company` | Company master & enrichment | company_master, company_source_urls | `company_unique_id` | 218K |
| `cl` | Company Lifecycle pipeline | company_identity, company_domains | `sovereign_company_id` | 477K |
| `dol` | DOL Form 5500 filings | form_5500, form_5500_sf | `ein` | 1.3M |
| `people` | People/contacts master | people_master, company_slot | `person_unique_id` | 259K |
| `intake` | Data intake staging | company_raw_intake, people_raw_intake | varies | 183K |
| `shq` | Error/signal tracking | error_log, audit_log | `error_id` | 116K |
| `sales` | **LANE A** - Appointment Reactivation | appointment_history | `appointment_uid` | 0 |
| `partners` | **LANE B** - Fractional CFO Partners | fractional_cfo_master, partner_appointments | `fractional_cfo_id` | 0 |
| `bit` | BIT scoring/intent | movement_events, proof_lines, reactivation_intent, partner_intent | varies | ~17K |

---

## ISOLATED LANES (NOT Connected to Outreach Spine)

⚠️ **WARNING: The following schemas are INTENTIONALLY ISOLATED from the outreach pipeline.**

| Lane | Schema | Purpose | Connection |
|------|--------|---------|------------|
| **A** | `sales.*` | Appointment Reactivation | ISOLATED - optional FK to company/people |
| **B** | `partners.*` | Fractional CFO Partners | ISOLATED - no connection to outreach |

**DO NOT**:
- Create cross-lane FKs (sales.* → partners.*)
- Join sales/partners to outreach.outreach
- Combine scoring from different lanes

**See**: `docs/architecture/DUAL_LANE_ARCHITECTURE.md` for full ERD and isolation rules.

---

## ID Relationships (How Tables Connect)

```
outreach.outreach.outreach_id (MASTER - 46,494 commercial)
    │
    ├── outreach.blog.outreach_id
    ├── outreach.dol.outreach_id  
    ├── outreach.company_target.outreach_id
    ├── outreach.bit_scores.outreach_id
    │
    └── company.company_master.outreach_id
            │
            ├── company.company_source_urls.company_unique_id
            ├── people.company_slot.company_unique_id
            └── clay.company_raw.company_unique_id

cl.company_identity.sovereign_company_id (AUTHORITY - 51,910)
    │
    ├── cl.company_domains.sovereign_company_id
    └── cl.company_identity_bridge → company.company_master

dol.form_5500.sponsor_dfe_ein (DOL SOURCE - 1M+)
    │
    └── outreach.dol.ein (matched via EIN)
```

---

## Sub-Hub Details

### 1. OUTREACH Schema (~300K rows)

**Purpose**: Operational spine for all outreach activities.

**Cleanup (2026-01-27)**: Removed 5,067 duplicate domains + 1,210 non-commercial entities.

| Table | Rows | Key Columns | Enrichment Status |
|-------|------|-------------|-------------------|
| `outreach` | **46,494** | outreach_id, sovereign_id, domain | ✅ domain 100% (commercial only) |
| `outreach_excluded` | 1,210 | outreach_id, domain, exclusion_reason | Non-commercial (gov/edu/church/etc) |
| `blog` | ~46K | outreach_id, source_url, context_summary | ❌ source_url 0% |
| `company_target` | **45,816** | outreach_id, outreach_status, email_method | ✅ email_method 91% |
| `dol` | 13,829 | outreach_id, ein, filing_present | ✅ ein 100% |
| `people` | 426 | person_id, email, email_verified | ✅ email 100% |
| `bit_scores` | 17,227 | outreach_id, score, score_tier | Active scoring |
| `company_hub_status` | 68,908 | company_unique_id, hub_id, status | Hub tracking |
| `dol_errors` | 37,319 | outreach_id, failure_code | Error queue |

**Key Finding**: `outreach.blog.source_url` is 0% populated - needs enrichment!

---

### 2. COMPANY Schema (217,667 rows)

**Purpose**: Company master data and enrichment storage.

| Table | Rows | Key Columns | Enrichment Status |
|-------|------|-------------|-------------------|
| `company_master` | 74,641 | company_unique_id, website_url, ein | ✅ website 98%, ⚠️ ein 27% |
| `company_source_urls` | 97,124 | company_unique_id, source_url | ✅ 100% - use this for URLs! |
| `url_discovery_failures` | 42,348 | company_unique_id, failure_reason | Failed URL lookups |

**company_master enrichment coverage:**
| Column | Populated | Coverage |
|--------|-----------|----------|
| website_url | 73,005 | 97.8% |
| linkedin_url | 63,295 | 84.8% |
| ein | 20,378 | 27.3% |
| phone | 12,451 | 16.7% |
| employees_count | 0 | 0% |
| industry | 0 | 0% |

---

### 3. CL (Company Lifecycle) Schema (476,795 rows)

**Purpose**: Authority registry for company identity resolution.

| Table | Rows | Key Columns | Notes |
|-------|------|-------------|-------|
| `company_identity` | 51,910 | sovereign_company_id, canonical_name | Authority master |
| `company_domains` | 51,910 | sovereign_company_id, domain, is_verified | Domain registry |
| `company_identity_bridge` | 71,820 | sovereign_company_id, company_unique_id | Links to company_master |
| `company_candidate` | 62,162 | candidate_id, domain, source | Pending resolution |
| `domain_hierarchy` | 4,705 | parent_domain, child_domain | Domain relationships |

---

### 4. DOL Schema (1,448,460 rows)

**Purpose**: DOL Form 5500 filing data + URL discovery.

| Table | Rows | Key Columns | Notes |
|-------|------|-------------|-------|
| `form_5500` | 230,482 | sponsor_dfe_ein, sponsor_dfe_name | Large filers (100+ participants) |
| `form_5500_sf` | 760,652 | sf_spons_ein, sf_sponsor_name | Small filers (<100 participants) |
| `schedule_a` | 337,476 | ein, provider_ein | Insurance/service providers |
| `ein_urls` | **119,409** | ein, domain, url | ✅ **EIN→URL discovery (FREE)** |

**DOL form_5500 has NO URL field** - only: ein, name, address, city, state, zip, phone

**ein_urls** - Discovered URLs for DOL EINs (domain construction):
| Column | Description |
|--------|-------------|
| `ein` | Primary key - EIN from DOL filing |
| `company_name` | Sponsor name from DOL |
| `city`, `state` | Location |
| `domain` | Discovered domain (e.g., company.com) |
| `url` | Full URL with https:// |
| `discovery_method` | How found: domain_construction, clay, manual |

**Coverage by state:**
| State | Records |
|-------|---------|
| OH | 27,568 |
| PA | 26,208 |
| VA | 16,599 |
| NC | 15,863 |
| MD | 14,876 |
| KY | 8,099 |
| OK | 4,991 |
| DE | 2,993 |
| WV | 2,212 |

---

### 5. PEOPLE Schema (259,436 rows)

**Purpose**: People/contact master data and slot assignments.

| Table | Rows | Key Columns | Notes |
|-------|------|-------------|-------|
| `people_master` | 26,299 | person_unique_id, email, linkedin_url | Primary contacts |
| `company_slot` | 153,444 | company_unique_id, slot_type, person_unique_id | 17.5% filled |
| `people_errors` | 1,053 | error details | Processing errors |

**people_master enrichment coverage:**
| Column | Populated | Coverage |
|--------|-----------|----------|
| email | 25,224 | 95.9% |
| linkedin_url | 21,891 | 83.2% |
| phone | 2,854 | 10.9% |

---

### 6. INTAKE Schema (182,766 rows)

**Purpose**: Staging area for incoming data before processing.

| Table | Rows | Key Columns | Notes |
|-------|------|-------------|-------|
| `company_raw_intake` | 563 | Pending company records | Awaiting processing |
| `company_raw_wv` | 62,146 | WV-specific intake | State-specific |
| `people_raw_intake` | 120,045 | Raw people/contact data | Awaiting processing |
| `quarantine` | 2 | Bad data quarantine | Validation failures |

---

### 7. SHQ (Signal Hub Queue) Schema (116,366 rows)

**Purpose**: Error tracking and signal processing.

| Table | Rows | Notes |
|-------|------|-------|
| `error_log` | 116,361 | ~95K unresolved errors |
| `audit_log` | 5 | System audit trail |

---

## Enrichment History by Sub-Hub

### Outreach Sub-Hub
| Enrichment | Date | Source | Records | Status |
|------------|------|--------|---------|--------|
| Domain extraction | Prior | CL pipeline | 51,148 | ✅ Complete |
| Blog source_url | - | - | 0 | ❌ PENDING |
| DOL EIN matching | 2026-01 | DOL files | 13,829 | ✅ Complete |

### Company Sub-Hub  
| Enrichment | Date | Source | Records | Status |
|------------|------|--------|---------|--------|
| Website URLs | Prior | Multiple | 73,005 | ✅ 98% |
| LinkedIn URLs | Prior | Clay? | 63,295 | ✅ 85% |
| EIN matching | 2026-01 | DOL | 20,378 | ⚠️ 27% |
| Source URLs | Prior | Crawl | 97,124 | ✅ 100% |

### People Sub-Hub
| Enrichment | Date | Source | Records | Status |
|------------|------|--------|---------|--------|
| Email verification | Prior | Multiple | 25,224 | ✅ 96% |
| LinkedIn URLs | Prior | Clay? | 21,891 | ✅ 83% |
| Slot assignment | Ongoing | Pipeline | 26,831 | ⚠️ 17.5% |

---

## CSV Files in Workspace (scripts/)

| File | Records | Content |
|------|---------|---------|
| `domain_results_VALID.csv` | 119,469 | DOL domain discovery (validated URLs) |
| `domain_results_ALL.csv` | 128,453 | All DOL domain construction results |
| `outreach_blog_url_matches.csv` | 3,020 | Matched outreach→DOL URLs |
| `clay_test_output.csv` | 1,000 | Clay enrichment test results |
| `domain_results_{STATE}.csv` | varies | Per-state DOL results (NC,PA,OH,VA,MD,KY,OK,WV,DE) |

---

## Common Queries

### Find URL for an outreach_id
```sql
-- Option 1: From outreach.outreach domain
SELECT 'https://' || domain FROM outreach.outreach WHERE outreach_id = ?;

-- Option 2: From company_master via join
SELECT cm.website_url 
FROM outreach.outreach o
JOIN company.company_master cm ON cm.outreach_id = o.outreach_id
WHERE o.outreach_id = ?;

-- Option 3: From company_source_urls
SELECT csu.source_url
FROM outreach.outreach o
JOIN company.company_master cm ON cm.outreach_id = o.outreach_id
JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
WHERE o.outreach_id = ?;
```

### Find EIN for an outreach_id
```sql
SELECT d.ein 
FROM outreach.dol d 
WHERE d.outreach_id = ?;
```

### Check enrichment coverage for a table
```sql
SELECT 
    COUNT(*) as total,
    COUNT(column_name) as populated,
    ROUND(100.0 * COUNT(column_name) / COUNT(*), 1) as pct
FROM schema.table;
```

---

## Rules for Adding Enrichment

1. **Check this document FIRST** - data may already exist
2. **Use existing IDs** - outreach_id links everything
3. **Update existing tables** - don't create new ones unless necessary
4. **Document the enrichment** - add to the history table above
5. **Coverage targets**: 
   - URLs: aim for 95%+
   - EINs: aim for 50%+
   - Emails: aim for 95%+

---

## Gaps Requiring Attention

| Gap | Table | Column | Current | Target |
|-----|-------|--------|---------|--------|
| Blog URLs | outreach.blog | source_url | 0% | 95% |
| EIN coverage | company.company_master | ein | 27% | 50% |
| Slot fill rate | people.company_slot | person_unique_id | 17.5% | 50% |
| Employee count | company.company_master | employees_count | 0% | 80% |
| Industry | company.company_master | industry | 0% | 80% |

---

*Last updated: 2026-01-28*

---

## Changelog

### 2026-01-27: Outreach Table Cleanup
- **Removed 5,067 duplicate domains** (kept oldest per normalized domain)
- **Moved 1,210 non-commercial entities** to `outreach.outreach_excluded`:
  - TLD exclusions: .gov (14), .edu (84), .org (675), .church (17), .coop (40)
  - Keyword exclusions: government, school, church, insurance, etc. (380)
- **Net result**: 46,494 clean, commercial companies in outreach spine
- Sub-hub cascades: dol (18,575), company_target (45,816)
