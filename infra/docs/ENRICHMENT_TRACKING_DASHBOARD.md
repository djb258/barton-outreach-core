# Executive Enrichment Monitoring Dashboard

## 📊 Overview

This dashboard provides real-time monitoring of executive enrichment jobs for CFO, CEO, and HR positions. It allows you to track which enrichments haven't happened, monitor agent performance, and see how long enrichment jobs are taking.

**Dashboard URL:** http://localhost:3000/d/executive-enrichment-monitoring

## 🎯 Purpose

Monitor and track:
- Which executive slots (CFO/CEO/HR) need enrichment
- Currently running enrichment jobs and their duration
- Failed jobs that need retry
- Agent performance metrics (success rates, duration, cost)
- Historical enrichment activity trends

## 📈 Dashboard Sections

### Row 1: Real-Time Metrics (Stat Panels)

#### Panel 1: Pending Jobs
- **What it shows:** Count of enrichment jobs waiting to start
- **Thresholds:**
  - Green: 0-4 jobs
  - Yellow: 5-19 jobs
  - Red: 20+ jobs (backlog building up)
- **Refresh:** 10 seconds
- **Action needed if red:** Check if agents are running, investigate why jobs aren't starting

#### Panel 2: Running Jobs
- **What it shows:** Count of enrichment jobs currently executing
- **Thresholds:**
  - Blue: 0-2 jobs (normal)
  - Orange: 3-9 jobs (busy)
  - Red: 10+ jobs (possible bottleneck)
- **Refresh:** 10 seconds
- **Action needed if red:** Check for stuck jobs in the "Jobs In Progress" table below

#### Panel 3: Failed (Last Hour)
- **What it shows:** Count of jobs that failed in the last hour
- **Thresholds:**
  - Green: 0 failures
  - Red: 1+ failures (needs attention)
- **Refresh:** 10 seconds
- **Action needed if red:** Check "Failed Jobs" table for error details

#### Panel 4: Success Rate (Today)
- **What it shows:** Percentage of successful enrichments today
- **Thresholds:**
  - Red: <70% (critical)
  - Yellow: 70-89% (needs improvement)
  - Green: 90%+ (healthy)
- **Refresh:** 10 seconds
- **Action needed if red/yellow:** Review failed jobs and agent configuration

#### Panel 5: Avg Duration (Last Hour)
- **What it shows:** Average time (in minutes) for successful enrichments
- **Thresholds:**
  - Green: <3 minutes (fast)
  - Yellow: 3-5 minutes (normal)
  - Red: 5+ minutes (slow)
- **Refresh:** 10 seconds
- **Action needed if red:** Check for rate limiting or API slowdowns

### Row 2: Executive Slots Status

#### Panel 6: Executive Slots Pending Enrichment (Left)
- **What it shows:** Table of CFO/CEO/HR slots that need enrichment
- **Columns:**
  - **Company:** Company name
  - **Role:** CEO, CFO, or HR
  - **Is Filled:** true/false (is someone assigned to this slot?)
  - **Filled Date:** When the slot was filled
  - **Last Refreshed:** When data was last updated
  - **Freshness Status:**
    - **Never Enriched** (red) - Urgent, never been enriched
    - **Stale (7+ days)** (orange) - Very old data
    - **Needs Refresh (3+ days)** (yellow) - Moderately old data
    - **Recent** (green) - Fresh data
  - **Days Since Last Refresh:** How many days since last update
  - **Executive Name:** Name of the person in this slot
  - **LinkedIn URL:** Their LinkedIn profile
  - **Company ID:** Unique identifier
- **Refresh:** 30 seconds
- **How to use:**
  - Focus on rows with "Never Enriched" status first
  - Then prioritize "Stale (7+ days)" entries
  - Click LinkedIn URLs to verify data quality
  - Use Company ID to trigger manual enrichment if needed

#### Panel 7: Enrichment Jobs In Progress (Right)
- **What it shows:** Table of currently running enrichment jobs
- **Columns:**
  - **Company:** Company being enriched
  - **Agent:** Which agent is doing the work (Apify, Abacus, Firecrawl, etc.)
  - **Type:** executive, linkedin, or profile
  - **Status:** pending or running
  - **Started:** When the job started
  - **Minutes Running:** Duration in minutes
  - **Performance:**
    - **✅ Fast** (green) - <5 minutes
    - **⚡ Normal** (blue) - 5-10 minutes
    - **⚠️ Slow** (orange) - 10+ minutes (may be stuck)
  - **Job ID:** Unique identifier
- **Refresh:** 10 seconds
- **How to use:**
  - Watch for jobs stuck in "⚠️ Slow" status
  - If a job is running >15 minutes, it may be hung
  - Note which agents are consistently fast vs slow

### Row 3: Failed Jobs

#### Panel 8: Failed Enrichment Jobs (Last 24 Hours)
- **What it shows:** Table of all failed enrichments in the last day
- **Columns:**
  - **Company:** Company where enrichment failed
  - **Agent:** Which agent failed
  - **Type:** executive, linkedin, or profile
  - **Status:** failed, timeout, or rate_limited (color-coded red/orange/yellow)
  - **Error:** Error message from the failure
  - **Attempted At:** When the failure occurred
  - **Hours Ago:** How long ago
  - **Credits Wasted:** How many API credits were consumed
  - **Job ID:** Unique identifier
  - **Company ID:** Company identifier for retry
- **Refresh:** 1 minute
- **How to use:**
  - Look for patterns in error messages
  - Check if specific agents are failing more often
  - Use Job ID to investigate logs
  - Use Company ID to manually retry enrichment
  - Monitor credits wasted to track API costs

### Row 4: Performance Analysis

#### Panel 9: Agent Performance (Last 7 Days) - Bar Chart (Left)
- **What it shows:** Success rates and metrics for each agent over 7 days
- **Columns:**
  - **Agent:** Agent name (Apify, Abacus, Firecrawl, etc.)
  - **Total Jobs:** Total enrichments attempted
  - **Successful:** Number of successes
  - **Failed:** Number of failures
  - **Timeouts:** Number of timeouts
  - **Success Rate %:** Percentage successful
  - **Avg Duration (min):** Average time per successful job
  - **Total Credits:** Total API credits consumed
  - **Credits Per Success:** Cost per successful enrichment
  - **Last Used:** Most recent usage
- **Refresh:** 5 minutes
- **How to use:**
  - Compare success rates across agents
  - Identify which agents are most reliable
  - Monitor cost efficiency (credits per success)
  - Consider switching agents if one is consistently underperforming

#### Panel 10: Executive Enrichment Timeline (Last 24 Hours) - Time Series (Right)
- **What it shows:** Hourly breakdown of enrichment activity
- **Lines:**
  - **Total Jobs** (gray) - All enrichments
  - **Successful** (green) - Successful enrichments
  - **Failed** (red) - Failed enrichments
  - **Running** (blue) - Currently running
  - **Success Rate %** (overlaid)
- **Refresh:** 1 minute
- **How to use:**
  - Identify peak enrichment hours
  - Spot sudden drops in success rate
  - Detect if failures correlate with certain times of day
  - See if rate limiting occurs during busy periods

## 🚨 Alert Conditions

### Critical (Immediate Action Required)
- **Success Rate Today < 70%**
  - Action: Check "Failed Jobs" panel, review agent logs
- **Failed Jobs > 10 in last hour**
  - Action: Check for systemic issues (API downtime, rate limiting)
- **Running Jobs > 10**
  - Action: Check for stuck jobs, may need to restart agents
- **Job running > 15 minutes**
  - Action: Job likely stuck, consider canceling and retrying

### Warning (Monitor Closely)
- **Pending Jobs > 20**
  - Action: Agents may be overloaded, consider scaling
- **Success Rate Today 70-89%**
  - Action: Review failed job patterns
- **Avg Duration > 5 minutes**
  - Action: Check for API slowdowns or rate limiting

### Info (Normal Operation)
- **Pending Jobs < 5**
- **Success Rate > 90%**
- **Avg Duration < 3 minutes**

## 🔧 Common Actions

### Action 1: Investigate Failed Job
1. Find job in "Failed Enrichment Jobs" panel
2. Note the **Error** message
3. Note the **Agent** that failed
4. Copy the **Job ID**
5. Check agent logs: `grep <Job ID> /var/log/enrichment-agent.log`
6. Retry manually if needed using **Company ID**

### Action 2: Manually Trigger Enrichment
1. Find company in "Executive Slots Pending Enrichment"
2. Copy the **Company ID**
3. Run manual enrichment:
   ```bash
   curl -X POST http://localhost:8000/api/v1/enrichment/trigger \
     -H "Content-Type: application/json" \
     -d '{"company_unique_id": "<Company ID>", "slot_type": "CEO"}'
   ```

### Action 3: Check Stuck Job
1. Find job in "Jobs In Progress" with "⚠️ Slow" status
2. Note the **Job ID**
3. Check job status in database:
   ```sql
   SELECT * FROM marketing.data_enrichment_log
   WHERE enrichment_id = '<Job ID>';
   ```
4. Cancel if truly stuck:
   ```bash
   curl -X POST http://localhost:8000/api/v1/enrichment/cancel/<Job ID>
   ```

### Action 4: Review Agent Performance
1. Look at "Agent Performance" bar chart
2. Identify agent with lowest success rate
3. Check if failures are due to:
   - Rate limiting (switch API tier or add delays)
   - Timeouts (increase timeout threshold)
   - Bad credentials (refresh API keys)
4. Consider disabling underperforming agent temporarily

## 📊 Expected Metrics (Healthy System)

| Metric | Healthy Range | Warning Range | Critical Range |
|--------|---------------|---------------|----------------|
| Success Rate | 90-100% | 70-89% | <70% |
| Avg Duration | <3 min | 3-5 min | >5 min |
| Pending Jobs | 0-5 | 5-20 | >20 |
| Running Jobs | 0-3 | 3-10 | >10 |
| Failed (last hour) | 0 | 1-5 | >5 |

## 🔄 Refresh Intervals

All panels have automatic refresh intervals:
- **10 seconds:** Real-time metrics, in-progress jobs
- **30 seconds:** Pending enrichment slots
- **1 minute:** Failed jobs, timeline chart
- **5 minutes:** Agent performance (less volatile)

You can force a refresh by clicking the refresh icon in the top right of the dashboard.

## 🎨 Color Coding

### Freshness Status (Panel 6)
- 🔴 **Dark Red:** Never Enriched (urgent)
- 🟠 **Dark Orange:** Stale 7+ days (high priority)
- 🟡 **Dark Yellow:** Needs refresh 3+ days (medium priority)
- 🟢 **Dark Green:** Recent (good)

### Performance Status (Panel 7)
- 🟢 **Green:** Fast (<5 min)
- 🔵 **Blue:** Normal (5-10 min)
- 🟠 **Orange:** Slow (>10 min)

### Job Status (Panel 8)
- 🔴 **Red:** Failed
- 🟠 **Orange:** Timeout
- 🟡 **Yellow:** Rate Limited

## 📝 Usage Tips

1. **Daily Morning Check:**
   - Review "Pending Jobs" count
   - Check "Success Rate (Today)" - should be building toward 90%+
   - Scan "Failed Jobs" for any critical errors

2. **During Business Hours:**
   - Monitor "Running Jobs" count
   - Watch for stuck jobs (>10 min duration)
   - Review "Timeline" for unusual patterns

3. **End of Day Review:**
   - Check "Agent Performance" to identify trends
   - Review total enrichments completed
   - Plan manual retries for any failed companies

4. **Weekly Analysis:**
   - Compare agent success rates over 7 days
   - Review cost efficiency (credits per success)
   - Adjust agent priorities based on performance

## 🔗 Related Queries

All SQL queries used in this dashboard are documented in:
`infra/docs/ENRICHMENT_TRACKING_QUERIES.sql`

You can copy these queries to:
- Create custom panels
- Run ad-hoc analysis in a SQL client
- Export data for reporting

## 🆘 Troubleshooting

### Dashboard Not Loading
1. Verify Grafana is running: `docker ps | grep grafana`
2. Check datasource connection: Settings → Data Sources → Neon PostgreSQL
3. Test datasource with "Save & Test" button

### No Data Showing
1. Verify tables exist:
   ```sql
   SELECT COUNT(*) FROM marketing.data_enrichment_log;
   SELECT COUNT(*) FROM marketing.company_slot;
   ```
2. Check if enrichment agents are running
3. Verify time range picker (top right) covers recent data

### Queries Timing Out
1. Check database connection in Neon console
2. Verify indexes exist on key columns:
   - `data_enrichment_log.status`
   - `data_enrichment_log.enrichment_type`
   - `data_enrichment_log.created_at`
   - `company_slot.slot_type`
   - `company_slot.last_refreshed_at`

### Panels Showing Errors
1. Click panel title → Edit
2. Check query syntax in Query tab
3. Verify table/column names match your schema
4. Test query directly in Neon console

## 🚀 Next Steps

Once Grafana is restarted and running:

1. **Access the dashboard:**
   - Go to http://localhost:3000
   - No login required (authentication disabled)
   - Click "Dashboards" in left menu
   - Click "Executive Enrichment Monitoring"

2. **Customize as needed:**
   - Add more panels for specific agents
   - Create alerts for critical conditions
   - Adjust refresh intervals
   - Add annotations for important events

3. **Set up alerts (optional):**
   - Configure Grafana alerting for critical thresholds
   - Send notifications to Slack/Email when success rate drops
   - Alert when jobs are stuck >15 minutes

---

**Dashboard UID:** `executive-enrichment-monitoring`
**Created:** 2025-11-06
**Last Updated:** 2025-11-06
**Refresh:** 30 seconds (configurable)
