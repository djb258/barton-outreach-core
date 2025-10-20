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

## 1️⃣1️⃣ Barton Doctrine Numbering System

The **Barton Doctrine Numbering System** provides a standardized, hierarchical identification scheme for all operations across the outreach pipeline. Every process execution is assigned both a **unique_id** (numeric, 6-part) and a **process_id** (human-readable, Verb + Object).

---

### **unique_id Format**

The `unique_id` follows a **6-part dotted decimal notation** that encodes the full operational context:

```
[database].[subhive].[microprocess].[tool].[altitude].[step]
```

### **Segment Breakdown**

| Segment | Description | Example |
|---------|-------------|---------|
| **database** | 2-digit code for Neon hive | `04` |
| **subhive** | 2-digit for doctrine subhive (e.g., 01 = outreach) | `01` |
| **microprocess** | 2-digit identifier for logical workflow group | `03` |
| **tool** | 2-digit from `shq_tool_registry` (e.g., Neon=04, Apify=05, VibeOS=06, MillionVerify=07, BIT=08, PLE=09) | `06` |
| **altitude** | 5-digit decimal (30000, 20000, 10000, 05000, 01000) | `05000` |
| **step** | 3-digit increment per microprocess | `001` |

### **Example unique_id**

```
04.01.03.06.05000.001
```

**Translation**:
- `04` = Neon database hive
- `01` = Outreach subhive
- `03` = Messaging microprocess group
- `06` = VibeOS tool
- `05000` = Execution altitude
- `001` = First step in messaging microprocess

**Human-readable**: "Send Segmented Messaging via VibeOS"

---

### **Tool Registry Reference**

| Tool Code | Tool Name | Purpose |
|-----------|-----------|---------|
| `04` | Neon | Database operations |
| `05` | Apify | Web scraping |
| `06` | VibeOS | AI-powered messaging |
| `07` | MillionVerify | Email verification |
| `08` | BIT | Buyer Intent Tool |
| `09` | PLE | Pipeline Logic Engine |
| `10` | Apollo | Lead enrichment |
| `11` | Instantly | Email delivery |
| `12` | HeyReach | LinkedIn outreach |

---

### **process_id Format**

The `process_id` is a **human-readable string** that describes the operation using the pattern:

```
[Verb] + [Object] + [Context]
```

**Examples**:
- `Load WV–OH Companies into Neon`
- `Enrich Contacts from Apify`
- `Verify Contacts with MillionVerify`
- `Send Segmented Messaging via VibeOS`
- `Process Buyer Intent Signals`

**Rules**:
- Start with an action verb (Load, Enrich, Verify, Send, Process, etc.)
- Include the object being acted upon (Companies, Contacts, Signals, etc.)
- Add context if needed (from/via/with tool name)
- Keep it under 60 characters for readability

---

### **Process ID Mapping Table**

This table maps existing operations to their doctrine-compliant IDs:

| Altitude | Process ID | unique_id | Tool | Table |
|----------|------------|-----------|------|-------|
| **20k** | Load WV–OH Companies into Neon | `04.01.01.04.20000.001–005` | Neon | `marketing.company_intake` |
| **10k** | Enrich Contacts from Apify | `04.01.02.05.10000.001` | Apify | `marketing.company_people` |
| **10k** | Verify Contacts with MillionVerify | `04.01.02.07.10000.002` | MillionVerify | `marketing.company_people` |
| **10k** | Maintain Segmented Templates | `04.01.03.06.10000.003` | VibeOS | `marketing.message_templates` |
| **5k** | Send Segmented Messaging via VibeOS | `04.01.03.06.05000.001` | VibeOS | `marketing.message_templates` |
| **5k** | Process Buyer Intent Signals | `04.01.03.08.05000.002` | BIT | `bit.signal` |
| **5k** | Operate Perpetual Lead Engine | `04.01.03.09.05000.003` | PLE | `ple.lead_cycles` |

---

### **ID Generation Rules**

#### **When to Generate a New unique_id**

Generate a new `unique_id` for:
- Every new process execution
- Each distinct step within a microprocess
- All agent operations that modify data
- Any operation logged to audit trail

#### **When to Reuse a unique_id**

Reuse the same `unique_id` for:
- Retry attempts of the same operation
- Progress updates within a single step
- Log entries for the same execution

#### **Step Numbering Convention**

- `001–099`: Primary operations
- `100–199`: Validation and error handling
- `200–299`: Cleanup and post-processing
- `900–999`: Rollback and recovery

**Example Microprocess Flow**:
```
04.01.02.05.10000.001  →  Scrape company website
04.01.02.05.10000.002  →  Scrape LinkedIn profile
04.01.02.05.10000.003  →  Scrape news sources
04.01.02.05.10000.101  →  Validate scraped data
04.01.02.05.10000.201  →  Clean and normalize data
04.01.02.05.10000.901  →  Rollback on failure
```

---

### **Implementation Example**

**JavaScript ID Generation**:
```javascript
function generateUniqueId(microprocess, tool, altitude, step) {
  const database = '04';  // Neon hive
  const subhive = '01';   // Outreach
  return `${database}.${subhive}.${microprocess}.${tool}.${altitude}.${step}`;
}

// Usage
const uniqueId = generateUniqueId('03', '06', '05000', '001');
// Result: "04.01.03.06.05000.001"

const processId = "Send Segmented Messaging via VibeOS";
```

**SQL Query with ID Logging**:
```sql
-- Log operation start
INSERT INTO process_registry (unique_id, process_id, altitude, status, started_at)
VALUES ('04.01.03.06.05000.001', 'Send Segmented Messaging via VibeOS', 5000, 'in_progress', now());

-- Perform operation
INSERT INTO marketing.message_log (campaign_id, contact_id, subject, body, sent_at)
VALUES (123, 456, 'Q1 Renewal Notice', '...', now());

-- Log operation completion
UPDATE process_registry
SET status = 'completed', completed_at = now()
WHERE unique_id = '04.01.03.06.05000.001';
```

---

### **Doctrine Compliance Checks**

All operations must validate their IDs against these rules:

✅ **Valid unique_id**:
- Exactly 6 segments separated by dots
- Each segment matches expected pattern (2, 2, 2, 2, 5, 3 digits)
- Tool code exists in `shq_tool_registry`
- Altitude matches predefined list (30000, 20000, 10000, 05000, 01000)

✅ **Valid process_id**:
- Starts with uppercase verb
- Contains object being acted upon
- Under 60 characters
- No special characters except hyphens and spaces

**Validation Function**:
```javascript
function validateDoctrineId(uniqueId, processId) {
  // Validate unique_id format
  const pattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  if (!pattern.test(uniqueId)) {
    throw new Error(`Invalid unique_id format: ${uniqueId}`);
  }

  // Validate altitude
  const altitude = uniqueId.split('.')[4];
  const validAltitudes = ['30000', '20000', '10000', '05000', '01000'];
  if (!validAltitudes.includes(altitude)) {
    throw new Error(`Invalid altitude: ${altitude}`);
  }

  // Validate process_id length
  if (processId.length > 60) {
    throw new Error(`process_id too long: ${processId}`);
  }

  return true;
}
```

---

## 1️⃣2️⃣ Master Error Table

The **Master Error Table** (`shq_error_log`) is a centralized, global error tracking system that captures every system or agent error across all altitudes and microprocesses.

---

### **Table Schema**

```sql
CREATE TABLE IF NOT EXISTS shq_error_log (
    id SERIAL PRIMARY KEY,
    error_id TEXT UNIQUE,
    timestamp TIMESTAMPTZ DEFAULT now(),
    agent_name TEXT,
    process_id TEXT,
    unique_id TEXT,
    severity TEXT CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT,
    stack_trace TEXT,
    resolved BOOLEAN DEFAULT false,
    resolution_notes TEXT,
    last_touched TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_error_log_agent ON shq_error_log(agent_name);
CREATE INDEX idx_error_log_process ON shq_error_log(process_id);
CREATE INDEX idx_error_log_unique ON shq_error_log(unique_id);
CREATE INDEX idx_error_log_severity ON shq_error_log(severity);
CREATE INDEX idx_error_log_resolved ON shq_error_log(resolved);
CREATE INDEX idx_error_log_timestamp ON shq_error_log(timestamp DESC);
```

---

### **Field Definitions**

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Auto-incrementing primary key |
| `error_id` | TEXT | UUID v4 for global error tracking |
| `timestamp` | TIMESTAMPTZ | When the error occurred |
| `agent_name` | TEXT | Name of the agent that encountered the error |
| `process_id` | TEXT | Human-readable process identifier (e.g., "Enrich Contacts from Apify") |
| `unique_id` | TEXT | Doctrine numeric ID (e.g., "04.01.02.05.10000.001") |
| `severity` | TEXT | Error severity level: `info`, `warning`, `error`, `critical` |
| `message` | TEXT | Human-readable error message |
| `stack_trace` | TEXT | Full stack trace for debugging |
| `resolved` | BOOLEAN | Whether the error has been resolved (default: false) |
| `resolution_notes` | TEXT | Notes on how the error was resolved |
| `last_touched` | TIMESTAMPTZ | Last time this error was updated |

---

### **Severity Levels**

| Level | Description | Action Required | Example |
|-------|-------------|-----------------|---------|
| `info` | Informational, no action needed | Monitor | "Contact already exists in database" |
| `warning` | Potential issue, degraded service | Review within 24 hours | "Email verification confidence below 80%" |
| `error` | Operation failed, retry possible | Investigate within 4 hours | "Apify scrape timeout after 30s" |
| `critical` | System failure, immediate action | Immediate investigation | "Database connection lost" |

---

### **Error Handling Doctrine**

All agents, scripts, and tools **must** adhere to these rules:

#### **1. Mandatory Error Logging**

Every error must be logged to `shq_error_log`:
- ✅ Use UUID v4 for `error_id`
- ✅ Include both `process_id` and `unique_id`
- ✅ Capture full `stack_trace` when available
- ✅ Set appropriate `severity` level

#### **2. Error ID Uniqueness**

Each error occurrence gets a unique `error_id`:
- Use `gen_random_uuid()` in PostgreSQL
- Use `crypto.randomUUID()` in Node.js
- Never reuse error IDs across different errors

#### **3. Context Propagation**

Errors must include context for debugging:
- Agent name (e.g., "Apify Orchestrator")
- Process ID (e.g., "Enrich Contacts from Apify")
- Unique ID (e.g., "04.01.02.05.10000.001")
- Full stack trace when available

#### **4. Firebase Dashboard Integration**

All errors are visible in Firebase dashboards:
- Real-time error stream for monitoring
- Severity-based alerts (critical → instant notification)
- Error resolution tracking

---

### **SQL Insert Examples**

#### **Basic Error Logging**

```sql
INSERT INTO shq_error_log (
    error_id,
    agent_name,
    process_id,
    unique_id,
    severity,
    message
)
VALUES (
    gen_random_uuid()::TEXT,
    'Validator Agent',
    'Enrich Contacts from Apify',
    '04.01.02.05.10000.001',
    'error',
    'Apify scrape failed due to timeout'
);
```

#### **Error with Stack Trace**

```sql
INSERT INTO shq_error_log (
    error_id,
    agent_name,
    process_id,
    unique_id,
    severity,
    message,
    stack_trace
)
VALUES (
    gen_random_uuid()::TEXT,
    'MillionVerify Orchestrator',
    'Verify Contacts with MillionVerify',
    '04.01.02.07.10000.002',
    'critical',
    'MillionVerify API authentication failed',
    'Error: 401 Unauthorized\n  at apiClient.verify (/agents/specialists/millionVerifyRunner.js:45:10)'
);
```

#### **Mark Error as Resolved**

```sql
UPDATE shq_error_log
SET resolved = true,
    resolution_notes = 'Updated API key and retried successfully',
    last_touched = now()
WHERE error_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
```

---

### **JavaScript Error Logging Helper**

```javascript
async function logError({
  agentName,
  processId,
  uniqueId,
  severity,
  message,
  error
}) {
  const errorId = crypto.randomUUID();
  const stackTrace = error?.stack || '';

  const query = `
    INSERT INTO shq_error_log (
      error_id, agent_name, process_id, unique_id,
      severity, message, stack_trace
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING id, error_id
  `;

  const values = [
    errorId,
    agentName,
    processId,
    uniqueId,
    severity,
    message,
    stackTrace
  ];

  const result = await db.query(query, values);

  // Also log to Firebase for real-time dashboards
  await firebaseLogError({
    errorId,
    agentName,
    processId,
    severity,
    message,
    timestamp: new Date()
  });

  return result.rows[0];
}

// Usage in agents
try {
  await apifyRunner.scrape(companyUrl);
} catch (error) {
  await logError({
    agentName: 'Apify Orchestrator',
    processId: 'Enrich Contacts from Apify',
    uniqueId: '04.01.02.05.10000.001',
    severity: 'error',
    message: `Failed to scrape ${companyUrl}`,
    error
  });

  throw error; // Re-throw after logging
}
```

---

### **Error Analysis Queries**

#### **Unresolved Errors by Severity**

```sql
SELECT severity, COUNT(*) as error_count
FROM shq_error_log
WHERE resolved = false
GROUP BY severity
ORDER BY
  CASE severity
    WHEN 'critical' THEN 1
    WHEN 'error' THEN 2
    WHEN 'warning' THEN 3
    WHEN 'info' THEN 4
  END;
```

#### **Top 10 Most Common Errors**

```sql
SELECT message, COUNT(*) as occurrences, MAX(timestamp) as last_seen
FROM shq_error_log
WHERE timestamp > now() - INTERVAL '7 days'
GROUP BY message
ORDER BY occurrences DESC
LIMIT 10;
```

#### **Agent Error Rate**

```sql
SELECT
  agent_name,
  COUNT(*) as total_errors,
  SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_errors,
  SUM(CASE WHEN resolved THEN 1 ELSE 0 END) as resolved_errors,
  ROUND(100.0 * SUM(CASE WHEN resolved THEN 1 ELSE 0 END) / COUNT(*), 2) as resolution_rate
FROM shq_error_log
WHERE timestamp > now() - INTERVAL '30 days'
GROUP BY agent_name
ORDER BY total_errors DESC;
```

#### **Error Timeline (Daily)**

```sql
SELECT
  DATE(timestamp) as error_date,
  severity,
  COUNT(*) as error_count
FROM shq_error_log
WHERE timestamp > now() - INTERVAL '30 days'
GROUP BY DATE(timestamp), severity
ORDER BY error_date DESC, severity;
```

---

### **Firebase Dashboard Integration**

The error log is mirrored to Firebase for real-time monitoring:

**Firestore Collection**: `errors`

**Document Structure**:
```json
{
  "errorId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "agentName": "Apify Orchestrator",
  "processId": "Enrich Contacts from Apify",
  "uniqueId": "04.01.02.05.10000.001",
  "severity": "error",
  "message": "Apify scrape failed due to timeout",
  "timestamp": "2025-01-20T15:30:00Z",
  "resolved": false,
  "resolutionNotes": null
}
```

**Dashboard Features**:
- 🔴 Critical error alerts (instant push notifications)
- 📊 Error rate trends by agent and severity
- 🔍 Full-text search across error messages
- ✅ One-click error resolution marking
- 📈 Resolution time metrics (MTTD, MTTR)

---

### **Error Handling Best Practices**

#### **1. Fail Fast, Log Everything**
```javascript
// ❌ Bad: Silent failure
if (!data) return;

// ✅ Good: Log and throw
if (!data) {
  await logError({
    agentName: 'Data Validator',
    processId: 'Validate Input Data',
    uniqueId: '04.01.01.04.20000.101',
    severity: 'error',
    message: 'Missing required data field'
  });
  throw new Error('Missing required data');
}
```

#### **2. Include Context in Error Messages**
```javascript
// ❌ Bad: Generic message
throw new Error('Scrape failed');

// ✅ Good: Detailed message
throw new Error(`Apify scrape failed for company_id=${companyId}, url=${url}, reason=timeout`);
```

#### **3. Use Appropriate Severity Levels**
```javascript
// Info: Operational notes
await logError({ severity: 'info', message: 'Contact already verified, skipping' });

// Warning: Degraded service
await logError({ severity: 'warning', message: 'Email confidence 75% (below 80% threshold)' });

// Error: Operation failed, retry possible
await logError({ severity: 'error', message: 'Apify timeout, will retry in 60s' });

// Critical: System failure
await logError({ severity: 'critical', message: 'Database connection lost' });
```

#### **4. Implement Retry Logic with Error Logging**
```javascript
async function retryWithLogging(operation, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const severity = attempt === maxRetries ? 'error' : 'warning';

      await logError({
        agentName: 'Retry Handler',
        processId: operation.name,
        uniqueId: operation.uniqueId,
        severity,
        message: `Attempt ${attempt}/${maxRetries} failed: ${error.message}`,
        error
      });

      if (attempt === maxRetries) throw error;

      // Exponential backoff
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

---

## 🔟 Summary

With the **Barton Doctrine Numbering System** and **Master Error Table** in place, the Barton Outreach system achieves:

✅ **Complete Traceability**: Every operation tracked with unique_id and process_id
✅ **Error Visibility**: All errors logged and visible in real-time dashboards
✅ **Operational Insights**: Analytics on error patterns, agent performance, and system health
✅ **Doctrine Compliance**: Standardized ID format enforced across all agents and tools
✅ **Rapid Debugging**: Full context (agent, process, unique_id, stack trace) for every error

---

**End of Outreach Doctrine A→Z Guide**
