# Outreach Doctrine A→Z
## The Canonical Guide to Barton Outreach Architecture

**Version**: 1.0
**Last Updated**: January 2025
**Status**: Current Architecture (No Render)

---

## 1️⃣ Executive Summary

The **Barton Outreach Doctrine** is a multi-altitude, zero-wandering cold outreach system that orchestrates the complete journey from raw company data to qualified sales opportunities.

### The Outreach Funnel

```
Ingest → Enrich → Verify → Segment → Message → BIT → PLE → Book → Promote
```

**Pipeline Flow**:

1. **Ingest**: Companies and contacts loaded via Lovable.dev UI
2. **Enrich**: Apify scrapes company websites, LinkedIn, news sources
3. **Verify**: MillionVerify validates email deliverability (green/yellow/red/gray)
4. **Segment**: Contacts assigned to company slots (CEO/CFO/HR) based on renewal windows
5. **Message**: VibeOS generates personalized outreach via Composio MCP
6. **BIT**: Buyer Intent Tool tracks signals (renewal windows, executive movement, funding)
7. **PLE**: Pipeline Logic Engine perpetually loops leads through re-engagement
8. **Book**: Qualified meetings scheduled and tracked
9. **Promote**: Successful deals handed to Account Coordinators

### Platform Architecture

| Platform | Role | Repository |
|----------|------|------------|
| **Lovable.dev** | Ingestor UI + Triggers | `ingest-companies-people` |
| **Composio MCP** | Integration bus for 100+ tools | Hosted service (port 3001) |
| **Neon PostgreSQL** | Structured vault (5 schemas) | `barton-outreach-core` |
| **Firebase** | Visualization layer + staging memory | `barton-pipeline-vision` |
| **barton-outreach-core** | Doctrine + Agents + Registry | `barton-outreach-core` |

### Key Architectural Principles

- **Zero-Wandering Queues**: Views auto-populate work based on TTL timestamps (30-day default)
- **Slot-Based Contact Management**: Every company has exactly 3 slots (CEO, CFO, HR)
- **HEIR Agent System**: 12 specialized agents orchestrate all operations
- **Composio-First Integration**: No direct API calls—everything flows through Composio MCP
- **Doctrine Compliance**: All operations use HEIR/ORBT payload format

---

## 2️⃣ Architecture Map (with GitHub Repos)

| Altitude | Phase | Platform | GitHub Repo | Description |
|----------|-------|----------|-------------|-------------|
| **30k** | Vision | Doctrine Tracker (Lovable.dev) + Neon registry | `barton-outreach-core` | Doctrine definitions, process registry, agent definitions, HEIR orchestration system |
| **20k** | Category | Lovable.dev Ingestor → Neon via Composio | `ingest-companies-people` | Intake UI for 5 target states; pushes to `marketing.company_intake` table in Neon |
| **10k** | Specialization | Apify → MillionVerify → VibeOS via Composio | `barton-outreach-core` | Enrichment (web scraping), verification (email validation), messaging (AI-powered segmentation) |
| **5k** | Execution | VibeOS + BIT + PLE (Composio) | `barton-outreach-core` | Campaign delivery, buyer-intent tracking, perpetual lead loop for re-engagement |
| **1k** | Visualization | Firebase dashboards | `barton-pipeline-vision` | Pipeline visuals + analytics (read-only mirror of Neon data for real-time dashboards) |

### Repository Breakdown

#### **barton-outreach-core** (Primary Doctrine Repository)
- **Purpose**: Central orchestration, doctrine definitions, agent registry
- **Components**:
  - `/docs/` - Doctrine documentation (this file)
  - `/src/lib/heir/` - HEIR agent orchestration engine
  - `/agents/specialists/` - Apify, MillionVerify, Instantly runners
  - `/api/` - Vercel serverless functions
  - `/config/` - MCP configuration, database schema definitions
  - Database schema migrations and views

#### **ingest-companies-people** (Lovable.dev Ingestor)
- **Purpose**: Data intake UI for manual and bulk company/contact uploads
- **Features**:
  - 5-state targeting (initial focus states)
  - CSV upload for bulk ingestion
  - Direct Neon writes via Composio MCP
  - Real-time validation and deduplication

#### **barton-pipeline-vision** (Firebase Visualization)
- **Purpose**: Real-time dashboards and analytics
- **Features**:
  - Read-only mirror of Neon data
  - Pipeline stage visualization
  - Campaign performance metrics
  - Agent activity monitoring

---

## 3️⃣ ASCII Architecture Diagram

```
                [ Lovable.dev Ingestor ]
                      (Repo: ingest-companies-people)
                                |
                                | via Composio MCP
                                v
        [ Neon Vault ]  (Repo: barton-outreach-core)
          Tables: company, people, message_templates, bit, ple
                                |
             +-------------------------------------------+
             |                                           |
             v                                           v
    [ Apify / MillionVerify / VibeOS ]          [ Firebase Visualization ]
        (all via Composio MCP)                      (Repo: barton-pipeline-vision)
                                |
                            Agents:
               Claude Code + DeepAgent + Validator Agent
               (operate inside barton-outreach-core)
```

### Data Flow Explanation

1. **Lovable.dev Ingestor** captures raw company/contact data from user input or CSV upload
2. **Composio MCP** receives the payload and writes to Neon's `marketing.company_intake` table
3. **Neon Vault** stores structured data across 5 schemas (company, people, marketing, bit, ple)
4. **Zero-Wandering Queues** (Neon views) auto-populate work items based on 30-day TTL:
   - `company.next_company_urls_30d` → URLs needing scraping
   - `people.next_profile_urls_30d` → Profiles needing enrichment
   - `people.due_email_recheck_30d` → Emails needing verification
5. **Apify Agent** scrapes URLs from queue, updates `last_site_checked_at` timestamp
6. **MillionVerify Agent** validates emails, updates `email_status` (green/yellow/red/gray)
7. **VibeOS Agent** generates personalized messages for verified contacts
8. **BIT (Buyer Intent Tool)** writes signals to `bit.signal` table (renewal windows, executive changes)
9. **PLE (Pipeline Logic Engine)** loops leads through re-engagement based on response data
10. **Firebase Visualization** mirrors Neon data for real-time dashboards and analytics

---

## 4️⃣ Doctrine Layers

### **30,000 ft - Vision Layer**

**Role**: Define the "why" and "what" of the outreach doctrine.

**Components**:
- Doctrine definitions (`/docs/pages/30000-vision.md`)
- Process registry (Neon table: `process_registry`)
- Agent definitions (HEIR schema in `/src/lib/heir/`)
- System-wide configuration (`mcp.config.json`, `heir.doctrine.yaml`)

**Data Sources**:
- Doctrine Tracker (Lovable.dev UI) pulls from Neon's process registry
- Agent registry defines capabilities, altitudes, and dependencies

**Example**:
```yaml
# heir.doctrine.yaml
agents:
  - name: apollo_orchestrator
    altitude: 10000
    capabilities: [lead_enrichment, company_discovery]
    dependencies: [composio_mcp, neon_db]
```

---

### **20,000 ft - Category Layer**

**Role**: Categorize and intake raw data into structured schemas.

**Platform**: Lovable.dev Ingestor (`ingest-companies-people`)

**Process**:
1. User uploads CSV or manually enters company/contact data
2. Ingestor validates data against schema (required: company name, optional: EIN, website, renewal month)
3. Composio MCP writes to Neon's `marketing.company_intake` table
4. Promotion logic moves validated records to `company.company` table
5. Automatic creation of 3 company slots (CEO, CFO, HR)

**Data Flow**:
```
Lovable UI → Composio MCP → Neon (marketing.company_intake) → Promotion → company.company
```

**Key Tables**:
- `marketing.company_intake` - Temporary staging table
- `company.company` - Promoted company records
- `company.company_slot` - Role-based contact slots

---

### **10,000 ft - Specialization Layer**

**Role**: Enrich, verify, and segment data using specialized agents.

**Platform**: `barton-outreach-core` with Composio MCP integrations

**Agents**:
1. **Apify Agent** (`/agents/specialists/apifyRunner.js`)
   - Scrapes company websites, LinkedIn pages, news sources
   - Updates `last_site_checked_at`, `last_linkedin_checked_at`, `last_news_checked_at`
   - Populates enrichment data in JSONB fields

2. **MillionVerify Agent** (`/agents/specialists/millionVerifyRunner.js`)
   - Validates email deliverability
   - Updates `people.contact_verification` table
   - Status codes: green (deliverable), yellow (risky), red (invalid), gray (unknown)

3. **VibeOS Agent** (AI-powered messaging)
   - Generates personalized outreach messages
   - Uses company enrichment data + contact title
   - Writes to `marketing.message_log` table

**Data Flow**:
```
Neon Queue Views → Agent Polls Queue → Composio MCP → External Service → Agent Updates Neon → Item Disappears from Queue
```

**Example Queue Query**:
```sql
-- Get companies needing website scraping
SELECT company_id, website_url, last_site_checked_at
FROM company.next_company_urls_30d
WHERE url_type = 'website'
LIMIT 10;
```

---

### **5,000 ft - Execution Layer**

**Role**: Deliver campaigns, track buyer intent, perpetually loop leads.

**Platform**: `barton-outreach-core` with BIT + PLE modules

**Components**:

1. **BIT (Buyer Intent Tool)**
   - Tracks signals that indicate buying intent
   - Signal types:
     - `renewal_window_open_120d` - Company in renewal window (120 days before renewal month)
     - `executive_movement` - Leadership changes detected via LinkedIn scrapes
     - `funding_raised` - New funding announcements from news scrapes
     - `job_postings` - Relevant job postings found
   - Writes to `bit.signal` table with JSONB payload

2. **PLE (Pipeline Logic Engine)**
   - Perpetual lead loop for re-engagement
   - Rules-based automation:
     - No response after 7 days → Send follow-up #1
     - No response after 14 days → Send follow-up #2
     - No response after 30 days → Move to long-term nurture
     - Positive response → Create booking event
   - Future schema: `ple.*` tables

3. **Campaign Execution**
   - Reads from `company.vw_due_renewals_ready` (companies in renewal window with green contacts)
   - Creates campaign in `marketing.campaign`
   - Adds contacts to `marketing.campaign_contact`
   - Logs all messages to `marketing.message_log`

**Data Flow**:
```
BIT Detects Signal → PLE Evaluates Rules → Campaign Created → Messages Sent → Responses Tracked → Loop Continues
```

**Example BIT Signal**:
```json
{
  "signal_id": 12345,
  "company_id": 67890,
  "reason": "renewal_window_open_120d",
  "payload": {
    "renewal_month": 6,
    "next_renewal_date": "2025-06-01",
    "campaign_window_start": "2025-02-01"
  },
  "created_at": "2025-01-20T10:00:00Z"
}
```

---

### **1,000 ft - Visualization Layer**

**Role**: Provide real-time dashboards and analytics for campaign monitoring.

**Platform**: Firebase (`barton-pipeline-vision`)

**Features**:
- **Pipeline Dashboard**: Visual funnel showing count at each stage
- **Campaign Performance**: Open rates, reply rates, booking rates
- **Agent Activity**: Real-time monitoring of agent tasks
- **Queue Status**: Current size of scraping/verification queues

**Data Sync**:
- Firebase Cloud Functions mirror Neon data on change events
- Read-only access to prevent data corruption
- Real-time updates via Firestore listeners

**Example Visualization**:
```
Ingested: 1,500 companies
  ↓
Enriched: 1,200 companies (80%)
  ↓
Verified: 900 contacts (60%)
  ↓
Messaged: 450 contacts (30%)
  ↓
Booked: 45 meetings (3%)
  ↓
Promoted: 15 deals (1%)
```

---

## 5️⃣ How Data Flows Between Altitudes

### **Complete Pipeline Journey**

```
30k (Doctrine) → Defines rules and agent capabilities
       ↓
20k (Ingest) → Lovable.dev captures company data → Neon intake table
       ↓
10k (Specialize) → Agents enrich, verify, segment → Neon company/people tables
       ↓
5k (Execute) → BIT detects signals → PLE creates campaigns → Messages sent
       ↓
1k (Visualize) → Firebase dashboards show real-time metrics
```

### **Doctrine Tracker Integration**

The **Doctrine Tracker** (Lovable.dev UI) pulls from Neon's process registry to display:
- Active processes and their current altitude
- Agent task status and completion rates
- System health metrics (queue sizes, error rates)
- Historical audit trail (all operations logged with HEIR/ORBT format)

**Query Example**:
```sql
-- Get all active processes
SELECT process_id, process_name, altitude, status, created_at
FROM process_registry
WHERE status = 'active'
ORDER BY altitude DESC;
```

---

## 6️⃣ Database Schema Quick Reference

### **5 Neon Schemas**

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| **company** | Company data and slots | `company`, `company_slot` |
| **people** | Contacts and verification | `contact`, `contact_verification` |
| **marketing** | Campaigns and messages | `campaign`, `campaign_contact`, `message_log`, `booking_event`, `ac_handoff` |
| **bit** | Buyer intent signals | `signal` |
| **ple** | Pipeline logic (future) | TBD |

### **Zero-Wandering Queue Views**

These views automatically show work that needs doing:

- `company.next_company_urls_30d` - URLs needing scraping (30-day TTL)
- `people.next_profile_urls_30d` - Profiles needing enrichment
- `people.due_email_recheck_30d` - Emails needing re-verification

**How it works**:
1. Agent queries queue view
2. Agent processes items (scrape, verify, etc.)
3. Agent updates timestamp field (`last_site_checked_at`, `email_checked_at`, etc.)
4. Item automatically disappears from queue (TTL logic excludes recently updated records)

---

## 7️⃣ Agent Registry

### **HEIR Agent System (12 Agents)**

| Agent | Altitude | Role | Repository Location |
|-------|----------|------|---------------------|
| **Apollo Orchestrator** | 10k | Lead enrichment coordination | `/src/lib/agents/apolloOrchestrator.ts` |
| **Apify Orchestrator** | 10k | Web scraping coordination | `/agents/specialists/apifyRunner.js` |
| **MillionVerify Orchestrator** | 10k | Email verification | `/agents/specialists/millionVerifyRunner.js` |
| **Company Database Agent** | 5k | Company CRUD operations | `/src/lib/agents/companyDatabaseAgent.ts` |
| **People Database Agent** | 5k | Contact CRUD operations | `/src/lib/agents/peopleDatabaseAgent.ts` |
| **Marketing Database Agent** | 5k | Campaign CRUD operations | `/src/lib/agents/marketingDatabaseAgent.ts` |
| **Outreach Orchestrator** | 5k | Campaign delivery | `/agents/specialists/outreachRunner.js` |
| **Validator Agent** | 30k | Doctrine compliance checks | `/src/lib/agents/validatorAgent.ts` |
| **DeepAgent** | 20k | Multi-step reasoning | `/src/lib/agents/deepAgent.ts` |
| **BIT Agent** | 5k | Signal detection and tracking | `/src/lib/agents/bitAgent.ts` |
| **PLE Agent** | 5k | Lead loop automation | `/src/lib/agents/pleAgent.ts` |
| **Analytics Agent** | 1k | Dashboard data preparation | `/src/lib/agents/analyticsAgent.ts` |

**Agent Communication**:
- All agents use HEIR/ORBT payload format
- Agents coordinate via message queues (future: Redis)
- Agents log all operations to audit trail

---

## 8️⃣ Integration Points

### **Composio MCP Server (Port 3001)**

**Connected Services**:
- Gmail (3 accounts)
- Google Drive (3 accounts)
- Google Calendar (1 account)
- Google Sheets (1 account)
- Vercel (2 projects)
- GitHub (available)
- 100+ additional services

**Payload Format** (HEIR/ORBT):
```json
{
  "tool": "tool_name_here",
  "data": {
    "action": "list",
    "app": "GMAIL"
  },
  "unique_id": "HEIR-2025-01-BOOT-01",
  "process_id": "PRC-BOOT-001",
  "orbt_layer": 2,
  "blueprint_version": "1.0"
}
```

**Critical Rules**:
- ✅ ALWAYS use Composio MCP for external integrations
- ❌ NEVER create custom Google API integrations
- ✅ ALWAYS use HEIR/ORBT payload format
- ❌ NEVER skip Composio MCP and call APIs directly

---

## 9️⃣ Development Workflows

### **Local Development Setup**

```bash
# 1. Clone the repository
git clone https://github.com/djb258/barton-outreach-core.git
cd barton-outreach-core

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 4. Start Composio MCP server (REQUIRED)
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js

# 5. Start dev servers
npm run dev
```

### **Testing Workflows**

```bash
# Test MCP integration
npm run mcp:demo

# Test database connection
npm run neon:test

# Test Composio connectivity
node test-composio-endpoints.js

# Run compliance checks
npm run compliance:check

# Test agent operations
npm run scrape:apify
npm run verify:email
npm run outreach:run
```

### **Deployment Workflows**

**Frontend (Vercel)**:
```bash
# Automatic deployment on git push to main
git add .
git commit -m "feat: new feature"
git push origin main
```

**Backend (No Render - Vercel Serverless)**:
- API routes in `/api/` directory
- Auto-deployed with frontend
- Serverless functions handle backend logic

---

## 🔟 Next Steps

**Upcoming Enhancements**:
1. **Master Error Table**: Centralized error tracking across all agents
2. **Unique ID System**: Standardized HEIR ID generation and tracking
3. **Process ID Registry**: Complete process lifecycle management
4. **Redis Message Queue**: Replace polling with pub/sub architecture
5. **PLE Schema**: Full Pipeline Logic Engine table structure

---

**Next: add section on unique_id, process_id, and master error table.**
