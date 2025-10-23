<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-802F212D
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Outreach → Neon Doctrine Tracker Pipeline Architecture

## Overview

The Outreach → Neon Doctrine Tracker is a comprehensive data processing pipeline that ingests, validates, enriches, and promotes contact/company data for outreach campaigns. The system follows the Barton Doctrine standards and implements a multi-layer architecture for robust data processing and governance.

## Architecture Layers

### 🔥 Firebase (Working Layer)

Firebase serves as the processing engine where all data transformations, validations, and enrichments occur before promotion to the permanent storage layer.

#### Step 1 – CSV Intake
- **Purpose**: Initial data ingestion from CSV files
- **Tables**: `company_raw_intake`, `person_raw_intake`
- **Process**: Raw CSV data is uploaded and parsed into staging tables
- **Output**: Standardized intake records ready for validation

#### Step 2A – Validator Agent
- **Purpose**: Data validation and error detection
- **Tables**: Updates validation status in intake tables, creates `validation_failed` records
- **Process**: Validates email formats, required fields, data consistency
- **Output**: Validated records ready for enrichment, failed records for manual review

#### Step 2B – Enrichment
- **Purpose**: Data normalization and enhancement
- **Tables**: `enrichment_jobs`, updates intake tables with enriched data
- **Process**: Normalizes emails/phones, infers job roles, enriches company information
- **Output**: Enriched and normalized records ready for scraping

#### Step 2C – Apify Scraping
- **Purpose**: Fresh data collection via web scraping
- **Tables**: Updates staging tables with scraped data
- **Process**: Uses Apify actors to scrape LinkedIn profiles, company websites
- **Output**: Up-to-date contact and company information

#### Step 3 – Adjuster Console
- **Purpose**: Human-in-the-loop error resolution
- **Tables**: Reads from all staging tables, allows manual corrections
- **Process**: UI for reviewing and correcting failed validations/enrichments
- **Output**: Manually corrected records ready for promotion

#### Step 4 – Promotion Console
- **Purpose**: Promotion of validated data to master tables
- **Tables**: Promotes to `company_master` and `person_master` in Neon
- **Process**: Final validation, duplicate detection, permanent ID assignment
- **Output**: Clean, deduplicated master records in Neon vault

### 💾 Neon (Vault Layer)

Neon serves as the permanent data vault where all processed and validated data is stored for long-term use and outreach operations.

#### Company Master (`company_master`)
- **Purpose**: Canonical company records
- **Data**: Company names, domains, industries, employee counts, addresses
- **IDs**: Permanent Barton Doctrine unique IDs (CMP-XXXXXXXX-XXXXXX)

#### Person Master (`person_master`)
- **Purpose**: Canonical person records with company relationships
- **Data**: Names, emails, phones, job titles, LinkedIn URLs
- **IDs**: Permanent Barton Doctrine unique IDs (PER-XXXXXXXX-XXXXXX)
- **Relationships**: Links to company_master via company_unique_id

#### Unified Audit Log (`marketing.unified_audit_log`)
- **Purpose**: Complete audit trail of all pipeline operations
- **Data**: Action logs, timestamps, process IDs, change details
- **Compliance**: Full traceability for governance and debugging

#### Outreach Sync Tracking (`outreach_sync_tracking`)
- **Purpose**: Back-reference tracking for outreach platform synchronization
- **Data**: Campaign IDs, sync status, external contact IDs, platform responses
- **Integration**: Links master records to outreach platform campaigns

#### Feedback Reports (`feedback_reports`)
- **Purpose**: Error pattern analysis and continuous improvement
- **Data**: Error summaries, pattern detection, recommended fixes
- **Analytics**: Data-driven insights for pipeline optimization

### 📤 Outreach Platforms

External platforms where processed contacts are synced for campaign execution.

#### Instantly Campaigns
- **Integration**: Via Composio MCP
- **Data Sync**: Promoted contacts with custom fields
- **Tracking**: Campaign performance and response tracking

#### HeyReach Campaigns
- **Integration**: Via Composio MCP
- **Data Sync**: Promoted contacts with company context
- **Tracking**: LinkedIn-specific campaign metrics

### 📊 Governance & Monitoring

Comprehensive monitoring and feedback systems for pipeline health and continuous improvement.

#### Step 5 – Audit Trail Integration
- **Purpose**: Standardized audit logging across all pipeline steps
- **Implementation**: Unified logging format, centralized audit collection
- **Compliance**: Ensures complete traceability and governance

#### Step 6 – Outreach Engine Sync ✅
- **Purpose**: Synchronize promoted contacts to outreach platforms
- **Implementation**: MCP-based sync to Instantly and HeyReach
- **Features**: Back-reference tracking, sync status monitoring, error recovery

#### Step 7 – Monitoring Dashboard ✅
- **Purpose**: Real-time pipeline health and performance monitoring
- **Implementation**: React dashboard with Firebase Cloud Functions backend
- **Features**: Stage counting, error analysis, throughput tracking, audit timeline

#### Step 8 – Feedback Loop
- **Purpose**: Automated error pattern detection and recommendations
- **Implementation**: ML-based pattern recognition, automated reporting
- **Features**: Error classification, root cause analysis, improvement suggestions

## Data Flow

```
CSV Upload → Validation → Enrichment → Scraping → Adjustment → Promotion → Sync
     ↓           ↓           ↓           ↓           ↓           ↓        ↓
Raw Intake → Validated → Enriched → Scraped → Corrected → Master → Campaigns
```

## Key Features

### Barton Doctrine Compliance
- Standardized unique ID format (NN.NN.NN.NN.NNNNN.NNN)
- HEIR/ORBT payload structure for all MCP calls
- Comprehensive audit logging with doctrine versioning

### Error Handling & Recovery
- Multi-step validation with human-in-the-loop correction
- Automatic retry mechanisms with exponential backoff
- Comprehensive error logging and pattern analysis

### Real-time Monitoring
- Pipeline health dashboard with stage-by-stage metrics
- Error rate tracking and resolution time analysis
- Throughput monitoring and performance optimization

### Data Governance
- Complete audit trail from intake to campaign sync
- Data lineage tracking with process IDs
- Compliance reporting and data quality metrics

### Platform Integration
- Composio MCP for secure API integration
- Firebase for scalable processing
- Neon for reliable data persistence
- React for modern UI components

## Technical Stack

- **Processing**: Firebase Cloud Functions v2
- **Storage**: Neon PostgreSQL
- **UI**: React with modern component architecture
- **Integration**: Composio MCP protocol
- **Monitoring**: Real-time dashboards with auto-refresh
- **Orchestration**: Step-by-step pipeline with error recovery

## Security & Compliance

- All API calls go through Composio MCP for secure credential management
- No direct API keys in code, all handled by MCP
- Complete audit logging for compliance requirements
- Data encryption in transit and at rest
- Role-based access controls for different pipeline stages

## Deployment Architecture

- **Firebase**: Cloud Functions for serverless processing
- **Neon**: Managed PostgreSQL for data persistence
- **Vercel**: Static site hosting for React components
- **GitHub**: Version control and CI/CD pipeline
- **Composio**: MCP server for secure API management

This architecture provides a robust, scalable, and auditable pipeline for processing outreach data while maintaining high standards for data quality, governance, and operational visibility.