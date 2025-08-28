# Email Validation Plan (20k)

**Altitude**: 20k (Design only - no implementation)
**Status**: Validation strategy, statuses, retry logic, and cost management

## Overview

This document defines the email validation pipeline design for the Company + People system, including validation states, retry strategies, batching optimization, and cost guardrails to manage validation expenses.

## Validation States

### Primary States
- **pending**: Newly ingested email, not yet validated
- **valid**: Passed validation, safe for outreach
- **invalid**: Failed validation, cannot be used for outreach  
- **risky**: Questionable quality, use with caution
- **throttled**: Validation delayed due to cost/rate limits
- **error**: Validation service error, needs retry

### State Transitions
```
pending → [validating] → valid/invalid/risky/error
error → [retry] → valid/invalid/risky/error
throttled → [delay] → pending → validating
```

## Validation Pipeline Architecture

### Stage 1: Pre-Validation Filters
**Purpose**: Eliminate obviously invalid emails before paid validation
**Checks**:
- Basic format validation (regex)
- Domain existence (DNS MX record check)
- Disposable email detection
- Known bounce list check

**Cost Impact**: Free filtering reduces paid validation volume by ~30%

### Stage 2: Batch Processing
**Purpose**: Optimize validation costs through batching
**Strategy**:
- Collect emails in validation queue
- Process in batches of 100-500 emails
- Schedule batches during low-cost periods
- Priority queuing for urgent validations

### Stage 3: External Validation Service
**Purpose**: Professional validation via MillionVerifier or similar
**Process**:
- Submit batch to validation service
- Receive detailed validation results
- Parse and store validation metadata
- Update person records with validation status

## Cost Guardrails

### Budget Controls
- **Daily Limit**: Maximum validation spend per day
- **Monthly Budget**: Total validation budget with alerts at 80%
- **Per-Email Cost**: Track cost per validation for optimization
- **ROI Tracking**: Monitor validation cost vs. outreach conversion

### Prioritization Rules
1. **High Priority**: CEO/CFO contacts, recent imports
2. **Medium Priority**: HR contacts, bulk imports
3. **Low Priority**: Legacy data, low-confidence links
4. **Deferred**: Duplicate emails, suspicious sources

### Throttling Strategy
- **Cost-Based**: Slow validation when approaching budget limits
- **Quality-Based**: Prioritize high-value contacts during throttling
- **Time-Based**: Schedule expensive validations during off-peak hours
- **Source-Based**: Different validation intensity by data source

## Batching Strategy

### Batch Size Optimization
- **Small Batches** (50-100): Quick turnaround, higher per-email cost
- **Medium Batches** (100-500): Balanced cost and speed
- **Large Batches** (500-1000): Best cost efficiency, slower processing

### Batch Composition Rules
1. **Source Mixing**: Combine high and low confidence emails
2. **Priority Weighting**: Include mix of urgent and routine validations
3. **Cost Balancing**: Avoid all expensive validations in single batch
4. **Geographic Grouping**: Batch by region for provider optimization

### Batch Scheduling
- **Peak Hours** (9 AM - 5 PM): High priority validations only
- **Off-Peak Hours** (6 PM - 8 AM): Bulk validation processing
- **Weekend Processing**: Large batch processing for cost savings
- **Month-End**: Budget-conscious processing near monthly limits

## Retry Logic

### Retry Categories
1. **Network Errors**: Temporary connectivity issues
2. **Rate Limits**: API throttling from validation service
3. **Service Errors**: Temporary provider outages
4. **Parse Errors**: Malformed response data

### Retry Strategy
```
Attempt 1: Immediate retry (0 delay)
Attempt 2: 5-minute delay
Attempt 3: 30-minute delay  
Attempt 4: 2-hour delay
Attempt 5: 24-hour delay
Final: Move to manual review queue
```

### Backoff Algorithm
- **Exponential Backoff**: Delay = base_delay * (2 ^ attempt_number)
- **Jitter**: Add random variance to prevent thundering herd
- **Circuit Breaker**: Temporarily disable validation if high failure rate
- **Dead Letter Queue**: Capture permanently failed validations

## Validation Providers

### Primary Provider: MillionVerifier
**Strengths**: Cost-effective, bulk processing, detailed results
**Limitations**: Rate limits, occasional downtime
**Cost Structure**: Tiered pricing with volume discounts

### Backup Provider: ZeroBounce (Future)
**Purpose**: Failover for high availability
**Strategy**: Switch during MillionVerifier outages
**Cost Impact**: Higher per-email cost, reserved for emergencies

### Provider Contract Requirements
- **Bulk API Support**: Handle large batch submissions
- **Detailed Results**: Confidence scores, deliverability ratings
- **Error Handling**: Clear error codes and retry guidance
- **Cost Transparency**: Predictable pricing with volume tiers

## Data Quality Integration

### Validation Result Storage
```json
{
  "person_id": "PE-20240828-000001",
  "email": "john@acme.com",
  "validation_status": "valid",
  "validation_score": 95,
  "provider": "millionverifier",
  "provider_response": {
    "result": "ok",
    "reason": "mailbox_exists",
    "disposable": false,
    "role_account": false,
    "free_provider": false
  },
  "validated_at": "2024-08-28T15:30:00Z",
  "validation_cost": 0.007
}
```

### Quality Metrics
- **Validation Success Rate**: Percentage of emails successfully validated
- **False Positive Rate**: Valid emails marked as invalid
- **Cost Per Valid Email**: Total cost divided by valid emails found
- **Time to Validation**: Average processing time per email

## Cost Monitoring & Alerts

### Budget Tracking
- **Real-Time Spend**: Current day/month validation costs
- **Forecast Spend**: Projected costs based on queue size
- **Cost Per Contact**: Validation cost amortized across person records
- **ROI Analysis**: Validation cost vs. successful outreach outcomes

### Alert Thresholds
- **75% Budget**: Warning alert, consider throttling
- **90% Budget**: Critical alert, implement strict throttling  
- **95% Budget**: Emergency alert, pause non-critical validation
- **Cost Spike**: Unusual increase in per-email costs

### Reporting Dashboard (Future)
- Daily/monthly validation volume and costs
- Provider performance comparison
- Quality score distribution
- Failed validation analysis

## Integration Points

### Ingest Process Integration
1. **New Person Creation**: Automatically queue email for validation
2. **Bulk Import**: Add all emails to batch validation queue
3. **Priority Flagging**: Mark high-value contacts for expedited validation

### Outreach System Integration
1. **Campaign Filtering**: Only target emails with valid status
2. **Risk Assessment**: Use validation score for send prioritization
3. **Bounce Prevention**: Block outreach to invalid/risky emails

### Data Quality Feedback
1. **Bounce Tracking**: Update validation status based on actual bounces
2. **Engagement Metrics**: Factor open/click rates into quality scoring
3. **Manual Corrections**: Allow override of validation results

## Privacy & Compliance

### Data Protection
- **Temporary Storage**: Validation requests stored only during processing
- **Result Retention**: Keep validation metadata for optimization
- **Provider Agreements**: Ensure validation providers meet privacy standards

### Compliance Requirements
- **GDPR**: Validation as legitimate business interest
- **Consent Management**: Respect opt-out preferences during validation
- **Data Minimization**: Validate only emails intended for outreach

## Error Handling

### Common Validation Errors
1. **API Timeout**: Validation service unresponsive
2. **Invalid Format**: Malformed validation response
3. **Quota Exceeded**: Hit daily/monthly validation limits
4. **Authentication**: API key issues or account problems

### Error Recovery Strategies
- **Graceful Degradation**: Continue with pre-validation filters
- **Provider Failover**: Switch to backup validation service
- **Manual Review**: Queue problematic emails for human review
- **Status Preservation**: Maintain last known validation state

## Performance Optimization

### Validation Performance Targets
- **Batch Processing Time**: <5 minutes for 100-email batch
- **Queue Processing**: Clear daily queue within 24 hours
- **Error Rate**: <2% permanent validation failures
- **Cost Efficiency**: <$0.01 per validated email

### Optimization Strategies
- **Cache Results**: Avoid re-validating recently validated emails
- **Deduplication**: Validate unique emails only once
- **Smart Queuing**: Balance cost, priority, and processing time
- **Provider Selection**: Route emails to most cost-effective provider

## 20k Constraints

⚠️ **Design Only**: Complete validation strategy without implementation
❌ **No Integration**: No actual validation service connections
❌ **No Database Operations**: Validation result storage deferred
✅ **Design Specification**: Comprehensive validation pipeline design