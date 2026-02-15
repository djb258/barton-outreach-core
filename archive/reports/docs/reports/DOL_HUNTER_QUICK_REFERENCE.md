# DOL Hunter - Outreach Matching Quick Reference

**Last Updated**: 2026-02-03

---

## TL;DR

- **3,216** companies discovered by Hunter.io with domains and EINs
- **53** domain matches with existing outreach records (1.65%)
- **3,163** new companies not in outreach database (98.35%)
- **0** EIN overlaps (Hunter results are entirely new companies)

---

## Key Tables

| Table | Schema | Records | Key Columns |
|-------|--------|---------|-------------|
| `ein_urls` | dol | 3,216 | ein, domain, company_name |
| `outreach` | outreach | 42,192 | outreach_id, domain |
| `dol` | outreach | 16,860 | outreach_id, ein |
| `company_target` | outreach | N/A | outreach_id (NO domain) |

**Important**: Domain is in `outreach.outreach`, NOT `outreach.company_target`

---

## Matching Strategy

### Domain Match (Current)
```sql
-- Find existing outreach records with matching domains
SELECT COUNT(*) FROM dol.ein_urls eu
INNER JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment';
-- Result: 53 matches
```

### EIN Match (Future)
```sql
-- Check for EIN overlaps
SELECT COUNT(*) FROM dol.ein_urls eu
INNER JOIN outreach.dol od ON eu.ein = od.ein
WHERE eu.discovery_method = 'hunter_dol_enrichment';
-- Result: 0 matches (all Hunter EINs are new)
```

---

## Column Reference

### dol.ein_urls (Hunter Source)
```
ein              varchar   - Employer ID (e.g., 852067737)
company_name     text      - Company name from DOL filing
city             text      - Company city
state            varchar   - State code
domain           text      - Hunter-discovered domain
url              text      - Full URL
discovered_at    timestamp - Discovery timestamp
discovery_method text      - 'hunter_dol_enrichment'
normalized_domain text     - Normalized domain
```

### outreach.outreach (Company Registry)
```
outreach_id  uuid      - Primary key
sovereign_id uuid      - FK to CL authority
domain       varchar   - Company domain (MATCHING KEY)
created_at   timestamp - Record creation
updated_at   timestamp - Last update
```

### outreach.dol (DOL Hub)
```
dol_id           uuid    - Primary key
outreach_id      uuid    - FK to outreach.outreach
ein              text    - Employer ID (ENRICHMENT TARGET)
filing_present   boolean - Has Form 5500
funding_type     text    - Plan funding type
broker_or_advisor text   - Broker name
carrier          text    - Insurance carrier
created_at       timestamp
updated_at       timestamp
```

---

## Execution Files

| File | Purpose |
|------|---------|
| `scripts/analyze_dol_outreach_matching.py` | Analysis script (Python) |
| `scripts/enrich_outreach_with_hunter_eins.sql` | Phase 1 enrichment (SQL) |
| `docs/reports/DOL_HUNTER_OUTREACH_MATCHING_ANALYSIS_2026-02-03.md` | Full analysis report |
| `docs/reports/DOL_HUNTER_MATCHING_SUMMARY_2026-02-03.md` | Executive summary |

---

## Quick Commands

### Run Analysis
```bash
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
doppler run -- python scripts/analyze_dol_outreach_matching.py
```

### Execute Phase 1 Enrichment
```bash
# Option 1: Via psql (if available)
doppler run -- psql "$DATABASE_URL" -f scripts/enrich_outreach_with_hunter_eins.sql

# Option 2: Via Python
doppler run -- python -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
with open('scripts/enrich_outreach_with_hunter_eins.sql') as f:
    cursor.execute(f.read())
conn.commit()
"
```

### Quick Stats Query
```sql
-- Hunter results summary
SELECT
    COUNT(*) as total_hunter,
    COUNT(DISTINCT domain) as unique_domains,
    COUNT(DISTINCT ein) as unique_eins
FROM dol.ein_urls
WHERE discovery_method = 'hunter_dol_enrichment';

-- Outreach coverage
SELECT
    COUNT(*) as total_outreach,
    COUNT(domain) as with_domain
FROM outreach.outreach;

-- Direct matches
SELECT COUNT(*) as domain_matches
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment';
```

---

## Sample Data

### Hunter Results
```
EIN: 852067737 | FAITH ACADEMY CHARTER SCHOOL, INC. | arts-cs.org
EIN: 852073359 | JST STRATEGIES LLC | gpstrategies.com
EIN: 852104502 | DOYLE, SCHULTZ & BHATIA PLLC | doyle.com.au
```

### Domain Matches
```
EIN: 852073359 | gpstrategies.com | outreach_id: 4245ec22-681e-48c2-b1cb-3a70f2b2e296
EIN: 852588652 | hidglobal.com    | outreach_id: 30f43651-de77-436f-a422-bc65eac5229e
EIN: 852658471 | drakenc.com      | outreach_id: 8015bddb-856e-480d-bb1d-17c38bc0f5de
```

### New Companies (Sample)
```
EIN: 874099467 | ACACIA CENTER FOR JUSTICE | acaciajustice.org | WASHINGTON, DC
EIN: 922479716 | ACCOUNTABLE FOR HEALTH INC | accountableforhealth.org | WASHINGTON, DC
EIN: 861352278 | ACG ANALYTICS, LLC | acg-analytics.com | WASHINGTON, DC
```

---

## Action Items

### Phase 1: Enrich 53 Matches (READY)
- File: `scripts/enrich_outreach_with_hunter_eins.sql`
- Impact: Link EINs to existing outreach records
- Risk: LOW (domain-validated matches)
- Time: ~5 minutes

### Phase 2: New Company Intake (PENDING)
- Count: 3,163 companies
- Next: Define intake criteria (state priority, domain quality)
- Risk: MEDIUM (new company validation required)
- Time: Variable (depends on intake scope)

### Phase 3: Automation (FUTURE)
- Build Hunter -> Outreach sync pipeline
- Monitor new Hunter results weekly
- Track conversion metrics

---

## Troubleshooting

### "No matches found"
- Check `discovery_method = 'hunter_dol_enrichment'` filter
- Verify Hunter import completed successfully
- Run: `SELECT COUNT(*) FROM dol.ein_urls WHERE discovery_method = 'hunter_dol_enrichment';`

### "Column ct.domain does not exist"
- Domain is in `outreach.outreach`, not `outreach.company_target`
- Use: `outreach.outreach.domain` for matching

### "EIN format mismatch"
- Both tables use 9-digit numeric EINs (no dashes)
- No format conversion needed
- Direct comparison: `eu.ein = od.ein`

---

## Contact

- Analysis: Database Specialist Agent
- Date: 2026-02-03
- Database: Neon PostgreSQL (Marketing DB)
- Environment: barton-outreach-core

---
