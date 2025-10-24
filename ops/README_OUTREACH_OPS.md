# 📡 Outreach Operations Guide

**System:** Event-Driven Outreach Pipeline
**Database:** Neon PostgreSQL (Single Source of Truth)
**Orchestration:** n8n Cloud (https://dbarton.app.n8n.cloud)
**Architecture:** Hybrid Event + REST API Monitoring

---

## 🏗️ System Architecture

### Event-Driven Model

```
┌─────────────────────────────────────────────────────────────────┐
│ EVENT-DRIVEN PIPELINE (Neon Triggers → n8n Webhooks)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data Change (INSERT/UPDATE)                                   │
│         ↓                                                       │
│  PostgreSQL Trigger Fires                                      │
│         ↓                                                       │
│  INSERT INTO marketing.pipeline_events                         │
│         ↓                                                       │
│  pg_notify('pipeline_event', payload)                          │
│         ↓                                                       │
│  n8n Webhook Receives Event                                    │
│         ↓                                                       │
│  Workflow Executes (validation/enrichment/delivery)            │
│         ↓                                                       │
│  Write Back to Neon (status updates)                           │
│         ↓                                                       │
│  Next Trigger Fires → Cascade Continues                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principles:**
1. **Single Source of Truth:** All state lives in Neon PostgreSQL
2. **Zero Polling:** Pure event-driven (no scheduled workflows checking for data)
3. **Cascading Events:** Each stage writes back, triggering the next stage
4. **Full Audit Trail:** Every event logged in `marketing.pipeline_events`

---

## 🔄 Hybrid Monitoring Strategy

### 1. Live Monitoring (n8n REST API)

Use n8n REST API for real-time workflow execution monitoring:

```javascript
// Get recent executions
GET https://dbarton.app.n8n.cloud/api/v1/executions

// Check workflow status
GET https://dbarton.app.n8n.cloud/api/v1/workflows/:workflowId

// Get execution details
GET https://dbarton.app.n8n.cloud/api/v1/executions/:executionId
```

**Use Cases:**
- Real-time debugging
- Active workflow monitoring
- Performance metrics (execution time, success rate)
- Error detection and alerts

### 2. Historical Analysis (Neon Tables)

Query Neon for historical data and long-term analytics:

```sql
-- Event processing latency
SELECT
  event_type,
  AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_latency_sec,
  COUNT(*) as total_events
FROM marketing.pipeline_events
WHERE processed_at IS NOT NULL
GROUP BY event_type;

-- Error rate by stage
SELECT * FROM marketing.vw_error_rate_24h;

-- Unresolved errors
SELECT * FROM marketing.vw_unresolved_errors;
```

**Use Cases:**
- Long-term trend analysis
- Pipeline performance optimization
- Error pattern identification
- Compliance and auditing

### 3. Hybrid Dashboard (Recommended)

Combine both for comprehensive monitoring:

```
┌──────────────────────────────────────────────────────────┐
│ OUTREACH PIPELINE DASHBOARD                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [n8n API] Real-Time Status                             │
│  • Active Workflows: 5/5                                │
│  • Current Executions: 3 running                        │
│  • Last 5 Minutes: 47 events processed                  │
│                                                          │
│  [Neon DB] Historical Metrics                           │
│  • Total Events (24h): 1,247                            │
│  • Success Rate: 98.3%                                  │
│  • Avg Latency: 2.1s                                    │
│  • Unresolved Errors: 4                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 Three Operational Phases

### Phase 1: Enrichment (Data Gathering)

**Goal:** Collect and validate contact information

**Stages:**
1. **Company Validation** - Verify company name and website
2. **Company Promotion** - Generate Barton IDs, insert into master table
3. **Slot Creation** - Create executive role slots (CEO, CFO, HR)
4. **Contact Enrichment** - Use Apify/LinkedIn to find contact details
5. **Email Verification** - Validate email deliverability with MillionVerifier

**Key Tables:**
- `intake.company_raw_intake` - Raw CSV imports
- `marketing.company_master` - Validated companies with Barton IDs
- `marketing.company_slots` - Executive role slots
- `marketing.contact_enrichment` - Enriched contact data
- `marketing.email_verification` - Email validation results

**Events:**
- `company_created` → Validation Gatekeeper
- `company_validated` → Promotion Runner
- `company_promoted` → Slot Creator
- `slots_created` → Apify Enrichment
- `contact_enriched` → MillionVerify Checker

**Success Criteria:**
- ✅ 95%+ validation success rate
- ✅ 90%+ email enrichment rate
- ✅ 85%+ email deliverability
- ✅ <5 minute end-to-end latency

---

### Phase 2: Messaging (Campaign Execution)

**Goal:** Personalize and send outreach messages

**Stages:**
1. **Segment Selection** - Filter contacts by criteria (industry, role, verification status)
2. **Message Personalization** - Generate personalized email content using templates + AI
3. **Campaign Scheduling** - Queue messages for delivery
4. **Send Execution** - Deliver via SMTP/SendGrid/Amazon SES
5. **Delivery Tracking** - Log send status, bounces, opens

**Key Tables:**
- `marketing.campaigns` - Campaign definitions
- `marketing.campaign_contacts` - Contacts in each campaign
- `marketing.message_templates` - Email templates
- `marketing.message_queue` - Queued messages
- `marketing.delivery_log` - Send results

**Events:**
- `campaign_created` → Segment Builder
- `segment_ready` → Message Personalizer
- `message_personalized` → Campaign Scheduler
- `message_queued` → Send Executor
- `message_sent` → Delivery Tracker

**Success Criteria:**
- ✅ 90%+ delivery rate (not bounced)
- ✅ 20%+ open rate
- ✅ 5%+ reply rate
- ✅ <10% unsubscribe rate

---

### Phase 3: Delivery & Engagement (Response Management)

**Goal:** Track responses, manage conversations, measure ROI

**Stages:**
1. **Engagement Tracking** - Monitor opens, clicks, replies
2. **Response Processing** - Parse and categorize email replies
3. **Lead Scoring** - Score leads based on engagement signals
4. **CRM Sync** - Push qualified leads to CRM (Salesforce, HubSpot)
5. **Follow-Up Automation** - Trigger follow-up sequences based on behavior

**Key Tables:**
- `marketing.engagement_events` - Opens, clicks, replies
- `marketing.responses` - Email replies with sentiment analysis
- `marketing.lead_scores` - Calculated lead scores
- `marketing.crm_sync_log` - CRM integration logs
- `marketing.follow_up_queue` - Scheduled follow-ups

**Events:**
- `email_opened` → Engagement Tracker
- `email_clicked` → Engagement Tracker
- `reply_received` → Response Processor
- `lead_qualified` → CRM Syncer
- `follow_up_due` → Follow-Up Sender

**Success Criteria:**
- ✅ 100% response capture (no missed replies)
- ✅ 80%+ sentiment analysis accuracy
- ✅ 15%+ lead qualification rate
- ✅ <1 hour CRM sync latency

---

## 🧠 Intelligence Layer (PLE + BIT)

### PLE (Pipeline Learning Engine)

**Purpose:** Learn from pipeline performance to optimize future campaigns

**Capabilities:**
1. **A/B Testing** - Test subject lines, message templates, send times
2. **Performance Analysis** - Identify which segments/messages perform best
3. **Predictive Scoring** - Predict likelihood of response before sending
4. **Dynamic Optimization** - Adjust campaigns in real-time based on results

**Implementation:**
```sql
-- Create PLE tables
CREATE TABLE marketing.ab_tests (
  test_id SERIAL PRIMARY KEY,
  test_name TEXT,
  variant_a JSONB,
  variant_b JSONB,
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  winner TEXT
);

CREATE TABLE marketing.performance_metrics (
  metric_id SERIAL PRIMARY KEY,
  campaign_id INT,
  segment TEXT,
  template_id INT,
  send_time TIME,
  open_rate NUMERIC,
  click_rate NUMERIC,
  reply_rate NUMERIC,
  measured_at TIMESTAMP
);
```

**Example Analysis:**
```sql
-- Find best performing segments
SELECT
  segment,
  AVG(open_rate) as avg_open,
  AVG(reply_rate) as avg_reply,
  COUNT(*) as campaigns
FROM marketing.performance_metrics
GROUP BY segment
ORDER BY avg_reply DESC;
```

---

### BIT (Barton Intelligence Tracker)

**Purpose:** Track long-term contact relationships and engagement history

**Capabilities:**
1. **Contact Timeline** - Full history of all interactions with each contact
2. **Relationship Mapping** - Track connections between contacts (same company, referrals)
3. **Engagement Patterns** - Identify optimal contact frequency and timing
4. **Lifetime Value** - Calculate ROI per contact/company over time

**Implementation:**
```sql
-- Create BIT tables
CREATE TABLE marketing.contact_timeline (
  event_id SERIAL PRIMARY KEY,
  contact_id INT,
  event_type TEXT, -- email_sent, reply_received, meeting_booked, deal_closed
  event_data JSONB,
  event_timestamp TIMESTAMP
);

CREATE TABLE marketing.relationship_graph (
  relationship_id SERIAL PRIMARY KEY,
  contact_a_id INT,
  contact_b_id INT,
  relationship_type TEXT, -- colleague, referral, manager
  discovered_at TIMESTAMP
);

CREATE TABLE marketing.contact_ltv (
  contact_id INT PRIMARY KEY,
  total_emails_sent INT,
  total_replies INT,
  meetings_booked INT,
  deals_closed INT,
  total_revenue NUMERIC,
  last_contact_at TIMESTAMP
);
```

**Example Analysis:**
```sql
-- Identify high-value contacts
SELECT
  c.full_name,
  c.company_name,
  ltv.total_revenue,
  ltv.meetings_booked,
  ltv.total_replies * 100.0 / NULLIF(ltv.total_emails_sent, 0) as reply_rate
FROM marketing.contact_ltv ltv
JOIN marketing.contact_enrichment c ON c.id = ltv.contact_id
WHERE ltv.total_revenue > 10000
ORDER BY ltv.total_revenue DESC;
```

---

## 📊 Monitoring Queries

### Event Queue Health

```sql
-- Pending events (should be low)
SELECT event_type, COUNT(*) as pending_count
FROM marketing.pipeline_events
WHERE status = 'pending'
GROUP BY event_type;

-- Processing latency by stage
SELECT
  event_type,
  AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_seconds,
  MAX(EXTRACT(EPOCH FROM (processed_at - created_at))) as max_seconds
FROM marketing.pipeline_events
WHERE processed_at IS NOT NULL
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY event_type
ORDER BY avg_seconds DESC;
```

### Error Monitoring

```sql
-- Recent errors
SELECT
  event_type,
  record_id,
  error_message,
  severity,
  created_at
FROM marketing.pipeline_errors
WHERE resolved = FALSE
ORDER BY created_at DESC
LIMIT 20;

-- Error rate by stage
SELECT
  event_type,
  COUNT(*) as error_count,
  COUNT(*) FILTER (WHERE severity = 'critical') as critical_count
FROM marketing.pipeline_errors
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY event_type
ORDER BY error_count DESC;
```

### Campaign Performance

```sql
-- Campaign overview (Phase 2)
SELECT
  c.campaign_name,
  COUNT(DISTINCT cc.contact_id) as total_contacts,
  COUNT(DISTINCT dl.contact_id) FILTER (WHERE dl.status = 'delivered') as delivered,
  COUNT(DISTINCT ee.contact_id) FILTER (WHERE ee.event_type = 'open') as opened,
  COUNT(DISTINCT r.contact_id) as replied
FROM marketing.campaigns c
LEFT JOIN marketing.campaign_contacts cc ON c.id = cc.campaign_id
LEFT JOIN marketing.delivery_log dl ON cc.contact_id = dl.contact_id
LEFT JOIN marketing.engagement_events ee ON cc.contact_id = ee.contact_id
LEFT JOIN marketing.responses r ON cc.contact_id = r.contact_id
WHERE c.created_at > NOW() - INTERVAL '7 days'
GROUP BY c.id, c.campaign_name
ORDER BY c.created_at DESC;
```

---

## 🚨 Operational Alerts

### Critical Alerts (Immediate Action)

1. **Pipeline Stalled**
   - Condition: >100 events stuck in 'pending' for >5 minutes
   - Action: Check n8n workflow status, restart if needed

2. **High Error Rate**
   - Condition: >10% error rate in any stage over 1 hour
   - Action: Review logs, check API credentials, fix data issues

3. **Email Deliverability Drop**
   - Condition: >20% bounce rate
   - Action: Check SMTP configuration, review email content for spam triggers

4. **CRM Sync Failure**
   - Condition: No successful syncs in last 30 minutes
   - Action: Verify CRM API credentials, check network connectivity

### Warning Alerts (Monitor Closely)

1. **Slow Processing**
   - Condition: Average event latency >10 seconds
   - Action: Check database performance, review workflow complexity

2. **Low Enrichment Rate**
   - Condition: <70% email enrichment success
   - Action: Review Apify quota, check LinkedIn data quality

3. **Reply Rate Drop**
   - Condition: <3% reply rate (below baseline)
   - Action: Review message templates, analyze engagement data

---

## 🛠️ Operational Commands

### n8n Workflow Management

```bash
# List all workflows
curl -X GET https://dbarton.app.n8n.cloud/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# Activate workflow
curl -X POST https://dbarton.app.n8n.cloud/api/v1/workflows/:id/activate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# Get recent executions
curl -X GET https://dbarton.app.n8n.cloud/api/v1/executions?limit=10 \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Database Maintenance

```sql
-- Purge old processed events (keep 30 days)
DELETE FROM marketing.pipeline_events
WHERE status = 'processed'
  AND processed_at < NOW() - INTERVAL '30 days';

-- Purge old resolved errors (keep 90 days)
DELETE FROM marketing.pipeline_errors
WHERE resolved = TRUE
  AND resolved_at < NOW() - INTERVAL '90 days';

-- Vacuum and analyze
VACUUM ANALYZE marketing.pipeline_events;
VACUUM ANALYZE marketing.pipeline_errors;
```

### Manual Event Triggering

```sql
-- Manually insert event for testing
INSERT INTO marketing.pipeline_events (event_type, payload, status)
VALUES (
  'company_created',
  jsonb_build_object(
    'record_id', 999,
    'company_name', 'Test Company',
    'website', 'https://test.com',
    'trigger_time', NOW()
  ),
  'pending'
);
```

---

## 📈 Success Metrics

### Phase 1: Enrichment
| Metric | Target | Excellent |
|--------|--------|-----------|
| Validation Success Rate | 90% | 95%+ |
| Email Enrichment Rate | 80% | 90%+ |
| Email Deliverability | 80% | 90%+ |
| End-to-End Latency | <10 min | <5 min |

### Phase 2: Messaging
| Metric | Target | Excellent |
|--------|--------|-----------|
| Delivery Rate | 85% | 95%+ |
| Open Rate | 15% | 25%+ |
| Click Rate | 3% | 8%+ |
| Reply Rate | 3% | 7%+ |

### Phase 3: Delivery
| Metric | Target | Excellent |
|--------|--------|-----------|
| Response Capture | 95% | 100% |
| Lead Qualification Rate | 10% | 20%+ |
| Meeting Booking Rate | 2% | 5%+ |
| Deal Close Rate | 0.5% | 2%+ |

---

## 🔐 Security & Compliance

### Data Protection

1. **Encryption at Rest** - Neon database encrypted
2. **Encryption in Transit** - All API calls over HTTPS
3. **Access Control** - Role-based permissions (n8n_user, owner)
4. **Credential Management** - API keys stored in n8n environment variables

### GDPR Compliance

1. **Right to Access** - Query all data for a contact
2. **Right to Erasure** - Delete contact and all associated events
3. **Consent Tracking** - Log opt-ins and opt-outs
4. **Data Retention** - Auto-delete old events (30-90 days)

```sql
-- GDPR: Export all data for a contact
SELECT * FROM marketing.contact_enrichment WHERE email = 'user@example.com';
SELECT * FROM marketing.engagement_events WHERE contact_id = 123;

-- GDPR: Delete all data for a contact
DELETE FROM marketing.engagement_events WHERE contact_id = 123;
DELETE FROM marketing.contact_enrichment WHERE id = 123;
```

---

## 📚 Related Documentation

- **[EVENT_DRIVEN_DEPLOYMENT_GUIDE.md](../docs/EVENT_DRIVEN_DEPLOYMENT_GUIDE.md)** - Full deployment instructions
- **[PIPELINE_EVENT_FLOW.md](../docs/PIPELINE_EVENT_FLOW.md)** - Event chain diagrams
- **[n8n_webhook_registry.json](../workflows/n8n_webhook_registry.json)** - Webhook URL mapping
- **[EVENT_DRIVEN_SYSTEM_README.md](../EVENT_DRIVEN_SYSTEM_README.md)** - Quick start guide

---

## 🆘 Support & Troubleshooting

### Common Issues

1. **Events not firing** → Check trigger definitions in Neon
2. **Webhooks not receiving** → Verify workflow is active in n8n
3. **High latency** → Check database query performance
4. **API rate limits** → Implement exponential backoff, increase quotas

### Escalation Path

1. **Level 1:** Check documentation, review error logs
2. **Level 2:** Query Neon tables for historical data
3. **Level 3:** Check n8n execution logs via REST API
4. **Level 4:** Contact platform support (Neon, n8n, Apify)

---

**Last Updated:** 2025-10-24
**Version:** 1.0.0
**Maintained By:** Pipeline Operations Team
