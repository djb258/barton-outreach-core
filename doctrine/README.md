# SVG-PLE Doctrine Library

**Version**: 1.0.0
**Last Updated**: 2026-01-20
**Barton Doctrine Compliance**: 100%
**Status**: v1.0 OPERATIONAL BASELINE

---

## v1.0 OPERATIONAL BASELINE STATUS

**Certification Date**: 2026-01-19
**Certification Status**: PASS (Safe to enable live marketing)
**Baseline Freeze Date**: 2026-01-20

### Key Documents

| Document | Purpose |
|----------|---------|
| [GO-LIVE_STATE_v1.0.md](../docs/GO-LIVE_STATE_v1.0.md) | What is live vs intentionally incomplete |
| [DO_NOT_MODIFY_REGISTRY.md](./DO_NOT_MODIFY_REGISTRY.md) | Frozen components requiring change request |
| [FINAL_CERTIFICATION_REPORT_2026-01-19.md](../docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md) | Certification audit results |

### Frozen Components

The following are FROZEN at v1.0 and require formal change request to modify:
- Authoritative views (vw_marketing_eligibility_with_overrides, vw_sovereign_completion)
- Tier computation logic and assignment rules
- Kill switch system (manual_overrides, override_audit_log)
- Marketing safety gate (HARD_FAIL enforcement)
- Hub registry and waterfall order

See [DO_NOT_MODIFY_REGISTRY.md](./DO_NOT_MODIFY_REGISTRY.md) for complete list.

---

## 📚 What is This Library?

The **Doctrine Library** is the authoritative source of truth for the Shenandoah Valley Group Perpetual Lead Engine (SVG-PLE) architecture, design patterns, and operational procedures. Each doctrine document defines a component of the PLE system at multiple altitude levels (Vision → Operations).

**Purpose**:
- ✅ Onboard new team members with complete system knowledge
- ✅ Maintain architectural consistency across development
- ✅ Document design decisions and trade-offs
- ✅ Enable future spokes/components to integrate seamlessly
- ✅ Provide operational runbooks for system monitoring

---

## 🎯 Quick Start

### New to SVG-PLE?

Start here:
1. **Read**: [`PLE-Doctrine.md`](./ple/PLE-Doctrine.md) - Master system overview
2. **View**: [`PLE-Hub-Spoke-Axle.mmd`](./diagrams/PLE-Hub-Spoke-Axle.mmd) - Visual architecture
3. **Understand**: [`BIT-Doctrine.md`](./ple/BIT-Doctrine.md) - Intent scoring engine
4. **Explore**: [`Talent-Flow-Doctrine.md`](./ple/Talent-Flow-Doctrine.md) - Movement detection

### Implementing a New Feature?

Reference the relevant doctrine:
- **Adding new spoke**: See [Spoke Template](#spoke-template) below
- **Modifying BIT scoring**: See [`BIT-Doctrine.md` Section 3](./ple/BIT-Doctrine.md#section-3-scoring-logic-and-weight-table)
- **Enrichment agent**: See [`PLE-Doctrine.md` Altitude 5,000 ft](./ple/PLE-Doctrine.md#-altitude-5000-ft-operations)
- **Database schema**: See [`schemas/`](./schemas/) directory

### Troubleshooting?

Check operational sections:
- **BIT scores not updating**: [`BIT-Doctrine.md` Section 9](./ple/BIT-Doctrine.md#section-9-audit--compliance-rules)
- **Movement not detected**: [`Talent-Flow-Doctrine.md` Section 8](./ple/Talent-Flow-Doctrine.md#section-8-audit--data-lineage-rules)
- **Enrichment failures**: [`PLE-Doctrine.md` Error Handling](./ple/PLE-Doctrine.md#error-handling)

---

## 📖 Doctrine Index

### 🎯 Master Doctrines (Altitude 30,000 ft - Vision)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[PLE-Doctrine.md](./ple/PLE-Doctrine.md)** | `01.04.01.04.30000.001` | Master system overview - Hub, Spokes, Axle, Wheel | ✅ Active |

**What's Inside**:
- Vision (Why PLE exists)
- System composition (Hub, Spokes, Axle, Wheel Rim)
- Execution flow (Enrichment → Scoring → Outreach)
- Operations (Agent interactions, monitoring)
- Doctrine numbering registry
- Grafana panel references

**When to Read**:
- First time learning about PLE
- Architecting new system components
- Understanding cross-system integration
- Onboarding new team members

---

### ⚙️ Component Doctrines (Altitude 20,000 ft - Category)

#### 🟡 Axle: BIT (Buyer Intent Tool)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[BIT-Doctrine.md](./ple/BIT-Doctrine.md)** | `01.04.03.04.10000.001` | Intent scoring engine - converts events to scores | ✅ Active |

**What's Inside**:
- Purpose and position (Axle of PLE)
- Logical flow (Event → Score → Category)
- Scoring logic (weights, decay, quality modifiers)
- Numbering convention (`01.04.03.04.10000.###`)
- Schema summary (tables, views, triggers)
- Example trigger (executive_movement → BIT event)
- Doctrine relationships (Hub/Spoke/Axle/Wheel)
- Cross-references (Grafana, APIs)
- Audit & compliance rules
- Example scenario (TechStart Inc case study)

**When to Read**:
- Implementing new BIT rules
- Debugging score calculations
- Understanding intent thresholds (Hot/Warm/Cold)
- Auditing BIT system compliance

**Related Schema**: [`schemas/bit-schema.sql`](./schemas/bit-schema.sql)

---

#### 🔴 Spoke 1: Talent Flow (People Movement Detection)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[Talent-Flow-Doctrine.md](./ple/Talent-Flow-Doctrine.md)** | `01.04.02.04.20000.001` | Movement detection spoke - hires, departures, promotions | ✅ Active |

**What's Inside**:
- Purpose and position (Spoke of PLE feeding BIT)
- Logical flow (Hub → Talent Flow → BIT)
- Event classification (hire, departure, promotion, transfer)
- Schema explanation (movements, movement_audit)
- Trigger logic (auto-create BIT events)
- Numbering + ID examples (`01.04.02.04.20000`)
- Relationship to PLE and outreach
- Audit + data lineage rules
- Example scenario (Sarah Martinez HR Director)

**When to Read**:
- Configuring enrichment agents
- Debugging movement detection
- Understanding BIT event creation
- Auditing Talent Flow compliance

**Related Schema**: [`schemas/talent_flow-schema.sql`](./schemas/talent_flow-schema.sql)

---

#### 🔴 Spoke 2: Renewal Intelligence (Contract Tracking)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **Renewal-Doctrine.md** (to be created) | `01.04.02.04.21000.001` | Contract renewal tracking - 120d/90d/60d/30d windows | 📅 Planned |

**Planned Contents**:
- Renewal window detection logic
- Contract data sources (CRM, manual tracking)
- BIT event creation (renewal_window_XXd)
- Alert mechanisms
- Compliance monitoring

**When Available**: Q1 2026 (target)

**Related Schema**: `schemas/renewal-schema.sql` (to be created)

---

#### 🔴 Company Target: Identity Resolution

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[COMPANY_TARGET_IDENTITY.md](./ple/COMPANY_TARGET_IDENTITY.md)** | `01.04.02.04.21000.001` | Identity resolution with EIN fuzzy matching | ✅ Active |

**SCOPE**:
- EIN fuzzy matching (ONLY place fuzzy logic is allowed)
- EIN_NOT_RESOLVED failure → ENRICHMENT routing
- Execution gate for DOL Subhub
- Company identity validation

**CANONICAL RULE**:
- ✅ Fuzzy logic allowed ONLY in Company Target
- ❌ DOL Subhub must NEVER see fuzzy logic
- ❌ Analytics views must NEVER see fuzzy logic

**Related Code**: [`ctb/sys/company-target/identity_validator.js`](../ctb/sys/company-target/identity_validator.js)

---

#### 🔴 Spoke 3: DOL EIN Resolution (EIN Linkage ONLY)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[DOL_EIN_RESOLUTION.md](./ple/DOL_EIN_RESOLUTION.md)** | `01.04.02.04.22000.001` | EIN ↔ company_unique_id linkage (ISOLATED) | ✅ Active |

**SCOPE (Refactored 2025-01-01)**:
- EIN resolution from DOL/EBSA filings (Form 5500)
- Identity gate validation (FAIL HARD)
- Append-only storage (no updates, no overwrites)
- AIR event logging for all operations

**EXECUTION GATE (CRITICAL)**:
- DOL requires: `ein IS NOT NULL` AND `company_target_status = PASS`
- If EIN not resolved → blocked until ENRICHMENT completes

**EXPLICIT NON-GOALS (REMOVED)**:
- ❌ NO buyer intent scoring
- ❌ NO BIT event creation
- ❌ NO OSHA/EEOC tracking
- ❌ NO Slack/Salesforce/Grafana integration
- ❌ NO outreach triggers
- ❌ NO fuzzy matching (Company Target only)

**Related Schema**: [`schemas/dol_ein_linkage-schema.sql`](./schemas/dol_ein_linkage-schema.sql)

---

#### 📊 Form 5500 Projection Layer (Read-Only Analytics)

| Document | Barton ID | Description | Status |
|----------|-----------|-------------|--------|
| **[5500_PROJECTION_LAYER.md](./ple/5500_PROJECTION_LAYER.md)** | `01.04.02.04.22100.001` | Read-only views for renewal month + insurance facts | ✅ Active |

**SCOPE (READ-ONLY VIEWS ONLY)**:
- `analytics.v_5500_renewal_month` — Renewal month extraction with confidence flags
- `analytics.v_5500_insurance_facts` — Schedule A / EZ facts on demand
- No writes, no scoring, no behavior

**EXPLICIT NON-GOALS**:
- ❌ Does NOT modify DOL Subhub
- ❌ Does NOT trigger campaigns
- ❌ Does NOT add scoring

**Related Migration**: `ctb/data/infra/migrations/011_5500_projection_views.sql`

---

### 🔵 Hub Doctrines (Core Data)

| Document | Description | Status |
|----------|-------------|--------|
| **[OUTREACH_DOCTRINE_A_Z_v1.3.2.md](../OUTREACH_DOCTRINE_A_Z_v1.3.2.md)** | Complete system documentation (marketing schema, Barton IDs) | ✅ Active |

**What's Inside**:
- Marketing schema (company_master, people_master, company_slot)
- Barton Doctrine ID format (`NN.NN.NN.NN.NNNNN.NNN`)
- Database architecture (Neon PostgreSQL)
- Enrichment tracking
- Error logging (shq_error_log)

**When to Read**:
- Understanding database structure
- Implementing Barton ID generation
- Debugging data integrity issues
- Compliance audits

---

## 🗺️ Visual Architecture

### Mermaid Diagrams

| Diagram | Description | Location |
|---------|-------------|----------|
| **[PLE-Hub-Spoke-Axle.mmd](./diagrams/PLE-Hub-Spoke-Axle.mmd)** | Master PLE architecture (color-coded) | [View](./diagrams/PLE-Hub-Spoke-Axle.mmd) |

**Color Coding**:
- 🔵 **Hub** (Blue): Core data lake (companies, people, jobs)
- 🟡 **Axle** (Gold): BIT scoring engine
- 🔴 **Spokes** (Crimson): Intelligence gathering (Talent Flow, Renewal, Compliance)
- 🔵 **Wheel Rim** (Teal): Outreach layer (email, CRM, alerts)

**How to View**:
- GitHub: Auto-renders Mermaid diagrams
- Obsidian: Install Mermaid plugin
- VS Code: Install Markdown Preview Mermaid Support extension
- Export PNG: Use [Mermaid Live Editor](https://mermaid.live/)

---

## 🗄️ Database Schemas

### Schema Files

| Schema | Description | Location | Status |
|--------|-------------|----------|--------|
| **bit-schema.sql** | BIT scoring engine (rules, events, scores) | [View](./schemas/bit-schema.sql) | ✅ Production |
| **talent_flow-schema.sql** | Talent Flow spoke (movements, audit) | [View](./schemas/talent_flow-schema.sql) | ✅ Production |
| **dol_ein_linkage-schema.sql** | DOL EIN Resolution spoke (EIN linkage ONLY) | [View](./schemas/dol_ein_linkage-schema.sql) | ✅ Production |
| **renewal-schema.sql** | Renewal Intelligence spoke | (to be created) | 📅 Planned |

### Schema Deployment

```bash
# Deploy BIT schema
psql $DATABASE_URL -f doctrine/schemas/bit-schema.sql

# Deploy Talent Flow schema
psql $DATABASE_URL -f doctrine/schemas/talent_flow-schema.sql

# Verify schema creation
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'bit';"
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'talent_flow';"
```

---

## 🏗️ Barton ID Registry

### ID Prefix Allocation

| Component | Barton ID Prefix | Range | Example | Usage |
|-----------|------------------|-------|---------|-------|
| **PLE Master** | `01.04.01.04.30000` | .001-.999 | `01.04.01.04.30000.001` | PLE-Doctrine.md |
| **Talent Flow** | `01.04.02.04.20000` | .001-.999 | `01.04.02.04.20000.001` | Talent-Flow-Doctrine.md |
| **Renewal** | `01.04.02.04.21000` | .001-.999 | `01.04.02.04.21000.001` | (future) |
| **Compliance** | `01.04.02.04.22000` | .001-.999 | `01.04.02.04.22000.001` | (future) |
| **Tech Stack** | `01.04.02.04.23000` | .001-.999 | `01.04.02.04.23000.001` | (future) |
| **Funding** | `01.04.02.04.24000` | .001-.999 | `01.04.02.04.24000.001` | (future) |
| **BIT** | `01.04.03.04.10000` | .001-.999 | `01.04.03.04.10000.001` | BIT-Doctrine.md |
| **BIT Rules** | `01.04.03.04.10000` | .101-.199 | `01.04.03.04.10000.101` | bit.rule_reference |
| **BIT Snapshots** | `01.04.03.04.10000` | .801-.899 | `01.04.03.04.10000.801` | bit.score_snapshots |
| **Company Master** | `04.04.02.04.30000` | .001-.999 | `04.04.02.04.30000.042` | marketing.company_master |
| **Company Slot** | `04.04.02.04.10000` | .001-.999 | `04.04.02.04.10000.123` | marketing.company_slot |
| **Error Log** | `04.04.02.04.40000` | .001-.999 | `04.04.02.04.40000.456` | public.shq_error_log |

### ID Format

```
NN.NN.NN.NN.NNNNN.NNN
│  │  │  │  │     │
│  │  │  │  │     └─ Entity ID (001-999)
│  │  │  │  └─────── Base Sequence (10000-40000)
│  │  │  └────────── Schema (04 = PLE system)
│  │  └───────────── Altitude (01=Vision, 02=Category, 03=Execution)
│  └──────────────── Application (04 = SVG-PLE)
└─────────────────── Subhive (01 = Marketing/Sales)
```

---

## 🎓 Doctrine Creation Template

### Spoke Template

Use this template when creating new spoke doctrines:

```markdown
# [Spoke Name] Doctrine — [Subtitle]
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.[XXXXX].001`
**Version**: 1.0.0
**Last Updated**: YYYY-MM-DD
**Altitude**: 20,000 ft (Category / Spoke Layer)
**Role**: [Description] spoke feeding BIT Axle
**Status**: Active | Production Ready

---

## Section 1: Purpose and Doctrine Position
[Why this spoke exists, position in PLE architecture]

## Section 2: Logical Flow (Hub → Spoke → BIT)
[Data flow from hub through spoke to BIT axle]

## Section 3: Event Classification Table
[Types of events detected, scoring rules]

## Section 4: Schema Explanation
[Database tables, columns, constraints]

## Section 5: Trigger Logic → Insert BIT Event
[Automatic BIT event creation logic]

## Section 6: Numbering + ID Examples
[Barton ID format and examples]

## Section 7: Relationship to PLE and Outreach
[Integration with other spokes, wheel rim]

## Section 8: Audit + Data Lineage Rules
[Compliance checks, monthly audits]

## Section 9: Example Scenario
[Real-world case study with timing and outcomes]
```

**File Naming**: `[Spoke-Name]-Doctrine.md` (e.g., `Renewal-Doctrine.md`)

**Schema File**: `schemas/[spoke_name]-schema.sql` (e.g., `renewal-schema.sql`)

---

## 📊 Grafana Dashboard References

### Active Dashboards

| Dashboard | URL | Description |
|-----------|-----|-------------|
| **SVG-PLE Overview** | [dbarton.grafana.net/d/svg-ple-dashboard](https://dbarton.grafana.net/d/svg-ple-dashboard) | BIT score heatmap, distribution, hot companies |
| **Executive Enrichment** | [dbarton.grafana.net/d/executive-enrichment-monitoring](https://dbarton.grafana.net/d/executive-enrichment-monitoring) | Pending enrichments, agent performance |
| **Barton Outreach** | [dbarton.grafana.net/d/barton-outreach-dashboard](https://dbarton.grafana.net/d/barton-outreach-dashboard) | Intent scores, movement events, opportunities |

### SQL Queries

**Location**: [`infra/docs/ENRICHMENT_TRACKING_QUERIES.sql`](../infra/docs/ENRICHMENT_TRACKING_QUERIES.sql)

**Contents**: 10 comprehensive queries for monitoring CFO/CEO/HR enrichments

---

## 🛠️ Integration Guides

### Obsidian Setup

1. **Create Vault**: Point to `/doctrine/` directory
2. **Install Plugins**:
   - Mermaid (for diagrams)
   - Dataview (for doctrine index)
   - Graph View (for doctrine relationships)
3. **Enable Links**: Settings → Files & Links → Automatically update links

**Linking Example**:
```markdown
The [[BIT-Doctrine]] receives events from [[Talent-Flow-Doctrine]].
See [[PLE-Hub-Spoke-Axle.mmd]] for visual architecture.
```

### GitKraken Workflow

1. **Open Repo**: File → Open Repository → barton-outreach-core
2. **Create Branch**: `feature/[spoke-name]-doctrine`
3. **Commit**: Stage files → Commit message → Push
4. **Pull Request**: Push → Create PR in GitHub

**Commit Message Format**:
```
feat: add [Spoke Name] doctrine and schema

- Created [Spoke-Name]-Doctrine.md with 9 sections
- Created schemas/[spoke_name]-schema.sql
- Updated doctrine/README.md index
- Added Mermaid diagram integration

Barton ID: 01.04.02.04.[XXXXX].001
Status: Production Ready
```

### GitHub Projects

**Board**: [SVG-PLE Development](https://github.com/orgs/shenandoah-valley-group/projects/1)

**Task Template**:
```markdown
## Task: Implement [Spoke Name] Doctrine

**Description**: Create complete doctrine and schema for [Spoke Name] spoke

**Deliverables**:
- [ ] [Spoke-Name]-Doctrine.md (9 sections)
- [ ] schemas/[spoke_name]-schema.sql
- [ ] Update doctrine/README.md
- [ ] Mermaid diagram (if needed)
- [ ] Test with sample data
- [ ] Verify Barton Doctrine compliance

**Barton ID**: 01.04.02.04.[XXXXX].001
**Altitude**: 20,000 ft (Category / Spoke)
**Status**: 📅 Planned → ⚙️ In Progress → ✅ Done
```

---

## ✅ Compliance Checklist

### Doctrine Document Requirements

Before merging any new doctrine:

- [ ] **Barton ID assigned** (from registry)
- [ ] **9 sections complete** (or equivalent structure)
- [ ] **Schema file created** (if database component)
- [ ] **Cross-references added** (to PLE-Doctrine.md, related doctrines)
- [ ] **Example scenario included** (real-world use case)
- [ ] **Mermaid diagram updated** (if architecture changes)
- [ ] **README.md updated** (add to index)
- [ ] **Audit queries provided** (monthly compliance checks)
- [ ] **Test data included** (sample INSERT statements)
- [ ] **Grafana panels documented** (if monitoring required)

### Schema File Requirements

- [ ] **CREATE SCHEMA** statement
- [ ] **All tables defined** (with comments)
- [ ] **Foreign keys configured** (with ON DELETE behavior)
- [ ] **Indexes created** (for common queries)
- [ ] **Triggers implemented** (auto-update, audit, BIT integration)
- [ ] **Helper functions** (queries, analysis)
- [ ] **Seed data** (standard configuration)
- [ ] **Verification queries** (post-deployment checks)
- [ ] **Example queries** (usage documentation)
- [ ] **Permissions** (role-based access)

---

## 📞 Support & Contributions

### Questions?

- **Architecture**: Review [PLE-Doctrine.md](./ple/PLE-Doctrine.md)
- **BIT Scoring**: Review [BIT-Doctrine.md](./ple/BIT-Doctrine.md)
- **Movement Detection**: Review [Talent-Flow-Doctrine.md](./ple/Talent-Flow-Doctrine.md)
- **Database**: Review [OUTREACH_DOCTRINE_A_Z_v1.3.2.md](../OUTREACH_DOCTRINE_A_Z_v1.3.2.md)

### Contributing

1. Read relevant doctrine(s) first
2. Create feature branch
3. Follow templates and checklists
4. Test thoroughly
5. Submit PR with detailed description
6. Link to GitHub Projects task

### Feedback

- **Doctrine Improvements**: Open issue with label `doctrine`
- **Schema Bugs**: Open issue with label `schema`
- **Architecture Suggestions**: Open issue with label `architecture`

---

## 📚 Additional Resources

### External Documentation

- **Barton Doctrine**: [OUTREACH_DOCTRINE_A_Z_v1.3.2.md](../OUTREACH_DOCTRINE_A_Z_v1.3.2.md)
- **Global Config**: [global-config.yaml](../global-config.yaml)
- **Schema Map**: [docs/schema_map.json](../docs/schema_map.json)
- **Bootstrap Guide**: [CLAUDE.md](../CLAUDE.md)

### Related Tools

- **Composio MCP**: Integration hub (port 3001)
- **Neon PostgreSQL**: Database (ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech)
- **Grafana Cloud**: Monitoring (https://dbarton.grafana.net)
- **GitHub Projects**: Task tracking

---

## 📋 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-07 | Barton Outreach Team | Initial doctrine library index creation |

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Barton Doctrine Compliance**: 100% ✅
