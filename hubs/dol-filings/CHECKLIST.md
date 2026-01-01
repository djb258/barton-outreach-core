# DOL Filings — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] Filings attached to existing companies only
- [ ] No company minting from DOL data

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = ACTIVE
- [ ] Gate enforced before filing attachment

---

## EIN Matching Compliance

- [ ] Exact EIN match only
- [ ] No fuzzy matching
- [ ] No retries on mismatch
- [ ] Unmatched filings logged but not attached

---

## Data Compliance

- [ ] Bulk CSV processing only
- [ ] No paid enrichment tools
- [ ] Form 5500, 5500-SF, Schedule A supported
- [ ] Filing match rate tracked

---

## Signal Compliance

- [ ] FORM_5500_FILED signal emitted correctly
- [ ] LARGE_PLAN signal for >= 100 participants
- [ ] BROKER_CHANGE signal for year-over-year changes

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
