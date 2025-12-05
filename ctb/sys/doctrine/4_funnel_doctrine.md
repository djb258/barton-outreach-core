# 4-Funnel GTM System Doctrine

## Version: 1.0.0
## Last Updated: 2025-12-05

---

## Overview

The 4-Funnel GTM (Go-To-Market) System defines how prospects move through the sales lifecycle from initial contact to signed client. Each funnel represents a distinct universe of prospects with specific engagement patterns, triggers, and outreach strategies.

This doctrine establishes the canonical definitions, lifecycle states, and movement rules that govern all outreach operations.

---

## The 4 Funnels

### Funnel 1: Cold Universe

**Definition**: Prospects with no prior engagement. These are net-new contacts sourced from enrichment pipelines, purchased lists, or inbound lead capture with zero historical interaction.

**Characteristics**:
- No email opens
- No email clicks
- No replies
- No meeting history
- No TalentFlow signals
- BIT score = 0 or minimal

**Entry Criteria**:
- New record enters system via intake
- Passed Phase 1-4 enrichment (Company Identity Pipeline)
- Has valid email address
- Not on suppression list

**Exit Criteria**:
- Any engagement signal (open, click, reply)
- TalentFlow movement detected
- BIT score threshold crossed

**Outreach Strategy**:
- Cold email sequences
- Volume-based approach
- Pattern testing
- A/B subject line testing

---

### Funnel 2: TalentFlow Universe

**Definition**: Prospects identified through job movement signals. These contacts have recently changed employers, received promotions, or been detected moving between companies in our target market.

**Characteristics**:
- TalentFlow signal detected
- Recent employer change (< 90 days)
- New role at target company
- May or may not have prior engagement

**Entry Criteria**:
- TalentFlow Phase 0 detects movement event
- Movement verified against company_master
- Contact enriched with new employer data
- Movement type classified (job_change, promotion, lateral)

**Exit Criteria**:
- Reply received (promotes to WARM or TALENTFLOW_WARM)
- Appointment booked
- Movement age > 90 days (recycles to Cold or Re-Engagement)

**Outreach Strategy**:
- Personalized congratulatory messaging
- Role-specific value propositions
- Accelerated sequence timing
- Priority placement in outreach queue

---

### Funnel 3: Warm Universe (Engaged)

**Definition**: Prospects who have demonstrated engagement through behavioral signals but have not yet booked an appointment. These contacts are actively considering or aware of our outreach.

**Characteristics**:
- Has opened emails (3+ opens threshold)
- Has clicked links (2+ clicks threshold)
- Has replied to emails
- Active engagement within last 30 days
- BIT score above warm threshold

**Entry Criteria**:
- 3+ email opens from same contact
- 2+ link clicks from same contact
- Any email reply (immediate promotion)
- BIT score >= WARM_THRESHOLD

**Exit Criteria**:
- Appointment booked (promotes to APPOINTMENT)
- 30+ days no engagement (demotes to Re-Engagement)
- Unsubscribe or hard bounce (exits system)

**Outreach Strategy**:
- Nurture sequences
- Value-driven content
- Case study sharing
- Soft CTAs leading to meeting requests
- Higher touch frequency

---

### Funnel 4: Re-Engagement Universe (Past Meetings)

**Definition**: Prospects who previously had meetings or significant engagement but did not convert, OR warm prospects who have gone cold. This funnel manages cyclical re-engagement on a 60-90 day timer.

**Characteristics**:
- Past meeting recorded (no close)
- Previously warm, now inactive 30+ days
- Historical engagement present
- Not marked as lost/disqualified

**Entry Criteria**:
- Past meeting with no signed contract
- Warm prospect with 30+ days inactivity
- Re-engagement timer triggered (60-90 day cycle)
- Not on do-not-contact list

**Exit Criteria**:
- Re-engagement successful (new reply/meeting)
- Marked as permanently lost
- Contact requests removal
- Re-engagement attempts exhausted (3 cycles max)

**Outreach Strategy**:
- "Checking back in" messaging
- New value proposition angles
- Industry news hooks
- Referral requests
- Extended timing between touches

---

## Funnel Hierarchy

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   CLIENT                            │
                    │              (Signed Contract)                      │
                    └───────────────────────▲─────────────────────────────┘
                                            │
                                    EVENT_CLIENT_SIGNED
                                            │
                    ┌───────────────────────┴─────────────────────────────┐
                    │                  APPOINTMENT                         │
                    │               (Meeting Booked)                       │
                    └───────────────────────▲─────────────────────────────┘
                                            │
                                    EVENT_APPOINTMENT
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│   Funnel 3        │           │   Funnel 2        │           │   Funnel 4        │
│   WARM UNIVERSE   │◀─────────▶│   TALENTFLOW      │◀─────────▶│   RE-ENGAGEMENT   │
│   (Engaged)       │           │   UNIVERSE        │           │   UNIVERSE        │
└─────────▲─────────┘           └─────────▲─────────┘           └─────────▲─────────┘
          │                               │                               │
    EVENT_REPLY                   EVENT_TALENTFLOW              EVENT_REENGAGEMENT
    EVENT_CLICKS_X2                    _MOVE                       _TRIGGER
    EVENT_OPENS_X3                                                        │
          │                               │                               │
          └───────────────────────────────┼───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                   Funnel 1                          │
                    │                COLD UNIVERSE                        │
                    │             (No Engagement)                         │
                    └─────────────────────────────────────────────────────┘
```

---

## Funnel Membership Rules

### Exclusive Membership
A contact can only belong to ONE funnel at any given time. Funnel membership is determined by the contact's current lifecycle state.

### Priority Resolution
When multiple funnel criteria are met simultaneously:

1. **APPOINTMENT** state always wins (highest priority)
2. **TalentFlow signals** take precedence over engagement signals
3. **Engagement signals** take precedence over re-engagement
4. **Re-Engagement** takes precedence over Cold

### State-to-Funnel Mapping

| Lifecycle State | Funnel Membership |
|-----------------|-------------------|
| SUSPECT | Funnel 1: Cold Universe |
| WARM | Funnel 3: Warm Universe |
| TALENTFLOW_WARM | Funnel 2: TalentFlow Universe |
| APPOINTMENT | N/A - In sales pipeline |
| CLIENT | N/A - Customer |

---

## Funnel Metrics

### Funnel 1: Cold Universe
- **Volume**: Primary metric (largest pool)
- **Conversion Rate**: % moving to Warm/TalentFlow
- **Bounce Rate**: Hard + soft bounces
- **Unsubscribe Rate**: Opt-out tracking

### Funnel 2: TalentFlow Universe
- **Signal Freshness**: Days since movement detected
- **Conversion Rate**: % moving to Appointment
- **Response Rate**: Reply rate on TalentFlow sequences
- **Movement Accuracy**: Verified vs. false positive rate

### Funnel 3: Warm Universe
- **Engagement Depth**: Opens, clicks, replies per contact
- **Time in Funnel**: Days from first engagement to appointment
- **Conversion Rate**: % booking appointments
- **Drop-off Rate**: % going inactive (to Re-Engagement)

### Funnel 4: Re-Engagement Universe
- **Cycle Count**: Number of re-engagement attempts
- **Recovery Rate**: % returning to Warm
- **Exhaustion Rate**: % reaching max attempts
- **Time Between Cycles**: 60-90 day measurement

---

## Cross-References

- **State Machine**: See `funnel_state_machine.md`
- **Movement Rules**: See `funnel_rules.md`
- **BIT Scoring**: See `bit_scoring_doctrine.md` (future)
- **TalentFlow**: See `talentflow_doctrine.md` (future)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | System | Initial doctrine creation |
