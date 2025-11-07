# Grafana Dashboard for Barton Outreach Engine

Complete Grafana setup for visualizing your Neon Marketing Database.

## 🚀 Quick Start

### 1. Start Grafana

```bash
docker-compose up -d
```

### 2. Access Grafana

- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

### 3. View Dashboard

The "Barton Outreach Dashboard" is automatically loaded with:
- Total companies, contacts, and tasks
- Slot fill rates by role (CEO/CFO/HR)
- Top companies by contact count
- Resolution queue breakdown

## 📊 Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| Total Companies | `SELECT COUNT(*) FROM marketing.company_master` | Company count |
| Total Contacts | `SELECT COUNT(*) FROM marketing.people_master` | Contact count |
| Pending Tasks | `SELECT COUNT(*) FROM people_resolution_queue WHERE status='pending'` | AI agent queue |
| Filled Slots | Group by role with JOIN | Slot fill visualization |
| Top Companies | Companies ranked by contact count | Enrichment status |
| Queue Breakdown | Issue types and assignments | Agent workload |

## 🔗 Embed in Lovable.dev

### Get Panel URL

1. Open a panel in Grafana
2. Click "Share" → "Link"
3. Toggle "Direct link rendered image"
4. Copy the URL

### Embed in Lovable

```jsx
// In your Lovable.dev component:
<iframe 
  src="http://localhost:3000/d-solo/barton_outreach/barton-outreach-dashboard?orgId=1&panelId=3"
  width="100%"
  height="400"
  frameBorder="0"
></iframe>
```

### Panel IDs

- Panel 1: Total Companies
- Panel 2: Total Contacts  
- Panel 3: Pending Resolution Tasks
- Panel 4: Filled Slots by Role
- Panel 5: Top 20 Companies
- Panel 6: Resolution Queue Breakdown

## 🔧 Customization

### Edit Dashboards

Dashboards are in `grafana/dashboards/` as JSON files. Edit directly or:
1. Edit in Grafana UI
2. Export JSON
3. Save to `grafana/dashboards/`

### Add New Panels

Example SQL queries you can use:

```sql
-- CEO fill rate
SELECT 
  COUNT(CASE WHEN pm.unique_id IS NOT NULL THEN 1 END) as filled,
  COUNT(*) as total
FROM marketing.company_slots cs
LEFT JOIN marketing.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
WHERE cs.slot_type = 'CEO';

-- Recent pipeline events
SELECT 
  event_type,
  COUNT(*) as count,
  MAX(created_at) as last_event
FROM marketing.pipeline_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY event_type;

-- Hot companies (when BIT is active)
SELECT 
  cm.company_name,
  bcs.score,
  bcs.signal_count
FROM marketing.company_master cm
JOIN bit.bit_company_score bcs ON cm.company_unique_id = bcs.company_unique_id
WHERE bcs.score_tier IN ('hot', 'warm')
ORDER BY bcs.score DESC;
```

## 🛠️ Troubleshooting

### Connection Issues

If Grafana can't connect to Neon:
1. Check `grafana/provisioning/datasources/neon.yaml`
2. Verify Neon connection string is correct
3. Ensure SSL mode is set to `require`
4. Check Neon project is not paused

### Dashboard Not Loading

```bash
# Restart Grafana to reload dashboards
docker-compose restart grafana
```

### View Logs

```bash
docker-compose logs -f grafana
```

## 📱 Mobile/Responsive

Grafana dashboards are responsive by default. Use:
- `&kiosk` in URL for fullscreen mode
- `&theme=light` for light theme
- `&refresh=30s` for auto-refresh

## 🎯 Production Deployment

For production (not localhost):

1. Update `docker-compose.yml` environment:
   ```yaml
   - GF_SERVER_ROOT_URL=https://your-domain.com
   - GF_SECURITY_ADMIN_PASSWORD=<strong-password>
   ```

2. Add SSL/TLS proxy (nginx, Caddy, etc.)

3. Restrict anonymous access:
   ```yaml
   - GF_AUTH_ANONYMOUS_ENABLED=false
   ```

---

**Created:** 2025-11-03  
**Neon Database:** Marketing DB (PostgreSQL 17)  
**Auto-refresh:** 30 seconds  
**Dashboard Count:** 1 (expandable)
