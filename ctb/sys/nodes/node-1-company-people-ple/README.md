<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-6C9C6CA8
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Node 1: Company + People Database + PLE (30k Altitude)

⚠️ **30k scaffolding only (no DDL/runtime)**

## IMO (Input-Middle-Output)

### Input
- **External Ingester**: [ingest-companies-people repo](https://github.com/djb258/ingest-companies-people)
- **Feeds**: Apollo.io data + CSV uploads (processed by external Ingester)
- **Interface**: Calls Render-for-DB endpoints for Neon database operations

### Middle (Current Scope - 30k)
- Assign company_uid (CO-YYYYMMDD-######) - **declared only**
- Create CEO/CFO/HR slots with slot_uids (SL-<company>-ROLE) - **declared only**  
- PLE (People-Lead-Entity) framework - **declared only**
- History policy management - **declared only**
- **Implementation deferred to higher altitudes**

### Output
- Company + slot UIDs (contract declared)
- PLE + History event declarations
- External dependency interface specifications

## ORBT Framework (30k Summary)

### Operate
- External Ingester dependency management
- Function contract interface declarations  
- Event schema definitions (no implementation)
- Orchestration build-only configuration

### Repair
- Dead-letter pattern declarations (via external Ingester)
- Idempotent operation contracts
- Error handling interface specifications
- External dependency failover strategies

### Build
- Contract-only schema placeholders
- CI checks for contract validation
- External repo dependency tracking
- Interface signature verification

### Train
- External Ingester integration documentation
- UID pattern specifications
- PLE event schema definitions
- Interface contract examples

## External Dependencies (30k)

### Primary Dependencies
- **Ingester Repository**: https://github.com/djb258/ingest-companies-people
  - **Purpose**: Apollo.io + CSV data ingestion and preprocessing
- **Render-for-DB Repository**: https://github.com/djb258/Render-for-DB.git
  - **Purpose**: Database interface layer for Neon database operations

### Integration Options (Declared)
1. Git submodule at `/external/ingestor` (future)
2. GitHub Actions artifact handoff (future)
3. Direct function contract interface (current 30k scope)

## Contracts (30k - Signature Only)

### Database Interface
```typescript
// Declared only - no implementation
function insert_company_with_slots(
  name: string,
  website?: string, 
  apollo_company_id?: string,
  ein_raw?: string
): company_id
```

### PLE Events (Declared)
- `SLOT_CREATED` - Role slot initialized
- `COMPANY_REGISTERED` - Company UID assigned  
- `PLE_DECLARED` - PLE framework event
- `HISTORY_TRACKED` - History policy event

## Altitude Constraints (30k)

❌ **Not Implemented at 30k**:
- No actual database DDL
- No runtime functions
- No people enrichment
- No email validation
- No movement signals
- No scraping logic

✅ **30k Scope Only**:
- Contract declarations
- Interface specifications
- External dependency management
- Event schema definitions
- Orchestration build configurations

## Folder Structure
```
node-1-company-people-ple/
├── README.md                    # This file
├── TODO.md                     # 30k checklist
├── orchestration.yaml          # Garage-MCP build-only config
├── tools.yaml                  # Contract signatures only
├── ingester/
│   └── INGESTER_DEPENDENCY.md  # External repo specifications
├── ple/
│   └── ple.contract.yaml       # PLE event declarations
└── history/
    └── history.contract.yaml   # History policy declarations
```

## Progress Tracking

📋 **Current Status**: 30k scaffolding in progress
📊 **Detailed Checklist**: [TODO.md](./TODO.md)
⭐ **40k Rollup**: [40k Star](../../docs/40k_star.md)