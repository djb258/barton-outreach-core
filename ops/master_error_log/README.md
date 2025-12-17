# Master Error Log (Cross-Cutting)

**PRD Reference**: `docs/prd/PRD_MASTER_ERROR_LOG.md`

## Purpose

Centralized, append-only error logging for all hub and spoke operations.

## Directory Structure

```
ops/master_error_log/
├── README.md
├── master_error_emitter.py # Error emission interface
└── migrations/
    ├── 002_create_master_error_log.sql
    └── 003_enforce_immutability.sql
```

## Key Features

- **Append-only**: Records cannot be modified or deleted
- **Immutability enforced**: Database triggers prevent UPDATE/DELETE
- **Structured format**: JSON payloads with process_id tracking
- **Cross-spoke visibility**: All hubs/spokes emit to same log

## Usage

```python
from ops.master_error_log.master_error_emitter import emit_error

emit_error(
    process_id="PRC-2025-12-001",
    error_type="COMPANY_MATCH_FAILED",
    payload={"company_name": "Acme Corp", "reason": "No domain found"},
    severity="WARNING"
)
```
