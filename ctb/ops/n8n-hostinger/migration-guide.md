## N8N Migration Guide: Cloud → Hostinger VPS

**Goal:** Migrate all workflows and credentials from n8n cloud to self-hosted instance

**Timeline:** 2-3 hours total

---

## Phase 1: Export from Cloud N8N (30 minutes)

### 1.1 Export All Workflows

1. Login to cloud n8n: https://dbarton.app.n8n.cloud
2. Go to **Workflows** (left sidebar)
3. Click **...** (three dots) → **Export**
4. Select **All workflows**
5. Download as JSON file → save as `n8n-cloud-workflows-export.json`

**OR export individual workflows:**
```bash
# For each workflow
Workflow → ... → Export → Download JSON
```

### 1.2 Export Credentials

⚠️ **IMPORTANT:** Credentials are **encrypted** and cannot be exported directly!

**Option A: Document manually**
1. Go to **Credentials** (left sidebar)
2. For each credential, note down:
   - Credential type (e.g., Gmail OAuth2, HTTP Header Auth)
   - Name
   - Configuration values
3. You'll need to **recreate** these in self-hosted n8n

**Option B: Use n8n API (if available)**
```bash
# Get all credentials (names only, not values)
curl https://dbarton.app.n8n.cloud/api/v1/credentials \
  -H "X-N8N-API-KEY: YOUR_API_KEY"
```

### 1.3 Export Active Executions (if needed)

1. Go to **Executions** (left sidebar)
2. Click **...** → **Export**
3. Select date range
4. Download CSV for audit trail

---

## Phase 2: Prepare Self-Hosted N8N (1 hour)

### 2.1 Ensure n8n is Running

```bash
# SSH into Hostinger VPS
ssh root@YOUR_VPS_IP

# Check n8n status
cd /opt/n8n
docker-compose ps

# View logs
docker-compose logs -f n8n
```

### 2.2 Access Self-Hosted n8n

1. Open browser: `https://n8n.svgagency.com` (or your domain)
2. Login with Basic Auth credentials from `.env`
3. Complete initial setup wizard (if first time)

### 2.3 Verify Database Connection

1. Go to **Settings** → **About**
2. Verify database type shows: **PostgreSQL**
3. Verify connected to: **Neon**

---

## Phase 3: Import Workflows (1 hour)

### 3.1 Import All Workflows

**Method 1: Bulk Import (Recommended)**

1. In self-hosted n8n, go to **Workflows**
2. Click **Import from file**
3. Select `n8n-cloud-workflows-export.json`
4. n8n will import all workflows

**Method 2: Individual Import**

For each workflow JSON file:
1. Workflows → **+** (New) → **Import from file**
2. Select workflow JSON
3. Click **Import**

### 3.2 Verify Workflows

After import, check each workflow:

1. Open workflow
2. Check for **missing credentials** (yellow warning icon)
3. Check for **missing nodes** (red error icon)
4. Verify connections between nodes

### 3.3 Fix Missing Credentials

For each workflow with credential warnings:

1. Click the node with warning
2. Select **Create New Credential**
3. Re-enter credential values (refer to Phase 1.2 notes)
4. Save

**Common Credentials to Recreate:**
- Google OAuth2 (for Gmail, Sheets, Drive)
- HTTP Header Auth (for custom APIs)
- PostgreSQL (for Neon database)
- n8n API credentials (if workflows call other n8n instances)

---

## Phase 4: Update Webhook URLs (30 minutes)

⚠️ **CRITICAL:** Webhook URLs change from cloud to self-hosted!

### 4.1 Identify Workflows with Webhooks

In self-hosted n8n:
1. Open each workflow
2. Look for **Webhook** nodes
3. Note the webhook trigger URLs

### 4.2 Update External Webhooks

If external services call your workflows:

**Old Cloud URL:**
```
https://dbarton.app.n8n.cloud/webhook/abc123
```

**New Self-Hosted URL:**
```
https://n8n.svgagency.com/webhook/abc123
```

**Update in:**
- GitHub webhooks
- Stripe webhooks
- Zapier/Make integrations
- Custom app webhooks

### 4.3 Update Internal Webhooks

If workflows call each other via webhooks:
1. Find workflows with **HTTP Request** nodes calling n8n webhooks
2. Update URLs:
   - From: `https://dbarton.app.n8n.cloud/webhook/*`
   - To: `https://n8n.svgagency.com/webhook/*`

### 4.4 Test Webhook Delivery

```bash
# Test webhook
curl -X POST https://n8n.svgagency.com/webhook/YOUR_WEBHOOK_ID \
  -H "Content-Type: application/json" \
  -d '{"test": "payload"}'

# Check execution in n8n
# Executions → Recent → Should see test execution
```

---

## Phase 5: Test Critical Workflows (1 hour)

### 5.1 Priority Testing Order

Test in this order:

1. **Simple workflows first** (no credentials, no webhooks)
2. **Workflows with credentials** (test DB connections, API calls)
3. **Workflows with webhooks** (test trigger firing)
4. **Complex multi-node workflows**

### 5.2 Test Each Workflow

For each workflow:

1. Open workflow
2. Click **Execute Workflow** (top right)
3. Verify all nodes execute successfully
4. Check output data looks correct
5. If errors:
   - Check credentials
   - Check node configuration
   - Check webhook URLs
   - View execution logs

### 5.3 Enable Workflows

After testing:
1. Click **Active** toggle (top right)
2. Workflow will now run on schedule/webhook triggers

### 5.4 Critical Workflows to Test

**For PLE System:**
- ✅ Enrichment queue processor trigger
- ✅ Movement detection webhook
- ✅ BIT score calculation
- ✅ Outreach promotion workflow
- ✅ Error notification workflow

---

## Phase 6: Monitor & Validate (Ongoing)

### 6.1 Monitor Executions

Check executions dashboard daily:
```
https://n8n.svgagency.com/executions
```

Look for:
- Failed executions (red)
- Long-running executions (potential timeout)
- Webhook triggers firing correctly

### 6.2 Set Up Alerts

Create workflow for error notifications:

**Trigger:** Workflow error
**Action:** Send email/Slack notification

Example workflow:
```
Error Trigger → Filter (only critical errors) → Send Email
```

### 6.3 Verify Database Persistence

1. Create test workflow
2. Execute it
3. Restart n8n: `docker-compose restart`
4. Verify workflow still exists
5. Verify execution history preserved

---

## Phase 7: Decommission Cloud N8N (After 1 week)

⚠️ **Wait 1 week** to ensure self-hosted is stable!

### 7.1 Final Checks

Before canceling cloud subscription:

- [ ] All workflows migrated and tested
- [ ] All credentials recreated
- [ ] All webhook URLs updated
- [ ] All external integrations working
- [ ] Backups configured and tested
- [ ] No executions running on cloud n8n

### 7.2 Cancel Cloud Subscription

1. Login to n8n cloud
2. Settings → Billing
3. Cancel subscription
4. Download final backup
5. Delete cloud account (optional)

### 7.3 Update Documentation

Update references to n8n URL:
- Internal docs
- Team wikis
- Runbooks
- Integration guides

---

## Troubleshooting

### Issue: Workflows won't import

**Solution:**
- Check JSON file is valid (not corrupted)
- Try importing one workflow at a time
- Check n8n version compatibility (cloud vs self-hosted)

### Issue: Credentials missing after import

**Solution:**
- Credentials are encrypted, cannot be exported
- Must manually recreate all credentials
- Use notes from Phase 1.2

### Issue: Webhooks not firing

**Solution:**
- Check webhook URL is correct
- Verify nginx is forwarding `/webhook` paths
- Check firewall allows port 443
- Test with curl (see Phase 4.4)

### Issue: Database connection fails

**Solution:**
- Verify Neon connection string in `.env`
- Check Neon database is accessible from VPS IP
- Test connection: `docker-compose logs n8n | grep database`

### Issue: SSL certificate error

**Solution:**
```bash
# Renew certificate
sudo certbot renew

# Or obtain new one
sudo certbot --nginx -d n8n.svgagency.com
```

---

## Cost Savings

**Cloud n8n:** $20/month + execution limits
**Self-hosted:** $10-20/month VPS (no execution limits)

**Annual savings:** ~$120-240/year
**Unlimited executions:** Priceless for automation!

---

## Rollback Plan

If self-hosted fails:

1. Re-enable cloud n8n subscription
2. Workflows still exist in cloud (if not deleted)
3. Update webhook URLs back to cloud
4. Resume using cloud n8n

**OR:**

1. Restore from backup:
   ```bash
   bash /opt/n8n/backup.sh
   ```

2. Import workflows from local backup

---

## Success Criteria

✅ All workflows migrated
✅ All workflows executing successfully
✅ All webhooks firing correctly
✅ All credentials recreated
✅ Executions persisting to Neon database
✅ Backups running daily
✅ SSL certificate valid
✅ No errors in logs

---

**Last Updated:** 2025-11-25
**Migration Status:** Ready to execute
**Estimated Downtime:** 0 (parallel migration, switch DNS when ready)
