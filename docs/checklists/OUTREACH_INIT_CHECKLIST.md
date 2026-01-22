# Outreach Init Checklist

## Version: 1.0.0
## Last Updated: 2026-01-22
## Doctrine: CL Authority Registry + Outreach Operational Spine
## ADR: ADR-011_CL_Authority_Registry_Outreach_Spine.md

---

## Pre-Init Verification

- [ ] **Verify sovereign_company_id exists in CL**
  ```sql
  SELECT sovereign_company_id, outreach_id
  FROM cl.company_identity
  WHERE sovereign_company_id = $sid;
  ```

- [ ] **Verify outreach_id is NULL (not already claimed)**
  ```sql
  -- MUST return NULL
  SELECT outreach_id FROM cl.company_identity
  WHERE sovereign_company_id = $sid;
  ```

- [ ] **Verify identity_status = 'PASS'** (if applicable)

---

## Outreach Init Steps

### Step 1: Mint outreach_id in Operational Spine

- [ ] **Generate new outreach_id** (UUID or Barton ID format)
- [ ] **Insert into outreach.outreach**
  ```sql
  INSERT INTO outreach.outreach (outreach_id, sovereign_company_id, status, created_at)
  VALUES ($new_outreach_id, $sid, 'INIT', NOW());
  ```
- [ ] **Verify insert succeeded**

### Step 2: Register in CL Authority Registry

- [ ] **Execute guarded UPDATE**
  ```sql
  UPDATE cl.company_identity
  SET outreach_id = $new_outreach_id
  WHERE sovereign_company_id = $sid
    AND outreach_id IS NULL;
  ```

- [ ] **Check affected_rows == 1**
  - If affected_rows != 1 → ROLLBACK + HARD_FAIL
  - Error: "Outreach ID already claimed or invalid SID"

- [ ] **Log success to audit trail**

### Step 3: Post-Init Verification

- [ ] **Verify CL registration**
  ```sql
  SELECT outreach_id FROM cl.company_identity
  WHERE sovereign_company_id = $sid;
  -- MUST return $new_outreach_id
  ```

- [ ] **Verify spine record**
  ```sql
  SELECT * FROM outreach.outreach
  WHERE outreach_id = $new_outreach_id;
  ```

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| affected_rows = 0 | SID not found or already claimed | ROLLBACK, log error, HARD_FAIL |
| affected_rows > 1 | Duplicate SIDs (data integrity issue) | ROLLBACK, ALERT, HARD_FAIL |
| Spine insert fails | DB constraint or connection | ROLLBACK, retry with backoff |

---

## NEVER DO

- [ ] **NEVER write outreach_id to CL more than ONCE**
- [ ] **NEVER skip the affected_rows check**
- [ ] **NEVER write workflow state to CL** (CL = identity pointers only)
- [ ] **NEVER mint sovereign_company_id** (CL owns this)
- [ ] **NEVER mint sales_process_id or client_id** (those hubs own them)

---

## Calendar Link Generation (Post-Init)

After successful init, generate calendar link:

- [ ] **Build signed params**
  - `sid` = sovereign_company_id
  - `oid` = outreach_id
  - `sig` = HMAC signature
  - `exp` = TTL expiration

- [ ] **Generate URL**
  ```
  https://calendar.example.com/book?sid=...&oid=...&sig=...&exp=...
  ```

- [ ] **Store link in outreach record** (optional)

---

## Handoff Checklist (Meeting Booked)

When meeting is booked:

- [ ] **Webhook receives booking event**
- [ ] **Validate signature** (anti-replay)
- [ ] **Extract sid + oid from params**
- [ ] **Emit handoff event to Sales Init worker**
- [ ] **Outreach responsibility ENDS here**

Sales Init worker will:
- Snapshot Outreach data
- Mint sales_process_id
- Write sales_process_id to CL (ONCE)

---

## Compliance Verification

| Check | Status |
|-------|--------|
| CL = identity pointers only | [ ] |
| outreach.outreach = operational spine | [ ] |
| WRITE-ONCE enforcement | [ ] |
| affected_rows validation | [ ] |
| Webhook handoff (not direct invocation) | [ ] |

---

**Checklist Version:** 1.0.0
**Last Updated:** 2026-01-22
**Doctrine:** CL Authority Registry + Outreach Operational Spine
