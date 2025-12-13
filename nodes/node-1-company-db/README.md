# Node 1: Company + DB (30k Altitude - Input Only)

## IMO (Input-Middle-Output)

### Input
- **Feeds**: Apollo exports, CSV uploads
- **UI**: Ingestor Control Panel, Company Upload Form

### Middle (Current Scope)
- Insert brand-new companies
- Assign company_uid (CO-YYYYMMDD-######)
- Create exactly 3 slots per company (CEO/CFO/HR)
- Each slot gets slot_uid (SL-<company_uid>-ROLE)
- NO people enrichment, email validation, or movement signals at this altitude

### Output
- Company records with company_uid
- Three slot records per company with distinct slot_uids
- Basic logs

## ORBT Framework

### Operate
- Log ingestor runs with timestamp and record count
- Track company creations with UIDs
- Monitor slot generation (3 per company)
- Basic health checks on insert operations

### Repair
- Dead-letter pattern for bad CSV rows
- Idempotent re-run capability (check existing UIDs)
- Error recovery with transaction rollback
- Manual intervention queue for complex failures

### Build
- Versioned SQL migrations (001_init.sql)
- CI checks for DDL validation
- Automated testing for UID generators
- Schema documentation maintained

### Train
- How to run the ingestor locally
- Understanding UID patterns (CO- and SL- prefixes)
- Role slot allocation (CEO/CFO/HR)
- Troubleshooting common import errors

## Acceptance Criteria (30k Altitude)

- [ ] Each new company gets a unique company_uid
- [ ] Each company has exactly 3 slots with distinct slot_uids
- [ ] Re-runs do not create duplicate slots (idempotent)
- [ ] CI: ddl-validate passes
- [ ] CI: orbt-check passes
- [ ] CI: lint passes
- [ ] No credentials in repository
- [ ] Dead-letter handling for bad rows

## UID Generation Patterns

### Company UID
Format: `CO-YYYYMMDD-######`
- CO: Company prefix
- YYYYMMDD: Date of creation
- ######: Sequential number (padded to 6 digits)

### Slot UID
Format: `SL-<company_uid>-<ROLE>`
- SL: Slot prefix
- company_uid: Parent company's UID
- ROLE: One of CEO, CFO, HR

## Local Development

### Prerequisites
- PostgreSQL 14+
- Node.js 18+
- CSV sample data

### Running the Ingestor
```bash
# Set up database
psql -f schema/001_init.sql

# Run ingestor with sample data
node ingestor/run.js --file ingestor/seed.sample.csv --dry-run

# Production run
node ingestor/run.js --file data/companies.csv --commit
```

### Testing UID Generation
```sql
-- Test company UID generation
SELECT gen_company_uid();

-- Test slot UID generation
SELECT gen_slot_uid('CO-20240101-000001', 'CEO');

-- Test full company insertion with slots
SELECT insert_company_with_slots(
  'Acme Corp',
  'acme.com',
  'apollo_123',
  '12-3456789'
);
```

## Folder Structure
```
node-1-company-db/
├── README.md              # This file
├── orchestration.yaml     # Garage-MCP + sub-agents
├── tools.yaml            # Neon functions + CI checks
├── schema/               # Database DDL
│   └── 001_init.sql     # Initial schema + functions
├── ingestor/            # Data intake
│   └── seed.sample.csv  # Sample data
├── ple/                 # (Future: People, Lead, Entity)
└── enrich/              # (Future: Data enrichment)
```

## Progress

📋 **Detailed Status**: [TODO.md](./TODO.md)

This node progresses through 4 altitudes:
- **30k**: Scaffolding & Contracts ⏳ *in progress*
- **20k**: People Linking & Validation ⏸️ *planned*
- **10k**: Scraper & PLE Mechanics ⏸️ *planned*  
- **5k**: Runtime & Operations ⏸️ *planned*

Current progress tracked in the TODO checklist. Node completion feeds into the [40k Star](../../docs/40k_star.md) tracking.

## Constraints
- No people enrichment at 30k altitude
- No email validation at this level
- No movement signal detection
- Keep credentials in environment variables
- All operations must be idempotent