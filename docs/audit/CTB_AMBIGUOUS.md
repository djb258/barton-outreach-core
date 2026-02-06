# CTB Ambiguous Tables Report

**Date**: 2026-02-06
**Type**: READ-ONLY AUDIT
**Scope**: Tables requiring human decision for CTB placement

---

## Summary

**Total Ambiguous Tables**: 10

These tables cannot be placed in the CTB without additional information. Each requires a specific question to be answered before placement.

---

## Ambiguous Table Details

### 1. company.company_source_urls

| Field | Value |
|-------|-------|
| Schema | company |
| Table | company_source_urls |
| Rows | 104,012 |
| PK | source_id |
| Columns | source_id, company_unique_id, url_type, url, discovered_at, verified_at |

**Question**: Which sub-hub owns URL discovery?
- Option A: `Outreach.outreach_id.company_target_id` (CT owns domain/URL)
- Option B: `Outreach.outreach_id.blog_id` (Blog owns about/news URLs)
- Option C: Split by url_type (CT for domain, Blog for content)

**Cannot place without knowing URL ownership model.**

---

### 2. company.company_events

| Field | Value |
|-------|-------|
| Schema | company |
| Table | company_events |
| Rows | 0 |
| PK | id |
| Columns | id, company_unique_id, event_type, event_data, created_at |

**Question**: What is the purpose of this table?
- Option A: Audit log for CL changes → `CL.sovereign_company_id.audit`
- Option B: Pipeline events → `Outreach.audit`
- Option C: Deprecated → Remove

**Cannot place without knowing table purpose.**

---

### 3. company.company_sidecar

| Field | Value |
|-------|-------|
| Schema | company |
| Table | company_sidecar |
| Rows | 0 |
| PK | company_unique_id |
| Columns | company_unique_id, metadata |

**Question**: Is this a CL extension or Outreach extension?
- Option A: CL sidecar → `CL.sovereign_company_id.sidecar`
- Option B: CT sidecar → `Outreach.outreach_id.company_target_id.sidecar`
- Option C: Deprecated → Remove

**Cannot place without knowing ownership.**

---

### 4. company.contact_enrichment

| Field | Value |
|-------|-------|
| Schema | company |
| Table | contact_enrichment |
| Rows | 0 |
| PK | id |
| Columns | id, contact_id, enrichment_type, enrichment_data |

**Question**: What contact entity does this enrich?
- Option A: People enrichment → `Outreach.outreach_id.people_id.company_id.person_id.enrichment`
- Option B: Hunter enrichment → `SOURCE.hunter.enrichment`
- Option C: Deprecated → Remove

**Cannot place without knowing contact source.**

---

### 5. company.email_verification

| Field | Value |
|-------|-------|
| Schema | company |
| Table | email_verification |
| Rows | 0 |
| PK | id |
| Columns | id, email, verification_status, verified_at |

**Question**: Is this pattern verification or person email verification?
- Option A: Pattern verification → `Outreach.outreach_id.company_target_id.verification`
- Option B: Person email verification → `Outreach.outreach_id.people_id.company_id.person_id.verification`
- Option C: Deprecated → Remove

**Cannot place without knowing verification type.**

---

### 6. company.pipeline_errors

| Field | Value |
|-------|-------|
| Schema | company |
| Table | pipeline_errors |
| Rows | 0 |
| PK | id |
| Columns | id, error_type, error_message, created_at |

**Question**: Which pipeline does this serve?
- Option A: CT pipeline → Merge into `outreach.company_target_errors`
- Option B: General outreach → Merge into `outreach.outreach_errors`
- Option C: Deprecated → Remove

**Cannot place without knowing pipeline ownership.**

---

### 7. company.pipeline_events

| Field | Value |
|-------|-------|
| Schema | company |
| Table | pipeline_events |
| Rows | 2,185 |
| PK | id |
| Columns | id, event_type, event_data, company_unique_id, created_at |

**Question**: Which pipeline do these events track?
- Option A: CT pipeline → `Outreach.outreach_id.company_target_id.audit`
- Option B: General outreach → `Outreach.audit`
- Option C: CL pipeline → `CL.sovereign_company_id.audit`

**Cannot place without knowing pipeline ownership.**

---

### 8. company.validation_failures_log

| Field | Value |
|-------|-------|
| Schema | company |
| Table | validation_failures_log |
| Rows | 0 |
| PK | id |
| Columns | id, validation_type, failure_reason, created_at |

**Question**: What validation is this tracking?
- Option A: CL validation → `CL.sovereign_company_id.errors`
- Option B: CT validation → `Outreach.outreach_id.company_target_id.errors`
- Option C: Deprecated → Remove

**Cannot place without knowing validation scope.**

---

### 9. marketing.review_queue

| Field | Value |
|-------|-------|
| Schema | marketing |
| Table | review_queue |
| Rows | 516 |
| PK | review_id |
| Columns | review_id, person_id, company_unique_id, review_type, status, created_at |

**Question**: What is being reviewed and by which sub-hub?
- Option A: People review → `Outreach.outreach_id.people_id.queue`
- Option B: CT review → `Outreach.outreach_id.company_target_id.queue`
- Option C: General outreach review → `Outreach.queue`

**Cannot place without knowing review ownership.**

---

### 10. dol.form_5500_icp_filtered

| Field | Value |
|-------|-------|
| Schema | dol |
| Table | form_5500_icp_filtered |
| Rows | 24,892 |
| PK | **NO PK** |
| Columns | (filtered subset of form_5500) |

**Question**: Is this a materialized view or a staging table?
- Option A: MV of form_5500 → `Outreach.outreach_id.dol_id.company_id.EIN.form_5500.mv`
- Option B: Staging table → `Outreach.outreach_id.dol_id.staging`
- Note: **Needs a PK defined regardless of placement**

**Cannot place without knowing table purpose. Also needs PK.**

---

## Resolution Process

For each ambiguous table:

1. **Owner Decision Required**: A human must determine the table's purpose
2. **CTB Assignment**: Once purpose is known, assign to correct CTB node
3. **Migration Plan**: If table needs to move, create migration plan
4. **Deprecation**: If table is unused, mark for deprecation

---

## Tables Likely Deprecated (Recommendation)

Based on row counts and purpose ambiguity, these tables are candidates for deprecation review:

| Table | Rows | Reason |
|-------|------|--------|
| company.company_events | 0 | Empty, unclear purpose |
| company.company_sidecar | 0 | Empty, unclear purpose |
| company.contact_enrichment | 0 | Empty, unclear purpose |
| company.email_verification | 0 | Empty, unclear purpose |
| company.pipeline_errors | 0 | Empty, unclear purpose |
| company.validation_failures_log | 0 | Empty, unclear purpose |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | READ-ONLY AUDIT |
| Status | AWAITING HUMAN DECISION |
| Action | NONE (audit only) |
