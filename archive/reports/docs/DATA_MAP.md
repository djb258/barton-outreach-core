# Data Map — Where Everything Lives

> **Purpose**: Complete inventory of all data in the system. Use this to find where any piece of data lives, how tables connect, and what's been provided but not yet promoted.
>
> **Companion to**: [OSAM.md](OSAM.md) (query routing for production data)
>
> **Last verified**: 2026-02-09

---

## Quick Lookup — "I Need..."

| I need... | Go to | Join via | Notes |
|-----------|-------|----------|-------|
| Company LinkedIn URL | `cl.company_identity.linkedin_company_url` | outreach_id | 46.6% filled (44,236/95,004 eligible) |
| Company LinkedIn (broader) | `company.company_master.linkedin_url` | domain bridge | 99.4% filled but only 46% bridgeable |
| Person LinkedIn URL | `people.people_master.linkedin_url` | person_unique_id → company_slot | 80.9% filled (147,764/182,946) |
| Person LinkedIn (Clay CSVs) | `intake.people_raw_intake.linkedin_url` | company_name only | 99.9% filled (119,950) — NOT promoted |
| Person LinkedIn (Hunter) | `enrichment.hunter_contact.linkedin_url` | outreach_id or domain | 60.8% filled (354,647/583,433) |
| Company name | `cl.company_identity.company_name` | outreach_id | 100% filled |
| Domain | `outreach.outreach.domain` | outreach_id | 100% filled (bare domain, no http) |
| Domain status (alive/dead) | `outreach.sitemap_discovery` | outreach_id | 95,004 scanned |
| Email pattern | `outreach.company_target.email_method` | outreach_id | 86.5% filled |
| Contact email | `people.people_master.email` | company_slot → outreach_id | — |
| Phone number | `people.people_master.work_phone_e164` | company_slot → outreach_id | — |
| About/Press/Blog URLs | `company.company_source_urls` | company_unique_id (Barton ID) | 114,736 URLs, 40,381 companies |
| DOL filing data | `outreach.dol` | outreach_id | 73.8% (70,150/95,004) |
| Form 5500 details | `dol.form_5500` / `dol.form_5500_sf` | EIN | 11.1M rows across 27 tables |
| Hunter company data | `enrichment.hunter_company` | outreach_id (65.8%) or domain | 88,405 rows |
| Hunter contact data | `enrichment.hunter_contact` | outreach_id (57.6%) or domain | 583,433 rows |
| CLS scores | `outreach.bit_scores` | outreach_id | 13,226 scored |
| Appointments already had | `sales.appointments_already_had` | appointment_uid | 771 records |
| Fractional CFO partners | `partners.fractional_cfo_master` | fractional_cfo_id | 833 records |
| Appointment tracking | `outreach.appointments` | appointment_id | 704 records |
| Clay person imports | `intake.people_raw_intake` | company_name (no outreach_id!) | 120,045 rows |
| Scraped leadership names | `intake.people_staging` | company_unique_id (Barton ID) | 139,861 rows |

---

## Production Tables (The Spine)

All production data flows through `outreach_id`.

```
cl.company_identity (102,922 total / 95,004 eligible + 6,499 excluded + 1,419 new lanes)
        │ outreach_id
        ▼
outreach.outreach (95,837) ──── THE SPINE (95,004 cold + 833 fractional CFO)
        │ outreach_id
        ├──→ outreach.company_target    95,837   Company firmographics, email pattern
        ├──→ outreach.dol               70,150   DOL/EIN, funding type, renewal month
        ├──→ outreach.blog              95,004   Blog/content signals
        ├──→ outreach.bit_scores        13,226   CLS scores
        ├──→ outreach.sitemap_discovery 95,004   Domain alive/dead, sitemap URL
        ├──→ outreach.appointments         704   Appointment tracking
        ├──→ people.company_slot       285,012   3 slots per company (CEO/CFO/HR)
        │         │ person_unique_id
        │         ▼
        │    people.people_master      182,946   Contact details, email, LinkedIn, phone
        │
        ├──→ enrichment.hunter_company  58,153   Hunter company data (65.8% have outreach_id)
        └──→ enrichment.hunter_contact 336,071   Hunter contacts (57.6% have outreach_id)

THREE MESSAGING LANES:
  Lane 1: Cold Outreach     → outreach.company_target (95,837) via CLS scoring
  Lane 2: Appointments      → sales.appointments_already_had (771) — reactivation
  Lane 3: Fractional CFO    → partners.fractional_cfo_master (833) — partner outreach
```

---

## Enrichment Tables

### enrichment.hunter_company — 88,405 rows

| Column | Fill | Notes |
|--------|------|-------|
| domain | 100% (88,405) | Bare domain, unique per row |
| organization | 100% | Company name from Hunter |
| outreach_id | 65.8% (58,153) | Direct spine join |
| email_pattern | varies | Email format template |
| industry | varies | Hunter's industry classification |
| headcount | varies | Employee count range |
| company_unique_id | varies | Barton ID where mapped |

**Does NOT have**: company LinkedIn URL column

### enrichment.hunter_contact — 583,433 rows

| Column | Fill | Notes |
|--------|------|-------|
| domain | 100% (583,433) | Company domain |
| email | 100% | Contact email address |
| outreach_id | 57.6% (336,071) | Direct spine join |
| linkedin_url | 60.8% (354,647) | **Person** LinkedIn (`/in/` URLs) |
| first_name, last_name | 100% | Contact name |
| job_title | varies | Job title |
| phone_number | varies | Phone number |
| confidence_score | varies | Hunter confidence 0-100 |
| unique domains | 83,410 | Distinct companies |

---

## Company Schema

### company.company_master — 74,641 rows

**ID system**: Barton ID (`04.04.01.XX.XXXXX.XXX`) — NOT UUID. No FK to outreach_id.

| Column | Fill | Notes |
|--------|------|-------|
| company_unique_id | 100% | Barton ID (PK) |
| company_name | 100% | Company legal name |
| website_url | 100% | Full URL with `http://` prefix |
| linkedin_url | 99.4% (74,170) | **Company** LinkedIn URL |
| industry | varies | Industry classification |

**Bridge to outreach**: Domain normalization only (~46% match rate)
```sql
LOWER(REPLACE(o.domain, 'www.', '')) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
```

### company.company_source_urls — 114,736 rows

| source_type | URLs | Companies |
|------------|------|-----------|
| about_page | 29,483 | 29,483 |
| contact_page | 27,662 | 27,662 |
| careers_page | 17,659 | 17,659 |
| press_page | 16,603 | 16,603 |
| leadership_page | 12,829 | 12,829 |
| team_page | 9,287 | 9,287 |
| blog_page | 1,164 | 1,164 |
| investor_page | 49 | 49 |

**Total**: 114,736 URLs across 40,381 unique companies

**Join**: `company_unique_id` (Barton ID) → requires domain bridge from outreach

---

## Intake Tables (User-Provided Data)

### intake.people_raw_intake — 120,045 rows

**Source**: Clay.com CSV exports (10 state-level files)
**Content**: CEO, CFO, HR contacts with person details

| Backfill File | Rows |
|---------------|------|
| NC-CEO | 17,806 |
| PA-CEO | 11,766 |
| MD-HR | 11,362 |
| OH-CEO | 10,736 |
| OH-HR | 10,521 |
| VA-CEO | 8,886 |
| MD-CEO | 7,590 |
| NC-HR | 7,537 |
| KY-HR | 5,488 |
| KY-CEO | 5,470 |

**Slot breakdown**: CEO (64,830) | HR (37,010) | CFO (18,205)

| Key Field | Filled | Status |
|-----------|--------|--------|
| company_name | 120,045 (100%) | Available |
| first_name / last_name / full_name | 120,045 (100%) | Available |
| title | 120,045 (100%) | Available |
| slot_type | 120,045 (100%) | CEO/CFO/HR |
| **linkedin_url** | **119,950 (99.9%)** | **Person LinkedIn — NOT PROMOTED** |
| city / state | 120,045 (100%) | Available |
| bio / skills / education | varies | Available |
| company_unique_id | **0 (0%)** | **EMPTY — never mapped** |
| outreach_id | **N/A** | **Column doesn't exist** |
| email | **0 (0%)** | **EMPTY** |

**All 40 columns**: id, first_name, last_name, full_name, email, work_phone, personal_phone, title, seniority, department, company_name, company_unique_id, linkedin_url, twitter_url, facebook_url, bio, skills, education, certifications, city, state, state_abbrev, country, source_system, source_record_id, import_batch_id, validated, validation_notes, validated_at, validated_by, enrichment_attempt, chronic_bad, last_enriched_at, enriched_by, b2_file_path, b2_uploaded_at, created_at, updated_at, slot_type, backfill_source

### intake.company_raw_intake — 563 rows

| Key Field | Filled | Status |
|-----------|--------|--------|
| company | 563 (100%) | Company name |
| website | 563 (100%) | Company website URL |
| **company_linkedin_url** | **451 (80.1%)** | **Company LinkedIn** |
| industry | 563 (100%) | Available |
| num_employees | varies | Available |
| company_phone | varies | Available |
| outreach_id | **N/A** | **Column doesn't exist** |

**All 35 columns**: id, company, company_name_for_emails, num_employees, industry, website, company_linkedin_url, facebook_url, twitter_url, company_street, company_city, company_state, company_country, company_postal_code, company_address, company_phone, sic_codes, founded_year, created_at, state_abbrev, import_batch_id, validated, validation_notes, validated_at, validated_by, enrichment_attempt, chronic_bad, last_enriched_at, enriched_by, b2_file_path, b2_uploaded_at, apollo_id, last_hash, garage_bay, validation_reasons

### intake.people_staging — 139,861 rows

**Source**: Blog sub-hub scraping of leadership/about pages

| Key Field | Filled | Status |
|-----------|--------|--------|
| company_unique_id | 139,861 (100%) | Barton ID — maps to company_master |
| raw_name / first_name / last_name | 139,861 (100%) | Scraped names |
| raw_title / normalized_title | 139,861 (100%) | Job titles |
| mapped_slot_type | 139,861 (100%) | CEO/CFO/HR/UNKNOWN |
| linkedin_url | **0 (0%)** | **Not extracted during scraping** |
| email | **0 (0%)** | **Not extracted** |

### intake.people_candidate — 0 rows (UNUSED)

Empty candidate review queue. Direct promotion workflow used instead.

### intake.people_raw_wv — 10 rows

West Virginia test data. 7 have LinkedIn URLs.

---

## ID Systems — How Tables Connect

### outreach_id (UUID) — THE UNIVERSAL JOIN KEY

```
Tables that HAVE outreach_id:
  ✅ outreach.outreach (PK)
  ✅ outreach.company_target, .dol, .blog, .bit_scores, .sitemap_discovery
  ✅ cl.company_identity
  ✅ people.company_slot
  ✅ enrichment.hunter_company (58,153 / 88,405 = 65.8%)
  ✅ enrichment.hunter_contact (336,071 / 583,433 = 57.6%)

Tables that DO NOT have outreach_id:
  ❌ intake.people_raw_intake (must match via company_name)
  ❌ intake.company_raw_intake (must match via website/domain)
  ❌ intake.people_staging (has company_unique_id instead)
  ❌ company.company_master (has company_unique_id instead)
  ❌ company.company_source_urls (has company_unique_id instead)
```

### company_unique_id (Barton ID: 04.04.01.XX.XXXXX.XXX)

```
Tables that use company_unique_id:
  company.company_master (PK)
  company.company_source_urls
  intake.people_staging
  cl.company_identity
  people.company_slot
  people.people_master
  enrichment.hunter_company
  enrichment.hunter_contact
  outreach.company_target

NOT filled in:
  intake.people_raw_intake (column exists, always NULL)
```

### domain (bare domain: example.com)

```
Tables with bare domain:
  outreach.outreach.domain
  outreach.sitemap_discovery.domain
  enrichment.hunter_company.domain
  enrichment.hunter_contact.domain

Tables with full URL (needs normalization):
  company.company_master.website_url (http://www.example.com)
  intake.company_raw_intake.website
```

### company_name (text — fuzzy match only)

```
Tables with company_name:
  cl.company_identity.company_name
  intake.people_raw_intake.company_name
  enrichment.hunter_company.organization
  dol.ein_urls.company_name
  outreach.appointments.company_name

⚠ No FK — variations exist ("ABC Corp" vs "ABC Corporation" vs "Abc Corp.")
```

### person_unique_id (Barton ID: 04.04.02.YY.NNNNNN.NNN)

```
  people.people_master.unique_id (PK)
  people.company_slot.person_unique_id (FK when is_filled = TRUE)
```

---

## LinkedIn Coverage Summary

### Company LinkedIn

| Source | Records | Filled | Join to Outreach |
|--------|---------|--------|------------------|
| cl.company_identity | 102,922 (95,004 eligible) | 44,236 (46.6%) | outreach_id (direct) |
| company.company_master | 74,641 | 74,170 (99.4%) | domain bridge (~46%) |
| intake.company_raw_intake | 563 | 451 (80.1%) | no join key |

### Person LinkedIn

| Source | Records | Filled | Join to Outreach |
|--------|---------|--------|------------------|
| people.people_master | 182,946 | 147,764 (80.9%) | company_slot → outreach_id |
| intake.people_raw_intake | 120,045 | 119,950 (99.9%) | company_name only (fuzzy) |
| enrichment.hunter_contact | 583,433 | 354,647 (60.8%) | outreach_id (57.6%) or domain |
| intake.people_staging | 139,861 | 0 (0%) | company_unique_id |

---

## Domain Health (from sitemap_discovery)

| Status | Count | % |
|--------|-------|---|
| Alive (has sitemap) | 32,121 | 33.8% |
| Alive (no sitemap) | 53,400 | 56.2% |
| Dead | 9,483 | 10.0% |
| **Total** | **95,004** | **100% (original eligible)** |

---

## DOL Filing Data (dol.* schema)

27 data-bearing tables, 11.1M total rows across 2023-2025.

See [OSAM.md](OSAM.md) for complete DOL table inventory and query examples.

---

## Data Gaps

| Gap | Impact | Root Cause |
|-----|--------|------------|
| intake.people_raw_intake has no outreach_id | 119,950 person LinkedIn URLs sitting unused | company_unique_id never populated, no outreach_id column |
| company.company_master covers only 46% of outreach | 74,170 company LinkedIn URLs partially inaccessible | 50,761 outreach domains not in company_master |
| CL company LinkedIn at 46.6% | 50,768 companies missing company LinkedIn | Internal backfill exhausted (+2,044 from company_master) |
| intake.people_staging has 0 LinkedIn | 139,861 scraped records with no social links | LinkedIn not extracted during leadership page scraping |
| enrichment.hunter_contact missing 42.4% outreach_id | 247,362 Hunter contacts can't join to spine directly | Must use domain bridge instead |
| Clay schema not created | Migration written, never executed | `intake.company_raw_from_clay` and `intake.people_raw_from_clay` don't exist |

---

## CSV File Locations

| Directory | Files | Size | Content |
|-----------|-------|------|---------|
| data/5500/ | 73 | 1.6 GB | DOL Form 5500 source filings (2023-2025) |
| exports/ | 37 | 26 MB | Company exports, slot contacts, verification results |
| exports/ein_status/ | 5 | 8.8 MB | EIN matching results |
| exports/slot_contacts/ | 3 | 1.7 MB | Hunter-sourced CEO/CFO/HR contacts |
| exports/pattern_issues/ | 3 | 5.9 MB | Email pattern analysis |
| exports/samples/ | 33 | 162 KB | Schema documentation samples |
| docs/schema_csv/ | 14 | 50 KB | Table schema documentation |
| docs/audit/ | 13 | 620 KB | CTB audit reports |

### Key Export Files

| File | Rows | Purpose |
|------|------|---------|
| exports/missing_linkedin_for_clay.csv | 46,212 | People missing LinkedIn — queued for Clay |
| exports/clay_truly_stuck.csv | 2,365 | Companies with no email pattern + no Hunter data |
| exports/clay_has_linkedin_no_email.csv | 567 | Companies with LinkedIn but no email |
| exports/ceo_slot_contacts.csv | ~varies | CEO contacts from Hunter |
| exports/cfo_slot_contacts.csv | ~varies | CFO contacts from Hunter |
| exports/hr_slot_contacts.csv | ~varies | HR contacts from Hunter |

---

*Last updated: 2026-02-09*
