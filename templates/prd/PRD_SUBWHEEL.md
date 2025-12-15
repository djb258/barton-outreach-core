# PRD — SubWheel

## 1. Overview

- **SubWheel Name:**
- **Parent Spoke:**
- **Parent Hub:** Company Hub
- **Owner:**
- **Version:**
- **Doctrine ID:** 04.04.02.04.XXXXX.###

---

## 2. Purpose

_What does this SubWheel do? What fractal capability does it provide?_

---

## 3. Hierarchy

```
Company Hub (Master Node)
    └── [Parent Spoke Name]
            └── [This SubWheel] ← YOU ARE HERE
                    ├── [SubSpoke 1]
                    ├── [SubSpoke 2]
                    └── [SubSpoke N]
```

---

## 4. SubWheel Hub (Central Node)

| Attribute | Value |
|-----------|-------|
| SubWheel Hub | [Name - e.g., MillionVerifier] |
| Core Metric | [What does this hub measure?] |
| Anchor Fields | [Required fields from parent spoke] |

---

## 5. SubSpokes

| SubSpoke Name | Purpose | Cost | Priority |
|---------------|---------|------|----------|
| | | FREE / $X | 1 |
| | | | 2 |
| | | | 3 |

---

## 6. Processing Order

_SubWheels process clockwise through their SubSpokes:_

1. **SubSpoke 1** (e.g., FREE tier) - _Attempt first_
2. **SubSpoke 2** (e.g., PAID tier) - _Fallback if FREE fails_
3. **SubSpoke N** - _Final attempt_
4. **Failure** → Route to parent spoke's failure handler

---

## 7. Input Contract (from Parent Spoke)

| Field | Type | Required | Example |
|-------|------|----------|---------|
| | | | |

---

## 8. Output Contract (to Parent Spoke)

| Field | Type | Example |
|-------|------|---------|
| success | boolean | true/false |
| result | object | Verification result |
| cost | string | "FREE" / "$0.003" |
| | | |

---

## 9. Cost Hierarchy

| Tier | SubSpoke | Cost per Item | When to Use |
|------|----------|---------------|-------------|
| 1 | | FREE | Always try first |
| 2 | | $X.XX | After FREE exhausted |
| 3 | | $X.XX | After Tier 2 fails |

---

## 10. Failure Modes

| Failure | Severity | Routes To | Remediation |
|---------|----------|-----------|-------------|
| All SubSpokes fail | HIGH | Parent Spoke Failure Handler | Manual review |
| Rate limit hit | MEDIUM | Retry queue | Exponential backoff |
| | | | |

---

## 11. Guard Rails

| Guard Rail | Type | Threshold | Action |
|------------|------|-----------|--------|
| Daily API calls | Rate Limit | 10,000 | Queue for next day |
| Cost per batch | Budget | $50 | Alert, require approval |
| | | | |

---

## 12. Testing

| Test Case | Expected Result |
|-----------|-----------------|
| Valid input, FREE tier succeeds | Return result, cost=FREE |
| FREE fails, PAID succeeds | Return result, cost=$X |
| All tiers fail | Route to failure handler |

---

## 13. Dependencies

- Parent Spoke: [Name]
- External APIs: [List]
- Cost tracking: [Where costs are logged]

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Spoke Owner | | |
| SubWheel Owner | | |
| Reviewer | | |
