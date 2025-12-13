# Master Failure Hub - Centralized Error Architecture

> **"Failures are spokes, not exceptions."**
> -- Bicycle Wheel Doctrine

---

## The Master Failure Hub Concept

```
                              FAILURE PROPAGATION FLOW

     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
     │  SUB-HUB        │     │  SUB-HUB        │     │  SUB-HUB        │
     │  FAILURE        │     │  FAILURE        │     │  FAILURE        │
     └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                                      ▼
     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
     │  DOMAIN HUB     │     │  DOMAIN HUB     │     │  DOMAIN HUB     │
     │  FAILURE        │     │  FAILURE        │     │  FAILURE        │
     └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                                      ▼
                    ╔═════════════════════════════════════╗
                    ║                                     ║
                    ║      MASTER FAILURE HUB             ║
                    ║      (shq_error_log)                ║
                    ║                                     ║
                    ║   ┌───────────────────────────┐     ║
                    ║   │   AGGREGATION ENGINE      │     ║
                    ║   │   • Classify severity     │     ║
                    ║   │   • Track resolution      │     ║
                    ║   │   • Trigger auto-repair   │     ║
                    ║   │   • Feed diagnostics      │     ║
                    ║   └───────────────────────────┘     ║
                    ║                                     ║
                    ╚═════════════════════════════════════╝
                                      │
                                      │ Feeds health metrics
                                      ▼
                    ╔═════════════════════════════════════╗
                    ║           BIT ENGINE                ║
                    ║        (Core Metric)                ║
                    ╚═════════════════════════════════════╝
```

---

## Strategy: Distributed Centralized Reporting

Each hub in the Bicycle Wheel architecture tracks its own local failures, but ALL failures bubble up to the Master Failure Hub. This provides:

| Benefit | Description |
|---------|-------------|
| **Local Autonomy** | Each hub handles its own error recovery |
| **Global Visibility** | Central dashboard sees all failures |
| **Pattern Detection** | Identify systemic issues across hubs |
| **Auto-Repair Triggers** | Centralized hooks for self-healing |
| **Health Aggregation** | Feed failure metrics into BIT Engine |

---

## Master Failure Hub Table: `shq_error_log`

### Schema

```sql
CREATE TABLE public.shq_error_log (
    error_id           TEXT PRIMARY KEY,          -- Barton ID: 04.04.02.04.40000.###
    source_hub         TEXT NOT NULL,             -- Which hub generated the failure
    sub_hub            TEXT,                      -- Which sub-hub if applicable
    error_code         TEXT NOT NULL,             -- Standardized error code
    error_message      TEXT NOT NULL,             -- Human-readable description
    severity           TEXT NOT NULL,             -- info, warning, error, critical
    component          TEXT,                      -- Pipeline phase or module
    stack_trace        TEXT,                      -- Full stack trace if available
    user_id            TEXT,                      -- User context if applicable
    request_id         TEXT,                      -- Request/transaction ID
    resolution_status  TEXT DEFAULT 'open',       -- open, investigating, resolved, wont_fix
    auto_repair_triggered BOOLEAN DEFAULT FALSE,  -- Was auto-repair attempted?
    created_at         TIMESTAMP DEFAULT NOW(),
    updated_at         TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX idx_error_severity ON public.shq_error_log(severity);
CREATE INDEX idx_error_source_hub ON public.shq_error_log(source_hub);
CREATE INDEX idx_error_resolution ON public.shq_error_log(resolution_status);
CREATE INDEX idx_error_created ON public.shq_error_log(created_at DESC);
```

---

## Failure Spokes Registry

Each hub and sub-hub has its own failure spoke. These are NOT exceptions -- they are first-class citizens with their own tables and resolution paths.

### Company Hub Failures

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMPANY HUB FAILURE SPOKES                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────────────┐       ┌───────────────────────┐            │
│   │ FAILED_COMPANY_MATCH  │       │ FAILED_LOW_CONFIDENCE │            │
│   ├───────────────────────┤       ├───────────────────────┤            │
│   │ Phase: 2              │       │ Phase: 3              │            │
│   │ Trigger: Fuzzy < 80%  │       │ Trigger: Fuzzy 70-79% │            │
│   │ Resolution:           │       │ Resolution:           │            │
│   │ • Confirm             │       │ • Manual confirm      │            │
│   │ • Reject              │       │ • Reject              │            │
│   │ • Remap               │       │                       │            │
│   └───────────────────────┘       └───────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### People Node Failures

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PEOPLE NODE FAILURE SPOKES                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────────────┐       ┌───────────────────────┐            │
│   │ FAILED_SLOT_ASSIGNMENT│       │ FAILED_NO_PATTERN     │            │
│   ├───────────────────────┤       ├───────────────────────┤            │
│   │ Phase: 3              │       │ Phase: 4              │            │
│   │ Trigger: Lost         │       │ Trigger: No domain    │            │
│   │   seniority           │       │   or pattern          │            │
│   │ Resolution:           │       │ Resolution:           │            │
│   │ • Manual override     │       │ • Add manually        │            │
│   │ • Wait for vacancy    │       │ • Firecrawl enrich    │            │
│   └───────────────────────┘       └───────────────────────┘            │
│                                                                         │
│   ┌───────────────────────┐                                            │
│   │ FAILED_EMAIL_VERIFY   │                                            │
│   ├───────────────────────┤                                            │
│   │ Phase: 5              │                                            │
│   │ Trigger: MV invalid   │                                            │
│   │ Resolution:           │                                            │
│   │ • Try alternate       │                                            │
│   │ • Mark unverifiable   │                                            │
│   └───────────────────────┘                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Propagation Rules

### On Failure Event

```python
def on_failure(failure_event):
    """
    Failure propagation follows the spoke hierarchy:
    sub_hub -> hub -> central_hub -> master_failure_hub
    """

    # 1. Log locally at the source
    source_hub.log_local(failure_event)

    # 2. Attempt local auto-repair if configured
    if source_hub.auto_repair_enabled:
        repair_result = source_hub.attempt_repair(failure_event)
        if repair_result.success:
            failure_event.resolution_status = 'resolved'
            failure_event.auto_repair_triggered = True

    # 3. Report to parent hub
    parent_hub.receive_failure(failure_event)

    # 4. Always report to Master Failure Hub
    master_failure_hub.aggregate(failure_event)

    # 5. If critical, trigger alerts
    if failure_event.severity == 'critical':
        alert_system.notify(failure_event)
```

### Severity Levels

| Level | Description | Response |
|-------|-------------|----------|
| `info` | Informational, no action needed | Log only |
| `warning` | Potential issue, monitor | Log + flag for review |
| `error` | Failure requiring attention | Log + route to failure spoke |
| `critical` | System-level failure | Log + alert + auto-repair attempt |

---

## Auto-Repair Hooks

The Master Failure Hub can trigger automatic repair actions based on failure patterns:

```python
AUTO_REPAIR_HOOKS = {
    'FAILED_COMPANY_MATCH': {
        'threshold': 10,  # If 10+ failures in 1 hour
        'action': 'trigger_firecrawl_batch_enrich',
        'cooldown': 3600  # seconds
    },
    'FAILED_EMAIL_VERIFICATION': {
        'threshold': 50,
        'action': 'refresh_millionverifier_patterns',
        'cooldown': 7200
    },
    'FAILED_SLOT_ASSIGNMENT': {
        'threshold': 100,
        'action': 'generate_slot_availability_report',
        'cooldown': 86400
    }
}
```

---

## Querying the Master Failure Hub

### Recent Critical Failures

```sql
SELECT error_id, source_hub, error_message, created_at
FROM public.shq_error_log
WHERE severity = 'critical'
  AND resolution_status = 'open'
ORDER BY created_at DESC
LIMIT 20;
```

### Failure Distribution by Hub

```sql
SELECT source_hub,
       COUNT(*) as total_failures,
       COUNT(*) FILTER (WHERE severity = 'critical') as critical,
       COUNT(*) FILTER (WHERE severity = 'error') as errors,
       COUNT(*) FILTER (WHERE resolution_status = 'resolved') as resolved
FROM public.shq_error_log
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY source_hub
ORDER BY total_failures DESC;
```

### Auto-Repair Success Rate

```sql
SELECT source_hub,
       COUNT(*) FILTER (WHERE auto_repair_triggered = TRUE) as repair_attempts,
       COUNT(*) FILTER (WHERE auto_repair_triggered = TRUE AND resolution_status = 'resolved') as repair_successes,
       ROUND(100.0 *
         COUNT(*) FILTER (WHERE auto_repair_triggered = TRUE AND resolution_status = 'resolved') /
         NULLIF(COUNT(*) FILTER (WHERE auto_repair_triggered = TRUE), 0), 1
       ) as success_rate
FROM public.shq_error_log
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY source_hub;
```

---

## Integration with BIT Engine

The Master Failure Hub feeds health metrics back to the BIT Engine:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FAILURE -> BIT ENGINE SIGNAL                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Failure Pattern               Signal to BIT Engine                    │
│   ───────────────────────────   ────────────────────────────────────    │
│   High company match failures   Data quality score decrease             │
│   Email verification spikes     Pattern refresh needed                  │
│   Slot assignment backlogs      Capacity planning signal                │
│   DOL match failures            EIN mapping review needed               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- [[Bicycle Wheel Doctrine]] - The official architecture standard
- [[PLE Schema ERD]] - Database schema with failure tables
- [[imo-architecture.json]] - Machine-readable architecture definition

---

*Last Updated: December 2025*
*Architecture: Bicycle Wheel Doctrine v1.0*
*Strategy: Distributed Centralized Reporting*
