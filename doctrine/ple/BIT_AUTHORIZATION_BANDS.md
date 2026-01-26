# BIT Authorization Bands

**Authority:** ADR-017
**Status:** ACTIVE
**Version:** 1.0

---

## Overview

BIT (Buyer Intent Tool) is an **authorization index**, not a lead score. It determines what outreach actions are **permitted** for a given company based on detected organizational movement.

---

## Band Definitions

| Band | Range | Name | Description |
|------|-------|------|-------------|
| 0 | 0-9 | SILENT | No action permitted. Company has no detected movement. |
| 1 | 10-24 | WATCH | Internal flag only. No external contact permitted. |
| 2 | 25-39 | EXPLORATORY | 1 educational message per 60 days. No personalization. No product mention. |
| 3 | 40-59 | TARGETED | Persona-specific email. 3-touch max. **Proof line REQUIRED.** |
| 4 | 60-79 | ENGAGED | Phone (warm) permitted. 5-touch max. **Multi-source proof REQUIRED.** |
| 5 | 80+ | DIRECT | Direct contact. Meeting request. **Full-chain proof REQUIRED.** |

---

## Permitted Actions by Band

| Action | Band 0 | Band 1 | Band 2 | Band 3 | Band 4 | Band 5 |
|--------|--------|--------|--------|--------|--------|--------|
| Internal flag | - | YES | YES | YES | YES | YES |
| Educational content | - | - | YES | YES | YES | YES |
| Persona email | - | - | - | YES | YES | YES |
| Phone (warm) | - | - | - | - | YES | YES |
| Phone (cold) | - | - | - | - | - | YES |
| Meeting request | - | - | - | - | - | YES |

---

## Band Constraints

### Band 0: SILENT
- No external action of any kind
- Company should not appear in any outreach list
- Internal research permitted

### Band 1: WATCH
- Internal flagging and monitoring only
- No external contact
- No email, no phone, no LinkedIn
- Useful for companies with blog-only signals

### Band 2: EXPLORATORY
- Maximum 1 message per 60 days
- Content must be educational (industry insights, research)
- No personalization beyond company name
- No product mention
- No call-to-action beyond "learn more"

### Band 3: TARGETED
- Maximum 3 touches total
- Persona-specific messaging allowed
- **Proof line REQUIRED** (single-source)
- Product mention allowed in context of detected pressure
- No pricing discussion
- No urgency language

### Band 4: ENGAGED
- Maximum 5 touches total
- Phone calls (warm) permitted
- **Multi-source proof REQUIRED**
- Deeper product discussion allowed
- No unsolicited pricing
- Limited urgency language permitted

### Band 5: DIRECT
- Full contact methods available
- Meeting requests permitted
- **Full-chain proof REQUIRED**
- Pricing discussion after discovery
- Urgency language permitted if evidence-based

---

## Band Calculation Rules

### Domain Trust Hierarchy

| Domain | Trust Level | Max Solo Contribution |
|--------|-------------|----------------------|
| STRUCTURAL_PRESSURE (DOL) | Highest | No cap |
| DECISION_SURFACE (People) | High | Band 4 |
| NARRATIVE_VOLATILITY (Blog) | Lowest | Band 1 |

### Convergence Rules

1. **Blog alone = max Band 1**
   - Blog signals can never independently justify contact
   - Blog amplifies other domains but cannot stand alone

2. **No DOL = max Band 2**
   - Without structural pressure, no authority for targeted outreach
   - DOL provides the "gravity" that authorizes action

3. **Two domains aligned = watch/act**
   - When two domains point to same pressure class, Band 2-4 possible

4. **Three domains aligned = strong phase**
   - Full convergence enables Band 4-5

### Stasis Suppression

If a company shows no movement in a domain for 3+ years, that domain's signals are suppressed for that pressure class.

Example: If DOL shows same broker for 3+ years, VENDOR_DISSATISFACTION signals from DOL are suppressed.

---

## Band Transitions

Bands can only change based on:
1. New movement event detected
2. Movement event expires
3. Convergence state changes

Bands **cannot** change based on:
- Manual override (use kill switches instead)
- Sales request
- Time passage alone

---

## Relationship to Legacy Tiers

| Legacy Tier | Approximate Band | Key Difference |
|-------------|------------------|----------------|
| COLD | Band 0-1 | Legacy allowed educational at COLD |
| WARM | Band 2 | Legacy had no proof requirement |
| HOT | Band 3-4 | Legacy had no DOL requirement |
| BURNING | Band 5 | Legacy had no full-chain proof |

---

## Enforcement

All outreach systems MUST:
1. Check band before any action
2. Verify action is permitted at current band
3. Require proof at Band 3+
4. Log authorization decision

Violation = HARD_FAIL. No fallback. No workaround.

---

**Document Control:**
| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Authority | ADR-017 |
| Status | ACTIVE |
