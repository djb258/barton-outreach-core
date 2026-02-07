# HEIR Integration Guide

## Overview

HEIR (Hub Environment Identity Record) provides unique identity tracing for all operations in the Barton system. Combined with ORBT (Operate, Repair, Build, Train) for process lifecycle tracking, it enables complete end-to-end traceability.

## Quick Start

```python
from src.sys.heir import generate_unique_id, track_operation

# Generate a unique_id
unique_id = generate_unique_id()
# Output: outreach-core-001-20260207143022-a1b2c3d4

# Track an operation with both HEIR and ORBT
with track_operation("process_companies") as ctx:
    print(ctx.unique_id)    # HEIR identity
    print(ctx.process_id)   # ORBT process
    do_work(unique_id=ctx.unique_id)
```

## HEIR ID Formats

### Standard Format (Default)
```
<hub-id>-<timestamp>-<random_hex>
outreach-core-001-20260207143022-a1b2c3d4
```

### Formal Format
```
HEIR-<YYYY>-<MM>-<SYSTEM>-<MODE>-<VERSION>-<random_hex>
HEIR-2026-02-OUTREACH-PROD-V1-a1b2c3d4
```

## Core Components

### 1. HeirIdentity (src/sys/heir/heir_identity.py)

```python
from src.sys.heir import HeirIdentity, HeirFormat

heir = HeirIdentity()

# Generate standard ID
heir_id = heir.generate()

# Generate formal ID
heir_id = heir.generate(format=HeirFormat.FORMAL)

# Get current context
current = heir.current()
```

### 2. OrbtProcess (src/sys/heir/orbt_process.py)

```python
from src.sys.heir import OrbtProcess, OrbtLayer

orbt = OrbtProcess()

# Start a process
process = orbt.start_process(OrbtLayer.OPERATE)

# Log operations
orbt.log_operation("fetch_data", count=100)
orbt.log_operation("transform", success=True)

# End process
orbt.end_process(success=True)
```

### 3. Unified Tracker (src/sys/heir/tracking.py)

```python
from src.sys.heir import Tracker, track_operation, tracked

# Context manager
with track_operation("my_pipeline") as ctx:
    result = do_work(
        unique_id=ctx.unique_id,
        process_id=ctx.process_id
    )

# Decorator
@tracked("my_function")
def my_function():
    ctx = get_tracking_context()
    return ctx.unique_id
```

## ORBT Layers

| Layer | Purpose | When to Use |
|-------|---------|-------------|
| OPERATE | Normal execution | Default for all operations |
| REPAIR | Error recovery | When fixing failed processes |
| BUILD | Creation/modification | Schema changes, new entities |
| TRAIN | Learning/optimization | ML training, parameter tuning |

## Integration Patterns

### Pipeline Integration

```python
from src.sys.heir import track_operation, OrbtLayer

def run_pipeline():
    with track_operation("ceo_pipeline", layer=OrbtLayer.OPERATE) as ctx:
        # Phase 1
        companies = fetch_companies(unique_id=ctx.unique_id)

        # Phase 2
        for company in companies:
            process_company(company, **ctx.as_params())

        return {"processed": len(companies)}
```

### Database Operations

```python
def insert_record(data, unique_id=None, process_id=None):
    unique_id = unique_id or require_unique_id()

    cursor.execute("""
        INSERT INTO people.people_master
        (unique_id, company_unique_id, ...)
        VALUES (%s, %s, ...)
    """, (generate_barton_id(), data['company_id'], ...))
```

### Error Correlation

```python
from src.sys.heir import get_tracking_context

def log_error(error):
    ctx = get_tracking_context()
    cursor.execute("""
        INSERT INTO shq_error_log
        (unique_id, process_id, error_message, ...)
        VALUES (%s, %s, %s, ...)
    """, (ctx.unique_id, ctx.process_id, str(error), ...))
```

## Configuration

HEIR reads configuration from `heir.doctrine.yaml`:

```yaml
hub:
  name: "outreach-core"
  id: "outreach-core-001"
  cc_layer_effective: "CC-02"

process:
  id_pattern: "outreach-core-001-${TIMESTAMP}-${RANDOM_HEX}"

orbt:
  layers: [OPERATE, REPAIR, BUILD, TRAIN]
  default_layer: "OPERATE"
  process_id_format: "PRC-OUTREACH-${EPOCH}"
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BARTON_ENV` | Mode detection (prod/dev/test) | prod |
| `BARTON_SYSTEM` | System name for ORBT | OUTREACH |

## Best Practices

1. **Always use tracking context** for database operations
2. **Propagate unique_id** across function calls
3. **Use decorators** for pipeline functions
4. **Log operations** within processes for auditability
5. **End processes explicitly** or use context managers

## Related Documentation

- `heir.doctrine.yaml` - Configuration file
- `src/sys/heir/__init__.py` - Module exports
- `docs/adr/ADR-014_BIT_Engine_Architecture.md` - BIT integration
