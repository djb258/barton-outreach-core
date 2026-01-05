# Blog Content Hub — CC-02

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-02 (Hub)
**Doctrine ID**: 04.04.05
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Authority Boundary

Blog Content owns:
- Content signal extraction
- News event monitoring
- BIT signal emission

## Identity Rules

| Identity | Owner | This Hub |
|----------|-------|----------|
| company_unique_id | CL via CT | CONSUME ONLY |
| article_id | This Hub | MINT |
| signal_id | This Hub | MINT |

## IMO Structure

```
blog-content/
├── CC.md
├── hub.manifest.yaml
├── __init__.py
└── imo/
    ├── input/            # Article ingestion
    │   └── ingest_article.py
    ├── middle/           # Content analysis
    │   ├── classify_event.py
    │   ├── extract_entities.py
    │   ├── match_company.py
    │   ├── parse_content.py
    │   └── validate_signal.py
    └── output/           # BIT signal emission
        └── emit_bit_signal.py
```

## Upstream Dependencies

| Upstream | Signal Consumed | Required |
|----------|-----------------|----------|
| Company Target | company_unique_id, domain | YES |

## Waterfall Position

Executes after People Intelligence (04.04.02).
Consumer only — does not emit to other hubs.
