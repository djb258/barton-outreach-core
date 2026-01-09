# Ops Directory — CC-04

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-04 (Process)
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Definition

Operations are runtime execution instances. They operate at CC-04 and:
- Execute within a context (CC-03)
- Are bound by PIDs (Process IDs)
- Cannot write to CC-03 or above

## Contained Operations

| Directory | Purpose | PID Scope |
|-----------|---------|-----------|
| cc_enforcement/ | CC doctrine enforcement | Per-run |
| enforcement/ | Doctrine enforcement checks | Per-run |
| validation/ | Runtime validation | Per-record |
| master_error_log/ | Error logging | Append-only |
| phase_registry/ | Phase execution tracking | Per-pipeline |
| migrations/ | Database migrations | Per-deploy |
| neon/ | Neon database operations | Per-query |
| scripts/ | Operational scripts | Per-execution |
| tests/ | Test execution | Per-suite |
| tooling/ | Operational tooling | Per-run |
| tools/ | CLI tools | Per-invocation |
| infra/ | Infrastructure management | Per-deploy |
| monitoring/grafana/ | Monitoring dashboards | N/A (config) |
| diagnostics/ | Runtime diagnostics | Per-check |

## Rules

1. **PID required** — Every operation has a unique PID
2. **No upward writes** — Cannot modify CC-03 or above
3. **Read-only context** — May read context, not write
4. **Immutable errors** — Error log is append-only

## PID Contents

Each Process ID carries:
- Executor identity
- Version identifier
- Timestamp of mint

## Write Permissions

| Target | Permitted? | Notes |
|--------|------------|-------|
| CC-01 | DENIED | External |
| CC-02 | DENIED | Hub owned |
| CC-03 | DENIED | Read only |
| CC-04 | PERMITTED | Within PID scope |
