# 🚀 Generic Validation & Promotion Framework

**Schema-Agnostic Data Pipeline: Neon (Vault) → Supabase (Workspace) → Validation → Promotion**

---

## 📋 Overview

This framework provides a **completely generic, reusable system** for validating and promoting data between Neon PostgreSQL (vault) and Supabase (workspace).

**Key Features**:
- ✅ **Schema-Agnostic** - Works with ANY table structure
- ✅ **Configuration-Driven** - Add new entities via YAML, zero code changes
- ✅ **Doctrine Compliant** - Full audit trail and Barton ID support
- ✅ **Multi-Language** - Python and Node.js validators included
- ✅ **n8n Ready** - Workflow template for automation
- ✅ **Production-Grade** - Error handling, logging, cost tracking

---

## 🏗️ Architecture

```
┌──────────────┐
│  Neon (Vault)│
│              │
│  source_table│◄────── Raw data ingestion
│  ↓ processed │
│  target_table│◄────── Validated data promoted here
└──────────────┘
        │
        │ 1. Fetch unprocessed
        ↓
┌─────────────────────┐
│  Supabase (Workspace)│
│                      │
│  workspace_table     │◄──── 2. Load for validation
│  validation_log      │◄──── 3. Run rules
│  audit_trail         │◄──── 4. Log everything
└─────────────────────┘
        │
        │ 5. Promote PASSED
        │ 6. Flag FAILED for enrichment
        ↓
┌──────────────┐
│  Neon Master │◄──── Only validated data
└──────────────┘
```

---

## 🎯 Use Cases

### Current Implementations
- **Company Data**: Intake → Validation → Company Master
- **People Data**: Intake → Validation → People Master

### Easy to Add
- Client data
- Benefits data
- Compliance records
- Any structured data requiring validation

---

## 🚀 Quick Start

### 1️⃣  Prerequisites

```bash
# Required
- Neon PostgreSQL account
- Supabase account
- Python 3.9+ or Node.js 18+
- (Optional) n8n account for automation

# Database Access
- Read/write access to Neon
- Read/write access to Supabase
```

### 2️⃣  Installation

```bash
# Clone or navigate to framework
cd ctb/data/validation-framework

# Install Python dependencies
cd scripts/python
pip install -r requirements.txt

# Or Node.js dependencies
cd scripts/nodejs
npm install
```

### 3️⃣  Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Required variables:
# - NEON_DATABASE_URL
# - SUPABASE_DATABASE_URL
```

### 4️⃣  Initialize Supabase

```bash
# Run initial setup SQL
psql $SUPABASE_DATABASE_URL -f sql/supabase_init.sql

# This creates:
# - validation_log table
# - audit_trail table
# - workspace tables (company_needs_enrichment, people_needs_enrichment)
# - helper views
```

### 5️⃣  Run Validation

```bash
# Python
python scripts/python/validator.py --entity company --batch-size 100

# Dry run (no database writes)
python scripts/python/validator.py --entity person --dry-run

# All entities
python scripts/python/validator.py --all-entities
```

---

## 📁 Directory Structure

```
validation-framework/
├── README.md                          # This file
├── .env.example                       # Environment template
│
├── config/
│   ├── validation_config.yaml        # Master configuration
│   └── entities/                      # Entity-specific configs
│       ├── company.yaml
│       └── person.yaml
│
├── sql/
│   ├── supabase_init.sql             # Initial Supabase setup
│   └── templates/                     # SQL templates
│       ├── workspace_table.sql
│       └── validation_log.sql
│
├── scripts/
│   ├── python/
│   │   ├── validator.py              # Main Python validator
│   │   ├── requirements.txt          # Python dependencies
│   │   └── run_validation.py        # CLI runner
│   └── nodejs/
│       ├── validator.js              # Main Node.js validator
│       ├── package.json              # Node dependencies
│       └── run_validation.js        # CLI runner
│
├── n8n/
│   ├── workflow_spec.json            # n8n workflow template
│   └── WORKFLOW_GUIDE.md             # n8n setup instructions
│
└── docs/
    ├── ADDING_NEW_ENTITY.md          # 3-step guide
    ├── ARCHITECTURE.md               # System design
    └── TROUBLESHOOTING.md            # Common issues
```

---

## ⚙️  Configuration

### Master Config: `config/validation_config.yaml`

```yaml
entities:
  company:
    enabled: true
    source_table: "intake.company_raw_intake"
    target_table: "marketing.company_master"
    workspace_table: "company_needs_enrichment"

    rules:
      - field: company_name
        rule: not_null
        severity: critical

      - field: website
        rule: starts_with
        params: { prefix: "http" }
        severity: warning
```

### Built-in Validation Rules

| Rule | Description | Example |
|------|-------------|---------|
| `not_null` | Value must not be null/empty | `company_name` |
| `min_length` | Minimum string length | `min_length: 2` |
| `contains` | Must contain substring | `email` contains `@` |
| `email_format` | Valid email format | `user@domain.com` |
| `phone_format` | Valid phone format | `+1234567890` |
| `url_format` | Valid URL format | `https://example.com` |
| `positive_integer` | Must be positive integer | `employee_count` |
| `in_range` | Number within range | `revenue: [0, 1000000]` |

**Add custom rules** by extending `ValidationEngine` class in `validator.py`

---

## 🔧 Adding a New Entity (3 Steps)

### Step 1: Add to Configuration

Edit `config/validation_config.yaml`:

```yaml
entities:
  your_entity:
    enabled: true
    source_table: "intake.your_entity_raw"
    target_table: "marketing.your_entity_master"
    workspace_table: "your_entity_needs_enrichment"
    key_field: "unique_id"

    field_mapping:
      source_field: target_field

    rules:
      - field: required_field
        rule: not_null
        severity: critical
```

### Step 2: Create Supabase Workspace Table

```sql
CREATE TABLE IF NOT EXISTS public.your_entity_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  payload JSONB NOT NULL,
  validation_status TEXT DEFAULT 'PENDING',
  validation_errors JSONB,
  validation_warnings JSONB,
  -- ... (copy from template in supabase_init.sql)
);
```

### Step 3: Run Validator

```bash
python scripts/python/validator.py --entity your_entity
```

**That's it!** Framework handles the rest automatically.

---

## 🤖 n8n Automation

### Import Workflow

1. Open n8n
2. Create new workflow
3. Import `n8n/workflow_spec.json`
4. Configure credentials (Neon, Supabase)
5. Update "Set Entity Config" node
6. Test and activate

### Workflow Steps

1. **Schedule Trigger** - Runs every 30 min (configurable)
2. **Fetch from Neon** - Get unprocessed records
3. **Load to Supabase** - Insert into workspace
4. **Run Validator** - Execute Python/Node script
5. **Check Results** - Query validation status
6. **Split by Status** - Route PASSED vs FAILED
7. **Promote** - PASSED → Neon master
8. **Flag Enrichment** - FAILED → Needs review
9. **Mark Processed** - Update source table
10. **Notify** - Send to dashboard/Slack

---

## 📊 Monitoring

### View Pending Validations

```sql
SELECT * FROM public.vw_pending_validations;
```

### View Failed Validations

```sql
SELECT * FROM public.vw_failed_validations;
```

### View Ready for Promotion

```sql
SELECT * FROM public.vw_ready_for_promotion;
```

### Check Validation Log

```sql
SELECT entity, status, COUNT(*)
FROM public.validation_log
WHERE timestamp > now() - INTERVAL '24 hours'
GROUP BY entity, status;
```

---

## 🛡️ Doctrine Compliance

### Barton ID Format
```
NN.NN.NN.NN.NNNNN.NNN
```

Framework enforces:
- ✅ All promoted records must have valid Barton IDs
- ✅ Complete audit trail in `audit_trail` table
- ✅ Validation log retention (90 days default)
- ✅ Timestamp tracking on all operations

### Data Quality Gates

- **Minimum Pass Rate**: 80% (configurable)
- **Maximum Error Rate**: 10% (configurable)
- **Critical Errors**: Block promotion
- **Warnings**: Allow promotion with review

---

## 💰 Cost Tracking

Framework tracks costs for:
- Validation operations
- Promotion operations
- Enrichment operations (future)

View costs:

```sql
SELECT
  entity,
  SUM(cost_usd) as total_cost,
  COUNT(*) as operations
FROM validation_log
WHERE timestamp > now() - INTERVAL '30 days'
GROUP BY entity;
```

---

## 🐛 Troubleshooting

### Validator Not Connecting

```bash
# Test Neon connection
psql $NEON_DATABASE_URL -c "SELECT 1;"

# Test Supabase connection
psql $SUPABASE_DATABASE_URL -c "SELECT 1;"
```

### No Records Fetched

```bash
# Check source table
psql $NEON_DATABASE_URL -c "
  SELECT COUNT(*)
  FROM intake.company_raw_intake
  WHERE processed_at IS NULL;
"
```

### Validation Failing

```bash
# Run with dry-run to see errors without writes
python scripts/python/validator.py --entity company --dry-run

# Check validation log
psql $SUPABASE_DATABASE_URL -c "
  SELECT * FROM validation_log
  WHERE status = 'FAILED'
  ORDER BY timestamp DESC
  LIMIT 10;
"
```

---

## 📚 Additional Documentation

- **[ADDING_NEW_ENTITY.md](docs/ADDING_NEW_ENTITY.md)** - Detailed guide with examples
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design deep-dive
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🔄 Typical Workflow

### Daily Operation

```bash
# Morning: Run validation for all entities
python scripts/python/validator.py --all-entities

# Check results
psql $SUPABASE_DATABASE_URL -c "
  SELECT entity, validation_status, COUNT(*)
  FROM (
    SELECT 'company' as entity, validation_status
    FROM company_needs_enrichment
    UNION ALL
    SELECT 'person', validation_status
    FROM people_needs_enrichment
  ) t
  GROUP BY entity, validation_status;
"

# Review failures
psql $SUPABASE_DATABASE_URL -c "
  SELECT * FROM vw_failed_validations LIMIT 20;
"

# Fix data or adjust rules, then re-run
```

---

## 🚀 Advanced Features

### Batch Processing

```bash
# Process in smaller batches
python scripts/python/validator.py --entity company --batch-size 50

# Process large volumes
python scripts/python/validator.py --entity company --batch-size 1000
```

### Custom Validation Rules

Add to `scripts/python/validator.py`:

```python
def _rule_custom_check(self, value: Any, params: Dict):
    """Your custom validation logic"""
    if not your_condition(value):
        return False, "Custom error message"
    return True, None
```

Then use in config:

```yaml
rules:
  - field: your_field
    rule: custom_check
    severity: critical
```

---

## 📈 Performance

### Benchmarks

- **Validation**: ~100 records/second
- **Promotion**: ~50 records/second
- **Database Query**: <100ms per operation

### Optimization Tips

- Adjust `batch_size` based on record complexity
- Use `concurrent_batches` for parallel processing
- Enable connection pooling for high volume
- Set appropriate indexes on `unique_id` fields

---

## 🤝 Contributing

Framework is designed to be extended. Common additions:

1. **New validation rules** → Add to `ValidationEngine`
2. **Custom enrichment agents** → Extend enrichment logic
3. **Additional languages** → Port validator to other languages
4. **Enhanced logging** → Add custom log formats

---

## 📄 License

Part of Barton Outreach Core - see repository root for license.

---

## 🆘 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review validation logs in Supabase
3. Run with `--dry-run` to debug
4. Check environment variables in `.env`

---

**Status**: Production Ready ✅
**Version**: 1.0.0
**Last Updated**: 2025-11-07
**CTB Branch**: data/validation-framework
**Barton ID**: 05.03.00
