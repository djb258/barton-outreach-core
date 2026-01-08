# Blog Content Sub-Hub

**Status:** PRODUCTION LOCKED
**Waterfall Position:** 4th (LAST)
**Doctrine:** Spine-First Architecture v1.1

---

## Quick Reference

| Field | Value |
|-------|-------|
| Hub ID | HUB-BLOG-001 |
| IMO Gate | `hubs/blog-content/imo/blog_imo.py` |
| CI Guard | `blog_imo_guard.yml` (15 guards) |
| Tables | outreach.blog, outreach.blog_errors |
| Upstream Gate | CT execution_status = 'ready' |

---

## Doctrine Guards

```python
ENFORCE_OUTREACH_SPINE_ONLY = True   # Spine-first
DISALLOW_SOCIAL_METRICS = True       # Company-level only
ENFORCE_ERROR_PERSISTENCE = True     # No silent failures
```

---

## Event Types (Locked BIT Impacts)

| Event | Impact |
|-------|--------|
| FUNDING_EVENT | +15.0 |
| ACQUISITION | +12.0 |
| LEADERSHIP_CHANGE | +8.0 |
| EXPANSION | +7.0 |
| PRODUCT_LAUNCH | +5.0 |
| PARTNERSHIP | +5.0 |
| LAYOFF | -3.0 |
| NEGATIVE_NEWS | -5.0 |

---

## Scope Lock

> Records *where* a company publishes, not *how large* the audience is.

**Forbidden:** followers, engagement, likes, views, sentiment, post analytics

---

## Error Codes

| Code | Description |
|------|-------------|
| BLOG-I-NO-OUTREACH | No outreach_id |
| BLOG-I-NOT-FOUND | Not in spine |
| BLOG-I-UPSTREAM-FAIL | CT not ready |
| BLOG-I-ALREADY-PROCESSED | Idempotent skip |
| BLOG-M-CLASSIFY-FAIL | Classification failed |
| BLOG-O-WRITE-FAIL | Neon write failed |

---

## Related Files

- [[hubs/blog-content/PRD.md]] - Hub PRD
- [[hubs/blog-content/ADR.md]] - Architecture Decisions
- [[hubs/blog-content/CHECKLIST.md]] - Compliance Checklist
- [[hubs/blog-content/imo/BLOG_SUBHUB_ERD.md]] - Entity Relationship Diagram
- [[hubs/blog-content/PRODUCTION_VERIFICATION.md]] - Production Verification
- [[hubs/blog-content/ERROR_HANDLING_VERIFICATION.md]] - Error Handling Verification

---

## Verification Status

- [x] Replay Test PASS (10 records, 2 runs)
- [x] Forced Failure Test PASS
- [x] All 15 CI Guards configured
- [x] Error persistence verified

---

**Last Updated:** 2026-01-08
