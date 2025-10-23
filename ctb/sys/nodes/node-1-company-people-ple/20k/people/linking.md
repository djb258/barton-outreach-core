<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-1D8D7717
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# People-Company Linking Design (20k)

**Altitude**: 20k (Design only - no implementation)
**Status**: Linking rules and conflict resolution design

## Overview

This document defines how people records link to companies and slots, including conflict resolution, history tracking, and decision rules for ambiguous cases.

## Linking Architecture

### Primary Link: Person → Company
```
Person (person_id) → Company (company_uid)
- Relationship: MANY-TO-ONE (person works at one primary company)
- Constraint: Required (every person must have company association)
- Source: Determined during ingestion from Apollo/CSV data
```

### Secondary Link: Person → Slot
```  
Person (person_id) → Company Slot (slot_uid)
- Relationship: ONE-TO-ONE (person fills at most one slot)
- Constraint: Optional (person may not fill a tracked slot)
- Purpose: Role-based outreach targeting (CEO/CFO/HR)
```

### Tertiary Link: Historical Associations
```
Person → Company History (time-series)
- Relationship: ONE-TO-MANY (person may have worked at multiple companies)
- Purpose: Track career moves and maintain relationship context
- Storage: Separate history table (future implementation)
```

## Linking Rules

### Rule 1: Direct Company Match
**Trigger**: Person data includes company identifier
**Action**: Link person to matching company_uid
**Confidence**: High (direct match)

```
Input: person_data.company = "Acme Corp"
Query: SELECT company_uid FROM companies WHERE company_name = "Acme Corp"
Result: Link if single match found
```

### Rule 2: Domain-Based Linking  
**Trigger**: Person email domain matches company website
**Action**: Link person to company with matching domain
**Confidence**: Medium (domain inference)

```
Input: person_data.email = "john@acme.com"  
Query: SELECT company_uid FROM companies WHERE website LIKE "%acme.com%"
Result: Link if single unambiguous match
```

### Rule 3: Slot Assignment
**Trigger**: Person role matches available company slot
**Action**: Assign person to appropriate slot  
**Confidence**: High if role explicitly stated

```
Input: person_data.role = "CEO"
Logic: Find open CEO slot for person's company
Action: Update slot with person_id, mark slot as "filled"
```

### Rule 4: LinkedIn Profile Matching
**Trigger**: LinkedIn URL contains company information
**Action**: Parse company from LinkedIn and attempt match
**Confidence**: Medium (requires validation)

```
Input: linkedin_url = "linkedin.com/in/john-smith-ceo-acme"
Parse: Extract company hints from profile URL/description
Validate: Confirm against known companies
```

## Conflict Resolution

### Scenario 1: Multiple Company Matches
**Problem**: Person could belong to multiple companies with similar names
**Resolution Strategy**: 
1. Exact name match takes precedence
2. Domain match as tiebreaker
3. Manual review queue for ambiguous cases
4. Default to "unlinked" status pending resolution

**Example**:
```
Person: John Smith, john@acme.com
Companies: "Acme Corp", "Acme Industries", "Acme Solutions"
Resolution: Domain match to company with website "acme.com"
```

### Scenario 2: Slot Conflicts
**Problem**: Multiple people claim same slot (e.g., two CEOs)
**Resolution Strategy**:
1. Source priority: Apollo > CSV > Manual
2. Recency: Most recently updated person wins
3. Confidence score: Higher validation status wins
4. Escalation: Manual review for important conflicts

**Example**:
```
Conflict: Two people assigned to CEO slot at same company
Person A: Apollo source, validated email, updated yesterday  
Person B: CSV source, pending validation, updated last week
Resolution: Person A takes slot, Person B marked as "former/deputy"
```

### Scenario 3: Company History Tracking
**Problem**: Person moves between companies
**Resolution Strategy**:
1. Maintain primary (current) company link
2. Archive previous associations in history table
3. Update slot assignments (free up old slot)
4. Preserve relationship context for outreach

**Example**:
```
Timeline: John Smith moves from Acme Corp (CEO) to Beta Inc (CTO)
Action: 
- Update primary company: Beta Inc
- Archive history: Acme Corp (CEO, 2020-2024)
- Free Acme CEO slot
- Assign Beta CTO slot (if tracked)
```

## History Tracking Notes

### Change Events to Track
1. **Company Changes**: Person moves between companies
2. **Role Changes**: Title/position updates within same company  
3. **Slot Reassignments**: Movement between tracked slots
4. **Validation Updates**: Email/contact information changes
5. **Source Updates**: Data source changes or refreshes

### History Storage Design (Future)
```sql
-- DESIGN ONLY - NO IMPLEMENTATION
people_history:
  - history_id: UUID
  - person_id: FK to person
  - change_type: ENUM(company, role, slot, validation, source)
  - old_value: TEXT (JSON or string)
  - new_value: TEXT (JSON or string) 
  - changed_at: TIMESTAMP
  - changed_by: VARCHAR (system/user)
  - reason: TEXT (optional explanation)
```

### Historical Relationship Benefits
1. **Outreach Context**: "I see you recently moved from Acme to Beta..."
2. **Network Analysis**: Track people movement between companies
3. **Data Quality**: Detect suspicious rapid changes
4. **Compliance**: Audit trail for all data modifications

## Decision Trees

### Company Linking Decision Tree
```
New Person Record
├── Has explicit company_name?
│   ├── Yes → Exact match found?
│   │   ├── Yes → Link to company ✓
│   │   └── No → Check domain match
│   └── No → Extract from email domain
│       ├── Domain match found?
│       │   ├── Single match → Link to company ✓
│       │   ├── Multiple matches → Conflict resolution
│       │   └── No matches → Manual review queue
│       └── No domain → LinkedIn/manual review
```

### Slot Assignment Decision Tree  
```
Person Linked to Company
├── Has explicit role?
│   ├── Yes → Role matches tracked slot (CEO/CFO/HR)?
│   │   ├── Yes → Slot available?
│   │   │   ├── Yes → Assign to slot ✓
│   │   │   └── No → Conflict resolution
│   │   └── No → Store role, no slot assignment
│   └── No → Infer from title/LinkedIn
│       ├── Inference successful → Check slot availability
│       └── Inference failed → No slot assignment
```

## Validation & Quality Checks

### Link Quality Scores
- **High Confidence** (90-100%): Direct name match + domain match  
- **Medium Confidence** (70-89%): Single criterion match (name OR domain)
- **Low Confidence** (50-69%): Inference-based or LinkedIn parsing
- **Manual Review** (<50%): Multiple conflicts or no clear match

### Quality Assurance Rules
1. **Consistency Check**: Person's email domain should align with company website
2. **Slot Logic Check**: Person cannot fill multiple slots simultaneously
3. **Historical Validation**: Career moves should be chronologically sensible
4. **Cross-Reference**: LinkedIn profile should support company assignment

## Integration with Other Systems

### Ingest Process Integration
1. **Pre-Processing**: Company resolution happens before person creation
2. **Batch Processing**: Link people in batches after company ingestion
3. **Error Handling**: Failed links go to manual review queue
4. **Retry Logic**: Retry failed links after company database updates

### Validation System Integration
1. **Validation Triggers**: New links trigger email validation
2. **Quality Scoring**: Link confidence factors into validation priority
3. **Failed Validation**: Poor links may indicate data quality issues

### Outreach System Integration  
1. **Campaign Targeting**: Use slot assignments for role-based campaigns
2. **Personalization**: Leverage company context for message customization
3. **Relationship History**: Use historical associations for warmer outreach

## Manual Review Process

### Review Queue Criteria
- Multiple company matches with similar confidence
- Slot conflicts requiring business decision
- Suspicious patterns (rapid role changes)
- Data quality anomalies

### Review Interface Requirements (Future)
- Side-by-side comparison of conflicting options
- Historical context and timeline view
- Bulk resolution tools for similar patterns
- Integration with data sources for verification

## Error Handling & Monitoring

### Common Linking Errors
1. **Ambiguous Company**: Multiple reasonable matches
2. **Missing Company**: Person's company not in database  
3. **Stale Data**: Person moved but record not updated
4. **Data Conflicts**: Inconsistent information across sources

### Monitoring Metrics
- **Link Success Rate**: Percentage of people successfully linked
- **Manual Review Volume**: Queue size and resolution time  
- **Conflict Rate**: Frequency of linking conflicts
- **Quality Score Distribution**: Overall linking confidence levels

## 20k Constraints

⚠️ **Design Only**: Complete linking strategy without implementation
❌ **No Code**: No SQL queries, functions, or application logic
❌ **No Database Operations**: Schema and table creation deferred
✅ **Design Specification**: Comprehensive linking rules and conflict resolution