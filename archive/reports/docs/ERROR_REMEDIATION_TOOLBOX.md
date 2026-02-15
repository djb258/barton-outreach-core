# Error Remediation Toolbox

**Version**: 1.0
**Updated**: 2026-02-02
**Priority**: FREE → CHEAP → ACCURATE

---

## Current Error State

| Hub | Table | Count | Disposition | Action Needed |
|-----|-------|------:|-------------|---------------|
| CL | `cl.cl_errors_archive` | 16,103 | ARCHIVED | None (historical) |
| CT | `outreach.company_target_errors` | 4,404 | RETRY: 4,378 / PARKED: 26 | Pattern discovery |
| DOL | `outreach.dol_errors` | 29,740 | PARKED | Archive |
| PEOPLE | `people.people_errors` | 1,053 | RETRY | Enrichment retry |
| BLOG | `outreach.blog_errors` | 2 | — | Auto-resolves |
| SHQ | `shq.error_master` | 86,411 | IGNORE | None (accounted) |

---

## API Keys Status

| Tool | Key | Status | Tier | Cost |
|------|-----|--------|------|------|
| MX Lookup | N/A | FREE | 0 | $0 |
| SMTP Check | N/A | FREE | 0 | $0 |
| Web Scraper | N/A | FREE | 0 | $0 |
| **MillionVerifier** | `MILLIONVERIFIER_API_KEY` | **SET** | 2 | ~$0.004/email |
| **Apollo** | `APOLLO_API_KEY` | **SET** | 1 | ~$0.05/credit |
| **Prospeo** | `PROSPEO_API_KEY` | **SET** | 2 | ~$0.02/email |
| **Clay** | `CLAY_API_KEY` | **SET** | 2 | ~$0.10/record |
| Hunter | `HUNTER_API_KEY` | NOT SET | 1 | ~$0.03/request |
| Firecrawl | `FIRECRAWL_API_KEY` | NOT SET | 0 | Free tier: 500/mo |
| GooglePlaces | `GOOGLE_PLACES_API_KEY` | NOT SET | 0 | Free tier available |

---

## Error → Tool Mapping

### CT-M-NO-MX (4,404 records)

**Error**: Domain has no MX records or email pattern discovery failed.

**Tool Waterfall** (in order):

| Step | Tool | Tier | Cost | Action |
|------|------|------|------|--------|
| 1 | MX Lookup (dnspython) | 0 | FREE | Re-verify domain has MX records |
| 2 | Web Scraper | 0 | FREE | Scrape contact pages for emails |
| 3 | Apollo | 1 | ~$0.05 | Search for employees with emails |
| 4 | MillionVerifier | 2 | ~$0.004 | Verify email pattern with test addresses |

**Expected Outcome**:
- ~60% resolved by free tools (MX + scraping)
- ~30% resolved by Apollo
- ~10% remain unresolvable (no valid domain)

**Estimated Cost**: ~$50-100 for 4,378 RETRY records

---

### DOL NO_MATCH / NO_STATE (29,740 records)

**Error**: Company has no EIN match in DOL data OR is in non-applicable state.

**Tool Waterfall**: NONE

| Action | Tool | Cost |
|--------|------|------|
| Archive | SQL script | FREE |

**Reason**: These are **structural failures**. The company either:
- Doesn't file Form 5500 (legitimate)
- Is in a state without DOL coverage
- Uses a different legal name for filings

**No external tool can fix this**. Archive and move on.

---

### PI-E001 (1,053 records)

**Error**: People enrichment failed.

**Tool Waterfall** (in order):

| Step | Tool | Tier | Cost | Action |
|------|------|------|------|--------|
| 1 | Apollo | 1 | ~$0.05 | Search for person by name + company |
| 2 | MillionVerifier | 2 | ~$0.004 | Verify generated email |

**Expected Outcome**:
- ~70% resolved by Apollo enrichment
- ~20% resolved by email verification
- ~10% remain (person not findable)

**Estimated Cost**: ~$60 for 1,053 records

---

### BLOG-I-UPSTREAM-FAIL (2 records)

**Error**: Blog tried to process before CT completed.

**Tool Waterfall**: NONE (auto-resolves)

| Action | Tool | Cost |
|--------|------|------|
| Wait for CT | N/A | FREE |

**Reason**: Once CT completes for these 2 records, Blog will auto-retry and succeed.

---

## Remediation Priority (Cost-Optimized)

### Phase 1: FREE Actions (Cost: $0)

| Action | Records | Tool |
|--------|--------:|------|
| Archive DOL structural errors | 29,740 | SQL |
| Archive CT parked errors | 26 | SQL |
| Delete stale validation log | 2 | SQL |
| Run MX re-verification on CT errors | 4,378 | dnspython |
| Run web scraping on CT errors | ~2,500 | httpx |

**Expected Resolution**: ~1,500 CT errors (pattern found via scraping)

---

### Phase 2: CHEAP Actions (Cost: ~$50-80)

| Action | Records | Tool | Est. Cost |
|--------|--------:|------|----------:|
| Apollo enrichment for CT failures | ~2,800 | Apollo | ~$50 |
| Apollo enrichment for People failures | 1,053 | Apollo | ~$30 |

**Expected Resolution**: ~2,000 CT + ~700 People

---

### Phase 3: VERIFICATION (Cost: ~$20-40)

| Action | Records | Tool | Est. Cost |
|--------|--------:|------|----------:|
| MillionVerifier on discovered patterns | ~2,500 | MillionVerifier | ~$10 |
| MillionVerifier on generated emails | ~700 | MillionVerifier | ~$3 |

**Expected Resolution**: Validate all patterns before marking CT DONE

---

## Tool Scripts Available

### FREE Tools (Claude Code can run)

```python
# MX Lookup - TOOL-001 (FREE)
import dns.resolver

def verify_mx(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False
```

```python
# Web Scraper - TOOL-003 (FREE)
import httpx
import re

def scrape_emails(domain: str) -> list:
    urls = [f"https://{domain}/contact", f"https://{domain}/about"]
    emails = []
    for url in urls:
        try:
            r = httpx.get(url, timeout=10)
            found = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', r.text)
            emails.extend([e for e in found if domain in e])
        except:
            pass
    return list(set(emails))
```

### PAID Tools (Require API key)

```python
# Apollo - TOOL-009 (Tier 1)
from ops.providers.providers import ApolloProvider

provider = ApolloProvider(api_key=os.environ['APOLLO_API_KEY'])
result = provider.discover_pattern(domain, company_name)
```

```python
# MillionVerifier - TOOL-010 (Tier 2)
import httpx

async def verify_email(email: str, api_key: str) -> dict:
    r = await httpx.get(
        "https://api.millionverifier.com/api/v3/",
        params={"api": api_key, "email": email}
    )
    return r.json()
```

---

## Execution Scripts Location

| Script | Purpose | Location |
|--------|---------|----------|
| Archive DOL errors | Move to archive | `scripts/archive_dol_errors.py` (TO CREATE) |
| CT MX retry | Re-verify domains | `scripts/ct_mx_retry.py` (TO CREATE) |
| CT pattern discovery | Find email patterns | `scripts/ct_pattern_discovery.py` (TO CREATE) |
| People enrichment | Apollo + verify | `scripts/people_enrichment.py` (TO CREATE) |

---

## Cost Summary

| Phase | Actions | Est. Cost | Records Resolved |
|-------|---------|----------:|----------------:|
| Phase 1 (FREE) | Archive + MX + Scrape | $0 | ~31,000 |
| Phase 2 (CHEAP) | Apollo enrichment | ~$80 | ~2,700 |
| Phase 3 (VERIFY) | MillionVerifier | ~$15 | (validation) |
| **TOTAL** | — | **~$95** | **~33,700** |

---

## Path to Zero

```
CURRENT STATE                          TARGET STATE
─────────────────────────────────────  ────────────────────
CT errors:        4,404                CT errors:        0
  - RETRY:        4,378     ──────►      - Resolved:   ~3,800
  - PARKED:          26                  - Archived:      26
                                         - Unresolvable: ~500

DOL errors:      29,740                DOL errors:        0
  - PARKED:      29,740     ──────►      - Archived:  29,740

People errors:    1,053                People errors:     0
  - RETRY:        1,053     ──────►      - Resolved:    ~750
                                         - Unresolvable: ~300

Blog errors:          2                Blog errors:       0
  - UPSTREAM:         2     ──────►      - Auto-resolved:  2

SHQ master:      86,411                SHQ master:        0
  - IGNORE:      86,411     ──────►      - Archive after 90d TTL

CL archive:      16,103                CL archive:   16,103
  - ARCHIVED:    16,103                  - (permanent)
```

---

## Recommended Execution Order

1. **Run archive script** for DOL + CT parked + stale records (FREE)
2. **Run MX re-verification** on CT RETRY errors (FREE)
3. **Run web scraping** on CT RETRY with valid MX (FREE)
4. **Run Apollo enrichment** on remaining CT + People (PAID ~$80)
5. **Run MillionVerifier** on discovered patterns (PAID ~$15)
6. **Archive remaining unresolvable** after 90d TTL

---

## Document Control

| Field | Value |
|-------|-------|
| Author | Remediation Agent |
| Approved | System Owner |
| Review | After each phase completion |

---

**Ready to execute Phase 1 (FREE) on your command.**
