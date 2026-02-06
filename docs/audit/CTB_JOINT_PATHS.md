# CTB Joint Paths — ID-Only Diagram

**Date**: 2026-02-06
**Type**: READ-ONLY AUDIT

---

## Canonical Tree Structure (IDs Only)

```
CL
└── sovereign_company_id
    │
    ├── outreach_id
    │   │
    │   ├── company_target_id
    │   │   └── (leaf: domain, pattern)
    │   │
    │   ├── dol_id
    │   │   └── company_id
    │   │       └── EIN
    │   │           ├── form_5500 [filing_id]
    │   │           ├── form_5500_sf [filing_id]
    │   │           └── schedule_a [schedule_id]
    │   │
    │   ├── blog_id
    │   │   └── company_id
    │   │       └── url
    │   │           └── article_id
    │   │
    │   └── people_id
    │       └── company_id
    │           └── person_id
    │               └── slot_id
    │                   ├── CEO
    │                   ├── CFO
    │                   └── HR
    │
    ├── sales_id (OUT OF SCOPE)
    │
    └── client_id (OUT OF SCOPE)
```

---

## Physical Table → CTB Path Mapping

### CL Schema (Root)

| Table | CTB Path |
|-------|----------|
| company_identity | `CL.sovereign_company_id` |
| company_domains | `CL.sovereign_company_id → domain_id` |
| company_names | `CL.sovereign_company_id → name_id` |
| identity_confidence | `CL.sovereign_company_id → confidence` |
| domain_hierarchy | `CL.sovereign_company_id → domain_id → hierarchy` |
| company_candidate | `CL.sovereign_company_id.staging` |

---

### Outreach Schema (Hub Spine)

| Table | CTB Path |
|-------|----------|
| outreach | `CL.sovereign_company_id → outreach_id` |

---

### Company Target Sub-Hub

| Table | CTB Path |
|-------|----------|
| company_target | `outreach_id → company_target_id` |
| company_hub_status | `outreach_id → company_target_id → status` |

---

### DOL Sub-Hub

| Table | CTB Path |
|-------|----------|
| outreach.dol | `outreach_id → dol_id` |
| dol.ein_urls | `outreach_id → dol_id → company_id → EIN` |
| dol.form_5500 | `outreach_id → dol_id → company_id → EIN → filing_id` |
| dol.form_5500_sf | `outreach_id → dol_id → company_id → EIN → filing_id` |
| dol.schedule_a | `outreach_id → dol_id → company_id → EIN → schedule_id` |
| dol.renewal_calendar | `outreach_id → dol_id → company_id → EIN → renewal_id` |

---

### Blog Sub-Hub

| Table | CTB Path |
|-------|----------|
| outreach.blog | `outreach_id → blog_id` |

---

### People Sub-Hub

| Table | CTB Path |
|-------|----------|
| people.people_master | `outreach_id → people_id → company_id → person_id` |
| people.company_slot | `outreach_id → people_id → company_id → person_id → slot_id` |

---

### BIT Sub-Hub

| Table | CTB Path |
|-------|----------|
| outreach.bit_scores | `outreach_id → bit` |

---

### Execution Sub-Hub

| Table | CTB Path |
|-------|----------|
| outreach.appointments | `outreach_id → execution` |
| outreach.campaigns | `outreach_id → execution` |
| outreach.sequences | `outreach_id → execution` |
| outreach.send_log | `outreach_id → execution → audit` |

---

## Join Key Summary

| Join | From | To |
|------|------|----|
| sovereign_company_id | CL | Outreach |
| outreach_id | Outreach | All Sub-Hubs |
| company_target_id | Outreach | CT Tables |
| dol_id | Outreach | DOL Match |
| EIN | DOL Match | DOL Source Tables |
| blog_id | Outreach | Blog Tables |
| people_id | Outreach | People Tables |
| person_id | People | Slot Assignment |
| slot_id | Person | Slot Type |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | READ-ONLY |
| Status | AUDIT COMPLETE |
