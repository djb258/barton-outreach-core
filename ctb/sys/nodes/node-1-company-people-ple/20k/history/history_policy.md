<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-CA39D76D
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# History Policy Design (20k)

**Altitude**: 20k (Design only - no implementation)  
**Status**: Data freshness thresholds and skip/refresh decision framework

## Overview

This document defines the history and data freshness policy for the Company + People + PLE system. It establishes thresholds for data staleness, decision rules for skip vs. refresh operations, and strategies for maintaining data quality while minimizing processing costs.

## Freshness Thresholds

### Company Data Freshness
- **Fresh**: Updated within 30 days
- **Stale**: 31-90 days since last update
- **Expired**: >90 days since last update
- **Ancient**: >365 days since last update

### People Data Freshness  
- **Fresh**: Updated within 7 days
- **Stale**: 8-30 days since last update
- **Expired**: >30 days since last update
- **Ancient**: >180 days since last update

### Validation Data Freshness
- **Fresh**: Validated within 24 hours
- **Stale**: 25 hours - 7 days since validation
- **Expired**: >7 days since validation
- **Ancient**: >30 days since validation

### Contact Engagement Freshness
- **Active**: Engaged within 30 days (opens, clicks, replies)
- **Dormant**: 31-90 days since last engagement
- **Inactive**: >90 days since engagement
- **Cold**: >365 days since engagement

## Skip vs. Refresh Decision Matrix

### High-Value Contacts (CEO/CFO)
| Data Age | Engagement | Decision | Rationale |
|----------|------------|----------|-----------|
| Fresh | Active | **SKIP** | Recent and engaged |
| Fresh | Dormant | **SKIP** | Recently updated |
| Stale | Active | **REFRESH** | Engaged but data aging |
| Stale | Inactive | **CONDITIONAL** | Check campaign priority |
| Expired | Any | **REFRESH** | Data too old |

### Medium-Value Contacts (HR/Manager)
| Data Age | Engagement | Decision | Rationale |
|----------|------------|----------|-----------|
| Fresh | Active | **SKIP** | Recent and engaged |
| Fresh | Dormant | **SKIP** | Recently updated |
| Stale | Active | **REFRESH** | Worth updating if engaged |
| Stale | Inactive | **SKIP** | Low priority for refresh |
| Expired | Active | **REFRESH** | Engagement justifies update |
| Expired | Inactive | **ARCHIVE** | Consider removing |

### Low-Value Contacts (General)
| Data Age | Engagement | Decision | Rationale |
|----------|------------|----------|-----------|
| Fresh | Any | **SKIP** | Recently updated |
| Stale | Active | **CONDITIONAL** | Budget permitting |
| Stale | Inactive | **SKIP** | Not worth refreshing |
| Expired | Active | **CONDITIONAL** | High engagement only |
| Expired | Inactive | **ARCHIVE** | Remove from active pool |

## Decision Tree Logic

### Primary Decision Factors
1. **Contact Value** (CEO > CFO > HR > Manager > Individual Contributor)
2. **Data Freshness** (Fresh > Stale > Expired > Ancient)
3. **Engagement Level** (Active > Dormant > Inactive > Cold)
4. **Campaign Priority** (High > Medium > Low priority campaigns)
5. **Processing Budget** (Available budget for refreshes)

### Decision Tree Implementation
```
New Processing Request
├── Is contact high-value? (CEO/CFO)
│   ├── Yes → Is data fresh? (<7 days)
│   │   ├── Yes → SKIP (recent high-value data)
│   │   └── No → Is contact engaged? (<30 days)
│   │       ├── Yes → REFRESH (engaged high-value)
│   │       └── No → Is data expired? (>30 days)
│   │           ├── Yes → REFRESH (expired high-value)
│   │           └── No → CONDITIONAL (stale high-value)
│   └── No → Is data fresh? (<7 days)  
│       ├── Yes → SKIP (recent data)
│       └── No → Is contact engaged? (<30 days)
│           ├── Yes → Is budget available?
│           │   ├── Yes → REFRESH (engaged + budget)
│           │   └── No → QUEUE (wait for budget)
│           └── No → Is data ancient? (>180 days)
│               ├── Yes → ARCHIVE (too old, no engagement)
│               └── No → SKIP (not worth refreshing)
```

## Skip Strategies

### Skip Categories
1. **HARD_SKIP**: Never process (recent, high-quality data)
2. **SOFT_SKIP**: Skip now, reconsider later (budget-dependent)
3. **CONDITIONAL_SKIP**: Skip unless specific criteria met
4. **DEFERRED_SKIP**: Skip now, schedule for later processing

### Skip Reasons Tracking
- `recent_update`: Data updated within freshness threshold
- `low_priority`: Contact value doesn't justify processing cost
- `budget_exhausted`: No budget remaining for refreshes
- `engagement_poor`: No recent engagement history
- `validation_current`: Email validation still valid
- `campaign_inactive`: No active campaigns targeting contact

## Refresh Strategies

### Refresh Prioritization
1. **URGENT**: High-value contacts in active campaigns
2. **HIGH**: CEO/CFO contacts with stale but not expired data  
3. **MEDIUM**: Engaged contacts with expired data
4. **LOW**: Background refresh of inactive contacts
5. **DEFERRED**: Budget-permitting refresh of archived data

### Refresh Data Sources
- **Primary**: Apollo.io API refresh for most current data
- **Secondary**: LinkedIn profile scraping for role/company changes
- **Tertiary**: Manual research queue for critical contacts
- **Fallback**: Previous data with staleness flag

### Refresh Scope Options
- **FULL_REFRESH**: Complete contact and company data update
- **CONTACT_ONLY**: Update person data, skip company refresh
- **VALIDATION_ONLY**: Re-validate email, skip data refresh
- **MINIMAL_REFRESH**: Update key fields only (title, company)

## History Tracking Design

### Change Event Types
- **DATA_REFRESH**: Full data update from external source
- **VALIDATION_REFRESH**: Email re-validation only
- **ENGAGEMENT_UPDATE**: Contact engagement status change
- **MANUAL_UPDATE**: Human-initiated data correction
- **AUTOMATED_CLEANUP**: System-initiated archiving/cleanup

### History Record Structure (Future Implementation)
```json
{
  "history_id": "hist_20240828_001",
  "person_id": "PE-20240828-000001", 
  "event_type": "DATA_REFRESH",
  "old_values": {
    "title": "Senior Manager",
    "company_uid": "CO-20240101-000001",
    "validation_status": "stale"
  },
  "new_values": {
    "title": "VP Marketing", 
    "company_uid": "CO-20240101-000001",
    "validation_status": "valid"
  },
  "change_reason": "apollo_refresh",
  "data_source": "apollo.io",
  "changed_at": "2024-08-28T15:30:00Z",
  "cost": 0.05
}
```

## Budget and Cost Management

### Cost Tracking by Operation
- **Data Refresh**: Cost per Apollo.io API call
- **Email Validation**: Cost per validation check
- **LinkedIn Scraping**: Cost per profile access
- **Manual Research**: Time cost for human review

### Budget Allocation Strategy
- **70%**: High-value contact refreshes (CEO/CFO/key prospects)
- **20%**: Medium-value contact validation and updates
- **10%**: Experimental/bulk refresh operations

### Cost Optimization Rules
1. **Batch Processing**: Group refreshes for volume discounts
2. **Source Selection**: Use cheapest appropriate data source
3. **Incremental Updates**: Refresh only changed fields when possible
4. **Cache Results**: Avoid duplicate refreshes within short timeframes

## Data Quality Metrics

### Freshness Metrics
- **Average Data Age**: Mean age across all contact records
- **Stale Data Percentage**: Portion of records exceeding freshness threshold
- **Refresh Success Rate**: Percentage of refreshes that improve data quality
- **Cost Per Quality Point**: Budget spent per data quality improvement

### Skip/Refresh Analytics
- **Skip Rate**: Percentage of contacts skipped during processing
- **Refresh Rate**: Percentage of contacts refreshed 
- **Accuracy Improvement**: Quality gain from refresh operations
- **Budget Utilization**: Percentage of refresh budget used

## Compliance and Privacy

### Data Retention Policy
- **Active Contacts**: Retain while business relationship exists
- **Inactive Contacts**: Archive after 12 months of no engagement
- **Historical Changes**: Keep change history for 2 years
- **Deleted Records**: Purge completely after 30-day recovery window

### Privacy Considerations
- **Minimal Refresh**: Only update data necessary for business purpose
- **Consent Respect**: Honor opt-out requests during refresh operations
- **Data Minimization**: Remove unnecessary fields during refresh
- **Source Attribution**: Track data source for privacy compliance

## Error Handling

### Refresh Failure Scenarios
1. **Source Unavailable**: External API/service downtime
2. **Rate Limit Hit**: Exceeded API call limits
3. **Data Not Found**: Contact no longer exists at source
4. **Validation Failed**: New data fails quality checks
5. **Budget Exhausted**: No funds remaining for refresh

### Failure Recovery Strategies
- **Retry Logic**: Exponential backoff for temporary failures
- **Alternative Sources**: Fall back to secondary data sources
- **Partial Updates**: Save partial data if full refresh fails
- **Manual Queue**: Escalate critical failures for human review
- **Status Preservation**: Maintain last known good state

## Performance Targets

### Processing Performance
- **Skip Decision Time**: <100ms per contact evaluation
- **Refresh Processing**: <5 seconds per contact refresh
- **Batch Processing**: Handle 1,000 contacts per hour
- **Queue Clearance**: Process daily refresh queue within 8 hours

### Quality Targets
- **Data Freshness**: 90% of active contacts have fresh data
- **Validation Currency**: 95% of outreach emails validated within 7 days
- **Accuracy Improvement**: 80% of refreshes result in data quality gains
- **Cost Efficiency**: Achieve quality targets within budget constraints

## 20k Constraints

⚠️ **Design Only**: Complete history policy specification
❌ **No Implementation**: No database operations or processing logic
❌ **No Automation**: Decision tree logic defined but not coded
✅ **Policy Framework**: Comprehensive freshness and refresh strategy