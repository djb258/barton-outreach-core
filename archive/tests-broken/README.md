# Broken Test Files

**Archived**: 2026-02-20
**Reason**: These test files import modules that were never implemented. They are PRD-based test scaffolds that fail with ImportError on every run.

## Files

| Test File | Missing Module | Notes |
|-----------|---------------|-------|
| `test_phases.py` (spokes/people) | `spokes.people.phases.*`, `spokes.people.movement_engine` | People pipeline phases never built as spokes |
| `test_dol_spoke.py` (spokes/dol) | `spokes.dol.dol_spoke`, `wheel.bicycle_wheel`, `wheel.wheel_result` | DOL spoke + wheel framework never implemented |
| `test_cl_gate.py` (hub/company) | `hubs/company-target/imo/middle/utils/cl_gate.py` | Utils directory never created |
| `test_pipeline_context_enforcement.py` | `hubs/company-target/imo/middle/utils/context_manager.py` | Utils directory never created |
| `test_tier2_kill_switch.py` | `hubs/company-target/imo/middle/utils/context_manager.py` | Utils directory never created |

## Working Tests (still in `tests/`)

- `tests/test_doctrine_enforcement.py` — Enforcement module tests (PASS)
- `tests/ops/test_master_error_log.py` — Error log tests (PASS)
- `tests/guards/test_no_illegal_writers.py` — Hub writer guard (PASS)
- `tests/hubs/test_hub_status_truthfulness.py` — Hub status checks (PASS)
- `tests/hub/company/test_phases.py` — Company phase tests (partial match issues)
