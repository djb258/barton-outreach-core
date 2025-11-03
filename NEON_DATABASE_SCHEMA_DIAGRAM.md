# Neon Database Schema Diagram

Complete visual representation of all 8 schemas and their tables/views in the Marketing DB.

## Database Structure Overview

```mermaid
graph TB
    subgraph DB["🗄️ MARKETING DB (Neon PostgreSQL)"]
        
        subgraph BIT["🔔 BIT Schema (Buyer Intent Tool)"]
            BIT_STATUS["⏳ Ready - No tables yet<br/>Purpose: Intelligence signals"]
        end
        
        subgraph PLE["🔄 PLE Schema (Pipeline Logic Engine)"]
            PLE_STATUS["⏳ Ready - No tables yet<br/>Purpose: Lead loop automation"]
        end
        
        subgraph INTAKE["📥 INTAKE Schema (Raw Data Staging)"]
            INTAKE_T1["📊 company_raw_intake<br/>447 rows | 25 cols"]
        end
        
        subgraph MARKETING["📢 MARKETING Schema (Core Business)"]
            MARK_T1["📊 company_master<br/>708 rows | 29 cols"]
            MARK_T2["📊 company_slots<br/>1,232 rows | 5 cols"]
            MARK_T3["📊 contact_enrichment<br/>0 rows | 11 cols"]
            MARK_T4["📊 email_verification<br/>0 rows | 8 cols"]
            MARK_T5["📊 people_master<br/>0 rows | 26 cols"]
            MARK_T6["📊 pipeline_errors<br/>0 rows | 11 cols"]
            MARK_T7["📊 pipeline_events<br/>52 rows | 8 cols"]
            
            MARK_V1["👁️ marketing_ceo"]
            MARK_V2["👁️ marketing_cfo"]
            MARK_V3["👁️ marketing_hr"]
            MARK_V4["👁️ v_phase_stats"]
            MARK_V5["👁️ vw_error_rate_24h"]
            MARK_V6["👁️ vw_health_crawl_staleness"]
            MARK_V7["👁️ vw_health_profile_staleness"]
            MARK_V8["👁️ vw_queue_sizes"]
            MARK_V9["👁️ vw_unresolved_errors"]
        end
        
        subgraph COMPANY["🏢 COMPANY Schema (Company Views)"]
            COMP_V1["👁️ next_company_urls_30d"]
            COMP_V2["👁️ vw_anchor_staleness"]
            COMP_V3["👁️ vw_company_slots"]
            COMP_V4["👁️ vw_due_renewals_ready"]
            COMP_V5["👁️ vw_next_renewal"]
        end
        
        subgraph PEOPLE["👥 PEOPLE Schema (Contact Views)"]
            PEOPLE_V1["👁️ contact_enhanced_view"]
            PEOPLE_V2["👁️ due_email_recheck_30d"]
            PEOPLE_V3["👁️ next_profile_urls_30d"]
            PEOPLE_V4["👁️ vw_profile_monitoring"]
            PEOPLE_V5["👁️ vw_profile_staleness"]
        end
        
        subgraph PUBLIC["🌐 PUBLIC Schema (System)"]
            PUB_T1["📊 shq_validation_log<br/>1 row | 9 cols"]
            PUB_V1["👁️ due_email_recheck_30d"]
            PUB_V2["👁️ next_company_urls_30d"]
            PUB_V3["👁️ next_profile_urls_30d"]
        end
        
        subgraph ARCHIVE["📦 ARCHIVE Schema (Historical)"]
            ARCH_INFO["46 tables | 48,000+ rows<br/>8.5 MB archived data<br/><br/>Key tables:<br/>• storage_evaluation_state_county_zip_v2 (41,551 rows)<br/>• storage_evaluation_focus_states (6,337 rows)<br/>• shq_schema_registry (688 rows)<br/>• Various archived marketing/people tables"]
        end
    end
    
    style BIT fill:#fff4e6,stroke:#ff9800,stroke-width:3px
    style PLE fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style INTAKE fill:#e3f2fd,stroke:#2196f3,stroke-width:3px
    style MARKETING fill:#fce4ec,stroke:#e91e63,stroke-width:4px
    style COMPANY fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style PEOPLE fill:#e0f2f1,stroke:#009688,stroke-width:3px
    style PUBLIC fill:#fff9c4,stroke:#fbc02d,stroke-width:3px
    style ARCHIVE fill:#efebe9,stroke:#795548,stroke-width:3px
```

## Detailed Schema Breakdown

### 📊 Table Distribution

| Schema | Tables | Views | Total Rows | Purpose |
|--------|--------|-------|------------|---------|
| **BIT** | 0 | 0 | 0 | Buyer intent signals (future) |
| **PLE** | 0 | 0 | 0 | Lead automation (future) |
| **INTAKE** | 1 | 0 | 447 | Raw data staging |
| **MARKETING** | 7 | 9 | 1,992 | Core business logic |
| **COMPANY** | 0 | 5 | - | Company management views |
| **PEOPLE** | 0 | 5 | - | Contact management views |
| **PUBLIC** | 1 | 3 | 1 | System utilities |
| **ARCHIVE** | 46 | 0 | 48,000+ | Historical data |
| **TOTAL** | **55** | **22** | **50,440+** | - |

## Data Flow Diagram

```mermaid
graph LR
    A[External Sources] -->|Raw Data| B[intake.company_raw_intake]
    B -->|Promotion| C[marketing.company_master]
    C -->|Slot Creation| D[marketing.company_slots]
    D -->|Enrichment| E[marketing.contact_enrichment]
    E -->|Validation| F[marketing.email_verification]
    F -->|Promotion| G[marketing.people_master]
    
    C -.->|Views| H[company.vw_company_slots]
    G -.->|Views| I[people.contact_enhanced_view]
    
    J[Pipeline Events] -->|Tracking| K[marketing.pipeline_events]
    K -->|Errors| L[marketing.pipeline_errors]
    
    style A fill:#e1f5fe
    style B fill:#b3e5fc
    style C fill:#4fc3f7
    style D fill:#29b6f6
    style E fill:#03a9f4
    style F fill:#039be5
    style G fill:#0288d1
    style H fill:#f3e5f5
    style I fill:#e0f2f1
    style J fill:#fff9c4
    style K fill:#fff59d
    style L fill:#ffcdd2
```

## Entity Relationship Overview

```mermaid
erDiagram
    INTAKE_COMPANY_RAW_INTAKE ||--o{ MARKETING_COMPANY_MASTER : promotes_to
    MARKETING_COMPANY_MASTER ||--o{ MARKETING_COMPANY_SLOTS : has_slots
    MARKETING_COMPANY_SLOTS ||--o| MARKETING_CONTACT_ENRICHMENT : enriches_to
    MARKETING_CONTACT_ENRICHMENT ||--o| MARKETING_EMAIL_VERIFICATION : validates
    MARKETING_EMAIL_VERIFICATION ||--o| MARKETING_PEOPLE_MASTER : promotes_to
    MARKETING_COMPANY_MASTER ||--o{ MARKETING_PEOPLE_MASTER : employs
    
    MARKETING_COMPANY_MASTER {
        text company_unique_id PK
        text company_name
        text website_url
        text industry
        int employee_count
    }
    
    MARKETING_COMPANY_SLOTS {
        text company_slot_unique_id PK
        text company_unique_id FK
        text slot_type
        text slot_label
    }
    
    MARKETING_PEOPLE_MASTER {
        text unique_id PK
        text company_unique_id FK
        text first_name
        text last_name
        text email
    }
    
    MARKETING_PIPELINE_EVENTS {
        int id PK
        text event_type
        jsonb payload
        text status
    }
```

## Schema Purposes

### 🔔 **BIT** (Buyer Intent Tool)
- **Purpose:** Track buying intent signals
- **Status:** Schema ready, awaiting table creation
- **Future Tables:** `signal`, `company_intelligence`, `people_intelligence`

### 🔄 **PLE** (Pipeline Logic Engine)
- **Purpose:** Perpetual lead loop automation
- **Status:** Schema ready, awaiting table creation
- **Future Tables:** `lead_cycles`, `re_engagement_rules`

### 📥 **INTAKE**
- **Purpose:** Raw data ingestion and staging
- **Tables:** `company_raw_intake` (447 companies awaiting promotion)
- **Flow:** External sources → Intake → Marketing

### 📢 **MARKETING** (Primary Schema)
- **Purpose:** Core business operations
- **Active Data:** 1,992 rows across 7 tables
- **Key Tables:**
  - `company_master` - Golden company records (708)
  - `company_slots` - Role-based positions (1,232)
  - `people_master` - Contact records (ready for data)
  - `pipeline_events` - Event tracking (52)

### 🏢 **COMPANY**
- **Purpose:** Company-focused analytical views
- **Views Only:** 5 views for monitoring and querying
- **Key Views:**
  - Renewal tracking
  - Staleness monitoring
  - URL queues

### 👥 **PEOPLE**
- **Purpose:** Contact-focused analytical views
- **Views Only:** 5 views for contact management
- **Key Views:**
  - Email recheck queues
  - Profile staleness
  - Enhanced contact data

### 🌐 **PUBLIC**
- **Purpose:** System utilities and legacy compatibility
- **Tables:** `shq_validation_log` (1 row)
- **Views:** 3 legacy compatibility views

### 📦 **ARCHIVE**
- **Purpose:** Historical data preservation
- **Tables:** 46 archived tables (8.5 MB)
- **Data:** 48,000+ archived rows from Oct 2024 cleanup
- **Notable:** State/county/zip data, schema registry history

---

**Generated:** 2025-11-03  
**Database:** Marketing DB (Neon PostgreSQL 17)  
**Total Size:** ~10 MB (1.4 MB active + 8.5 MB archived)

