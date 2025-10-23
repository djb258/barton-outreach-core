# 🏗️ Architecture Diagrams

Visual representation of Barton Outreach system architecture.

---

## System Overview

```mermaid
graph TB
    subgraph "External Data Sources"
        Apollo[Apollo.io]
        Apify[Apify Scrapers]
        Manual[Manual Import]
    end

    subgraph "Ingestion Layer"
        API[API Server<br/>Port 3000]
        Ingest[intake.f_ingest_json]
    end

    subgraph "Database Layer - Neon PostgreSQL"
        Raw[intake.raw_loads<br/>Staging]
        Vault[vault.contacts<br/>Validated]
        Company[company.master<br/>Golden Records]
        People[people.master<br/>Golden Records]
        Marketing[marketing.*<br/>Campaigns]
    end

    subgraph "Processing Layer"
        Promote[vault.f_promote_contacts]
        MCP[Garage Bay MCP<br/>Orchestrator]
        Agents[Specialized Agents<br/>Enrichment/Scraping]
    end

    subgraph "Presentation Layer"
        Frontend[React Frontend<br/>Port 5173]
        Analytics[Analytics Dashboard]
    end

    Apollo -->|CSV/JSON| API
    Apify -->|JSON| API
    Manual -->|CSV/JSON| API

    API -->|Call function| Ingest
    Ingest -->|Insert| Raw

    Raw -->|Promote| Promote
    Promote -->|Upsert| Vault
    Promote -->|Create/Update| Company
    Promote -->|Create/Update| People

    MCP -->|Trigger| Agents
    Agents -->|Write enriched data| Company
    Agents -->|Write enriched data| People

    Vault -->|Track outreach| Marketing
    People -->|Campaign targets| Marketing

    API -->|Query| Vault
    API -->|Query| Company
    API -->|Query| People
    API -->|Query| Marketing

    Frontend -->|REST API| API
    Analytics -->|REST API| API
```

---

## Data Ingestion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant Ingest as intake.f_ingest_json()
    participant Raw as intake.raw_loads
    participant Promote as vault.f_promote_contacts()
    participant Vault as vault.contacts
    participant Audit as intake.audit_log

    Client->>API: POST /api/ingest<br/>{source, batch_id, rows}
    API->>Ingest: Call with JSONB array

    loop For each row
        Ingest->>Ingest: Check for duplicates<br/>(last 30 days)
        alt Not duplicate
            Ingest->>Raw: INSERT with status='pending'
            Ingest->>Audit: Log 'contact_ingested'
        else Is duplicate
            Ingest->>Raw: INSERT with status='duplicate'
        end
    end

    Ingest->>API: Return summary<br/>{inserted, skipped}
    API->>Client: 200 OK<br/>{success, batch_id, counts}

    Note over Client,API: Promotion Step (separate request)

    Client->>API: POST /api/promote
    API->>Promote: Call with load_ids or NULL

    loop For each pending load
        Promote->>Promote: Validate email
        alt Valid contact
            Promote->>Vault: UPSERT by email
            Promote->>Raw: UPDATE promoted_at
            Promote->>Audit: Log 'contact_promoted'
        else Invalid
            Promote->>Raw: UPDATE status='failed'
        end
    end

    Promote->>API: Return counts<br/>{promoted, updated, failed}
    API->>Client: 200 OK<br/>{success, counts}
```

---

## Campaign Outreach Flow

```mermaid
flowchart LR
    subgraph "1. Campaign Setup"
        Create[Create Campaign]
        Define[Define Target Criteria]
        Template[Create Message Template]
    end

    subgraph "2. Target Selection"
        Query[Query vault.contacts]
        Filter[Apply Filters<br/>score >= 80<br/>status = active]
        Enrich[Enrich from people.master]
    end

    subgraph "3. Execution"
        Send[Send Messages]
        Track[Track in outreach_history]
        Update[Update sent_count]
    end

    subgraph "4. Response Tracking"
        Monitor[Monitor Responses]
        LogOpen[Log opened_at]
        LogReply[Log replied_at]
        UpdateMetrics[Update response_count]
    end

    subgraph "5. Attribution"
        Convert[Conversion Event]
        Attr[marketing.attribution]
        Report[feedback_reports]
    end

    Create --> Define --> Template
    Template --> Query
    Query --> Filter --> Enrich
    Enrich --> Send
    Send --> Track --> Update
    Update --> Monitor
    Monitor --> LogOpen --> LogReply --> UpdateMetrics
    UpdateMetrics --> Convert --> Attr --> Report
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DevLocal[Local Machine]
        DevDB[(Neon Dev DB)]
        DevLocal -->|psql| DevDB
    end

    subgraph "CI/CD"
        GitHub[GitHub Repository]
        Actions[GitHub Actions<br/>CTB Compliance Check]
        GitHub --> Actions
    end

    subgraph "Production - Frontend"
        Vercel[Vercel]
        VercelDeploy[Automated Deploy<br/>on main push]
        VercelApp[amplify-client<br/>https://barton-amplify.vercel.app]

        Vercel --> VercelDeploy --> VercelApp
    end

    subgraph "Production - Backend"
        Render[Render]
        RenderDeploy[Automated Deploy<br/>on main push]
        RenderAPI[API Server<br/>https://barton-outreach-api.onrender.com]

        Render --> RenderDeploy --> RenderAPI
    end

    subgraph "Production - Database"
        NeonProd[(Neon Production DB<br/>PostgreSQL 14)]
    end

    subgraph "Production - Agents"
        Agents[MCP Agents<br/>On-demand/Cron]
    end

    DevLocal -->|git push| GitHub
    Actions -->|On PR| Actions
    GitHub -->|Auto-deploy| Vercel
    GitHub -->|Auto-deploy| Render

    RenderAPI -->|Query/Write| NeonProd
    VercelApp -->|REST API| RenderAPI
    Agents -->|Write enriched data| NeonProd
    Agents -->|Call endpoints| RenderAPI
```

---

## Database Schema Layers

```mermaid
graph LR
    subgraph "Layer 1: Ingestion"
        Raw[intake.raw_loads<br/>Raw JSON staging]
        Audit[intake.audit_log<br/>Change tracking]
    end

    subgraph "Layer 2: Validation"
        Vault[vault.contacts<br/>Validated contacts]
    end

    subgraph "Layer 3: Master Data"
        CompanySlot[company.slot<br/>Pre-validation]
        PeopleSlot[people.slot<br/>Pre-validation]
        CompanyMaster[company.master<br/>Golden records]
        PeopleMaster[people.master<br/>Golden records]
    end

    subgraph "Layer 4: Enrichment"
        CompanyHistory[company.history<br/>Change log]
        PeopleHistory[people.history<br/>Change log]
        Intelligence[people.intelligence<br/>LinkedIn data<br/>30-day TTL]
    end

    subgraph "Layer 5: Marketing"
        Campaigns[marketing.campaigns]
        OutreachHistory[marketing.outreach_history]
        Attribution[marketing.attribution]
        Feedback[marketing.feedback_reports]
    end

    Raw -->|Promote| Vault
    Vault -->|Extract| CompanySlot
    Vault -->|Extract| PeopleSlot
    CompanySlot -->|Validate| CompanyMaster
    PeopleSlot -->|Validate| PeopleMaster
    CompanyMaster -->|Track changes| CompanyHistory
    PeopleMaster -->|Track changes| PeopleHistory
    PeopleMaster -->|Enrich| Intelligence
    PeopleMaster -->|Target| Campaigns
    Campaigns -->|Track| OutreachHistory
    OutreachHistory -->|Convert| Attribution
    Campaigns -->|Analyze| Feedback
```

---

## CTB Branch Dependencies

```mermaid
graph TD
    Data[data/<br/>Schemas & Migrations<br/>05.01.*]

    Sys[sys/<br/>API & CI/CD<br/>04.04.*]
    AI[ai/<br/>Agents & MCP<br/>03.01.*]

    UI[ui/<br/>Frontend Apps<br/>07.01.*]

    Docs[docs/<br/>Documentation<br/>06.01.*]
    Meta[meta/<br/>Configuration<br/>08.01.*]

    Data -->|Provides schemas| Sys
    Data -->|Provides schemas| AI

    Sys -->|Provides API| UI
    Sys -->|Provides API| AI

    Meta -.->|Config| Sys
    Meta -.->|Config| AI
    Meta -.->|Config| UI

    Docs -.->|Documents| Data
    Docs -.->|Documents| Sys
    Docs -.->|Documents| AI
    Docs -.->|Documents| UI

    style Data fill:#e1f5ff
    style Sys fill:#ffe1f5
    style AI fill:#f5ffe1
    style UI fill:#ffe1e1
    style Docs fill:#f5f5f5
    style Meta fill:#fff5e1
```

---

## MCP Orchestration Flow

```mermaid
sequenceDiagram
    participant User
    participant MCP as Garage Bay MCP
    participant Composio
    participant Apollo as Apollo Agent
    participant Apify as Apify Agent
    participant DB as Neon Database
    participant API

    User->>MCP: Trigger enrichment workflow
    MCP->>Composio: Initialize tools

    par Parallel Enrichment
        MCP->>Apollo: Fetch contact data
        Apollo->>DB: Write to people.slot

        MCP->>Apify: Scrape LinkedIn
        Apify->>DB: Write to people.intelligence
    end

    MCP->>API: POST /api/promote
    API->>DB: Promote contacts to master tables

    DB->>API: Return promoted counts
    API->>MCP: Success response
    MCP->>User: Workflow complete<br/>{enriched_count, promoted_count}
```

---

## User Interaction Flow

```mermaid
flowchart TD
    Start([User Opens App])

    Start --> Dashboard[Dashboard View]

    Dashboard --> ViewContacts[View Contacts]
    Dashboard --> ViewCampaigns[View Campaigns]
    Dashboard --> ViewAnalytics[View Analytics]

    ViewContacts --> SearchContacts[Search/Filter]
    SearchContacts --> ContactDetail[Contact Detail Page]
    ContactDetail --> EditContact[Edit Contact]
    EditContact -->|PATCH /api/contacts/:id| UpdateDB[(Database Update)]

    ViewCampaigns --> CampaignDetail[Campaign Detail]
    CampaignDetail --> ViewOutreach[View Outreach History]
    ViewOutreach --> Metrics[Performance Metrics]

    ViewAnalytics --> DashMetrics[Dashboard Metrics]
    DashMetrics --> Reports[Generate Reports]

    UpdateDB --> Refresh[Refresh View]
    Refresh --> Dashboard

    style Start fill:#e1f5ff
    style Dashboard fill:#ffe1f5
    style UpdateDB fill:#f5ffe1
```

---

## Security & Access Control

```mermaid
graph TB
    subgraph "Authentication Layer"
        Auth[API Key / Session Token]
    end

    subgraph "API Layer"
        Endpoint[API Endpoint]
        Validate[Validate Token]
        RateLimit[Rate Limiting<br/>100 req/min]
    end

    subgraph "Database Layer"
        RLS[Row Level Security]
        Functions[SECURITY DEFINER Functions]
        DirectAccess[Direct Table Access<br/>BLOCKED]
    end

    subgraph "Audit Layer"
        AuditLog[intake.audit_log<br/>All operations logged]
    end

    Client[Client Request]

    Client -->|Authorization header| Auth
    Auth --> Endpoint
    Endpoint --> Validate

    Validate -->|Valid| RateLimit
    Validate -->|Invalid| Reject401[401 Unauthorized]

    RateLimit -->|Within limit| Functions
    RateLimit -->|Exceeded| Reject429[429 Too Many Requests]

    Functions -->|Execute| RLS
    RLS -->|Allow| Success[200 Success]
    RLS -->|Deny| Reject403[403 Forbidden]

    Functions --> AuditLog

    DirectAccess -.->|Prevented by| RLS

    style DirectAccess fill:#ffcccc
    style RLS fill:#ccffcc
    style AuditLog fill:#cce5ff
```

---

## Backup & Recovery

```mermaid
flowchart LR
    subgraph "Live Data"
        Live[(Neon Primary DB)]
    end

    subgraph "Backup Strategy"
        AutoBackup[Neon Automated Backups<br/>Point-in-time recovery]
        GitHistory[Git History<br/>Schema versions]
        AuditLog[Audit Log<br/>Operation history]
    end

    subgraph "Recovery Scenarios"
        DataCorruption[Data Corruption]
        SchemaIssue[Schema Migration Failed]
        AccidentalDelete[Accidental Deletion]
    end

    subgraph "Recovery Actions"
        RestoreNeon[Restore from Neon backup]
        RollbackMigration[Rollback migration<br/>Reapply from git]
        AuditReview[Review audit log<br/>Reconstruct data]
    end

    Live -->|Continuous| AutoBackup
    Live -->|Logged| AuditLog

    DataCorruption --> RestoreNeon
    SchemaIssue --> RollbackMigration
    AccidentalDelete --> AuditReview

    RestoreNeon --> AutoBackup
    RollbackMigration --> GitHistory
    AuditReview --> AuditLog
```

---

## Performance Optimization

```mermaid
mindmap
    root((Performance))
        Database
            Indexes on email, company_id
            Partial indexes for status
            JSONB indexes for raw_data
            Query plan analysis
        API
            Response caching
            Connection pooling
            Pagination default 100
            Batch operations
        Frontend
            Code splitting
            Lazy loading routes
            Virtual scrolling
            Memoized components
        Infrastructure
            Neon autoscaling
            Render auto-deploy
            CDN for static assets
            Rate limiting
```

---

## Monitoring & Observability

```mermaid
graph TB
    subgraph "Application Layer"
        API[API Server]
        Frontend[Frontend App]
        Agents[MCP Agents]
    end

    subgraph "Monitoring Points"
        Health[Health Endpoints<br/>GET /health]
        Metrics[Dashboard Metrics<br/>GET /api/analytics/dashboard]
        Audit[Audit Log<br/>intake.audit_log]
    end

    subgraph "Alerts & Notifications"
        HighError[High Error Rate]
        SlowQueries[Slow Queries]
        FailedMigrations[Failed Migrations]
    end

    subgraph "Response Actions"
        Investigate[Investigate Logs]
        Rollback[Rollback Deployment]
        ScaleUp[Scale Resources]
    end

    API --> Health
    API --> Metrics
    API --> Audit

    Health -->|Check every 5min| HighError
    Metrics -->|Monitor| SlowQueries
    Audit -->|Track| FailedMigrations

    HighError --> Investigate
    SlowQueries --> Investigate
    FailedMigrations --> Rollback

    Investigate --> ScaleUp
```

---

**Diagram Format**: Mermaid (renders in GitHub, VS Code, many documentation systems)

**Last Updated**: 2025-10-23

**Related Docs**:
- System overview: `ctb/sys/README.md`
- Database details: `ctb/data/SCHEMA.md`
- API reference: `ctb/sys/api/API.md`
- Dependencies: `DEPENDENCIES.md`
