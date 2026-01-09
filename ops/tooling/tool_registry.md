# Tool Registry (AUTHORITATIVE)

**Status:** LOCKED
**Last Updated:** 2026-01-07
**Authority:** This is the ONLY authoritative list of approved tools.

---

## CRITICAL RULES

1. **NO ADDITIONAL TOOLS ALLOWED** without ADR approval
2. Each tool is scoped to specific sub-hub(s)
3. Tier-2 tools: MAX ONE attempt per `outreach_context_id`
4. All spend logged against `(company_sov_id + outreach_context_id)`
5. Firewall must block illegal calls

---

## APPROVED TOOLS

| Tool | Tier | Allowed Sub-Hubs | Cost Class | Lifecycle Gate |
|------|------|------------------|------------|----------------|
| **Firecrawl** | 0 | Company Target | Free | None |
| **Google Places** | 0 | Company Target | Low | None |
| **Hunter.io** | 1 | Company Target | Low | >= ACTIVE |
| **Clearbit** | 1 | Company Target | Low | >= ACTIVE |
| **Apollo** | 1 | Company Target, People | Low | >= ACTIVE |
| **Prospeo** | 2 | Company Target | Premium | >= ACTIVE + BIT |
| **Snov** | 2 | Company Target | Premium | >= ACTIVE + BIT |
| **Clay** | 2 | Company Target, People | Premium | >= ACTIVE + BIT |
| **MillionVerifier** | 1 | People | Per-use | >= TARGETABLE |
| **DOL CSV** | Bulk | DOL | Free | >= ACTIVE |
| **EIN Matcher** | Local | DOL | Free | None |
| **Title Classifier** | Local | People | Free | None |
| **News Feed Parser** | Local | Blog | Free | None |
| **Signal Classifier** | Local | Blog | Free | None |
| **Email Sender** | Core | Outreach Execution | Per-use | >= TARGETABLE |
| **Engagement Tracker** | Core | Outreach Execution | Free | None |
| **Sequence Engine** | Core | Outreach Execution | Free | None |
| **SMTP Check** | Local | Company Target | Free | None |
| **MX Lookup** | Local | Gate Zero (external) | Free | None |
| **LinkedIn Check** | Local | Gate Zero (external) | Free | None |
| **Neon** | Core | All | Included | None |
| **n8n** | Core | Orchestration | Fixed | None |
| **Python** | Core | Workers | Free | None |
| **GitHub Actions** | Core | CI | Fixed | None |
| **DuckDB** | Core | Local | Free | None |
| **Backblaze B2** | Archive | Logs | Low | None |

---

## TIER DEFINITIONS

### Tier 0 (Free)
- No lifecycle gate required
- Unlimited calls
- Firecrawl, Google Places, Web Scraper

### Tier 1 (Low Cost)
- Requires lifecycle >= ACTIVE
- Call frequency monitored
- Hunter, Clearbit, Apollo, MillionVerifier

### Tier 2 (Premium)
- Requires lifecycle >= ACTIVE
- Requires BIT threshold met
- **MAX ONE attempt per outreach_context_id**
- Prospeo, Snov, Clay

### Bulk
- CSV-based batch processing
- DOL filings only

### Local
- No external API calls
- Free, unlimited

### Core
- Infrastructure tools
- Always available

---

## ENFORCEMENT RULES

### Before ANY Paid Tool Call:

```python
def can_call_tool(tool_name: str, tier: int, context: OutreachContext) -> bool:
    """
    Firewall check before tool execution.
    """
    # Rule 1: Context must be active
    if not context.is_active:
        return False

    # Rule 2: Context must not be expired
    if context.is_expired():
        return False

    # Rule 3: Lifecycle gate
    if tier >= 1:
        if context.lifecycle_state not in ['ACTIVE', 'TARGETABLE', 'ENGAGED', 'CLIENT']:
            return False

    # Rule 4: BIT threshold for Tier 2
    if tier == 2:
        if context.bit_score < 25:  # BIT_THRESHOLD_WARM
            return False

    # Rule 5: Single attempt for Tier 2
    if tier == 2:
        if context.has_tier2_attempt(tool_name):
            return False

    return True
```

### After ANY Tool Call:

```python
def log_tool_call(
    tool_name: str,
    tier: int,
    context_id: str,
    company_sov_id: str,
    cost_credits: float,
    success: bool,
    sub_hub: str
):
    """
    Log every tool call to spend_log.
    """
    outreach_ctx.log_tool_attempt(
        p_context_id=context_id,
        p_company_sov_id=company_sov_id,
        p_tool_name=tool_name,
        p_tool_tier=tier,
        p_cost_credits=cost_credits,
        p_success=success,
        p_sub_hub=sub_hub
    )
```

---

## COST ESTIMATES

| Tool | Cost per Call | Monthly Budget Alert |
|------|---------------|---------------------|
| Firecrawl | $0.0001 | N/A |
| Google Places | $0.003 | $50 |
| Hunter.io | $0.008 | $100 |
| Clearbit | $0.01 | $100 |
| Apollo | $0.005 | $100 |
| Prospeo | $0.003 | $50 |
| Snov | $0.004 | $50 |
| Clay | $0.01 | $100 |
| MillionVerifier | ~$0.0037 | $50 |

---

## VIOLATIONS

Any tool call that bypasses this registry is a **HARD VIOLATION**.

Violations must be:
1. Logged to `shq_error_log` with severity = CRITICAL
2. Blocked (not executed)
3. Reported in daily audit

---

## ADDING NEW TOOLS

To add a new tool:

1. Create ADR documenting:
   - Why this tool is needed
   - What it replaces or complements
   - Cost analysis
   - Lifecycle gate requirements

2. Get ADR approved by Hub Owner

3. Update this registry with:
   - Tool name
   - Tier assignment
   - Allowed sub-hubs
   - Cost class
   - Lifecycle gate

4. Implement firewall rules

5. Add to spend logging

**NO SHORTCUTS. NO EXCEPTIONS.**
