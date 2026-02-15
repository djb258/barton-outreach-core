# Quick Reference: Joining company_source_urls to outreach

## The Problem
You want to join `company.company_source_urls` to `outreach.outreach`, but there's no direct foreign key.

## The Solution: 4-Table Join Path

```sql
company.company_source_urls
    ↓ (company_unique_id)
company.company_master
    ↓ (company_unique_id)
cl.company_identity
    ↓ (outreach_id)
outreach.outreach
```

## Copy-Paste Template

```sql
SELECT
    o.outreach_id,
    ci.company_name,
    csu.source_type,
    csu.source_url,
    csu.is_accessible
FROM company.company_source_urls csu
INNER JOIN company.company_master cm
    ON csu.company_unique_id = cm.company_unique_id
INNER JOIN cl.company_identity ci
    ON cm.company_unique_id = ci.company_unique_id
INNER JOIN outreach.outreach o
    ON ci.outreach_id = o.outreach_id
WHERE ci.outreach_id IS NOT NULL;  -- Only companies in outreach
```

## Reverse Direction (Outreach → URLs)

```sql
SELECT
    o.outreach_id,
    csu.source_type,
    csu.source_url
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id;
```

## Key Points

| Point | Details |
|-------|---------|
| **Direct FK?** | NO - must go through CL |
| **Join Key** | `company_unique_id` (all tables match) |
| **CL Pointer** | `cl.company_identity.outreach_id` |
| **NULL Safety** | Filter `ci.outreach_id IS NOT NULL` if you only want outreach companies |
| **Optional URLs** | Use `LEFT JOIN` for company_source_urls if some companies may lack URLs |

## Why This Path?

1. **CL is authority registry** - owns all company identity pointers
2. **Outreach_id is write-once in CL** - confirms company is in Outreach
3. **company_source_urls has no outreach FK** - must go through parent CL
4. **This enforces doctrine** - respects parent-child separation

## Table Sizes (Reference)

| Table | Rows | Notes |
|-------|------|-------|
| company.company_source_urls | ~97,000+ | Not all companies have URLs |
| company.company_master | 453 | Master records |
| cl.company_identity | 52,675 | Authority registry |
| outreach.outreach | 49,737 | Outreach operational spine |

## Common Filters

### Only Companies with Accessible URLs
```sql
AND csu.is_accessible = true
```

### Only Press Pages
```sql
AND csu.source_type = 'press_page'
```

### Only Companies Missing URLs
```sql
WHERE csu.id IS NULL  -- Use in LEFT JOIN version
```

### Only Recently Discovered
```sql
AND csu.discovered_at > NOW() - INTERVAL '7 days'
```

## Full Join Documentation

See `/docs/JOIN_GUIDE_company_source_urls_to_outreach.md` for detailed guide with:
- Complete schema definitions
- Multiple join patterns
- Performance tips
- Real-world examples
- Null safety guidance

---

**Quick Fact**: The path enforces the **CL Parent-Child Doctrine** where CL (Company Lifecycle) is the authority registry and Outreach is a child sub-hub that owns only workflow state, not identity.
