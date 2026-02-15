# Root Cause Analysis - Sub-Hub Coverage Gaps

**Date**: 2026-02-04
**Analyst**: Database Operations Team
**Status**: Initial Analysis Complete

---

## EXECUTIVE SUMMARY

Two distinct pipeline failures have been identified:

1. **Company Target Pipeline Failure** (767 companies)
   - Created: 2026-01-27 to 2026-01-30
   - Root Cause: Pipeline never executed
   - Cascading Effect: Blog records also missing

2. **People Intelligence Pipeline Failure** (1,343 companies)
   - Created: 2026-02-04
   - Root Cause: Company Target completed but email_method is NULL
   - Blocking Issue: No email pattern = No slot assignment possible

---

## PATTERN A: COMPANY TARGET PIPELINE FAILURE

### Affected Companies: 767

### Characteristics

| Attribute | Value |
|-----------|-------|
| Domain | 100% have valid domains |
| EIN | 100% NULL |
| Created Window | 2026-01-27 through 2026-01-30 (4 days) |
| CT Record | Missing |
| Blog Record | Missing (cascading failure) |

### Sample Companies

```
outreach_id: 028b6afa-02e4-44a7-8cf5-b33a337d4a48
domain: campbelloil.net
created_at: 2026-01-30 13:25:34

outreach_id: e67c09f1-b7cd-416d-b718-749de4d37ed6
domain: trinityacademy.com
created_at: 2026-01-30 13:25:34

outreach_id: c354ba82-aa1c-4b2d-9c53-d748d92bf3f2
domain: alphaacademy.education
created_at: 2026-01-30 13:25:34
```

### Temporal Distribution

| Date | Companies Created | % of Total Gap |
|------|-------------------|----------------|
| 2026-01-27 | 289 | 37.7% |
| 2026-01-28 | 419 | 54.6% |
| 2026-01-29 | 38 | 5.0% |
| 2026-01-30 | 21 | 2.7% |

### Root Cause Hypothesis

**Primary Hypothesis**: Company Target pipeline worker was down or not processing during this 4-day window.

**Supporting Evidence**:
1. All companies created during this window have the same failure pattern
2. Companies created before (2026-01-06) and after (2026-02-04) this window were processed successfully
3. 100% of companies in this window are missing CT records
4. No partial failures - suggests batch processing issue, not individual company issues

**Possible Causes**:
1. Worker/scheduler outage during 2026-01-27 to 2026-01-30
2. Deployment or maintenance window that disabled pipeline
3. Queue processing failure
4. Waterfall gate malfunction preventing CT initialization

**Investigation Required**:
- [ ] Check pipeline execution logs for 2026-01-27 to 2026-01-30
- [ ] Check worker/scheduler status during this window
- [ ] Check deployment logs for any changes during this period
- [ ] Check system monitoring/alerts for outages
- [ ] Check queue depth/processing metrics

---

## PATTERN B: PEOPLE INTELLIGENCE PIPELINE FAILURE

### Affected Companies: 1,343

### Characteristics

| Attribute | Value |
|-----------|-------|
| Domain | 100% have valid domains |
| CT Record | Present (100%) |
| Blog Record | Present (100%) |
| email_method | NULL (100%) |
| method_type | NULL (100%) |
| confidence_score | NULL (100%) |
| execution_status | "pending" (100%) |
| Created Date | 2026-02-04 (single day) |

### Sample Companies

```
outreach_id: 1f390627-fed0-408e-a91d-87f86dd10d95
domain: tiffin.edu
email_method: NULL
execution_status: pending
created_at: 2026-02-04 12:55:15

outreach_id: 87dc83ec-7e75-47c1-b4e5-839f317364fe
domain: honeybrookah.com
email_method: NULL
execution_status: pending
created_at: 2026-02-04 12:55:15

outreach_id: ad0b9c71-849d-4396-80da-77da5e737aa5
domain: chthealthcare.com
email_method: NULL
execution_status: pending
created_at: 2026-02-04 12:55:15
```

### Root Cause Hypothesis

**Primary Hypothesis**: Company Target completed initialization but email pattern discovery (Phases 2-4) failed for these companies.

**Supporting Evidence**:
1. Company Target record exists (company_target row created)
2. `email_method` is NULL (email pattern waterfall did not complete)
3. `execution_status` is "pending" (pipeline never progressed beyond init)
4. People Intelligence cannot proceed without email pattern
5. All failures occurred on single day (2026-02-04)

**Waterfall Context**:
```
Company Target Pipeline:
├─ Phase 1: Company Matching ✓ (completed)
├─ Phase 2: Domain Resolution ✓ (completed - domains present)
├─ Phase 3: Email Pattern Waterfall ✗ (FAILED - email_method is NULL)
└─ Phase 4: Pattern Verification ✗ (BLOCKED by Phase 3)

People Intelligence Pipeline:
├─ Phase 5: Email Generation ✗ (BLOCKED - requires email_method)
├─ Phase 6: Slot Assignment ✗ (BLOCKED by Phase 5)
├─ Phase 7: Enrichment Queue ✗ (BLOCKED by Phase 6)
└─ Phase 8: Output Writer ✗ (BLOCKED by Phase 7)
```

**Possible Causes**:
1. Email pattern waterfall services unavailable on 2026-02-04
2. Hunter.io, EmailHippo, or other email verification services rate-limited or down
3. Phase 3 worker exhausted API credits or quota
4. Network connectivity issues to external email verification services
5. Timeout configuration too aggressive for this batch
6. Bug in Phase 3 error handling (failed but marked as "pending" instead of "failed")

**Investigation Required**:
- [ ] Check Phase 3 (Email Pattern Waterfall) execution logs for 2026-02-04
- [ ] Check external service status (Hunter.io, EmailHippo) on 2026-02-04
- [ ] Check API quota/rate limit logs for email verification services
- [ ] Check network logs for connectivity issues
- [ ] Check timeout configurations for Phase 3
- [ ] Check error handling logic in Phase 3 (why "pending" instead of "failed"?)

---

## KEY FINDING: EMAIL PATTERN IS BLOCKER

### Current State

```sql
-- Companies with CT but no email_method
SELECT COUNT(*) FROM outreach.company_target
WHERE email_method IS NULL;
-- Result: 1,343
```

### Waterfall Gate Logic

The waterfall doctrine requires:
1. Company Target MUST complete Phases 1-4 before People Intelligence can start
2. People Intelligence REQUIRES `email_method` from Company Target
3. If `email_method` is NULL, People Intelligence is BLOCKED

### Status Interpretation

| execution_status | Meaning | Next Action |
|------------------|---------|-------------|
| "pending" | Phase 1 completed, waiting for Phase 2-4 | Re-run email pattern waterfall |
| "completed" | All phases completed | Ready for People Intelligence |
| "failed" | Pipeline error, needs investigation | Manual review + retry |

**Observation**: All 1,343 companies have `execution_status = "pending"`, suggesting:
- Phase 1 (Company Matching) completed
- Phases 2-4 (Domain Resolution, Email Pattern, Verification) did not complete
- Worker stopped processing before completing the full waterfall

---

## COMPARISON: PATTERN A vs PATTERN B

| Attribute | Pattern A (CT Failure) | Pattern B (People Failure) |
|-----------|------------------------|---------------------------|
| **Companies** | 767 | 1,343 |
| **Date Window** | 2026-01-27 to 2026-01-30 (4 days) | 2026-02-04 (1 day) |
| **CT Record** | Missing | Present |
| **Blog Record** | Missing | Present |
| **email_method** | N/A (no CT record) | NULL |
| **execution_status** | N/A (no CT record) | "pending" |
| **Phase Reached** | Phase 0 (never started) | Phase 1 (stopped after init) |
| **Overlap** | 0 companies (distinct sets) | 0 companies (distinct sets) |

**Key Insight**: These are TWO SEPARATE failure modes:
- Pattern A: Pipeline never started
- Pattern B: Pipeline started but stopped early

---

## REMEDIATION APPROACH

### For Pattern A (CT/Blog Gaps - 767 companies)

**Approach**: Full pipeline re-run from Phase 1

```python
# Load gap companies
import pandas as pd
ct_gaps = pd.read_csv('ct_blog_gaps_20260204_163005.csv')

# Re-run Company Target pipeline for each
from hubs.company_target import CompanyPipeline

for _, row in ct_gaps.iterrows():
    pipeline = CompanyPipeline(
        outreach_id=row['outreach_id'],
        domain=row['domain'],
        persist_to_neon=True
    )
    result = pipeline.run()  # Phases 1-4

    # Blog should auto-generate when CT completes
```

**Expected Outcome**:
- Company Target record created with email_method
- Blog record auto-generated
- Coverage: 99.20% → 100.00%

### For Pattern B (People Gaps - 1,343 companies)

**Approach**: Resume from Phase 2 (email pattern waterfall)

```python
# Load gap companies
people_gaps = pd.read_csv('people_slot_gaps_20260204_163006.csv')

# Option 1: Resume Phase 2-4 for Company Target
from hubs.company_target.imo.middle.phases import Phase3EmailPatternWaterfall

for _, row in people_gaps.iterrows():
    # Resume email pattern discovery
    result = Phase3EmailPatternWaterfall.execute(
        outreach_id=row['outreach_id'],
        domain=row['domain']
    )

    if result.success and result.email_method:
        # Mark CT as completed
        update_execution_status(row['outreach_id'], 'completed')

        # Trigger People Intelligence
        people_pipeline = PeoplePipeline(outreach_id=row['outreach_id'])
        people_pipeline.run()  # Phases 5-8
```

**Expected Outcome**:
- Company Target email_method populated
- Company Target execution_status = "completed"
- People slots created (CEO, CFO, HR)
- Coverage: 98.61% → 100.00%

---

## PREVENTIVE MEASURES

### 1. Pipeline Health Monitoring

**Implement**:
- Real-time pipeline execution monitoring
- Alert on stalled pipelines (execution_status = "pending" for > 24 hours)
- Alert on coverage drops below 99%
- Daily automated coverage audits

**Metrics to Track**:
- Company Target completion rate (Phase 1 vs Phase 4)
- Email pattern discovery success rate
- People slot assignment completion rate
- Average time from spine creation to full coverage

### 2. Waterfall Gate Validation

**Implement**:
- Pre-flight checks before each phase
- Hard validation of prerequisites (domain exists, email_method exists, etc.)
- Better error handling with explicit failure states
- Retry logic with exponential backoff

**Status States**:
- "pending" → Waiting for prerequisites
- "in_progress" → Currently executing
- "completed" → All phases done
- "failed" → Explicit failure requiring investigation
- "blocked" → Missing prerequisites, cannot proceed

### 3. External Service Resilience

**Implement**:
- Circuit breaker pattern for external services
- API quota monitoring and alerting
- Fallback services for email verification
- Graceful degradation when services unavailable

**Services to Monitor**:
- Hunter.io (email pattern discovery)
- EmailHippo (email verification)
- Any other external email verification services

### 4. Automated Gap Detection

**Implement Daily Cron**:
```bash
# Run at 6 AM daily
0 6 * * * cd /app && doppler run -- python ops/audit_subhub_coverage.py
```

**Alert Thresholds**:
- Company Target coverage < 99%: HIGH severity
- People Slots coverage < 99%: HIGH severity
- Any gap > 100 companies: CRITICAL
- Any gap older than 48 hours: CRITICAL

---

## NEXT STEPS

### Immediate (Next 24 Hours)
1. [ ] Re-run Company Target pipeline for 767 companies (Pattern A)
2. [ ] Resume email pattern waterfall for 1,343 companies (Pattern B)
3. [ ] Verify 100% coverage achievement
4. [ ] Document actual root causes found during remediation

### Short-Term (Next Week)
1. [ ] Review pipeline execution logs for both failure windows
2. [ ] Implement pipeline health monitoring
3. [ ] Add daily automated coverage audits
4. [ ] Set up alerting for coverage drops

### Long-Term (Next Month)
1. [ ] Implement circuit breaker for external services
2. [ ] Add better error handling with explicit failure states
3. [ ] Create automated remediation workflows
4. [ ] Document incident response procedures

---

## INVESTIGATION CHECKLIST

### Pattern A Investigation (CT Pipeline Failure)
- [ ] Pipeline execution logs (2026-01-27 to 2026-01-30)
- [ ] Worker/scheduler status during window
- [ ] Deployment logs for changes during period
- [ ] System monitoring alerts for outages
- [ ] Queue depth/processing metrics

### Pattern B Investigation (Email Pattern Failure)
- [ ] Phase 3 execution logs (2026-02-04)
- [ ] External service status (Hunter.io, EmailHippo)
- [ ] API quota/rate limit logs
- [ ] Network logs for connectivity issues
- [ ] Timeout configuration review
- [ ] Error handling logic review

---

## CONCLUSIONS

1. **TWO DISTINCT FAILURES**: Company Target init failure (767) and email pattern discovery failure (1,343)
2. **ZERO OVERLAP**: Different companies, different failure modes, different remediation approaches
3. **TEMPORAL ISOLATION**: Pattern A (4-day window), Pattern B (single day) - suggests different root causes
4. **WATERFALL VALIDATION NEEDED**: Email pattern is critical blocker for People Intelligence
5. **MONITORING GAPS**: These failures went undetected for days - need automated coverage monitoring

**Severity**: HIGH - 2,110 companies (2.19%) require manual remediation

**Estimated Resolution Time**: 6-10 hours for remediation + 8-16 hours for investigation

---

**Report Generated**: 2026-02-04
**Next Update**: After remediation completion
