# KILL SWITCH REPORT
**Run ID**: 7aed0b56-b274-44cb-973f-f9e4b3eecad3
**Timestamp**: 2025-12-19T14:25:41.177738

## Summary
- Total Switches Evaluated: 4
- Switches Triggered: 2
- Switches Passed: 2

## TRIGGERED SWITCHES

### signal_flood_per_source
- **Trigger Condition**: Source people_spoke exceeded signal limit
- **Threshold**: 500
- **Actual Value**: 501
- **Where Fired**: people_spoke._emit_signal
- **What Stopped**: Signals from people_spoke halted
- **Timestamp**: 2025-12-19T14:25:41.230277

### daily_cost_ceiling
- **Trigger Condition**: Daily cost $215.98 exceeds ceiling
- **Threshold**: 50.0
- **Actual Value**: 215.97969999999998
- **Where Fired**: orchestrator._validate_kill_switches
- **What Stopped**: Further processing halted
- **Timestamp**: 2025-12-19T14:25:41.271356

## PASSED SWITCHES

### enrichment_queue_max
- **Condition**: Queue size < 10000
- **Threshold**: 10000
- **Actual Value**: 1546.00

### bit_spike_per_run
- **Condition**: Max BIT < 100
- **Threshold**: 100
- **Actual Value**: 100.00
