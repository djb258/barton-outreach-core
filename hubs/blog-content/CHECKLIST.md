# Blog Content — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] Cannot mint new companies
- [ ] Cannot revive dead companies
- [ ] Company Lifecycle read-only

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = ACTIVE
- [ ] Gate enforced before signal emission
- [ ] Lifecycle state never modified by this hub

---

## Signal-Only Compliance

- [ ] BIT modulation only
- [ ] Cannot trigger enrichment
- [ ] No paid tools used
- [ ] Signals emitted to BIT engine only

---

## Signal Types

- [ ] FUNDING_EVENT (+15.0) — configured correctly
- [ ] ACQUISITION (+12.0) — configured correctly
- [ ] LEADERSHIP_CHANGE (+8.0) — configured correctly
- [ ] EXPANSION (+7.0) — configured correctly
- [ ] PRODUCT_LAUNCH (+5.0) — configured correctly
- [ ] PARTNERSHIP (+5.0) — configured correctly
- [ ] LAYOFF (-3.0) — configured correctly
- [ ] NEGATIVE_NEWS (-5.0) — configured correctly

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
