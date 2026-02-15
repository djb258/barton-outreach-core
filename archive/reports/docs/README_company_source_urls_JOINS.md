# Documentation: Joining company_source_urls to outreach.outreach

**Date**: 2026-02-02
**Status**: Complete
**Location**: `/docs/` directory

---

## Overview

This documentation provides complete guidance for joining `company.company_source_urls` to `outreach.outreach` across the Barton Outreach Core database.

**Key Finding**: There is **no direct foreign key** between these tables. All joins must traverse through the CL (Company Lifecycle) authority registry.

---

## Documents Created

### 1. **JOIN_GUIDE_company_source_urls_to_outreach.md** (Primary Reference)
Comprehensive guide covering:
- Complete table schemas with all columns
- 4-step join path explanation
- Join principle documentation
- 4 different join patterns with examples
- Real-world query examples
- Performance optimization tips
- Null safety guidance
- Doctrine alignment explanation

**Use This For**: Understanding why the join path is structured this way, detailed schema knowledge, comprehensive examples.

**File**: `/docs/JOIN_GUIDE_company_source_urls_to_outreach.md`

---

### 2. **QUICK_REFERENCE_company_source_urls_JOIN.md** (Quick Start)
Fast reference guide with:
- Copy-paste join template
- Reverse direction example
- Key points summary table
- Common filters
- Link to full documentation

**Use This For**: Quick lookup, copy-paste templates, 30-second understanding.

**File**: `/docs/QUICK_REFERENCE_company_source_urls_JOIN.md`

---

### 3. **JOIN_PATTERNS_company_source_urls.sql** (SQL Examples)
10 production-ready SQL patterns:
1. Forward join (URLs → Outreach)
2. Reverse join (Outreach → URLs)
3. Companies with NO URLs
4. URL type coverage analysis
5. Per-company statistics
6. Join with company_target sub-hub
7. Filter by accessibility
8. Recent discoveries
9. Multiple URL types
10. Data integrity audit

Plus:
- Edge case handling
- NULL safety examples
- Performance optimization tips
- Verification queries

**Use This For**: Copy-paste working SQL, testing patterns, performance tuning.

**File**: `/docs/JOIN_PATTERNS_company_source_urls.sql`

---

## Quick Answer

### The Join Path

```
company.company_source_urls
    ├─ company_unique_id
    └─→ company.company_master
        ├─ company_unique_id
        └─→ cl.company_identity
            ├─ outreach_id (WRITE-ONCE pointer)
            └─→ outreach.outreach
```

### The SQL Template

```sql
SELECT
    o.outreach_id,
    ci.company_name,
    csu.source_url,
    csu.source_type
FROM company.company_source_urls csu
INNER JOIN company.company_master cm
    ON csu.company_unique_id = cm.company_unique_id
INNER JOIN cl.company_identity ci
    ON cm.company_unique_id = ci.company_unique_id
INNER JOIN outreach.outreach o
    ON ci.outreach_id = o.outreach_id
WHERE ci.outreach_id IS NOT NULL;
```

### Why This Path?

The CL Parent-Child Doctrine requires:
1. **CL stores identity pointers only** - includes outreach_id as WRITE-ONCE
2. **Outreach mints outreach_id** - stored in outreach.outreach
3. **Company tables are independent** - no direct FK to outreach
4. **All hubs authenticate through CL** - CL is single authority registry

---

## Doctrine Context

This join pattern enforces **CL Parent-Child Doctrine v1.1**:

| Component | Role | Authority |
|-----------|------|-----------|
| **CL (Company Lifecycle)** | Parent hub | Mints company_unique_id, stores outreach_id pointer |
| **company.company_master** | Atomic data | Source of truth for company attributes |
| **company.company_source_urls** | Derived data | URL discovery results, links to company_master |
| **outreach.outreach** | Child hub | Operational spine, owns outreach workflow state |

The join path respects this hierarchy by requiring all queries to traverse from company data → CL registry → outreach spine.

---

## Table of Contents

### Documentation Files
- [Full Join Guide](./JOIN_GUIDE_company_source_urls_to_outreach.md) - Complete reference
- [Quick Reference](./QUICK_REFERENCE_company_source_urls_JOIN.md) - 30-second lookup
- [SQL Patterns](./JOIN_PATTERNS_company_source_urls.sql) - 10 production patterns

### Related Documentation
- [CLAUDE.md](../CLAUDE.md) - Full CL Parent-Child Doctrine specification
- [DATABASE_QUERY_RESULTS.md](./DATABASE_QUERY_RESULTS.md) - Complete schema export
- [SCHEMA_REFERENCE.md](./SCHEMA_REFERENCE.md) - Schema reference guide

---

## Key Statistics

| Metric | Value |
|--------|-------|
| **company.company_source_urls rows** | ~97,000+ |
| **company.company_master rows** | 453 |
| **cl.company_identity rows** | 52,675 |
| **outreach.outreach rows** | 49,737 |
| **Companies with URLs** | 100% (all discovered) |
| **Companies in Outreach** | ~94% (49,737 / 52,675) |
| **Coverage: URLs for Outreach companies** | Variable (not all have discovered URLs) |

---

## Usage Examples

### Scenario 1: Find Press Pages for Outreach Companies
```sql
-- See: JOIN_GUIDE_company_source_urls_to_outreach.md → Example 1
-- Or: JOIN_PATTERNS_company_source_urls.sql → PATTERN 3
```

### Scenario 2: Companies Missing URL Discovery
```sql
-- See: JOIN_GUIDE_company_source_urls_to_outreach.md → Pattern 4
-- Or: JOIN_PATTERNS_company_source_urls.sql → PATTERN 3
```

### Scenario 3: URL Type Coverage Analysis
```sql
-- See: JOIN_PATTERNS_company_source_urls.sql → PATTERN 4
-- Or: JOIN_PATTERNS_company_source_urls.sql → PATTERN 5
```

---

## Common Questions

### Q: Why is there no direct FK from company_source_urls to outreach?
**A**: Because CL (Company Lifecycle) is the authority registry. All identity pointers (including outreach_id) flow through CL. This enforces the parent-child doctrine separation.

### Q: Can I join directly without going through CL?
**A**: Technically yes, but it violates the doctrine. The outreach_id pointer is stored in cl.company_identity, so you MUST join through there to get valid outreach_id values.

### Q: What if outreach_id is NULL?
**A**: The company hasn't been claimed by Outreach yet. It won't appear in outreach.outreach. Filter with `ci.outreach_id IS NOT NULL` to skip these.

### Q: What if a company has no company_source_urls rows?
**A**: URL discovery hasn't run yet, or the company's website is inaccessible. This is normal for new companies. Use `LEFT JOIN` for company_source_urls if optional.

### Q: Which join to use: INNER or LEFT?
**A**: Use `INNER JOIN` for mandatory data, `LEFT JOIN` for optional data.
- **INNER JOIN company_source_urls** = Only companies with discovered URLs
- **LEFT JOIN company_source_urls** = All outreach companies (with or without URLs)

---

## Performance Notes

### Indexes Available
- `company.company_source_urls` (id PK, unique on company_unique_id + source_url)
- `company.company_master` (company_unique_id PK)
- `cl.company_identity` (company_unique_id PK, FK on outreach_id)
- `outreach.outreach` (outreach_id PK, FK on sovereign_id)

### Recommended Filter Order
1. Filter on `cl.company_identity.outreach_id IS NOT NULL` first (reduces dataset early)
2. Then filter on `company.company_source_urls` columns if needed
3. Then join to `outreach.outreach` for final filtering

### Query Optimization Patterns
See [JOIN_PATTERNS_company_source_urls.sql](./JOIN_PATTERNS_company_source_urls.sql) → **PERFORMANCE OPTIMIZATION TIPS** section.

---

## Maintenance & Updates

**Last Verified**: 2026-02-02
**Schema Version**: As of 2026-01-28 database export
**Database**: Neon PostgreSQL (Marketing DB)

If the schema changes:
1. Update `/docs/DATABASE_QUERY_RESULTS.md` first
2. Then update join guides
3. Run verification queries in `/docs/JOIN_PATTERNS_company_source_urls.sql`

---

## Support & Questions

For questions about:
- **Join patterns**: See `/docs/JOIN_PATTERNS_company_source_urls.sql`
- **Full schema details**: See `/docs/JOIN_GUIDE_company_source_urls_to_outreach.md`
- **Quick reference**: See `/docs/QUICK_REFERENCE_company_source_urls_JOIN.md`
- **CL Doctrine**: See `/CLAUDE.md` (sections: "CORE ARCHITECTURE: CL AUTHORITY REGISTRY" and "Key Doctrine")

---

**Created By**: Database Schema Analysis (2026-02-02)
**Doctrine Source**: CL Parent-Child Doctrine v1.1
**Status**: Ready for Production Use
