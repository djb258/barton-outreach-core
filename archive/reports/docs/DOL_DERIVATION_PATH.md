# DOL Derivation Path

> **Last Updated:** 2026-02-06
> **Status:** CANONICAL
> **Validation:** Pressure-tested against production data

---

## The Principle

**DOL completion (EIN matched) enables derivation of Company Target and Blog.**

Once a company has a verified EIN match in DOL filings, we can derive:
1. **Domain** from `dol.ein_urls` (Hunter-enriched EIN→domain mapping)
2. **Email Pattern** via pattern discovery on that domain → Company Target complete
3. **Content URLs** via source URL discovery → Blog content

---

## Derivation Chain

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOL DERIVATION PATH                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DOL Complete (EIN matched, filing_present = TRUE)                          │
│       │                                                                      │
│       │   ┌─────────────────────────────────────────────────────────────┐   │
│       └──►│ dol.ein_urls                                                │   │
│           │ • 58,069 EINs with domains (Hunter-enriched)                │   │
│           │ • 99.993% domain agreement with outreach.outreach           │   │
│           └─────────────────────────────────────────────────────────────┘   │
│               │                                                              │
│               ▼                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                         DOMAIN DERIVED                                 │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│               │                                                              │
│       ┌───────┴───────┐                                                      │
│       ▼               ▼                                                      │
│   ┌─────────────┐ ┌─────────────────────────────────────────────────────┐   │
│   │ COMPANY     │ │ BLOG                                                │   │
│   │ TARGET      │ │                                                     │   │
│   ├─────────────┤ ├─────────────────────────────────────────────────────┤   │
│   │ Domain      │ │ Domain                                              │   │
│   │    ↓        │ │    ↓                                                │   │
│   │ Email       │ │ company.company_source_urls                         │   │
│   │ Pattern     │ │    ↓                                                │   │
│   │ Discovery   │ │ about_page, press_page URLs                         │   │
│   │    ↓        │ │    ↓                                                │   │
│   │ email_method│ │ Content scraping                                    │   │
│   │ populated   │ │    ↓                                                │   │
│   │    ↓        │ │ context_summary, signals                            │   │
│   │ CT COMPLETE │ │    ↓                                                │   │
│   │             │ │ BLOG COMPLETE                                       │   │
│   └─────────────┘ └─────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Validation Metrics (2026-02-06)

| Metric | Value | Notes |
|--------|-------|-------|
| DOL-complete records | 70,150 | EIN matched + filing found |
| With domain in ein_urls | 53,530 | 82.4% rescue potential |
| Domain conflicts | 4 | 0.007% - rebranding cases |
| Blog URL coverage | 6,937 | 13% have about/press pages |

---

## Join Paths

### EIN → Domain

```sql
SELECT
    d.outreach_id,
    d.ein,
    eu.domain AS dol_domain,
    o.domain AS outreach_domain
FROM outreach.dol d
JOIN dol.ein_urls eu ON d.ein = eu.ein
JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
WHERE d.filing_present = TRUE
  AND eu.domain IS NOT NULL;
```

### Domain → Company Target

```sql
-- Companies where DOL can rescue CT
SELECT
    d.outreach_id,
    eu.domain,
    ct.email_method,
    ct.execution_status
FROM outreach.dol d
JOIN dol.ein_urls eu ON d.ein = eu.ein
JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
WHERE d.filing_present = TRUE
  AND eu.domain IS NOT NULL
  AND (ct.email_method IS NULL OR ct.execution_status != 'ready');
```

### Domain → Blog Source URLs

```sql
SELECT
    o.outreach_id,
    o.domain,
    csu.source_type,
    csu.source_url
FROM outreach.outreach o
JOIN company.company_master cm ON LOWER(o.domain) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
JOIN company.company_source_urls csu ON cm.company_unique_id = csu.company_unique_id
WHERE csu.source_type IN ('about_page', 'press_page');
```

---

## Operational Use

### When to Use DOL Derivation

1. **Company Target incomplete** → Check if DOL has EIN → Derive domain → Run pattern discovery
2. **Blog needs content** → Check if DOL has EIN → Derive domain → Discover source URLs
3. **New company ingestion** → If EIN known first, DOL path may be faster than domain-first

### Workflow

```
Company needs enrichment
    │
    ├── Has EIN? ──► YES ──► DOL path (derive domain, cascade to CT/Blog)
    │
    └── No EIN? ──► Domain path (pattern discovery first, then EIN lookup)
```

---

## Domain Conflicts (4 cases)

These are rebranding/consolidation cases - DOL has newer domain:

| Outreach Domain | DOL Domain | EIN |
|-----------------|------------|-----|
| sweeperland.com | bortekindustries.com | 231703931 |
| a3consultingllc.com | a3.com | 263138777 |
| ccioh.com | cindustries.com | 311314332 |
| dstechnologiesinc.com | ds-technologies.com | 823856305 |

**Resolution:** Trust DOL domain (from official filings) as authoritative.

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-06 | Created after pressure test validation |
