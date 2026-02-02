# Tool Canon Enforcement Specification

**Policy Version**: 1.0.0
**Effective Date**: 2026-02-02
**Authority**: SNAP_ON_TOOLBOX.yaml (Constitutional)
**Doctrine**: "Snap-on - One tool, many jobs, config is the variable"

---

## 1. Hub and Sub-Hub Registry

| Hub ID | Hub Name | Doctrine ID | Waterfall Order | Gates Completion |
|--------|----------|-------------|-----------------|------------------|
| HUB-COMPANY-LIFECYCLE | Company Lifecycle (CL) | PARENT | 0 | YES |
| HUB-COMPANY-TARGET | Company Target | 04.04.01 | 1 | YES |
| HUB-DOL | DOL Filings | 04.04.03 | 2 | YES |
| HUB-PEOPLE | People Intelligence | 04.04.02 | 3 | YES |
| HUB-TALENT-FLOW | Talent Flow | 04.04.06 | 4 | YES |
| HUB-BLOG-001 | Blog Content | 04.04.05 | 5 | NO |
| HUB-OUTREACH | Outreach Execution | 04.04.04 | 6 | NO |

---

## 2. Tool Canon Registry

### Tier 0: Free Tools (No Gate Required)

| Tool ID | Tool Name | Software | Purpose |
|---------|-----------|----------|---------|
| TOOL-001 | MXLookup | dnspython | DNS MX record validation |
| TOOL-002 | SMTPCheck | smtplib (stdlib) | SMTP deliverability validation |
| TOOL-003 | LinkedInCheck | httpx | LinkedIn URL existence check |

### Tier 1: Cheap Tools (Budget-Capped)

| Tool ID | Tool Name | Software | Purpose | Monthly Budget |
|---------|-----------|----------|---------|----------------|
| TOOL-004 | Firecrawl | Firecrawl API | JS-rendered page scraping | 500/mo free |
| TOOL-005 | ScraperAPI | ScraperAPI | Anti-bot proxy | $100/mo |
| TOOL-006 | GooglePlaces | Google Places API | Business/address validation | $50/mo |
| TOOL-007 | ComposioRouter | Composio | Integration router (500+ apps) | $30/mo fixed |

### Tier 2: Surgical Tools (Gate Required)

| Tool ID | Tool Name | Software | Purpose | Gate Required |
|---------|-----------|----------|---------|---------------|
| TOOL-008 | HunterEnricher | Hunter.io API | Email finder, domain search | YES |
| TOOL-009 | ApolloEnricher | Apollo.io API | Contact/company enrichment | YES |
| TOOL-010 | EmailVerifier | MillionVerifier API | Pre-send email verification | YES |
| TOOL-011 | RetellCaller | Retell AI API | AI voice calling | YES + Human Approval |

---

## 3. Tool Interaction Types

| Interaction | Definition | Data Flow | Audit Required |
|-------------|------------|-----------|----------------|
| **READ** | Fetch data from external source without mutation | External → Hub | NO |
| **WRITE** | Persist data to internal storage | Hub → Database | YES |
| **ENRICH** | Augment existing record with external data | External → Hub → Database | YES |
| **VALIDATE** | Verify correctness of existing data | Hub → External → Hub | NO |

---

## 4. Hub Tool Allocation

### Company Target (04.04.01)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| MXLookup (TOOL-001) | VALIDATE | NO | Domain MX verification |
| LinkedInCheck (TOOL-003) | VALIDATE | NO | Company LinkedIn URL validation |
| HunterEnricher (TOOL-008) | ENRICH | **YES** | Domain email pattern discovery |
| GooglePlaces (TOOL-006) | VALIDATE | NO | Business existence validation |

**Primary Tools**: MXLookup, LinkedInCheck
**Fallback Tools**: GooglePlaces
**Gated Tools**: HunterEnricher (requires domain_verified=true)

### DOL Filings (04.04.03)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| (None) | — | — | DOL uses only federal data downloads |

**Primary Tools**: None (federal data only)
**Fallback Tools**: None
**Gated Tools**: None

**Note**: DOL Filings hub operates exclusively on federal data. No external tools permitted.

### People Intelligence (04.04.02)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| SMTPCheck (TOOL-002) | VALIDATE | NO | Email deliverability check |
| MXLookup (TOOL-001) | VALIDATE | NO | Domain MX check before SMTP |
| LinkedInCheck (TOOL-003) | VALIDATE | NO | Profile URL validation |
| EmailVerifier (TOOL-010) | VALIDATE | **YES** | Pre-send verification |
| ApolloEnricher (TOOL-009) | ENRICH | **YES** | Contact enrichment |
| HunterEnricher (TOOL-008) | ENRICH | **YES** | Email discovery fallback |

**Primary Tools**: SMTPCheck, MXLookup, LinkedInCheck
**Fallback Tools**: HunterEnricher (if pattern fails)
**Gated Tools**: EmailVerifier (requires email_generated=true), ApolloEnricher (requires slot_unfilled=true)

### Talent Flow (04.04.06)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| LinkedInCheck (TOOL-003) | VALIDATE | NO | Profile change detection |

**Primary Tools**: LinkedInCheck
**Fallback Tools**: None
**Gated Tools**: None

### Blog Content (04.04.05)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| Firecrawl (TOOL-004) | READ | NO | Blog/news page scraping |
| ScraperAPI (TOOL-005) | READ | NO | Anti-bot fallback |

**Primary Tools**: Firecrawl
**Fallback Tools**: ScraperAPI
**Gated Tools**: None

### Outreach Execution (04.04.04)

| Tool | Interaction | Gate | Notes |
|------|-------------|------|-------|
| ComposioRouter (TOOL-007) | WRITE | NO | Gmail send, Slack notify |
| RetellCaller (TOOL-011) | WRITE | **YES** | AI voice outreach |

**Primary Tools**: ComposioRouter
**Fallback Tools**: None
**Gated Tools**: RetellCaller (requires human_approval=true, bit_score>=75)

---

## 5. Summary Table

| Hub | Allowed Tools | Interaction Types | Gated Tools | Violation Severity |
|-----|---------------|-------------------|-------------|-------------------|
| Company Target | TOOL-001, TOOL-003, TOOL-006, TOOL-008 | VALIDATE, ENRICH | TOOL-008 | HIGH |
| DOL Filings | (none) | (none) | (none) | CRITICAL |
| People Intelligence | TOOL-001, TOOL-002, TOOL-003, TOOL-008, TOOL-009, TOOL-010 | VALIDATE, ENRICH | TOOL-008, TOOL-009, TOOL-010 | HIGH |
| Talent Flow | TOOL-003 | VALIDATE | (none) | MEDIUM |
| Blog Content | TOOL-004, TOOL-005 | READ | (none) | LOW |
| Outreach Execution | TOOL-007, TOOL-011 | WRITE | TOOL-011 | CRITICAL |

---

## 6. Violation Classes

### Class 1: Unauthorized Tool Usage

| Violation | Definition | Severity | Disposition |
|-----------|------------|----------|-------------|
| V-TOOL-001 | Tool not in SNAP_ON_TOOLBOX.yaml | CRITICAL | PARK |
| V-TOOL-002 | Banned vendor/library used | CRITICAL | PARK |
| V-TOOL-003 | Tool used without required API key | HIGH | RETRY |

### Class 2: Wrong Interaction Type

| Violation | Definition | Severity | Disposition |
|-----------|------------|----------|-------------|
| V-TYPE-001 | WRITE when only READ permitted | HIGH | PARK |
| V-TYPE-002 | ENRICH without audit trail | MEDIUM | RETRY |
| V-TYPE-003 | VALIDATE result not logged | LOW | IGNORE |

### Class 3: Tool Used Outside Hub Scope

| Violation | Definition | Severity | Disposition |
|-----------|------------|----------|-------------|
| V-SCOPE-001 | Tool invoked by unauthorized hub | CRITICAL | PARK |
| V-SCOPE-002 | Gated tool used without gate PASS | HIGH | PARK |
| V-SCOPE-003 | Tier 2 tool used without gate conditions | HIGH | PARK |

### Class 4: Gate Violations

| Violation | Definition | Severity | Disposition |
|-----------|------------|----------|-------------|
| V-GATE-001 | Tier 2 tool called without gate check | CRITICAL | PARK |
| V-GATE-002 | Human approval required but not obtained | CRITICAL | PARK |
| V-GATE-003 | Max attempts per context exceeded | HIGH | ARCHIVE |

---

## 7. Violation Severity → Error Policy Mapping

Reference: `ERROR_TTL_PARKING_POLICY.md`

| Violation Severity | TTL Tier | Default Disposition | Blocks Promotion |
|--------------------|----------|---------------------|------------------|
| CRITICAL | SHORT (7d) | PARK | **YES** |
| HIGH | MEDIUM (30d) | RETRY | **YES** |
| MEDIUM | MEDIUM (30d) | RETRY | NO |
| LOW | LONG (90d) | IGNORE | NO |

---

## 8. Gate Conditions by Gated Tool

### TOOL-008: HunterEnricher

| Gate Condition | Required State | Hub |
|----------------|----------------|-----|
| `domain_verified` | true | Company Target |
| `mx_present` | true | Company Target |
| `pattern_attempts` | < max_attempts (1) | Company Target |

### TOOL-009: ApolloEnricher

| Gate Condition | Required State | Hub |
|----------------|----------------|-----|
| `slot_unfilled` | true | People Intelligence |
| `company_target_pass` | true | People Intelligence |
| `enrichment_attempts` | < max_attempts (1) | People Intelligence |

### TOOL-010: EmailVerifier

| Gate Condition | Required State | Hub |
|----------------|----------------|-----|
| `email_generated` | true | People Intelligence |
| `email_format_valid` | true | People Intelligence |
| `verification_attempts` | < max_attempts (1) | People Intelligence |

### TOOL-011: RetellCaller

| Gate Condition | Required State | Hub |
|----------------|----------------|-----|
| `human_approval` | true | Outreach Execution |
| `bit_score` | >= 75 | Outreach Execution |
| `contact_verified` | true | Outreach Execution |
| `dnc_checked` | true | Outreach Execution |
| `calling_hours` | 9am-8pm local | Outreach Execution |

---

## 9. Banned List (Automatic CRITICAL Violation)

### Banned Vendors

| Vendor | Reason | Alternative |
|--------|--------|-------------|
| ZoomInfo | Cost prohibitive | Apollo |
| Lusha | Cost prohibitive | Hunter/Apollo |
| Seamless.AI | Cost prohibitive | Hunter/Apollo |
| LinkedIn Sales Navigator | ToS violation + cost | LinkedInCheck |
| Diffbot | Per-page pricing | Firecrawl |
| Clearbit | Pricing changed | Apollo |
| Clay | Margin markup | Direct vendors |
| Prospeo | Redundant | Hunter |
| Snov | Redundant | Hunter |

### Banned Libraries

| Library | Reason | Alternative |
|---------|--------|-------------|
| selenium | Overhead | playwright |
| requests | Legacy | httpx |
| lxml | Performance | selectolax |
| scrapy | Overkill | Firecrawl |
| beautifulsoup4 | Performance | selectolax |

### Banned Patterns

| Pattern | Reason |
|---------|--------|
| bulk_enrichment | Violates surgical doctrine |
| llm_as_spine | LLM is tail arbitration only |
| recursive_crawling | Cost explosion |
| scraping_linkedin_profiles | ToS violation |

---

## 10. Enforcement Points (Future Implementation)

### 10.1 Pre-Call Enforcement

| Enforcement Point | Location | Check |
|-------------------|----------|-------|
| Tool Registry Check | Before any tool invocation | Tool ID in SNAP_ON_TOOLBOX.yaml |
| Hub Scope Check | Before any tool invocation | Tool ID in hub's allowed_tools |
| Gate Check | Before Tier 2 tool invocation | Gate conditions satisfied |
| Banned Check | Before any tool invocation | Tool not in banned list |

### 10.2 Post-Call Enforcement

| Enforcement Point | Location | Check |
|-------------------|----------|-------|
| Audit Log | After any tool invocation | Call logged with correlation_id |
| Cost Tracking | After Tier 1/2 invocation | Cost recorded, budget checked |
| Rate Limit | After any tool invocation | Rate limits not exceeded |

### 10.3 Periodic Enforcement

| Enforcement Point | Frequency | Check |
|-------------------|-----------|-------|
| Budget Audit | Daily | Monthly budget caps not exceeded |
| Rate Limit Review | Weekly | Sustained rate violations |
| Banned Usage Scan | Weekly | No banned tools in codebase |
| Gate Bypass Scan | Weekly | No unaudited Tier 2 calls |

---

## 11. Tool Call Audit Schema (Specification Only)

```
tool_audit_log:
  audit_id: UUID (PK)
  correlation_id: UUID (required)
  hub_id: VARCHAR (required)
  tool_id: VARCHAR (required, e.g., "TOOL-008")
  interaction_type: ENUM (READ, WRITE, ENRICH, VALIDATE)
  gate_conditions_met: JSONB (for Tier 2)
  call_timestamp: TIMESTAMPTZ
  response_status: ENUM (SUCCESS, FAILURE, TIMEOUT)
  cost_usd: DECIMAL
  entity_id: VARCHAR (company_id, person_id, etc.)
  metadata: JSONB
```

---

## 12. Evaluation Order (Mandatory)

Before ANY tool invocation, the following checks MUST occur in order:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOOL EVALUATION ORDER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   STEP 1: CHECK BANNED LIST                                                 │
│           IF banned → STOP, log V-TOOL-002, CRITICAL                        │
│                                                                             │
│   STEP 2: CHECK TOOL REGISTRY                                               │
│           IF not in SNAP_ON_TOOLBOX.yaml → STOP, log V-TOOL-001, CRITICAL   │
│                                                                             │
│   STEP 3: CHECK HUB SCOPE                                                   │
│           IF tool not allowed for this hub → STOP, log V-SCOPE-001          │
│                                                                             │
│   STEP 4: CHECK TIER                                                        │
│           IF Tier 2 → proceed to gate check                                 │
│           IF Tier 0/1 → proceed to invocation                               │
│                                                                             │
│   STEP 5: CHECK GATE CONDITIONS (Tier 2 only)                               │
│           IF gate conditions not met → STOP, log V-GATE-001, CRITICAL       │
│           IF human approval required and not obtained → STOP, V-GATE-002    │
│                                                                             │
│   STEP 6: CHECK RATE LIMITS                                                 │
│           IF rate limit exceeded → WAIT or STOP per backoff strategy        │
│                                                                             │
│   STEP 7: INVOKE TOOL                                                       │
│           Log call with correlation_id                                      │
│           Track cost (Tier 1/2)                                             │
│                                                                             │
│   STEP 8: LOG RESULT                                                        │
│           Record success/failure                                            │
│           Update cost tracking                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Absence = Banned

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEFAULT DENY DOCTRINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   IF tool NOT in SNAP_ON_TOOLBOX.yaml:                                      │
│       → Tool is BANNED by default                                           │
│       → Usage is violation V-TOOL-001                                       │
│       → Severity: CRITICAL                                                  │
│       → Disposition: PARK                                                   │
│                                                                             │
│   IF hub NOT in tool's allowed_hubs:                                        │
│       → Tool is OUT OF SCOPE for that hub                                   │
│       → Usage is violation V-SCOPE-001                                      │
│       → Severity: CRITICAL                                                  │
│       → Disposition: PARK                                                   │
│                                                                             │
│   RULE: The canon is exhaustive. If it's not listed, it doesn't exist.     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Control

| Field | Value |
|-------|-------|
| Policy Version | 1.0.0 |
| Created | 2026-02-02 |
| Author | claude-code |
| Authority | SNAP_ON_TOOLBOX.yaml |
| Dependencies | ERROR_TTL_PARKING_POLICY.md |
| Enforcement Status | SPECIFICATION ONLY - NOT ENFORCED |
