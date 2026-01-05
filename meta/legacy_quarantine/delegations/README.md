# Delegation Artifacts

This directory contains delegation artifacts that grant CC layer authority to this repository.

## Current Status

| Field | Value |
|-------|-------|
| **Claimed CC Layer** | CC-02 |
| **Effective CC Layer** | CC-03 |
| **Status** | PENDING DELEGATION |

## Required Delegation

To claim CC-02 authority, this repository requires a delegation artifact from:

- **Upstream Hub**: `company-lifecycle-cl-001` (CC-02)
- **Or Sovereign**: `barton-enterprises` (CC-01)

## Delegation Artifact Format

```yaml
# outreach-core-001.yaml
delegation:
  # Identity
  id: "DEL-2026-001"
  version: "1.0.0"

  # Delegator (upstream authority)
  delegator:
    id: "company-lifecycle-cl-001"
    cc_layer: "CC-02"
    sovereign: "barton-enterprises"

  # Delegatee (this hub)
  delegatee:
    id: "outreach-core-001"
    name: "outreach-core"
    repository: "barton-outreach-core"

  # Authority granted
  grant:
    cc_layer: "CC-02"
    scope: "Marketing intelligence and outreach execution"
    constraints:
      - "Must reference company_unique_id from CL"
      - "No identity minting"
      - "Read-only access to cl.* schema"
      - "No upward writes to CC-01"

  # Validity
  issued_at: "2026-01-05T00:00:00Z"
  expires_at: null  # null = no expiration
  revocable: true

  # Signature (required for validation)
  signature:
    algorithm: "sha256"
    signer: "company-lifecycle-cl-001"
    value: "<signature-hash>"

  # Audit trail
  audit:
    adr_reference: "ADR-CL-001"
    approval_date: "2026-01-05"
    approved_by: "sovereign-operator"
```

## How to Obtain Delegation

1. **Request delegation** from upstream hub owner (company-lifecycle-cl)
2. **Upstream creates** delegation artifact with signature
3. **Place artifact** in this directory as `outreach-core-001.yaml`
4. **Update heir.doctrine.yaml**:
   ```yaml
   authority:
     delegation:
       artifact_ref: "delegations/outreach-core-001.yaml"
   ```
5. **Run validation**: `python ops/enforcement/authority_gate.py`
6. **Commit changes** and push

## Validation

Run the authority gate to validate delegation:

```bash
python ops/enforcement/authority_gate.py
```

Expected output with valid delegation:

```
======================================================================
CANONICAL AUTHORITY GATE — VALIDATION REPORT
======================================================================
Claimed CC Layer:   CC-02
Effective CC Layer: CC-02
Delegation Status:  Valid delegation from upstream authority
----------------------------------------------------------------------
✅ AUTHORITY GATE: PASSED
======================================================================
```

## Without Delegation

Without a valid delegation artifact, this repository operates at CC-03:

```
======================================================================
CANONICAL AUTHORITY GATE — VALIDATION REPORT
======================================================================
Claimed CC Layer:   CC-02
Effective CC Layer: CC-03
Delegation Status:  DOWNGRADED: No delegation artifact reference provided
----------------------------------------------------------------------
❌ AUTHORITY GATE: FAILED

To resolve:
1. Obtain delegation artifact from upstream CC-02 or CC-01
2. Place artifact at path specified in heir.doctrine.yaml
3. Update authority.delegation.artifact_ref with path
4. Re-run validation
======================================================================
```

## Doctrine Reference

- **Rule**: `claimed_cc_layer ≠ effective_cc_layer`
- **Enforcement**: CC-02 requires external delegation
- **Fail-closed**: Absence of proof = failure
- **No self-declaration**: CC-02 cannot be claimed without external warrant
