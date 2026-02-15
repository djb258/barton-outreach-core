# Implementation Gap Analysis — Hub & Spoke Configuration

**Generated**: 2025-12-19
**Purpose**: Identify what's implemented vs what needs to be built for each hub/spoke

---

## Executive Summary

| Component | Implementation | Status | Blocking Issues |
|-----------|---------------|--------|-----------------|
| **Company Hub** | 75% | ⚠️ Partial | Missing 4 utility modules |
| **BIT Engine** | 70% | ⚠️ Partial | Threshold discrepancy, decay stubs |
| **People Spoke** | 85% | ✅ Mostly Ready | n8n wiring, DB persistence |
| **DOL Spoke** | 70% | ⚠️ Partial | DB load, BROKER_CHANGE signal |
| **Blog Spoke** | 0% | ❌ Not Started | Entire spoke missing |
| **Enforcement** | 100% | ✅ Complete | None |

---

## COMPANY HUB (Tools 1-9)

### Tool Status

| Tool | Name | Status | Notes |
|------|------|--------|-------|
| 1 | Matcher | ✅ Complete | Domain & name index matching |
| 2 | Fuzzy Matcher | ✅ Complete | Jaro-Winkler + RapidFuzz in `utils/fuzzy.py` |
| 3 | Fuzzy Arbitration | ❌ Missing | Abacus.ai LLM not integrated |
| 4 | Domain Resolver | ✅ Complete | Multi-source resolution logic |
| 5 | DNS/MX Validator | ❌ Missing | `utils/verification.py` doesn't exist |
| 6 | Pattern Discovery | ⚠️ Partial | Core logic done, providers module missing |
| 7 | Pattern Generator | ✅ Complete | Full placeholder support in `utils/patterns.py` |
| 8 | Email Verifier Light | ❌ Stub Only | Skeleton code, no actual SMTP logic |
| 9 | Email Verifier Auth | ✅ Complete | MillionVerifier API in `email/bulk_verifier.py` |

### BLOCKING: Missing Utility Modules

These 4 modules are imported but don't exist:

```
hub/company/utils/verification.py    ← CRITICAL (blocks Phase 2 & 4)
hub/company/utils/providers.py       ← CRITICAL (blocks Phase 3)
hub/company/utils/logging.py         ← BLOCKING (all phases)
hub/company/utils/config.py          ← BLOCKING (all phases)
```

#### Required: `utils/verification.py`

```python
# Expected exports:
def verify_domain_dns(domain: str) -> DomainHealthStatus
def verify_domain_health(domain: str) -> DomainVerificationResult
def verify_mx_records(domain: str, timeout: float) -> List[str]
def verify_email(email: str, check_smtp: bool, smtp_timeout: int) -> VerificationResult
def verify_email_format(email: str) -> bool
def smtp_check(email: str) -> bool
def bulk_verify(emails: List[str]) -> List[VerificationResult]

class DomainHealthStatus(Enum): ...
class DomainVerificationResult: ...
class VerificationStatus(Enum): ...
class VerificationResult: ...
```

#### Required: `utils/providers.py`

```python
# Expected exports:
class ProviderRegistry: ...
class ProviderBase: ...
class ProviderTier(Enum): TIER_0, TIER_1, TIER_2
class ProviderResult: ...

# Provider implementations:
class FirecrawlProvider(ProviderBase): ...
class HunterProvider(ProviderBase): ...
class ApolloProvider(ProviderBase): ...
# ... etc

def execute_tier_waterfall(domain: str, tiers: List[ProviderTier]) -> ProviderResult
```

**NOTE**: Provider implementations exist at `ctb/sys/enrichment/pipeline_engine/utils/providers.py` (1501 lines). These need to be imported/linked to `hub/company/utils/`.

### TODO for Company Hub

1. [ ] Create `utils/verification.py` with DNS/MX/SMTP functions
2. [ ] Link or copy provider registry from `ctb/sys/enrichment/`
3. [ ] Create `utils/logging.py` with PipelineLogger
4. [ ] Create `utils/config.py` with PipelineConfig
5. [ ] Implement Tool 3 (Abacus.ai arbitration) for collision resolution
6. [ ] Implement Tool 8 (SMTP handshake verification)

---

## BIT ENGINE (Tools 10-11)

### Tool Status

| Tool | Name | Status | Notes |
|------|------|--------|-------|
| 10 | Signal Deduplicator | ✅ Complete | SHA256 hashing, 24h/365d windows |
| 11 | BIT Scoring Engine | ⚠️ Partial | Core works, decay/confidence stubbed |

### Implementation Details

**What's Working:**
- Signal intake from all spokes (People, DOL, Talent Flow, Blog)
- Weighted signal aggregation with 15 signal types
- Thread-safe deduplication with time windows
- Database schema ready (15 indexes)
- Score calculation formula implemented

**What's Stubbed:**
- Decay factor lookup returns 1.0 (always)
- Confidence modifier returns 1.0 (always)
- Person/company loading from actual database

### ISSUE: Threshold Discrepancy

```
BIT_SIGNAL_FLOW.md says:     "BIT >= 25: SUSPECT → WARM"
trigger_config.json says:     WARM = 50-99 range
bit_signal_log.sql says:      crossed_warm_threshold = 25
                              crossed_hot_threshold = 50
```

**Recommendation**: Clarify that:
- `25` = "Suspect Threshold" (worth watching)
- `50` = "Warm Outreach Threshold" (ready for outreach)

### TODO for BIT Engine

1. [ ] Resolve threshold discrepancy (document or fix)
2. [ ] Implement actual decay factor lookup from database
3. [ ] Implement confidence modifier lookup
4. [ ] Wire person/company data loading from Neon
5. [ ] Integrate SignalDeduplicator into spoke signal emission calls

---

## PEOPLE SPOKE (Tools 12-16)

### Tool Status

| Tool | Name | Status | Notes |
|------|------|--------|-------|
| 12 | People Classifier | ✅ Complete | Phase 0, 478 lines |
| 13 | Email Generator | ✅ Complete | Phase 5, 666 lines |
| 14 | Slot Assignment | ✅ Complete | Phase 6, 678 lines |
| 15 | Enrichment Queue | ⚠️ Partial | Phase 7, n8n not wired |
| 16 | Talent Movement | ⚠️ Shell | Separate system, not in spoke |

### Phase Implementation

| Phase | File | Lines | Status |
|-------|------|-------|--------|
| Phase 0 | `phase0_people_ingest.py` | 478 | ✅ Production Ready |
| Phase 5 | `phase5_email_generation.py` | 666 | ✅ Production Ready |
| Phase 6 | `phase6_slot_assignment.py` | 678 | ✅ Production Ready |
| Phase 7 | `phase7_enrichment_queue.py` | 809 | ⚠️ n8n stub |
| Phase 8 | `phase8_output_writer.py` | 677 | ✅ Production Ready |

**Total Implementation**: 5,500+ lines of production-ready code

### What's Missing

1. **n8n Queue Integration** (Phase 7)
   - Queue uses in-memory storage only
   - No actual n8n workflow trigger
   - Workflows exist at `ctb/sys/enrichment-agents/n8n-workflows/`

2. **Database Persistence**
   - All phases are CSV-only
   - No Neon PostgreSQL writes
   - Movement Engine signals created but not persisted

3. **Waterfall Integration** (Optional)
   - `Phase5WaterfallAdapter` referenced but may not exist
   - `Phase7WaterfallProcessor` referenced but may not exist
   - Gracefully disabled via try/except

### Talent Flow Sub-Hub

**Location**: `ctb/sys/talent-flow-agent/` (separate system)

**Status**: SHELL - Framework exists but not integrated

**Expected Integration**:
- LinkedIn profile snapshots → Movement detection
- EXECUTIVE_JOINED (+10.0) / EXECUTIVE_LEFT (+6.0) signals
- Feeds into People Spoke Phase 0 as `talentflow_movement` flag

### TODO for People Spoke

1. [ ] Wire n8n queue triggers in Phase 7
2. [ ] Add database persistence layer (Neon writes)
3. [ ] Complete Talent Flow integration (or keep as separate system)
4. [ ] Implement waterfall adapters if needed
5. [ ] Add MillionVerifier API calls in email verification sub-wheel

---

## DOL SPOKE (Tools 17-18)

### Tool Status

| Tool | Name | Status | Notes |
|------|------|--------|-------|
| 17 | DOL Importer | ⚠️ Partial | CSV staging done, no DB load |
| 18 | Exact EIN Matcher | ✅ Complete | Deterministic exact match |

### Import Scripts

| File | Data | Status |
|------|------|--------|
| `import_5500.py` | Form 5500 (large plans) | ✅ CSV staging |
| `import_5500_sf.py` | Form 5500-SF (small plans) | ✅ CSV staging |
| `import_schedule_a.py` | Schedule A (insurance) | ✅ CSV staging |

**Missing**: Database INSERT phase - scripts generate CSVs but don't load to Neon

### Signal Emission

| Signal | Status | Impact |
|--------|--------|--------|
| FORM_5500_FILED | ✅ Implemented | +5.0 |
| LARGE_PLAN | ✅ Implemented | +8.0 |
| BROKER_CHANGE | ❌ Not Implemented | +7.0 |
| RENEWAL_APPROACHING | ❌ Not Implemented | Planned |

### What's Working

- ✅ EIN normalization (remove hyphens, pad to 9 digits)
- ✅ Exact EIN lookup to company_master
- ✅ Hub gate validation
- ✅ Correlation ID enforcement
- ✅ Signal deduplication (365-day window)

### What's Missing

1. **Database Load Phase**
   - Import scripts generate CSVs only
   - Need INSERT into `marketing.form_5500`, etc.

2. **BROKER_CHANGE Detection**
   - Signal type defined but not implemented
   - Requires prior year broker comparison

3. **Schedule A Signal Emission**
   - Data extracted but no signals emitted
   - Missing carrier/policy type signals

### TODO for DOL Spoke

1. [ ] Add database INSERT phase to import scripts
2. [ ] Implement BROKER_CHANGE signal detection
3. [ ] Add Schedule A signal emission
4. [ ] Implement RENEWAL_APPROACHING signal
5. [ ] Add batch EIN lookup optimization

---

## BLOG SPOKE (Tool 19)

### Tool Status

| Tool | Name | Status | Notes |
|------|------|--------|-------|
| 19 | Blog/RSS Ingestor | ❌ Not Started | Directory empty |

### Current State

**Location**: `spokes/blog_news/` - EMPTY

**Status**: PLANNED (registered in `spokes/__init__.py` as Spoke #3)

### Infrastructure Ready

The BIT Engine already has blog signal types defined:
```python
FUNDING_EVENT     = +15.0  # Investment announced
ACQUISITION       = +12.0  # Company acquired/acquiring
LAYOFF            = -3.0   # Layoffs announced
LEADERSHIP_CHANGE = +8.0   # Executive change
NEWS_MENTION      = +1.0   # General news
```

n8n scheduler templates exist for scheduled RSS checks.

### TODO for Blog Spoke

1. [ ] Create Blog Spoke structure
2. [ ] Implement RSS feed parser
3. [ ] Implement news API integrations (optional)
4. [ ] Add event detection (funding, acquisition, leadership)
5. [ ] Wire signal emission to BIT Engine
6. [ ] Create n8n scheduled workflow for RSS checks

---

## ENFORCEMENT MODULES

### Status: 100% COMPLETE ✅

| Module | Status | Tests |
|--------|--------|-------|
| `correlation_id.py` | ✅ Complete | 8 tests |
| `hub_gate.py` | ✅ Complete | 7 tests |
| `signal_dedup.py` | ✅ Complete | 8 tests |
| `error_codes.py` | ✅ Complete | 8 tests |

**No work needed** - all enforcement modules are production-ready.

---

## PRIORITY ACTION ITEMS

### Critical (Blocks Execution)

| # | Task | Blocks |
|---|------|--------|
| 1 | Create `utils/verification.py` | Phase 2, Phase 4 |
| 2 | Link `utils/providers.py` from ctb/sys | Phase 3 |
| 3 | Create `utils/logging.py` | All phases |
| 4 | Create `utils/config.py` | All phases |

### High (Blocks Full Functionality)

| # | Task | Blocks |
|---|------|--------|
| 5 | Add DB load to DOL import scripts | DOL data availability |
| 6 | Implement BROKER_CHANGE signal | BIT scoring accuracy |
| 7 | Resolve BIT threshold discrepancy | Outreach routing |
| 8 | Wire n8n queue triggers | Automated enrichment |

### Medium (Enhancement)

| # | Task | Impact |
|---|------|--------|
| 9 | Implement Tool 3 (Abacus.ai arbitration) | Better collision resolution |
| 10 | Implement Tool 8 (SMTP verification) | Email validation |
| 11 | Add database persistence to People Spoke | Data durability |
| 12 | Implement Talent Flow integration | Movement signals |

### Low (Future)

| # | Task | Impact |
|---|------|--------|
| 13 | Build Blog Spoke | News/sentiment signals |
| 14 | Implement decay factors | Score accuracy |
| 15 | Add confidence modifiers | Score accuracy |

---

## Quick Wins (Can Do Now)

1. **Link providers.py**: The enrichment providers are fully implemented at `ctb/sys/enrichment/pipeline_engine/utils/providers.py`. Just need to import/link them to `hub/company/utils/`.

2. **Resolve threshold discrepancy**: Update documentation to clarify 25 = suspect threshold, 50 = warm threshold.

3. **Run People Spoke**: Phases 0, 5, 6, 8 are production-ready. Can run now with CSV output.

4. **Use enforcement modules**: All 4 modules (correlation_id, hub_gate, signal_dedup, error_codes) are complete and integrated.

---

## Estimated Effort

| Task Group | Effort | Priority |
|------------|--------|----------|
| Create 4 utility modules | 2-3 days | Critical |
| DOL database load + signals | 1-2 days | High |
| n8n queue wiring | 1 day | High |
| Tool 3 & 8 implementation | 2 days | Medium |
| Blog Spoke (full) | 3-5 days | Low |
| Talent Flow integration | 2-3 days | Medium |

**Total to Full Production**: ~2-3 weeks of focused work

---

*Gap Analysis Generated: 2025-12-19*
