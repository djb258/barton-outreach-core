# Technical Architecture Specification: Example Records

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Sample data showing what valid records look like — Pattern match, don't guess

---

## 1. CL Authority Registry

### cl.company_identity

```json
{
  "company_unique_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sovereign_company_id": "s9876543-21ab-cdef-0123-456789abcdef",
  "company_name": "Acme Corporation",
  "company_domain": "acmecorp.com",
  "normalized_domain": "acmecorp.com",
  "linkedin_company_url": "https://www.linkedin.com/company/acme-corporation",
  "source_system": "intake_csv",
  "company_fingerprint": "acme_corporation_acmecorp_com_ca",
  "lifecycle_run_id": "run_20260128_001",
  "existence_verified": true,
  "verification_run_id": "ver_20260128_001",
  "verified_at": "2026-01-28T10:30:00Z",
  "domain_status_code": 200,
  "name_match_score": 95,
  "state_match_result": "MATCH",
  "canonical_name": "Acme Corporation",
  "state_verified": "CA",
  "employee_count_band": "100-500",
  "identity_pass": 3,
  "identity_status": "RESOLVED",
  "last_pass_at": "2026-01-28T10:35:00Z",
  "eligibility_status": "ELIGIBLE",
  "exclusion_reason": null,
  "entity_role": "EMPLOYER",
  "final_outcome": null,
  "final_reason": null,
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "sales_process_id": null,
  "client_id": null,
  "outreach_attached_at": "2026-01-28T11:00:00Z",
  "sales_opened_at": null,
  "client_promoted_at": null,
  "created_at": "2026-01-28T09:00:00Z"
}
```

**Key Points**:
- `company_unique_id` is the PK, never changes
- `outreach_id` is WRITE-ONCE — once set, never update
- `identity_status` must be "RESOLVED" before outreach can start
- `eligibility_status` must be "ELIGIBLE" for marketing

---

## 2. Outreach Spine

### outreach.outreach

```json
{
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "sovereign_id": "s9876543-21ab-cdef-0123-456789abcdef",
  "domain": "acmecorp.com",
  "created_at": "2026-01-28T11:00:00Z",
  "updated_at": "2026-01-28T11:00:00Z"
}
```

**Key Points**:
- `outreach_id` is minted here, then registered in CL
- `sovereign_id` links to CL sovereign_company_id
- This is the FK target for ALL sub-hub tables

---

## 3. Company Target Sub-Hub (04.04.01)

### outreach.company_target

```json
{
  "target_id": "t1234567-89ab-cdef-0123-456789abcdef",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "company_unique_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email_method": "{first}.{last}@acmecorp.com",
  "method_type": "PATTERN",
  "confidence_score": 0.85,
  "is_catchall": false,
  "outreach_status": "active",
  "execution_status": "done",
  "bit_score_snapshot": 65,
  "sequence_count": 2,
  "active_sequence_id": "seq_002",
  "source": "intake_batch_20260128",
  "first_targeted_at": "2026-01-28T11:30:00Z",
  "last_targeted_at": "2026-01-28T14:00:00Z",
  "imo_completed_at": "2026-01-28T11:15:00Z",
  "created_at": "2026-01-28T11:05:00Z",
  "updated_at": "2026-01-28T14:00:00Z"
}
```

**Key Points**:
- `email_method` shows the discovered pattern
- `method_type` is PATTERN, CATCHALL, VERIFIED, or NONE
- `confidence_score` ranges 0.00-1.00
- `outreach_status` drives campaign execution

---

## 4. DOL Sub-Hub (04.04.03)

### outreach.dol

```json
{
  "dol_id": "d1234567-89ab-cdef-0123-456789abcdef",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "ein": "12-3456789",
  "filing_id": "20250115-12-3456789-001",
  "form_5500_matched": true,
  "schedule_a_matched": true,
  "match_confidence": 0.92,
  "match_method": "EXACT",
  "matched_at": "2026-01-28T11:20:00Z",
  "created_at": "2026-01-28T11:15:00Z",
  "updated_at": "2026-01-28T11:20:00Z"
}
```

### dol.form_5500

```json
{
  "filing_id": "20250115-12-3456789-001",
  "ein": "12-3456789",
  "plan_name": "Acme Corporation 401(k) Plan",
  "sponsor_name": "ACME CORPORATION",
  "sponsor_state": "CA",
  "plan_year": 2025,
  "plan_year_end_month": 12,
  "total_participants": 250,
  "total_assets": 15000000.00,
  "filing_date": "2025-01-15",
  "form_type": "5500",
  "plan_type": "401K",
  "is_large_plan": true,
  "created_at": "2025-01-15T00:00:00Z"
}
```

### dol.schedule_a

```json
{
  "schedule_id": "sa123456-789a-bcde-f012-3456789abcde",
  "filing_id": "20250115-12-3456789-001",
  "ein": "12-3456789",
  "insurance_carrier_name": "Blue Cross Blue Shield",
  "insurance_carrier_ein": "55-1234567",
  "commission_amount": 45000.00,
  "premium_amount": 450000.00,
  "policy_number": "BCBS-2025-12345",
  "coverage_type": "HEALTH",
  "coverage_start_date": "2025-01-01",
  "coverage_end_date": "2025-12-31",
  "created_at": "2025-01-15T00:00:00Z"
}
```

**Key Points**:
- `ein` format is XX-XXXXXXX
- `filing_id` is the DOL's unique identifier
- `is_large_plan` is true when total_participants >= 100

---

## 5. People Intelligence Sub-Hub (04.04.02)

### outreach.people

```json
{
  "person_id": "op123456-789a-bcde-f012-3456789abcde",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "person_unique_id": "pm123456-789a-bcde-f012-3456789abcde",
  "slot_type": "CEO",
  "email": "john.smith@acmecorp.com",
  "email_verified": true,
  "verification_method": "SMTP_CHECK",
  "linkedin_url": "https://www.linkedin.com/in/johnsmith",
  "title": "Chief Executive Officer",
  "seniority": "C-SUITE",
  "seniority_rank": 10,
  "created_at": "2026-01-28T11:25:00Z",
  "updated_at": "2026-01-28T11:30:00Z"
}
```

### people.people_master

```json
{
  "unique_id": "pm123456-789a-bcde-f012-3456789abcde",
  "company_unique_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "full_name": "John Smith",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@acmecorp.com",
  "email_verified": true,
  "title": "Chief Executive Officer",
  "seniority": "C-SUITE",
  "seniority_rank": 10,
  "linkedin_url": "https://www.linkedin.com/in/johnsmith",
  "slot_type": "CEO",
  "data_quality_score": 92.5,
  "source": "linkedin_enrichment",
  "created_at": "2026-01-15T00:00:00Z",
  "updated_at": "2026-01-28T11:25:00Z"
}
```

### people.company_slot

```json
{
  "slot_id": "cs123456-789a-bcde-f012-3456789abcde",
  "company_unique_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "slot_type": "CEO",
  "person_unique_id": "pm123456-789a-bcde-f012-3456789abcde",
  "is_filled": true,
  "fill_source": "linkedin_enrichment",
  "confidence_score": 0.95,
  "filled_at": "2026-01-28T11:25:00Z",
  "last_refreshed_at": "2026-01-28T11:25:00Z",
  "created_at": "2026-01-28T11:20:00Z",
  "updated_at": "2026-01-28T11:25:00Z"
}
```

**Key Points**:
- `slot_type` is one of: CEO, CFO, HR, CTO, CMO, COO
- `seniority_rank` ranges 1-10 (10 = C-suite)
- `person_unique_id` links outreach.people to people.people_master

---

## 6. Blog Sub-Hub (04.04.05)

### outreach.blog

```json
{
  "blog_id": "b1234567-89ab-cdef-0123-456789abcdef",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "blog_url": "https://acmecorp.com/blog",
  "rss_feed_url": "https://acmecorp.com/blog/feed",
  "blog_platform": "WordPress",
  "has_rss": true,
  "has_blog": true,
  "post_count": 45,
  "signal_count": 3,
  "last_post_date": "2026-01-25",
  "last_checked_at": "2026-01-28T11:35:00Z",
  "next_check_at": "2026-01-29T11:35:00Z",
  "check_status": "active",
  "created_at": "2026-01-28T11:30:00Z",
  "updated_at": "2026-01-28T11:35:00Z"
}
```

---

## 7. BIT Engine

### outreach.bit_scores

```json
{
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "bit_score": 65,
  "bit_tier": "GOLD",
  "tier_threshold": 60,
  "score_updated_at": "2026-01-28T11:40:00Z",
  "tier_assigned_at": "2026-01-28T11:40:00Z",
  "signal_count": 5,
  "dol_signal_count": 2,
  "blog_signal_count": 3,
  "movement_signal_count": 0,
  "custom_signal_count": 0,
  "score_velocity": 5.2,
  "created_at": "2026-01-28T11:40:00Z",
  "updated_at": "2026-01-28T11:40:00Z"
}
```

### outreach.bit_signals

```json
{
  "signal_id": "sig12345-6789-abcd-ef01-23456789abcd",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "signal_type": "DOL_FILING",
  "signal_subtype": "LARGE_PLAN",
  "signal_impact": 20,
  "signal_weight": 1,
  "signal_source": "dol_form_5500",
  "signal_hash": "abc123def456",
  "signal_payload": {
    "filing_id": "20250115-12-3456789-001",
    "total_participants": 250,
    "total_assets": 15000000
  },
  "signal_timestamp": "2026-01-28T11:20:00Z",
  "expires_at": "2027-01-28T11:20:00Z",
  "is_expired": false,
  "created_at": "2026-01-28T11:40:00Z"
}
```

**Key Points**:
- `bit_score` ranges 0-100
- `bit_tier` is PLATINUM (80+), GOLD (60-79), SILVER (40-59), BRONZE (20-39), NONE (<20)
- `signal_hash` used for 24h deduplication

---

## 8. Kill Switch

### outreach.manual_overrides

```json
{
  "override_id": "mo123456-789a-bcde-f012-3456789abcde",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "override_type": "EXCLUDE",
  "reason": "Customer requested no marketing contact",
  "applied_by": "support@company.com",
  "applied_at": "2026-01-28T15:00:00Z",
  "expires_at": null,
  "is_active": true
}
```

**Override Types**:
- `EXCLUDE` — Block all outreach
- `INCLUDE` — Force include despite other rules
- `TIER_FORCE` — Override BIT tier
- `PAUSE` — Temporary pause

---

## 9. Campaign & Execution

### outreach.campaigns

```json
{
  "campaign_id": "camp1234-5678-9abc-def0-123456789abc",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "campaign_name": "Q1 2026 Benefits Renewal",
  "campaign_type": "RENEWAL_OUTREACH",
  "campaign_status": "active",
  "started_at": "2026-01-28T12:00:00Z",
  "completed_at": null,
  "created_at": "2026-01-28T11:50:00Z",
  "updated_at": "2026-01-28T12:00:00Z"
}
```

### outreach.send_log

```json
{
  "send_id": "send1234-5678-9abc-def0-123456789abc",
  "outreach_id": "o7654321-fedc-ba09-8765-432109876543",
  "sequence_id": "seq12345-6789-abcd-ef01-23456789abcd",
  "recipient_email": "john.smith@acmecorp.com",
  "send_status": "delivered",
  "send_provider": "sendgrid",
  "scheduled_at": "2026-01-28T12:00:00Z",
  "sent_at": "2026-01-28T12:00:05Z",
  "opened_at": "2026-01-28T14:30:00Z",
  "clicked_at": "2026-01-28T14:31:00Z",
  "replied_at": null,
  "created_at": "2026-01-28T11:55:00Z"
}
```

---

## Quick Reference: UUID Format

All UUIDs in this system follow the format:
```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`

Generated via: `gen_random_uuid()` in PostgreSQL

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
