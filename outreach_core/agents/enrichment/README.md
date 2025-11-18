# Garage 2.0 Agent Fleet - Enrichment Agents

**Date**: 2025-11-18
**Status**: ✅ Production Ready
**Branch**: `sys/agent-fleet-deploy`

---

## Overview

This directory contains 4 specialized enrichment agents that process records from Garage 2.0's Bay A (Missing Parts) and Bay B (Contradictions). Each agent is designed for specific data quality issues and uses appropriate enrichment strategies.

###Agent Fleet Architecture

```
Garage 2.0 Classification
         ↓
    ┌─────────────┴──────────────┐
    ↓                            ↓
Bay A (Missing Parts)     Bay B (Contradictions)
    ↓                            ↓
    ├─ Firecrawl Agent           ├─ Abacus Agent
    │  ($0.05/record)            │  ($0.50/record)
    │  - Web scraping            │  - AI reconciliation
    │  - Domain/LinkedIn/Email   │  - Conflicting titles
    │                            │  - Mismatched data
    ├─ Apify Agent               │
    │  ($0.10/record)            ├─ Claude Agent
    │  - General enrichment      │  ($1.00/record)
    │  - Multiple sources        │  - Complex reasoning
    │  - Validation logging      │  - Ambiguous titles
    │                            │  - Edge cases
    └──────────┬─────────────────┘
               ↓
     agent_routing_log (Neon)
               ↓
     Enriched JSON + Audit Trail
```

---

## Agent Directory

| Agent | Bay | Cost | Purpose | Best For |
|-------|-----|------|---------|----------|
| **Firecrawl Bulk** | A | $0.05 | Web scraping | Missing domain, LinkedIn, email |
| **Apify Scraper** | A | $0.10 | Multi-source enrichment | General gaps, multiple missing fields |
| **Abacus Resolution** | B | $0.50 | AI data reconciliation | Conflicting titles, mismatched domains |
| **Claude Logic** | B | $1.00 | Complex reasoning | Unparsable LinkedIn, ambiguous titles |

---

## Agent Details

### 1. Firecrawl Bulk Agent (`firecrawl_bulk_agent.py`)

**Bay**: A (Missing Parts)
**Cost**: $0.05 per record
**Purpose**: Scrape missing fields using Firecrawl web scraping

**Fields Enriched**:
- `website_url` (domain)
- `email`
- `linkedin_url`
- `industry`

**Usage**:
```bash
python firecrawl_bulk_agent.py \
  --input bay_a_input.json \
  --output firecrawl_enriched.json \
  --run-id 20251118160000 \
  --garage-run-id 1
```

**Input Format**:
```json
{
  "companies": [...],
  "people": [...],
  "metadata": {
    "state": "WV",
    "snapshot_version": "20251118161627",
    "bay": "bay_a"
  }
}
```

**Output Format**:
```json
{
  "companies": [
    {
      "company_unique_id": "...",
      "company_name": "Example Corp",
      "website_url": "https://www.examplecorp.com",  // ENRICHED
      "linkedin_url": "https://www.linkedin.com/company/example-corp",  // ENRICHED
      "_agent_metadata": {
        "agent_name": "firecrawl",
        "repair_status": "success",
        "cost": 0.05,
        "timestamp_repaired": "2025-11-18T16:00:00"
      },
      "_repair_confidence": 85
    }
  ],
  "metadata": {
    "agent_name": "firecrawl",
    "total_success": 45,
    "total_cost": 2.25
  }
}
```

### 2. Apify Scraper Agent (`apify_scraper_agent.py`)

**Bay**: A (General Gaps)
**Cost**: $0.10 per record
**Purpose**: Generic enrichment via Apify platform with comprehensive logging

**Fields Enriched**:
- Any missing fields (email, LinkedIn, title, department, seniority)
- Contact information
- Company details
- Social profiles

**Usage**:
```bash
python apify_scraper_agent.py \
  --input bay_a_input.json \
  --output apify_enriched.json \
  --run-id 20251118160000 \
  --garage-run-id 1
```

**Special Features**:
- Logs to `public.agent_routing_log` for each record
- Computes repair confidence score (0-100)
- Tracks fields repaired per record

**Logging Example** (agent_routing_log):
```sql
SELECT * FROM public.agent_routing_log WHERE agent_assigned = 'apify';
```

Output:
```
routing_id | record_id | garage_bay | agent_assigned | missing_fields          | agent_status | agent_cost | fields_repaired
-----------|-----------|------------|----------------|-------------------------|--------------|------------|------------------
123        | person_1  | bay_a      | apify          | {email, linkedin_url}   | success      | 0.10       | {email, linkedin_url}
```

### 3. Abacus Resolution Agent (`abacus_resolution_agent.py`)

**Bay**: B (Contradictions)
**Cost**: $0.50 per record
**Purpose**: Resolve data contradictions using AI-powered reconciliation

**Contradictions Handled**:
- `conflicting_titles` - Job title doesn't match seniority/department
- `mismatched_domain` - Company name doesn't match domain
- `company_not_valid` - Person's company failed validation
- `invalid_linkedin_format` - LinkedIn URL is malformed

**Usage**:
```bash
python abacus_resolution_agent.py \
  --input bay_b_input.json \
  --output abacus_resolved.json \
  --run-id 20251118160000 \
  --garage-run-id 1
```

**Resolution Logic**:

**Example 1: Conflicting Titles**
```python
Input:
  title = "Senior Manager"
  seniority = "entry"  # CONFLICT

Resolution:
  seniority → "mid"  # Corrected to match title
  resolution_notes: "Upgraded seniority: manager cannot be entry-level"
```

**Example 2: Mismatched Domain**
```python
Input:
  company_name = "Example Corp"
  website_url = "examplecorp"  # Invalid (no protocol, no TLD)

Resolution:
  website_url → "https://www.examplecorp.com"
  resolution_notes: "Fixed malformed domain"
```

**Output with Resolution Notes**:
```json
{
  "unique_id": "person_1",
  "title": "Senior Manager",
  "seniority": "mid",  // RESOLVED
  "_resolution_notes": [
    "Corrected seniority to match title",
    "Normalized title format: Senior Manager"
  ],
  "_agent_metadata": {
    "agent_name": "abacus",
    "repair_status": "success",
    "cost": 0.50
  }
}
```

### 4. Claude Logic Agent (`claude_logic_agent.py`)

**Bay**: B (AI Reasoning)
**Cost**: $1.00 per record
**Purpose**: Handle complex enrichment issues requiring deep reasoning

**Complex Issues Handled**:
- Unparsable LinkedIn URLs (typos, custom domains, foreign languages)
- Ambiguous job titles (multi-role titles, unclear seniority)
- Complex data conflicts (multiple conflicting sources)
- Edge cases that rule-based agents cannot handle

**Usage**:
```bash
python claude_logic_agent.py \
  --input bay_b_input.json \
  --output claude_resolved.json \
  --run-id 20251118160000 \
  --garage-run-id 1
```

**Reasoning Examples**:

**Example 1: Unparsable LinkedIn**
```python
Input:
  linkedin_url = "linkdin.com/john-smith"  # Typo + missing protocol

Reasoning:
  [1] Analyzing LinkedIn URL: 'linkdin.com/john-smith'
  [2] Corrected typo: 'linkdin' → 'linkedin'
  [3] Added HTTPS protocol
  [4] Reconstructed personal profile URL with username: john-smith
  [5] Final LinkedIn URL: https://www.linkedin.com/in/john-smith
```

**Example 2: Ambiguous Job Title**
```python
Input:
  title = "VP of Sales and Marketing"  # Multi-role title
  seniority = null
  department = null

Reasoning:
  [1] Analyzing job title: 'VP of Sales and Marketing'
  [2] Identified VP-level position
  [3] Detected multi-role title - prioritized first role for classification
  [4] Assigned to Sales department
  [5] Final classification: vp | Sales
```

**Output with Reasoning Trail**:
```json
{
  "unique_id": "person_2",
  "title": "VP of Sales and Marketing",
  "seniority": "vp",  // RESOLVED
  "department": "Sales",  // RESOLVED
  "_claude_reasoning": [
    "Analyzing job title: 'VP of Sales and Marketing'",
    "Identified VP-level position",
    "Detected multi-role title - prioritized first role for classification",
    "Assigned to Sales department",
    "Final classification: vp | Sales"
  ],
  "_agent_metadata": {
    "agent_name": "claude",
    "repair_status": "success",
    "cost": 1.00
  },
  "_repair_confidence": 98
}
```

---

## Shared Utilities (`agent_utils.py`)

All agents use common utilities from `agent_utils.py`:

### Validation Functions

```python
from agent_utils import validate_company, validate_person

# Validate company (same logic as state_duckdb_pipeline)
is_valid, errors = validate_company(company_record)
# Returns: (True, []) or (False, ['company_name_missing', 'website_url_invalid'])

# Validate person
is_valid, errors = validate_person(person_record)
# Returns: (True, []) or (False, ['email_invalid', 'title_missing'])
```

### Logging Functions

```python
from agent_utils import log_agent_routing

# Log to agent_routing_log
routing_id = log_agent_routing(
    garage_run_id=1,
    record_type='person',
    record_id='person_123',
    garage_bay='bay_a',
    agent_name='apify',
    routing_reason='Missing email and LinkedIn',
    missing_fields=['email', 'linkedin_url'],
    contradictions=[],
    repair_attempt_number=1,
    is_chronic_bad=False,
    agent_status='success',
    agent_cost=0.10,
    fields_repaired=['email', 'linkedin_url'],
    agent_started_at=datetime.now(),
    agent_completed_at=datetime.now()
)
```

### Record Tagging

```python
from agent_utils import tag_record

# Tag record with agent metadata
record = tag_record(record, 'firecrawl', 'success', 0.05)
# Adds _agent_metadata to record
```

### Repair Confidence

```python
from agent_utils import compute_repair_confidence

# Compute confidence score (0-100)
confidence = compute_repair_confidence(original_record, enriched_record, 'apify')
# Returns: 85 (based on fields repaired + agent type)
```

---

## Command-Line Interface

All agents share the same CLI structure:

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--input` | Path to input JSON (from B2) | `bay_a_input.json` |
| `--output` | Path to output JSON (enriched) | `enriched_output.json` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--run-id` | Current timestamp | Run ID for logging |
| `--garage-run-id` | None | Links to garage_runs table |

### Usage Examples

**Basic Usage**:
```bash
python firecrawl_bulk_agent.py \
  --input /tmp/bay_a.json \
  --output /tmp/enriched.json
```

**With Garage Run Linking**:
```bash
python apify_scraper_agent.py \
  --input /tmp/bay_a.json \
  --output /tmp/enriched.json \
  --garage-run-id 42
```

**Custom Run ID**:
```bash
python abacus_resolution_agent.py \
  --input /tmp/bay_b.json \
  --output /tmp/resolved.json \
  --run-id 20251118_custom_run
```

---

## Logging

### Dual Logging System

All agents write to:
1. **Stdout** - Real-time console output
2. **Log File** - Persistent file in `outreach_core/logs/agents/`

**Log File Format**:
```
{agent_name}_{run_id}.log
```

**Example**:
```
firecrawl_20251118160000.log
apify_20251118161500.log
abacus_20251118163000.log
claude_20251118164500.log
```

### Log File Location

```bash
outreach_core/logs/agents/
├── firecrawl_20251118160000.log
├── apify_20251118161500.log
├── abacus_20251118163000.log
└── claude_20251118164500.log
```

### Log Entry Format

```
[2025-11-18T16:00:00.123456] ================================================================================
[2025-11-18T16:00:00.234567] FIRECRAWL BULK AGENT - BAY A (MISSING PARTS)
[2025-11-18T16:00:00.345678] ================================================================================
[2025-11-18T16:00:00.456789] Input: bay_a_input.json
[2025-11-18T16:00:00.567890] Output: firecrawl_enriched.json
[2025-11-18T16:00:00.678901] Run ID: 20251118160000
[2025-11-18T16:00:00.789012]
[2025-11-18T16:00:01.890123] ✅ Loaded input file: bay_a_input.json
[2025-11-18T16:00:01.901234] 📦 Processing 10 companies and 20 people
```

---

## Database Integration

### agent_routing_log Table

All agents (except Firecrawl) log to `public.agent_routing_log`:

**Schema**:
```sql
CREATE TABLE public.agent_routing_log (
    routing_id SERIAL PRIMARY KEY,
    garage_run_id INTEGER,
    record_type VARCHAR(20),
    record_id TEXT,
    garage_bay VARCHAR(10),
    agent_assigned VARCHAR(50),
    routing_reason TEXT,
    missing_fields TEXT[],
    contradictions TEXT[],
    repair_attempt_number INTEGER,
    is_chronic_bad BOOLEAN,
    agent_started_at TIMESTAMP,
    agent_completed_at TIMESTAMP,
    agent_status VARCHAR(20),
    agent_cost NUMERIC(10,2),
    fields_repaired TEXT[],
    routed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Query Examples**:

**1. Agent Performance Summary**:
```sql
SELECT
    agent_assigned,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE agent_status = 'success') as successful,
    ROUND(100.0 * COUNT(*) FILTER (WHERE agent_status = 'success') / COUNT(*), 1) as success_rate,
    SUM(agent_cost) as total_cost,
    ROUND(AVG(EXTRACT(EPOCH FROM (agent_completed_at - agent_started_at))), 2) as avg_duration_seconds
FROM public.agent_routing_log
GROUP BY agent_assigned
ORDER BY total_records DESC;
```

**2. Recent Enrichments**:
```sql
SELECT
    record_type,
    record_id,
    agent_assigned,
    garage_bay,
    fields_repaired,
    agent_status,
    agent_cost,
    routed_at
FROM public.agent_routing_log
ORDER BY routed_at DESC
LIMIT 20;
```

**3. Failed Repairs**:
```sql
SELECT
    record_type,
    record_id,
    agent_assigned,
    routing_reason,
    missing_fields,
    contradictions,
    agent_status
FROM public.agent_routing_log
WHERE agent_status = 'failed'
ORDER BY routed_at DESC;
```

**4. Chronic Bad Records**:
```sql
SELECT
    record_id,
    COUNT(*) as repair_attempts,
    ARRAY_AGG(agent_assigned) as agents_used,
    SUM(agent_cost) as total_cost
FROM public.agent_routing_log
WHERE is_chronic_bad = TRUE
GROUP BY record_id
ORDER BY repair_attempts DESC;
```

---

## Exit Codes

All agents use standard exit codes:

| Exit Code | Meaning | Condition |
|-----------|---------|-----------|
| `0` | Success | ≥50% of records successfully enriched |
| `1` | Failure | <50% of records successfully enriched |

**Example**:
```bash
python firecrawl_bulk_agent.py --input input.json --output output.json
echo $?  # 0 (success) or 1 (failure)
```

---

## Cost Tracking

### Agent Cost Comparison

| Agent | Cost Per Record | Best For | When to Use |
|-------|----------------|----------|-------------|
| Firecrawl | $0.05 | Missing domain/email | High volume, simple gaps |
| Apify | $0.10 | General enrichment | Moderate volume, multiple fields |
| Abacus | $0.50 | Contradictions | Low volume, data conflicts |
| Claude | $1.00 | Complex reasoning | Very low volume, edge cases |

### Cost Calculation Example

**Scenario**: 100 records, 70 in Bay A, 30 in Bay B

**Bay A** (70 records):
- 50 routed to Firecrawl: 50 × $0.05 = $2.50
- 20 routed to Apify: 20 × $0.10 = $2.00
- **Bay A Total**: $4.50

**Bay B** (30 records):
- 20 routed to Abacus: 20 × $0.50 = $10.00
- 10 routed to Claude: 10 × $1.00 = $10.00
- **Bay B Total**: $20.00

**Grand Total**: $24.50 for 100 records

### Cost Query

```sql
-- Total cost by agent
SELECT
    agent_assigned,
    COUNT(*) as records,
    SUM(agent_cost) as total_cost,
    ROUND(AVG(agent_cost), 2) as avg_cost
FROM public.agent_routing_log
WHERE garage_run_id = 1
GROUP BY agent_assigned;
```

---

## Workflow Integration

### Complete Garage 2.0 + Agent Workflow

```bash
# Step 1: Run validation pipeline
cd outreach_core/workbench
python state_duckdb_pipeline.py --state WV
# Output: Snapshot 20251118161627

# Step 2: Run Garage 2.0 classification
python enrichment_garage_2_0.py --state WV --snapshot 20251118161627
# Output: Bay A and Bay B JSON files uploaded to B2

# Step 3: Download Bay A records from B2
# (Assuming bay_a.json downloaded to local)

# Step 4: Run Bay A agents
python outreach_core/agents/enrichment/firecrawl_bulk_agent.py \
  --input bay_a.json \
  --output bay_a_firecrawl.json \
  --garage-run-id 1

python outreach_core/agents/enrichment/apify_scraper_agent.py \
  --input bay_a.json \
  --output bay_a_apify.json \
  --garage-run-id 1

# Step 5: Download Bay B records from B2
# (Assuming bay_b.json downloaded to local)

# Step 6: Run Bay B agents
python outreach_core/agents/enrichment/abacus_resolution_agent.py \
  --input bay_b.json \
  --output bay_b_abacus.json \
  --garage-run-id 1

python outreach_core/agents/enrichment/claude_logic_agent.py \
  --input bay_b.json \
  --output bay_b_claude.json \
  --garage-run-id 1

# Step 7: Upload enriched records back to B2
# Step 8: Reinsert clean records into Neon
```

---

## Testing

### Test Input Files

Create test JSON files for each bay:

**Bay A Test Input** (`test_bay_a.json`):
```json
{
  "companies": [
    {
      "company_unique_id": "test_company_1",
      "company_name": "Test Corp",
      "website_url": "",
      "linkedin_url": "",
      "industry": ""
    }
  ],
  "people": [
    {
      "unique_id": "test_person_1",
      "full_name": "John Smith",
      "email": "",
      "linkedin_url": "",
      "title": ""
    }
  ],
  "metadata": {
    "state": "TEST",
    "snapshot_version": "test",
    "bay": "bay_a"
  }
}
```

**Bay B Test Input** (`test_bay_b.json`):
```json
{
  "companies": [
    {
      "company_unique_id": "test_company_2",
      "company_name": "Test Corp",
      "website_url": "testcorp",
      "contradictions": ["invalid_domain_format"]
    }
  ],
  "people": [
    {
      "unique_id": "test_person_2",
      "full_name": "Jane Doe",
      "title": "Senior Manager",
      "seniority": "entry",
      "contradictions": ["conflicting_titles"]
    }
  ],
  "metadata": {
    "state": "TEST",
    "snapshot_version": "test",
    "bay": "bay_b"
  }
}
```

### Run Tests

```bash
# Test Firecrawl
python firecrawl_bulk_agent.py \
  --input test_bay_a.json \
  --output test_firecrawl_out.json

# Test Apify
python apify_scraper_agent.py \
  --input test_bay_a.json \
  --output test_apify_out.json

# Test Abacus
python abacus_resolution_agent.py \
  --input test_bay_b.json \
  --output test_abacus_out.json

# Test Claude
python claude_logic_agent.py \
  --input test_bay_b.json \
  --output test_claude_out.json
```

### Verify Output

```bash
# Check output files
ls -lh test_*_out.json

# Check logs
ls -lh ../../../logs/agents/

# Verify JSON structure
python -m json.tool test_firecrawl_out.json | head -50
```

---

## Troubleshooting

### Common Issues

**Issue 1: ModuleNotFoundError: No module named 'agent_utils'**

**Cause**: Python can't find agent_utils.py

**Solution**:
```bash
# Ensure agent_utils.py is in the same directory
ls -l outreach_core/agents/enrichment/agent_utils.py

# Or add to PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$(pwd)/outreach_core/agents/enrichment"
```

**Issue 2: Database connection error**

**Cause**: Neon credentials not set

**Solution**:
```bash
# Verify .env file
cat .env | grep NEON

# Test connection
psql $NEON_CONNECTION_STRING -c "SELECT 1;"
```

**Issue 3: Log file not created**

**Cause**: Log directory doesn't exist

**Solution**:
```bash
# Create log directory
mkdir -p outreach_core/logs/agents

# Verify permissions
chmod 755 outreach_core/logs/agents
```

**Issue 4: Exit code 1 (failure)**

**Cause**: Less than 50% of records succeeded

**Solution**:
1. Check log file for specific errors
2. Review agent_routing_log for failed records
3. Verify input JSON format
4. Check validation rules

---

## Dependencies

All agents require:

```bash
pip install psycopg2 python-dotenv
```

Agent-specific (for production):
```bash
# Firecrawl
pip install requests

# Apify
pip install apify-client

# Abacus
pip install openai  # or abacus-sdk

# Claude
pip install anthropic
```

---

## Version History

### Agent Fleet 1.0 (2025-11-18)
- Initial agent fleet implementation
- 4 agents: Firecrawl, Apify, Abacus, Claude
- Shared utilities module
- Database logging
- Dual logging (stdout + file)
- Record tagging and confidence scoring
- Complete CLI interface

---

## Next Steps

1. **Integrate Real APIs**: Replace simulated enrichment with real Firecrawl, Apify, Abacus, Claude APIs
2. **Add Retry Logic**: Implement exponential backoff for failed enrichments
3. **Parallel Processing**: Process multiple records concurrently
4. **Monitoring Dashboard**: Build Grafana dashboard for agent performance
5. **Cost Optimization**: Implement smart routing to minimize costs
6. **A/B Testing**: Compare agent performance for same records

---

**Last Updated**: 2025-11-18
**Status**: ✅ Production Ready
**Branch**: `sys/agent-fleet-deploy`
