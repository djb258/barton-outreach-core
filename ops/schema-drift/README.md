# Schema Drift Detection Tools

**Purpose**: Detect and report drift between ERD documentation (SCHEMA.md files) and actual Neon PostgreSQL database schema.

## Files

| File | Purpose |
|------|---------|
| `schema_drift_checker.py` | Connects to Neon and extracts complete schema snapshot |
| `analyze_schema_drift.py` | Compares ERD documentation against Neon snapshot |
| `README.md` | This file |

## Usage

### 1. Extract Neon Schema Snapshot

```bash
# Run from repository root
doppler run -- python ops/schema-drift/schema_drift_checker.py
```

**Output**: `neon_schema_snapshot.json` (saved to repository root)

**Contains**:
- All tables in relevant schemas (outreach, cl, people, dol, company, bit)
- All views in relevant schemas
- Column definitions (name, type, nullable, default)
- Foreign key relationships
- Primary key constraints

### 2. Analyze Drift

```bash
# Run from repository root
python ops/schema-drift/analyze_schema_drift.py
```

**Output**:
- `ERD_NEON_DRIFT_REPORT.md` (detailed drift report)
- Console summary

**Reports**:
1. Tables in Neon but NOT in ERD (undocumented tables)
2. Tables in ERD but NOT in Neon (stale documentation)
3. Column mismatches (different columns between ERD and Neon)
4. Data type mismatches
5. Recommendations for remediation

## ERD Documentation Format

The analyzer expects SCHEMA.md files in hub directories:

```
hubs/
├── blog-content/SCHEMA.md
├── company-target/SCHEMA.md
├── dol-filings/SCHEMA.md
├── outreach-execution/SCHEMA.md
├── people-intelligence/SCHEMA.md
└── talent-flow/SCHEMA.md
```

Each SCHEMA.md should contain Mermaid ERD diagrams:

```markdown
## Entity Relationship Diagram

\`\`\`mermaid
erDiagram
    SCHEMA_TABLE_NAME {
        data_type column_name constraints
        uuid id PK
        text name
        timestamptz created_at
    }
\`\`\`
```

**Naming Convention**:
- Entity names use `SCHEMA_TABLE` format (uppercase, underscore-separated)
- Example: `OUTREACH_COMPANY_TARGET` maps to `outreach.company_target`

## Automated Checks

### Weekly Ops Checklist

Add to weekly operations routine:

```bash
# Extract fresh snapshot
doppler run -- python ops/schema-drift/schema_drift_checker.py

# Analyze drift
python ops/schema-drift/analyze_schema_drift.py

# Review changes
git diff ERD_NEON_DRIFT_REPORT.md
```

### CI/CD Integration (Future)

```yaml
# .github/workflows/schema-drift.yml
name: Schema Drift Check
on:
  pull_request:
    paths:
      - 'neon/migrations/**'
      - 'hubs/**/SCHEMA.md'
  schedule:
    - cron: '0 9 * * 1'  # Weekly Monday 9am

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Extract Neon Schema
        run: doppler run -- python ops/schema-drift/schema_drift_checker.py
      - name: Analyze Drift
        run: python ops/schema-drift/analyze_schema_drift.py
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('ERD_NEON_DRIFT_REPORT.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

## Snapshot Versioning

Consider versioning the snapshot for historical analysis:

```bash
# Snapshot with timestamp
doppler run -- python ops/schema-drift/schema_drift_checker.py
cp neon_schema_snapshot.json "ops/schema-drift/snapshots/snapshot_$(date +%Y%m%d).json"

# Compare against previous snapshot
python ops/schema-drift/compare_snapshots.py \
  ops/schema-drift/snapshots/snapshot_20260125.json \
  neon_schema_snapshot.json
```

## Known Limitations

1. **Views**: Currently extracts view names but not view definitions
2. **Indexes**: Does not extract index definitions
3. **Triggers**: Does not extract trigger definitions
4. **RLS Policies**: Does not extract Row Level Security policies
5. **Functions**: Does not extract stored procedures/functions
6. **Mermaid Parsing**: Limited to entity blocks with columns
7. **Complex Types**: May not fully parse array, JSON, or custom types

## Troubleshooting

### Issue: psql not found

**Solution**: Use the Python script directly (already implemented with psycopg2)

### Issue: Connection timeout

**Solution**:
- Check Doppler secrets are loaded
- Verify Neon database is accessible
- Check firewall/VPN settings

### Issue: No tables found in ERD

**Solution**:
- Verify SCHEMA.md files exist in hub directories
- Check Mermaid block format (must be `erDiagram`)
- Verify entity naming follows `SCHEMA_TABLE` convention

### Issue: Type mismatches

**Solution**:
- Common issue: `timestamp` vs `timestamp with time zone`
- ERD should use actual PostgreSQL types
- Use `timestamptz` for timezone-aware timestamps

## Contributing

When adding new tables to Neon:

1. Run drift checker BEFORE migration
2. Document new tables in appropriate SCHEMA.md
3. Run drift checker AFTER migration
4. Verify zero drift in report
5. Include drift report in PR

When updating ERD documentation:

1. Update SCHEMA.md with changes
2. Run drift checker
3. Verify mismatches are reduced
4. Commit both SCHEMA.md and updated drift report

## Maintenance

**Frequency**: Weekly (or after each schema migration)

**Owner**: Database Engineering Team

**Escalation**: If drift exceeds 10 tables or 50 columns, escalate to Architecture Team

---

**Created**: 2026-02-02
**Last Updated**: 2026-02-02
**Version**: 1.0.0
