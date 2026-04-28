# CLAUDE.md — LCS Hub Worker

## Identity
- **Worker:** lcs-hub
- **URL:** https://lcs-hub.svg-outreach.workers.dev
- **D1 Spine:** svg-d1-spine (641a9a1e) — company identity, LCS pipeline tables
- **D1 Outreach:** svg-d1-outreach-ops (73a285b8) — all outreach sub-hub data
- **Hyperdrive:** neon-outreach — SEED operations ONLY (never during WORK phase)

## Pre-Flight: What Data Already Exists in D1

**BEFORE writing any query, pipeline, or SEED function — check this inventory.**

### Already in D1 (DO NOT re-SEED unless Neon data changes):
- `outreach_company_target` — 32,702 companies with targeting data
- `outreach_outreach` — 32,702 outreach status records
- `outreach_blog` — 32,702 blog records (materialized view)
- `outreach_dol` — 27,464 DOL summary records
- `people_company_slot` — 98,106 role-based slots (32,702 × 3)
- `people_people_master` — 58,890 full contact records
- `enrichment_hunter_contact` — 175,632 Hunter.io verified emails + contacts
- `enrichment_hunter_company` — 15,537 Hunter.io email patterns per domain
- `vendor_people` — 175,632 vendor-enriched contacts with slot mapping
- `vendor_ct` — 18,683 vendor-enriched company data + email patterns
- `cl_company_identity` — 32,702 sovereign identity records (spine D1)
- `outreach_people` — DEPRECATED (legacy pre-slot model)

### DOL Filing Detail (SEED COMPLETE 2026-03-25 — 171,040 rows, 27,868 companies):
- `dol_form_5500` — 14,252 Form 5500 filings (all years, all fields)
- `dol_schedule_a` — 17,890 broker/insurance detail records
- `dol_schedule_c` — 33,810 service provider records
- `dol_schedule_other` — 105,088 other schedule records (JSON)

### Pipeline Engine Tables (Session 28 — BAR-303 through BAR-308, spine D1):
- `lcs_signal_registry` — signal set definitions; compiler reads by `signal_set_hash`
- `lcs_engagement_rules` — closed-loop response rules per trigger event (BAR-303); human-owned, seeded at migration
- `lcs_sequence_def` — multi-step sequence playbook definitions: sequence_id, step_number, frame_id, channel, delay_hours, condition (BAR-304)
- `lcs_contact_sequence_state` — per-contact position in active sequences: current_step, status, next_step_after, last_engagement (BAR-304)
- `lcs_contact_engagement_score` — composite engagement score per contact: email_score, linkedin_score, composite_score, is_hot_lead (BAR-305; hot lead threshold = composite > 25)
- `lcs_contact_channel_state` — per-contact channel state machine: primary_channel, channel_state, email_status, linkedin_status (BAR-307; advisory — logs and tracks, does not hard-block)
- `lcs_voice_library` — Dave Barton voice constants per target role (VCE-BARTON-CEO/CFO/HR/ALL): tone, style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points (BAR-285)
- `lcs_m_registry` — engine constants registry (Dave's M inventory — 34 trunk constants); used by compiler and Dyno (BAR-306)
- `lcs_email_signature` — email signature templates per sender identity (BAR-308)

## Architecture Rules

1. **SEED → WORK → PUSH.** Neon is vault. D1 is workspace. Hyperdrive for SEED only.
2. **Pipeline reads D1 exclusively.** Zero Neon calls during compilation or delivery.
3. **BIT scoring is RETIRED.** Do not reference `outreach_bit_scores`.
4. **CQRS:** `lcs_event` = canonical (read). `lcs_err0` = error (write). Supporting tables serve these two.
5. **Domain rotation:** 14 Mailgun domains. Round-robin by LRU. Per-domain daily caps. Cron resets at 07:00 UTC.

## Key Joins
- Company identity: `cl_company_identity.outreach_id` → `outreach_company_target.outreach_id`
- People slots: `people_company_slot.outreach_id` → `people_people_master.unique_id` (NOT person_unique_id)
- DOL detail: `dol_form_5500.sponsor_dfe_ein` is the join key to Neon DOL data
- Coverage: `outreach_company_target.postal_code` → `coverage_service_agent_coverage.anchor_zip`
