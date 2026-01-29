# Process Declaration: Outreach Execution Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-04 (Process) |
| **Process Doctrine** | `templates/doctrine/PROCESS_DOCTRINE.md` |

---

## Process Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-OUTREACH |
| **Doctrine ID** | 04.04.04 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
outreach-execution-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `campaign` | Campaign creation | `outreach-execution-campaign-20260129-a1b2c3d4` |
| `sequence` | Sequence execution | `outreach-execution-sequence-20260129-b2c3d4e5` |
| `send` | Send scheduling | `outreach-execution-send-20260129-c3d4e5f6` |
| `engage` | Engagement processing | `outreach-execution-engage-20260129-d4e5f6a7` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_OUTREACH_SPOKE.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | outreach.outreach | Operational spine identifier |
| `bit_score` | BIT Engine | BIT score (must be >= 50 to execute) |
| `bit_tier` | BIT Engine | Tier assignment |
| `contact_list` | People Hub | Contacts for outreach |
| `email_method` | Company Target | Verified email pattern |
| `campaign_request` | User/System | Campaign creation request |

---

## Variables Produced

_Reference: `docs/prd/PRD_OUTREACH_SPOKE.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `campaign_id` | outreach.campaigns | Campaign identifier |
| `sequence_id` | outreach.sequences | Sequence identifier |
| `send_status` | outreach.send_log | Send status (scheduled/sent/failed) |
| `opened_at` | outreach.send_log | Email open timestamp |
| `clicked_at` | outreach.send_log | Link click timestamp |
| `replied_at` | outreach.send_log | Reply timestamp |
| `engagement_event` | outreach.engagement_events | Engagement record |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_OUTREACH_SPOKE.md` |
| **PRD Version** | 4.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive BIT-qualified companies, contact lists, campaign requests |
| **COMPUTE** | M (Middle) | Campaign management, sequence execution, send scheduling |
| **GOVERN** | O (Egress) | Track engagement, route replies, signal to CL |

---

## Execution Flow

```
1. CAPTURE: Receive BIT-qualified company (score >= 50)
   ↓
2. CAPTURE: Receive contact list with verified emails
   ↓
3. COMPUTE: Create campaign with appropriate tier strategy
   ↓
4. COMPUTE: Build sequence steps
   ↓
5. COMPUTE: Schedule sends
   ↓
6. GOVERN: Execute sends via email provider
   ↓
7. GOVERN: Track opens, clicks, replies
   ↓
8. GOVERN: Signal engagement back to CL
```

---

## BIT Gate Enforcement

| BIT Score | BIT Tier | Action |
|-----------|----------|--------|
| >= 75 | PLATINUM/GOLD | Immediate outreach |
| 50-74 | SILVER | Nurture sequence |
| < 50 | BRONZE/NONE | No outreach (blocked) |

**CRITICAL**: Outreach CANNOT execute without BIT score >= 50.

---

## Campaign State Machine

```
draft → scheduled → active → completed
          ↓
        paused
          ↓
       cancelled
```

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `OUT-001` | CRITICAL | BIT score below threshold (blocked) |
| `OUT-002` | HIGH | No verified contacts available |
| `OUT-003` | MEDIUM | Email send failed |
| `OUT-004` | LOW | Engagement tracking delayed |
| `OUT-005` | HIGH | Campaign creation failed |

---

## Non-Goals

| Will NOT Do | Reason |
|-------------|--------|
| Mint company_id | CL owns identity |
| Infer company from domain | CL resolves identity |
| Create shadow companies | CL is authoritative |
| Decide lifecycle transitions | Outreach signals inform, CL decides |
| Promote to sales/client | CL makes promotion decisions |

---

## Correlation ID Enforcement

- `correlation_id` inherited from BIT Engine evaluation
- Propagated through all campaign operations
- Included in all engagement events
- Stored in `outreach.outreach_errors` for tracing

---

## Calendar Handoff

When meeting is booked:
1. Outreach generates calendar link (signed: sid + oid + sig + TTL)
2. Meeting booked webhook fires
3. Outreach signals CL
4. **OUTREACH ENDS HERE** - Sales Hub takes over

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_OUTREACH_SPOKE.md` |
| **Tables READ** | `outreach.outreach`, `outreach.company_target`, `outreach.people`, `outreach.bit_scores` |
| **Tables WRITTEN** | `outreach.campaigns`, `outreach.sequences`, `outreach.send_log`, `outreach.engagement_events`, `outreach.outreach_errors` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
