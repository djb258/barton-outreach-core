<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-A64D533E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# Migration Manifest (30k Declaration)

**Status**: Schema planning only - NO DDL or migrations at 30k altitude

## Overview

This manifest declares the future database schema evolution strategy for the Company + People + PLE node. At 30k altitude, we define the migration approach but implement NO actual SQL or database operations.

## Migration Strategy (Declared)

### Altitude-Based Migration Plan

#### 30k - Schema Planning Only
- ❌ **NO DDL IMPLEMENTATION**
- ❌ **NO ACTUAL MIGRATIONS**
- ✅ **Schema design documentation only**
- ✅ **Migration strategy declarations**
- ✅ **Table structure planning**

#### 20k - Initial Schema Design
- Basic table definitions (company, company_slot, people)
- UID generation functions design
- Initial indexes and constraints planning
- Migration tooling selection

#### 10k - Advanced Schema Features
- PLE relationship tables
- History tracking tables
- Audit logging schema
- Performance optimization indexes

#### 5k - Production Schema Deployment
- Full DDL implementation
- Migration execution in production
- Schema monitoring and maintenance
- Backup and recovery procedures

## Planned Schema Components (Design Only)

### Core Tables (Future Implementation)
```sql
-- DESIGN ONLY - NO IMPLEMENTATION AT 30K

-- Companies table structure (planned)
marketing.company:
  - company_uid (PK): text, pattern CO-YYYYMMDD-######
  - company_name: text, required
  - website: text, unique
  - apollo_company_id: text, unique
  - ein_raw: text
  - created_at, updated_at: timestamp

-- Company slots table structure (planned)  
marketing.company_slot:
  - slot_uid (PK): text, pattern SL-<company_uid>-<ROLE>
  - company_uid (FK): references company(company_uid)
  - role: text, enum(CEO, CFO, HR)
  - person_id: text, nullable (future PLE integration)
  - status: text, enum(open, filled, pending)
  - created_at, updated_at: timestamp

-- People table structure (planned)
marketing.people:
  - person_id (PK): text, pattern PE-YYYYMMDD-######
  - name: text, required
  - email: text, unique
  - linkedin_url: text
  - validation_status: text
  - created_at, updated_at: timestamp
```

### Planned Functions (Design Only)
```sql
-- FUNCTION SIGNATURES ONLY - NO IMPLEMENTATION

-- UID Generation Functions (declared)
marketing.gen_company_uid() -> text
marketing.gen_slot_uid(company_uid text, role text) -> text  
marketing.gen_person_uid() -> text

-- Business Logic Functions (declared)
marketing.insert_company_with_slots(
  name text,
  website text,
  apollo_id text,
  ein text
) -> json

marketing.link_person_to_slot(
  person_id text,
  slot_uid text
) -> boolean
```

### Migration File Structure (Planned)
```
schema/migrations/
├── 001_initial_schema.sql        (20k altitude)
├── 002_add_people_table.sql      (20k altitude)
├── 003_add_ple_relationships.sql (10k altitude)
├── 004_add_history_tracking.sql  (10k altitude)
├── 005_performance_indexes.sql   (5k altitude)
└── rollback/                     (5k altitude)
    ├── 001_rollback.sql
    ├── 002_rollback.sql
    └── ...
```

## Migration Tooling Strategy (Declared)

### Database Migration Management
- **Tool**: TBD (Flyway, Alembic, or custom)
- **Version Control**: Git-based migration files
- **Environments**: Development → Staging → Production
- **Rollback Strategy**: Automated rollback scripts

### CI/CD Integration (Planned)
- **Validation**: DDL syntax checking in CI
- **Testing**: Migration testing in isolated environments  
- **Deployment**: Automated migration execution
- **Monitoring**: Migration success/failure tracking

## Data Integrity Strategy (Declared)

### Constraints and Validation
- **Primary Keys**: All tables have explicit PKs
- **Foreign Keys**: Referential integrity enforced
- **Unique Constraints**: Business logic uniqueness
- **Check Constraints**: Data validation rules

### Audit and Compliance
- **Audit Tables**: Change tracking for all core tables
- **Data Retention**: Configurable retention policies
- **Compliance**: PII handling and data sovereignty
- **Backup Strategy**: Automated backup and recovery

## Environment Configuration (Planned)

### Development Environment
- Local PostgreSQL with sample data
- Migration testing environment
- Schema validation tools
- Developer documentation

### Staging Environment  
- Production-like schema setup
- Migration rehearsal environment
- Performance testing dataset
- Integration testing suite

### Production Environment
- High availability configuration
- Automated backup and recovery
- Performance monitoring
- Disaster recovery procedures

## Schema Governance (Declared)

### Change Management Process
1. **Schema Design**: Document proposed changes
2. **Impact Analysis**: Assess breaking changes
3. **Migration Script**: Create forward and rollback scripts
4. **Testing**: Validate in staging environment
5. **Deployment**: Execute in production with monitoring
6. **Verification**: Confirm successful migration

### Documentation Requirements
- **Migration Log**: Track all schema changes
- **Breaking Changes**: Document compatibility impacts
- **Performance Impact**: Monitor query performance changes
- **Rollback Procedures**: Document recovery steps

## 30k Constraints

⚠️ **CRITICAL: NO IMPLEMENTATION AT 30K**

❌ **Forbidden at 30k**:
- No SQL DDL scripts
- No actual migration files
- No database connections
- No schema creation
- No data manipulation
- No function implementations

✅ **30k Scope Only**:
- Migration strategy documentation
- Schema design planning
- Tooling selection criteria
- Process definition
- Governance framework
- Future implementation roadmap

## Implementation Timeline

- **30k**: This manifest (planning only)
- **20k**: Initial schema design and basic migrations
- **10k**: Advanced features and relationship tables  
- **5k**: Production deployment and operational procedures

All actual SQL implementation is deferred to higher altitudes per 30k constraints.