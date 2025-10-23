<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-B7A730AE
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
-->

# Composio user_id Migration Checklist

**Date Created**: 2025-10-21
**Deadline**: November 1st, 2025
**Status**: ⚠️ **URGENT ACTION REQUIRED**

---

## Overview

Composio is requiring all MCP Server URLs to include a `user_id` query parameter starting November 1st, 2025. Without this update, all Composio integrations will fail.

## Documentation Updates Completed ✅

- [x] Updated `imo-creator-latest/COMPOSIO_INTEGRATION.md`
- [x] Updated `imo-creator/COMPOSIO_INTEGRATION.md`
- [x] Updated `barton-outreach-core/COMPOSIO_INTEGRATION.md`

---

## Action Items

### Step 1: Generate user_id (PRIORITY 1)

- [ ] Go to [Composio Platform](https://app.composio.dev)
- [ ] Login with your account
- [ ] Navigate to **Settings** → **MCP Servers**
- [ ] Generate MCP Server URL with `user_id`
- [ ] Save the generated `user_id` (format: `usr_XXXXXXXXX`)

**Alternative via API**:
```bash
curl -X POST https://backend.composio.dev/api/v2/cli/generate-mcp-url \
  -H "X-API-Key: YOUR_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "david_barton_primary"
  }'
```

**Expected Response**:
```json
{
  "mcp_server_url": "http://localhost:3001/tool?user_id=usr_XXXXXXXXX",
  "user_id": "usr_XXXXXXXXX",
  "expires_at": null
}
```

---

### Step 2: Update Environment Variables

#### barton-outreach-core repo
- [ ] Open `.env` file
- [ ] Add/Update:
```bash
COMPOSIO_USER_ID=usr_XXXXXXXXX
COMPOSIO_MCP_URL=http://localhost:3001/tool?user_id=usr_XXXXXXXXX
```

#### imo-creator repo
- [ ] Open `.env` file
- [ ] Add/Update:
```bash
COMPOSIO_USER_ID=usr_XXXXXXXXX
COMPOSIO_MCP_URL=http://localhost:3001/tool?user_id=usr_XXXXXXXXX
```

#### imo-creator-latest repo
- [ ] Open `.env` file
- [ ] Add/Update:
```bash
COMPOSIO_USER_ID=usr_XXXXXXXXX
COMPOSIO_MCP_URL=http://localhost:3001/tool?user_id=usr_XXXXXXXXX
```

---

### Step 3: Update Code References

Search for all hardcoded MCP Server URLs and update them:

#### Search Pattern
```bash
# Find all files with old MCP Server URL
grep -r "localhost:3001/tool" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx"
```

#### Files to Check (Examples)

**barton-outreach-core**:
- [ ] `apps/outreach-process-manager/services/enrichmentRouter.js`
- [ ] `apps/outreach-process-manager/services/apifyHandler.js`
- [ ] `agents/specialists/apifyRunner.js`
- [ ] Any API route files in `apps/api/`

**imo-creator**:
- [ ] `src/server/main.py` (FastAPI)
- [ ] `mcp-servers/composio-mcp/server.js`
- [ ] Any integration files

#### Code Update Pattern

**OLD**:
```javascript
const response = await fetch('http://localhost:3001/tool', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});
```

**NEW**:
```javascript
const COMPOSIO_USER_ID = process.env.COMPOSIO_USER_ID;
const COMPOSIO_MCP_URL = `http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}`;

const response = await fetch(COMPOSIO_MCP_URL, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});
```

---

### Step 4: Test Integrations

#### Test Composio Connection
```bash
# Set user_id first
export COMPOSIO_USER_ID=usr_XXXXXXXXX

# Test connection
curl -X POST "http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_composio_stats",
    "data": {},
    "unique_id": "HEIR-2025-10-TEST-01",
    "process_id": "PRC-TEST-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

**Expected Success Response**:
```json
{
  "success": true,
  "connected_accounts": [...],
  "available_services": [...]
}
```

#### Test Gmail Integration
```bash
curl -X POST "http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "manage_connected_account",
    "data": {"action": "list", "app": "GMAIL"},
    "unique_id": "HEIR-2025-10-GMAIL-01",
    "process_id": "PRC-GMAIL-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

#### Test Apify Integration
```bash
curl -X POST "http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "manage_connected_account",
    "data": {"action": "list", "app": "APIFY"},
    "unique_id": "HEIR-2025-10-APIFY-01",
    "process_id": "PRC-APIFY-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

---

### Step 5: Update MCP Server Configuration

If running a custom Composio MCP server:

- [ ] Update `mcp-servers/composio-mcp/server.js`
- [ ] Add user_id validation middleware
- [ ] Log user_id for audit trail

**Example Middleware**:
```javascript
// Add to server.js
app.use((req, res, next) => {
  const userId = req.query.user_id;

  if (!userId) {
    return res.status(400).json({
      error: 'user_id query parameter is required as of November 1st, 2025'
    });
  }

  // Attach user_id to request for logging
  req.composio_user_id = userId;
  next();
});
```

---

### Step 6: Verify All Repos

Check each repository for Composio usage:

#### barton-outreach-core
- [ ] All enrichment scripts use new URL
- [ ] Apify integration uses new URL
- [ ] Executive enrichment trial script updated
- [ ] Test with `node analysis/run_enrichment_trial.js` (when created)

#### imo-creator
- [ ] FastAPI endpoints updated
- [ ] Gmail integration tests pass
- [ ] Google Drive integration tests pass
- [ ] Vercel deployment integration works

#### imo-creator-latest
- [ ] All same checks as imo-creator
- [ ] Verify no regressions

---

## Deadline Tracking

| Task | Deadline | Status |
|------|----------|--------|
| Generate user_id | Oct 25, 2025 | ⏳ Pending |
| Update .env files | Oct 26, 2025 | ⏳ Pending |
| Update code references | Oct 28, 2025 | ⏳ Pending |
| Test all integrations | Oct 29, 2025 | ⏳ Pending |
| Final verification | Oct 30, 2025 | ⏳ Pending |
| **HARD DEADLINE** | **Nov 1, 2025** | ⚠️ **DO NOT MISS** |

---

## Affected Integrations

### Confirmed Using Composio
- ✅ Gmail (3 accounts)
- ✅ Google Drive (3 accounts)
- ✅ Google Calendar (1 account)
- ✅ Google Sheets (1 account)
- ✅ Apify (executive enrichment)
- ✅ Vercel (deployments)
- ✅ Million Verifier (email validation)

### May Be Affected
- ⚠️ GitHub (if using Composio)
- ⚠️ OpenAI (if using Composio)
- ⚠️ Anthropic (if using Composio)
- ⚠️ Any other MCP-connected services

---

## Rollback Plan (If Issues Arise)

If the migration causes problems before November 1st:

1. **Keep old URL working**: Composio supports both formats until Nov 1st
2. **Test in parallel**: Use new URL in staging, old URL in production
3. **Monitor logs**: Watch for user_id validation errors
4. **Contact support**: support@composio.dev

After November 1st, there is NO rollback - old URLs will fail.

---

## Support Resources

- 📖 [User Management Docs](https://docs.composio.dev/patterns/user-management)
- 🔧 [MCP URL Generation API](https://docs.composio.dev/api-reference/mcp/generate-url)
- 📧 [Composio Support](mailto:support@composio.dev)
- 💬 [Composio Discord](https://discord.gg/composio) (if available)

---

## Notes & Questions

### Questions to Answer
1. Do we need separate user_ids for different environments (dev/staging/prod)?
2. Should we create user_ids for different team members?
3. Do we need to update CI/CD pipelines with new URLs?

### Notes
- Add any migration issues or learnings here
- Document any unexpected behavior
- Track which integrations were tested and confirmed working

---

**Status**: Documentation updated ✅, Code migration pending ⏳

**Next Action**: Generate user_id from Composio Platform (Step 1)
