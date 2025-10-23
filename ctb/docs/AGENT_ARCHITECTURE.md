<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-89348035
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
-->

# Agent Architecture Document
## Barton Outreach Core Project

### Project Overview
- **Project Name**: Barton Outreach Core
- **Domain**: Marketing > Outreach
- **Branches**: 7 (Lead, Messaging, Delivery, Scheduling, Feedback, Compliance, Data Vault)
- **Agent Strategy**: Project-specific orchestrators + Global specialist agents

---

## Project-Specific Agents (Orchestrators)

### 1. Master Orchestrator
- **ID**: `barton-master-orchestrator`
- **Role**: Overall project coordination
- **Responsibilities**:
  - Cross-branch workflow coordination
  - Resource allocation between branches
  - Global error handling and recovery
  - Project-level metrics and reporting
- **Delegates To**: All branch orchestrators
- **Global Agents Used**: Database Agent, Error Logger, Metrics Collector

### 2. Lead Branch Orchestrator
- **ID**: `barton-lead-orchestrator`
- **Branches**: Branch 00 (Data Ingestion) + Branch 01 (Lead Intake & Validation)
- **Responsibilities**:
  - CSV ingestion → Apollo → Apify → Validation → People schema
  - Company canonicalization and role slot creation
  - Contact scraping and validation coordination
  - Lead pipeline status management
- **Workflow**: Company → Roles → People
- **Global Agents Used**: Database Agent, File Processor, Apollo API Agent, Apify Agent, Validation Agent

### 3. Messaging Branch Orchestrator
- **ID**: `barton-messaging-orchestrator`
- **Branch**: Branch 02 (Message Generation)
- **Responsibilities**:
  - Persona and tone resolution
  - Message drafting with templates
  - Personalization with LI/website snippets
  - Approval gates and policy checks
- **Workflow**: Draft → Personalize → Approvals
- **Global Agents Used**: Database Agent, LLM Agent, Template Engine, Policy Checker

### 4. Delivery Branch Orchestrator
- **ID**: `barton-delivery-orchestrator`
- **Branch**: Branch 03 (Campaign Execution & Telemetry)
- **Responsibilities**:
  - Channel mapping (email, LinkedIn, etc.)
  - Rate limiting and QPS guardrails
  - Send operations via Instantly/HeyReach
  - Reply routing and triage
- **Workflow**: Send → Track → Reply Handling
- **Global Agents Used**: Database Agent, Instantly Agent, HeyReach Agent, Rate Limiter, Email Parser

### 5. Scheduling Branch Orchestrator *(Future)*
- **ID**: `barton-scheduling-orchestrator`
- **Branch**: Branch 04 (Scheduling)
- **Responsibilities**: Qualify → Propose → Book → Confirm
- **Global Agents Used**: Database Agent, Calendar Agent, CRM Connector

### 6. Feedback Branch Orchestrator *(Future)*
- **ID**: `barton-feedback-orchestrator`
- **Branch**: Branch 05 (Feedback & Scoring)
- **Responsibilities**: Signal capture → Lead scoring → Phase promotion
- **Global Agents Used**: Database Agent, Analytics Engine, ML Scorer

### 7. Compliance Branch Orchestrator *(Future)*
- **ID**: `barton-compliance-orchestrator`
- **Branch**: Branch 06 (Compliance & Observability)
- **Responsibilities**: Error logging → Heartbeats → Dashboards → Opt-out registry
- **Global Agents Used**: Database Agent, Logger, Dashboard Builder, Compliance Checker

### 8. Data Vault Branch Orchestrator *(Future)*
- **ID**: `barton-vault-orchestrator`
- **Branch**: Branch 07 (Data Vault & Promotion)
- **Responsibilities**: Staging → Canonical → Vault → Backfill
- **Global Agents Used**: Database Agent, Validator, Migration Manager

---

## Global Agents (Reusable Specialists)

### Database & Storage
- **Global Database Agent**: Multi-platform database operations (Neon, Firebase, BigQuery)
- **File Processor Agent**: CSV/Excel parsing, validation, transformation
- **Migration Manager**: Schema migrations and data transformations

### External APIs
- **Apollo API Agent**: Company data acquisition
- **Apify Agent**: Web scraping and contact extraction
- **Instantly Agent**: Email campaign delivery
- **HeyReach Agent**: LinkedIn outreach
- **Validation Agent**: Email validation (MillionVerifier, etc.)
- **Calendar Agent**: Google/Outlook calendar integration
- **CRM Connector**: Salesforce/HubSpot integration

### AI & Processing
- **LLM Agent**: Text generation (Claude, GPT)
- **Template Engine**: Message template processing
- **Analytics Engine**: Data analysis and insights
- **ML Scorer**: Lead scoring and classification

### Infrastructure
- **Rate Limiter**: QPS controls and throttling
- **Policy Checker**: Compliance and approval gates
- **Error Logger**: Centralized error tracking
- **Metrics Collector**: Performance and usage metrics
- **Dashboard Builder**: Real-time reporting interfaces
- **Email Parser**: Reply parsing and classification
- **Compliance Checker**: GDPR, CAN-SPAM validation

---

## Agent Delegation Map

```
Master Orchestrator
├── Lead Branch Orchestrator
│   ├── Database Agent (people schema operations)
│   ├── File Processor Agent (CSV parsing)
│   ├── Apollo API Agent (company data)
│   ├── Apify Agent (contact scraping)
│   └── Validation Agent (email validation)
│
├── Messaging Branch Orchestrator
│   ├── Database Agent (message storage)
│   ├── LLM Agent (content generation)
│   ├── Template Engine (message templates)
│   └── Policy Checker (approval gates)
│
├── Delivery Branch Orchestrator
│   ├── Database Agent (delivery tracking)
│   ├── Instantly Agent (email delivery)
│   ├── HeyReach Agent (LinkedIn delivery)
│   ├── Rate Limiter (QPS control)
│   └── Email Parser (reply processing)
│
└── [Future Branch Orchestrators...]
```

---

## Implementation Guidelines

### For New Projects
1. **Create Agent Architecture Document** (copy this template)
2. **Define Project-Specific Orchestrators** for each major workflow/branch
3. **Identify Required Global Agents** from the shared registry
4. **Document Delegation Patterns** (who calls whom)
5. **Implement Orchestrators** with clear handoff points to global agents
6. **Register Agents** in project-specific and global registries

### Agent Development Standards
- **Project Orchestrators**: Handle workflow logic, state management, error recovery
- **Global Specialists**: Handle specific technical operations, pure functions when possible
- **Clear Interfaces**: Standardized request/response patterns
- **Error Propagation**: Global agents report errors back to orchestrators
- **Logging**: All agent interactions logged with Barton Doctrine compliance

### Global Agent Registry Location
- **Path**: `/global-agents/` (separate from project code)
- **Deployment**: Shared across all projects
- **Versioning**: Semantic versioning for compatibility
- **Configuration**: Environment-specific settings

---

## Barton Outreach Core Status

### ✅ Implemented
- Global Database Agent (multi-platform)
- Basic project structure
- People schema (Neon)

### 🚧 In Progress
- Project-specific orchestrators
- Agent registry updates

### 📋 TODO
- Global agent implementations
- Workflow coordination logic
- Error handling and recovery
- Performance monitoring

---

This document should be updated whenever agents are added, modified, or deprecated.