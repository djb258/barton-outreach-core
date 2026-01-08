# ADR: Blog Content — Signals Only, No Authority

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-BLOG-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |

---

## Context

Content signals (funding, acquisitions, leadership changes) provide valuable
timing information, but should not create authority over company existence.

---

## Decision

Blog Content is a **signal-only hub**:
- Emits BIT signals for timing optimization
- Cannot mint or revive companies
- Cannot trigger enrichment
- Lifecycle read-only

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Allow company creation from news | Would violate single-authority |
| Trigger enrichment on signals | Would bypass cost controls |
| Do Nothing | Would miss timing opportunities |

---

## Consequences

### Enables

- Timing optimization via BIT signals
- Clean separation of signal vs authority
- Safe integration of news sources

### Prevents

- Duplicate company creation
- Uncontrolled enrichment
- Authority conflicts

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |

---

# ADR: Blog Content — Error Discipline Enforcement

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-BLOG-002 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-08 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |

---

## Context

Blog Content Sub-Hub requires production-grade error handling that matches Company Target discipline. Errors must be:
- First-class outputs (not hidden logging)
- Persisted to dedicated error table
- Traceable via process_id
- Queryable for operational visibility

---

## Decision

Implement error handling discipline with:

1. **Dedicated Error Table**: `outreach.blog_errors` with full schema
2. **BlogPipelineError Exception**: Central exception class for all failures
3. **ENFORCE_ERROR_PERSISTENCE Guard**: Assertion enforced by CI
4. **process_id Tracking**: Every run gets a UUID for traceability
5. **No Silent Failures**: All errors persisted, not just logged

---

## Implementation

### Error Table

```sql
CREATE TABLE outreach.blog_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),
    pipeline_stage VARCHAR(50) NOT NULL,
    failure_code VARCHAR(20) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'ERROR',
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    process_id UUID,
    raw_input JSONB,
    stack_trace TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT
);
```

### CI Guards Added

| Guard | Check |
|-------|-------|
| 13 | `ENFORCE_ERROR_PERSISTENCE` assertion present |
| 14 | `blog_errors` table referenced |
| 15 | Print statements don't bypass persistence |

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Log-only errors | Not queryable, not traceable |
| Silent failures | Violates observability doctrine |
| Retry logic | Violates terminal failure doctrine |

---

## Consequences

### Enables

- Full error visibility in Neon
- Operational queries on failure patterns
- Process traceability via process_id
- Matches Company Target error discipline

### Prevents

- Silent failures
- Hidden error conditions
- Untraceable processing runs
- Operational blind spots

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | 2026-01-08 |
| Reviewer | | |

---

# ADR: Blog Content — Scope Lock (Company-Level Only)

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-BLOG-003 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-08 |

---

## Context

Blog Content must be scoped to company-level signals only. Social platform presence (LinkedIn, Twitter, etc.) is captured for verification, not audience metrics.

---

## Decision

**The Blog Sub-Hub records *where* a company publishes, not *how large* the audience is.**

Permanently prohibit:
- Follower/subscriber counts
- Engagement metrics (likes, views, comments)
- Sentiment analysis
- Post frequency analytics
- People-level social data

---

## Implementation

```python
DISALLOW_SOCIAL_METRICS = True
assert DISALLOW_SOCIAL_METRICS is True
```

CI Guards 11-12 enforce this scope lock.

---

## Consequences

### Enables

- Clean company-level signal extraction
- Avoids scope creep into social analytics
- Maintains signal-only purpose

### Prevents

- Feature creep toward social media analytics
- People-level data collection
- Engagement metric tracking

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | 2026-01-08 |
| Reviewer | | |
