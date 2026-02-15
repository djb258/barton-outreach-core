# Deployment Checklist - Barton Outreach Core

**Version:** 2.1
**Last Updated:** 2025-12-19

---

## Pre-Deployment Checklist

### 1. Code Quality

- [ ] All tests passing (`python -m pytest tests/`)
- [ ] No linting errors
- [ ] Type hints validated
- [ ] No hardcoded credentials
- [ ] No debug print statements

### 2. Documentation

- [ ] CLAUDE.md up to date
- [ ] All PRDs current (see `docs/prd/`)
- [ ] ADRs documented for architectural decisions
- [ ] API documentation current
- [ ] Schema changes documented

### 3. Database

- [ ] Migration scripts tested
- [ ] Rollback scripts prepared
- [ ] Schema changes applied to staging
- [ ] RLS policies verified
- [ ] Indexes optimized

### 4. Environment

- [ ] `.env.example` updated with new variables
- [ ] Doppler secrets synced
- [ ] No secrets in code
- [ ] Environment-specific configs separated

---

## Dry Run Validation

### 5. Pipeline Validation

- [ ] Dry run completed (`python tests/dry_run_orchestrator.py`)
- [ ] All kill switches validated
- [ ] Cost metrics within budget
- [ ] Volume metrics acceptable
- [ ] Quality metrics meet thresholds

### 6. Kill Switch Status

| Switch | Threshold | Status |
|--------|-----------|--------|
| `signal_flood_per_source` | 500 | [ ] Passed |
| `daily_cost_ceiling` | $50 | [ ] Passed |
| `enrichment_queue_max` | 10,000 | [ ] Passed |
| `bit_spike_per_run` | 100 | [ ] Passed |

### 7. Reports Generated

- [ ] `tests/dry_run_summary.md` reviewed
- [ ] `tests/dry_run_metrics.json` archived
- [ ] `tests/kill_switch_report.md` reviewed
- [ ] `tests/next_actions.md` addressed

---

## Deployment Steps

### 8. Pre-Deploy

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
python -m pytest tests/ -v

# 4. Run dry run
python tests/dry_run_orchestrator.py
```

### 9. Database Migration

```bash
# 1. Backup current database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Apply migrations
psql $DATABASE_URL < migrations/latest.sql

# 3. Verify schema
psql $DATABASE_URL -c "\dt marketing.*"
```

### 10. Deploy

```bash
# 1. Create deployment commit
git add .
git commit -m "deploy: v2.1 production release"

# 2. Push to main
git push origin main

# 3. Verify deployment
curl https://api.barton.com/health
```

---

## Post-Deployment Checklist

### 11. Verification

- [ ] Health check passing
- [ ] Error logs clean
- [ ] Metrics dashboards green
- [ ] Sample pipeline run successful

### 12. Monitoring

- [ ] Grafana dashboards configured
- [ ] Alert thresholds set
- [ ] On-call rotation notified
- [ ] Runbook accessible

### 13. Rollback Ready

- [ ] Previous version tagged
- [ ] Rollback script tested
- [ ] Database backup verified
- [ ] Team aware of rollback procedure

---

## Component Status

### Hub Components

| Component | File | Status |
|-----------|------|--------|
| Company Hub | `hub/company/company_hub.py` | [ ] Verified |
| Company Pipeline | `hub/company/company_pipeline.py` | [ ] Verified |
| BIT Engine | `hub/company/bit_engine.py` | [ ] Verified |
| Neon Writer | `hub/company/neon_writer.py` | [ ] Verified |

### Spoke Components

| Spoke | File | Status |
|-------|------|--------|
| People Spoke | `spokes/people/people_spoke.py` | [ ] Verified |
| DOL Spoke | `spokes/dol/dol_spoke.py` | [ ] Verified |
| Blog Spoke | `spokes/blog/blog_spoke.py` | [ ] Verified |
| Talent Flow | `spokes/talent_flow/talent_flow_spoke.py` | [ ] Verified |
| Outreach Spoke | `spokes/outreach/outreach_spoke.py` | [ ] Verified |

### Enforcement Components

| Component | File | Status |
|-----------|------|--------|
| Correlation ID | `ops/enforcement/correlation_id.py` | [ ] Verified |
| Signal Dedup | `ops/enforcement/signal_dedup.py` | [ ] Verified |
| Hub Gate | `ops/enforcement/hub_gate.py` | [ ] Verified |
| Error Codes | `ops/enforcement/error_codes.py` | [ ] Verified |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Reviewer | | | |
| Ops | | | |

---

## Emergency Contacts

| Role | Contact |
|------|---------|
| On-Call | TBD |
| Database | TBD |
| Escalation | TBD |

---

## Rollback Procedure

```bash
# 1. Revert to previous commit
git revert HEAD

# 2. Push rollback
git push origin main

# 3. Restore database (if needed)
psql $DATABASE_URL < backup_YYYYMMDD.sql

# 4. Notify team
# Send notification to #engineering channel
```

---

**Last Updated:** 2025-12-19
**Author:** Claude Code
