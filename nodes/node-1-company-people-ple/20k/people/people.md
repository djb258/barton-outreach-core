# People Entity Design (20k)

**Altitude**: 20k (Design only - no implementation)
**Status**: Design documentation for people data structure

## Overview

This document defines the minimal people entity structure for the Company + People + PLE system. The design focuses on essential fields needed for outreach operations while maintaining data privacy and operational efficiency.

## Minimal People Fields

### Core Identity
- **person_id**: Unique identifier (PE-YYYYMMDD-######)
- **name**: Full name (required for outreach)
- **email**: Primary contact method (required, validated)

### Company Association  
- **company_uid**: Link to company record (FK to marketing.company)
- **role**: Position at company (CEO/CFO/HR or custom)
- **slot_uid**: Link to company slot if assigned

### Contact Information
- **linkedin_url**: Professional profile for LinkedIn outreach
- **phone**: Optional phone number (E.164 format)
- **title**: Job title (as provided by source)

### Data Quality & Tracking
- **validation_status**: Email validation state
- **source**: Data origin (apollo, csv, manual)
- **created_at**: Record creation timestamp  
- **updated_at**: Last modification timestamp

## Field Rationale

### Why Minimal?
**Privacy by Design**: Store only data essential for outreach operations
**Cost Efficiency**: Reduce validation and storage costs
**Compliance**: Minimize PII exposure and GDPR/CCPA surface area
**Performance**: Faster queries and smaller indexes

### Why These Specific Fields?

#### person_id (PE-YYYYMMDD-######)
- **Purpose**: Unique identification across systems
- **Pattern**: Consistent with company_uid and slot_uid patterns
- **Benefits**: Sortable by date, collision-resistant, human-readable

#### name + email (Required)
- **Purpose**: Core outreach requirements
- **Rationale**: Cannot conduct outreach without name and validated email
- **Validation**: Email must pass validation pipeline before outreach

#### company_uid + role + slot_uid
- **Purpose**: Company-person relationship management
- **Design**: Flexible slot assignment (person can fill multiple roles)
- **Benefits**: Supports org chart changes and role transitions

#### linkedin_url (Optional)
- **Purpose**: Multi-channel outreach capability
- **Format**: Full LinkedIn profile URL for automation
- **Privacy**: Public profile information only

#### source (apollo/csv/manual)
- **Purpose**: Data lineage tracking
- **Benefits**: Quality assessment, refresh strategy, compliance auditing
- **Values**: Enum limited to known sources

### Excluded Fields (Rationale)

#### Demographics (age, gender, location)
- **Reason**: Not required for B2B outreach
- **Risk**: Potential bias and privacy concerns
- **Alternative**: Infer from company location if needed

#### Personal Details (address, personal phone)
- **Reason**: B2B focus on professional contact
- **Privacy**: Reduce PII storage
- **Compliance**: Lower regulatory burden

#### Social Media (except LinkedIn)  
- **Reason**: LinkedIn sufficient for professional outreach
- **Efficiency**: Reduce data sprawl and maintenance
- **Focus**: Quality over quantity

## Data Types & Constraints

### String Fields
- **name**: VARCHAR(255), NOT NULL
- **email**: VARCHAR(255), NOT NULL, UNIQUE
- **linkedin_url**: TEXT, NULLABLE
- **title**: VARCHAR(255), NULLABLE
- **source**: ENUM('apollo', 'csv', 'manual'), NOT NULL

### ID Fields  
- **person_id**: VARCHAR(50), PRIMARY KEY, pattern PE-YYYYMMDD-######
- **company_uid**: VARCHAR(50), FOREIGN KEY, NOT NULL
- **slot_uid**: VARCHAR(50), FOREIGN KEY, NULLABLE

### Status Fields
- **validation_status**: ENUM('pending', 'valid', 'invalid', 'risky'), DEFAULT 'pending'
- **role**: VARCHAR(100), NOT NULL

### Timestamps
- **created_at**: TIMESTAMP, DEFAULT NOW(), NOT NULL
- **updated_at**: TIMESTAMP, DEFAULT NOW() ON UPDATE, NOT NULL

## Business Rules

### Validation Requirements
1. **Email Format**: Must pass regex validation before storage
2. **LinkedIn URL**: Must be linkedin.com domain if provided  
3. **Name Normalization**: Trim whitespace, title case
4. **Source Tracking**: Must specify source for all records

### Relationship Rules
1. **Company Link**: Every person must link to valid company
2. **Slot Assignment**: Optional but recommended for key roles
3. **Role Flexibility**: Support standard roles (CEO/CFO/HR) plus custom
4. **Multi-Role**: Person can fill multiple slots over time (history tracked)

### Data Quality Standards
1. **Required Validation**: Email must be validated before outreach
2. **Source Attribution**: All records must specify data source
3. **Update Tracking**: Timestamp all modifications
4. **Deduplication**: Prevent duplicate emails across records

## Privacy & Compliance

### Data Minimization
- Store only essential fields for business function
- No demographic or sensitive personal information
- Professional contact information only

### Retention Policy
- Active records: Maintain while business relationship exists
- Inactive records: Archive after 2 years of no engagement
- Validation results: Keep for compliance auditing

### Access Controls
- Read access: Outreach team and analytics
- Write access: Data ingestion systems only
- Admin access: Data governance team

## Integration Points

### Inbound Data Sources
- **Apollo.io**: Company + people data via ingest repo
- **CSV Uploads**: Manual data entry via ingest repo
- **CRM Systems**: Future integration point

### Outbound Consumers
- **Validation Service**: Email validation pipeline
- **Outreach Platform**: Campaign execution system
- **Analytics**: Performance and quality reporting

## Future Considerations (Not 20k Scope)

### Enrichment Fields (Future)
- Social media profiles (beyond LinkedIn)
- Professional certifications
- Company tenure and history
- Contact preferences

### Advanced Features (Future)
- Consent management integration
- Communication history tracking
- Preference and opt-out management
- Advanced deduplication algorithms

## 20k Constraints

⚠️ **Design Only**: This is design documentation only
❌ **No Implementation**: No SQL DDL or code at 20k altitude
❌ **No Database Operations**: Schema creation deferred to higher altitudes
✅ **Design Specification**: Complete field design and rationale