# Error Codes Registry

**Status:** AUTHORITATIVE
**Last Updated:** 2026-01-01

---

## Doctrine

> **A pipeline never "pauses." It either PASSes or FAILs.**
> **FAIL = emit error row + exit.**
> **Failures are WORK ITEMS, not states.**

### Enforcement Rules

1. Any pipeline failure **MUST** write to its hub's error table
2. Writing an error **TERMINATES** execution
3. Error rows **FREEZE spend** for that context
4. Resolution requires:
   - Manual intervention, **OR**
   - New `outreach_context_id`

**No silent failures. No retries inside the same context.**

---

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| `info` | Informational, non-blocking | Log and continue |
| `warning` | Needs attention, may proceed | Log, alert, continue cautiously |
| `blocking` | STOP execution immediately | Emit error, terminate, freeze spend |

---

## Company Target (CT) Error Codes

| Code | Description | Retry Allowed | Resolution Owner |
|------|-------------|---------------|------------------|
| `CT_MATCH_NO_COMPANY` | No company found for input record | No | Human (investigate source) |
| `CT_MATCH_AMBIGUOUS` | Multiple companies matched | No | Human (disambiguate) |
| `CT_MATCH_COLLISION` | Collision threshold exceeded | No | Human (verify match) |
| `CT_DOMAIN_UNRESOLVED` | Domain could not be resolved | Yes (new context) | Human/Agent |
| `CT_DOMAIN_DNS_FAIL` | DNS lookup failed | Yes (new context) | Agent (retry) |
| `CT_DOMAIN_MX_FAIL` | MX record lookup failed | Yes (new context) | Agent (retry) |
| `CT_PATTERN_NOT_FOUND` | No email pattern discovered | No | Human (manual research) |
| `CT_TIER2_EXHAUSTED` | All Tier-2 attempts used in context | No | New context required |
| `CT_PROVIDER_ERROR` | External provider returned error | Yes (new context) | Agent (retry) |
| `CT_LIFECYCLE_GATE_FAIL` | Company lifecycle < ACTIVE | No | Wait for lifecycle change |
| `CT_BIT_THRESHOLD_FAIL` | BIT score below threshold | No | Wait for BIT improvement |
| `CT_VERIFICATION_FAIL` | Pattern verification failed | No | Human (investigate) |
| `CT_SMTP_REJECT` | SMTP server rejected test | No | Human (investigate domain) |
| `CT_MISSING_SOV_ID` | No company_sov_id provided | No | Human (fix input) |
| `CT_MISSING_CONTEXT_ID` | No outreach_context_id provided | No | Human (fix pipeline) |
| `CT_NEON_WRITE_FAIL` | Database write failed | Yes (new context) | Agent (retry) |
| `CT_UNKNOWN_ERROR` | Unexpected error | No | Human (investigate) |

---

## People Intelligence (PI) Error Codes

| Code | Description | Retry Allowed | Resolution Owner |
|------|-------------|---------------|------------------|
| `PI_NO_PATTERN_AVAILABLE` | No verified pattern from Company Target | No | Resolve CT first |
| `PI_EMAIL_GEN_FAIL` | Email generation failed | No | Human (investigate) |
| `PI_INVALID_NAME` | Person name invalid/missing | No | Human (fix data) |
| `PI_SLOT_COLLISION` | Multiple people assigned same slot | No | Human (choose winner) |
| `PI_NO_SLOTS_DEFINED` | No slot types defined for company | No | Human (configure slots) |
| `PI_INVALID_TITLE` | Cannot classify title to slot | No | Human (update rules) |
| `PI_ENRICHMENT_NO_DEFICIT` | No measured slot deficit | No | N/A (correct behavior) |
| `PI_TIER2_EXHAUSTED` | All Tier-2 attempts used | No | New context required |
| `PI_LIFECYCLE_GATE_FAIL` | Lifecycle < TARGETABLE | No | Wait for lifecycle |
| `PI_OUTPUT_WRITE_FAIL` | CSV output failed | Yes (new context) | Agent (retry) |
| `PI_CSV_FORMAT_ERROR` | CSV formatting error | No | Human (fix format) |
| `PI_VERIFICATION_FAIL` | Email verification failed | No | Human (investigate) |
| `PI_MILLIONVERIFIER_ERROR` | MillionVerifier API error | Yes (new context) | Agent (retry) |
| `PI_BATCH_LIMIT_EXCEEDED` | Verification batch too large | No | Human (reduce batch) |
| `PI_MISSING_COMPANY_ANCHOR` | No company_sov_id for person | No | Human (fix data) |
| `PI_MISSING_CONTEXT_ID` | No outreach_context_id | No | Human (fix pipeline) |
| `PI_UNKNOWN_ERROR` | Unexpected error | No | Human (investigate) |

---

## DOL Filings (DOL) Error Codes

| Code | Description | Retry Allowed | Resolution Owner |
|------|-------------|---------------|------------------|
| `DOL_CSV_NOT_FOUND` | DOL CSV file not found | No | Human (locate file) |
| `DOL_CSV_FORMAT_ERROR` | CSV format invalid | No | Human (fix file) |
| `DOL_CSV_ENCODING_ERROR` | Character encoding error | No | Human (fix encoding) |
| `DOL_MISSING_EIN` | EIN field empty in filing | No | Skip record |
| `DOL_INVALID_EIN_FORMAT` | EIN format invalid | No | Skip record |
| `DOL_MISSING_REQUIRED_FIELD` | Required field missing | No | Skip record |
| `DOL_EIN_NO_MATCH` | EIN not found in company_master | No | N/A (expected for some) |
| `DOL_EIN_MULTIPLE_MATCH` | EIN matched multiple companies | No | Human (fix duplicates) |
| `DOL_LIFECYCLE_GATE_FAIL` | Company lifecycle < ACTIVE | No | Wait for lifecycle |
| `DOL_ATTACH_DUPLICATE` | Filing already attached | No | N/A (idempotent) |
| `DOL_NEON_WRITE_FAIL` | Database write failed | Yes (new context) | Agent (retry) |
| `DOL_MISSING_CONTEXT_ID` | No outreach_context_id | No | Human (fix pipeline) |
| `DOL_UNKNOWN_ERROR` | Unexpected error | No | Human (investigate) |

---

## Outreach Execution (OE) Error Codes

| Code | Description | Retry Allowed | Resolution Owner |
|------|-------------|---------------|------------------|
| `OE_MISSING_SOV_ID` | Golden Rule: No company_sov_id | No | Human (fix data) |
| `OE_MISSING_DOMAIN` | Golden Rule: No domain | No | Resolve CT first |
| `OE_MISSING_PATTERN` | Golden Rule: No email pattern | No | Resolve CT first |
| `OE_LIFECYCLE_GATE_FAIL` | Lifecycle < TARGETABLE | No | Wait for lifecycle |
| `OE_BIT_BELOW_THRESHOLD` | BIT score < 25 | No | Wait for BIT improvement |
| `OE_BIT_ENGINE_ERROR` | BIT engine error | Yes (new context) | Agent (retry) |
| `OE_NO_CONTACTS_AVAILABLE` | No slotted contacts | No | Resolve PI first |
| `OE_COOLING_OFF_ACTIVE` | Company in cooling-off period | No | Wait for cooldown |
| `OE_RATE_LIMIT_EXCEEDED` | Daily send limit reached | No | Wait for reset |
| `OE_CAMPAIGN_CREATE_FAIL` | Campaign creation failed | Yes (new context) | Agent (retry) |
| `OE_SEQUENCE_NOT_FOUND` | Email sequence not found | No | Human (configure) |
| `OE_SEND_FAIL` | Email send failed | Yes (new context) | Agent (retry) |
| `OE_BOUNCE_DETECTED` | Email bounced | No | Human (investigate) |
| `OE_SPAM_FLAGGED` | Email flagged as spam | No | Human (investigate) |
| `OE_MISSING_CONTEXT_ID` | No outreach_context_id | No | Human (fix pipeline) |
| `OE_UNKNOWN_ERROR` | Unexpected error | No | Human (investigate) |

---

## Blog Content (BC) Error Codes

| Code | Description | Retry Allowed | Resolution Owner |
|------|-------------|---------------|------------------|
| `BC_SOURCE_UNAVAILABLE` | Content source unavailable | Yes (new context) | Agent (retry) |
| `BC_PARSE_ERROR` | Content parsing failed | No | Human (investigate) |
| `BC_COMPANY_NOT_FOUND` | Company not found in CL | No | N/A (cannot mint) |
| `BC_AMBIGUOUS_COMPANY` | Multiple company matches | No | Human (disambiguate) |
| `BC_UNKNOWN_EVENT_TYPE` | Event type not recognized | No | Human (update rules) |
| `BC_CLASSIFICATION_ERROR` | Classification failed | No | Human (investigate) |
| `BC_LIFECYCLE_GATE_FAIL` | Lifecycle < ACTIVE | No | Wait for lifecycle |
| `BC_COMPANY_NOT_ACTIVE` | Company not in ACTIVE state | No | Wait for lifecycle |
| `BC_SIGNAL_EMIT_FAIL` | BIT signal emission failed | Yes (new context) | Agent (retry) |
| `BC_BIT_ENGINE_ERROR` | BIT engine error | Yes (new context) | Agent (retry) |
| `BC_MISSING_CONTEXT_ID` | No outreach_context_id | No | Human (fix pipeline) |
| `BC_UNKNOWN_ERROR` | Unexpected error | No | Human (investigate) |

---

## Resolution Workflow

### For Blocking Errors:

1. **Identify** — Query `outreach_errors.all_unresolved_errors`
2. **Triage** — Determine resolution owner (Human vs Agent vs Wait)
3. **Resolve** — Either:
   - Fix root cause + call `outreach_errors.resolve_error()`
   - Create new `outreach_context_id` and re-run
4. **Verify** — Confirm error is resolved and pipeline can proceed

### For Retryable Errors:

1. **Create new context** — `outreach_ctx.create_context()`
2. **Re-run pipeline** — With new context ID
3. **Monitor** — Check for same error recurring

---

## Cross-Hub Repair Rules

Some errors in one hub require resolution in another hub first. This defines the repair dependency chain.

### Repair Dependency Matrix

| Error in Hub | Requires Resolution in | Reason |
|--------------|----------------------|--------|
| `PI_NO_PATTERN_AVAILABLE` | Company Target | Pattern must be discovered first |
| `OE_MISSING_DOMAIN` | Company Target | Domain resolution is CT's job |
| `OE_MISSING_PATTERN` | Company Target | Pattern discovery is CT's job |
| `OE_NO_CONTACTS_AVAILABLE` | People Intelligence | Contacts must be slotted first |
| `OE_BIT_BELOW_THRESHOLD` | Company Target (BIT) | BIT score improvement needed |

### Cross-Hub Repair Constraints

1. **Upstream First** — Always resolve upstream hub errors before downstream
2. **No Sideways Repairs** — Hubs cannot fix each other's errors directly
3. **Context Isolation** — Each repair attempt requires new `outreach_context_id`
4. **Spend Inheritance** — New context starts fresh; old context spend is frozen

### Repair Order

```
Company Target (CT) errors → MUST resolve first
        ↓
People Intelligence (PI) errors → Resolve second
        ↓
Outreach Execution (OE) errors → Resolve last
```

DOL Filings and Blog Content operate independently (no cross-hub dependencies).

---

## UNKNOWN_ERROR Kill-Switch Doctrine

> **Any `*_UNKNOWN_ERROR` is an immediate FAIL with mandatory human investigation.**

### Kill-Switch Enforcement

| Error Code | Action | Consequence |
|------------|--------|-------------|
| `CT_UNKNOWN_ERROR` | Immediate FAIL | Context finalized, spend frozen |
| `PI_UNKNOWN_ERROR` | Immediate FAIL | Context finalized, spend frozen |
| `DOL_UNKNOWN_ERROR` | Immediate FAIL | Context finalized, spend frozen |
| `OE_UNKNOWN_ERROR` | Immediate FAIL | Context finalized, spend frozen |
| `BC_UNKNOWN_ERROR` | Immediate FAIL | Context finalized, spend frozen |

### Why Kill-Switch?

1. **Unknown errors indicate code bugs** — Not data issues, not transient failures
2. **Continuing is dangerous** — Could corrupt data or burn unlimited spend
3. **Immediate visibility** — Forces investigation, prevents silent failures
4. **Cost protection** — Frozen spend prevents runaway costs

### Response Protocol

1. **Alert** — `UNKNOWN_ERROR` triggers immediate alert (PagerDuty, Slack, etc.)
2. **Investigate** — Human must inspect `stack_trace` and `raw_input` columns
3. **Classify** — Either:
   - Add new error code if this is a known failure mode
   - Fix code bug if this is a code defect
4. **Document** — Update error_codes.md with new code if applicable
5. **Resume** — Create new context after fix deployed

---

## Monitoring Queries

```sql
-- All unresolved blocking errors
SELECT * FROM outreach_errors.all_unresolved_errors
WHERE severity = 'blocking'
ORDER BY created_at DESC;

-- Error summary by hub
SELECT * FROM outreach_errors.error_summary;

-- Check if context is frozen
SELECT outreach_errors.context_has_blocking_errors('your-context-id');
```
