# Builder.io Data Binding Guide
## Connect Live API Data to Your Components

---

## 📊 Available API Endpoints

Your FastAPI backend provides these endpoints for live data:

| Endpoint | Method | Returns | Use Case |
|----------|--------|---------|----------|
| `/api/neon/v_phase_stats` | GET | Phase statistics | PhaseCard component |
| `/api/neon/v_error_recent` | GET | Recent errors | ErrorConsole (auto) |
| `/api/neon/company_master` | GET | Company list | Custom displays |
| `/api/n8n/errors` | GET | n8n workflow errors | ErrorConsole (auto) |
| `/api/n8n/executions` | GET | n8n execution history | Custom displays |
| `/api/apify/actors` | GET | Apify actor list | PhaseDetail |

**Base URL:** `http://localhost:8000`

---

## 🎯 Quick Start: Bind Data to PhaseCard

### Step 1: Create a Builder.io Page

1. Go to https://builder.io/content
2. Click **+ New** → **Page**
3. Set URL to: `/builder` or `/dashboard`
4. Click **Create**

### Step 2: Add Data Source

In the Builder.io editor:

1. Click **Data** tab (left sidebar)
2. Click **+ Add Data**
3. Select **Custom Code**
4. Paste this code:

```javascript
async function fetchPhaseStats() {
  try {
    const response = await fetch('http://localhost:8000/api/neon/v_phase_stats');
    if (!response.ok) throw new Error('API request failed');

    const result = await response.json();

    // Group stats by phase
    const grouped = {};
    result.data.forEach(stat => {
      if (!grouped[stat.phase]) {
        grouped[stat.phase] = [];
      }
      grouped[stat.phase].push(stat);
    });

    return {
      phases: Object.keys(grouped),
      groupedStats: grouped,
      allStats: result.data,
      totalCompanies: result.data.reduce((sum, s) => sum + s.count, 0)
    };
  } catch (error) {
    console.error('Failed to fetch phase stats:', error);
    return {
      phases: [],
      groupedStats: {},
      allStats: [],
      totalCompanies: 0
    };
  }
}

return await fetchPhaseStats();
```

### Step 3: Add PhaseCard Component

1. Click **+ Insert**
2. Scroll to **Custom Components**
3. Drag **PhaseCard** onto canvas
4. In the right panel, set props:
   - **phase**: Type a phase name (e.g., "Company Discovery")
   - **stats**: Click **Bind Data** → `state.groupedStats['Company Discovery']`

### Step 4: Add Multiple Phase Cards

Repeat for each phase:
- "Company Discovery" → `state.groupedStats['Company Discovery']`
- "People Enrichment" → `state.groupedStats['People Enrichment']`
- "Email Validation" → `state.groupedStats['Email Validation']`

### Step 5: Publish

Click **Publish** and visit `http://localhost:5174/builder`

---

## 📖 Example: Complete Dashboard Setup

### Full Data Binding Code

```javascript
// Fetch all data needed for dashboard
async function fetchDashboardData() {
  const API_BASE = 'http://localhost:8000';

  try {
    // Fetch phase stats
    const phaseResponse = await fetch(`${API_BASE}/api/neon/v_phase_stats`);
    const phaseData = await phaseResponse.json();

    // Fetch companies
    const companyResponse = await fetch(`${API_BASE}/api/neon/company_master?limit=50`);
    const companyData = await companyResponse.json();

    // Group stats by phase
    const grouped = {};
    phaseData.data.forEach(stat => {
      if (!grouped[stat.phase]) grouped[stat.phase] = [];
      grouped[stat.phase].push(stat);
    });

    return {
      // For PhaseCard
      phases: Object.keys(grouped),
      groupedStats: grouped,

      // For total count displays
      totalCompanies: phaseData.data.reduce((sum, s) => sum + s.count, 0),

      // For company tables
      companies: companyData.data || [],

      // Raw data
      rawStats: phaseData.data
    };
  } catch (error) {
    console.error('Dashboard data fetch failed:', error);
    return {
      phases: [],
      groupedStats: {},
      totalCompanies: 0,
      companies: [],
      rawStats: []
    };
  }
}

return await fetchDashboardData();
```

---

## 🎨 Component-Specific Binding

### PhaseCard

**Expected Props:**
```typescript
{
  phase: string,
  stats: Array<{
    status: 'completed' | 'processing' | 'pending' | 'failed',
    count: number,
    last_updated: string
  }>
}
```

**Data Binding:**
```javascript
// In Builder Data tab
async function getPhaseData() {
  const res = await fetch('http://localhost:8000/api/neon/v_phase_stats');
  const data = await res.json();

  // Group by phase
  const grouped = data.data.reduce((acc, stat) => {
    if (!acc[stat.phase]) acc[stat.phase] = [];
    acc[stat.phase].push(stat);
    return acc;
  }, {});

  return { phaseStats: grouped };
}

return await getPhaseData();
```

**In Component Props:**
- phase: `"Company Discovery"` (hardcoded string)
- stats: `state.phaseStats['Company Discovery']` (bound to data)

---

### PhaseDetail

**Expected Props:**
```typescript
{
  phase: string,
  stats: Array<{...}>,  // same as PhaseCard
  apifyActorId?: string
}
```

**Data Binding:** Same as PhaseCard

**In Component Props:**
- phase: `"People Enrichment"`
- stats: `state.phaseStats['People Enrichment']`
- apifyActorId: `"apify/web-scraper"` (optional)

---

### ErrorConsole

**No props needed** - Fetches data automatically from:
- `/api/neon/v_error_recent`
- `/api/n8n/errors`

Just drag onto canvas and it works!

---

### AccordionItem

**Expected Props:**
```typescript
{
  title: string,
  defaultOpen?: boolean,
  badge?: string | number,
  children: ReactNode
}
```

**Example Usage:**
1. Drag AccordionItem onto canvas
2. Set title: `"Phase Overview"`
3. Set badge: `state.totalCompanies` (from data binding)
4. Drag PhaseCard inside as children

---

## 🔄 Dynamic Phase List

To create cards dynamically for all phases:

### Option 1: Manual (Recommended for Builder.io)

Create separate PhaseCard for each known phase:
- Company Discovery
- People Enrichment
- Email Validation

### Option 2: Repeater Pattern

Use Builder's **Repeat** feature:

1. Add PhaseCard
2. Click **Repeat** in options panel
3. Set collection: `state.phases`
4. Bind props:
   - phase: `item` (current phase name)
   - stats: `state.groupedStats[item]`

---

## 🧪 Testing Data Binding

### Test 1: Check Data in Console

In Builder editor, open browser console:

```javascript
// Check if data loaded
console.log('Builder state:', builderState);

// Should see:
// {
//   phases: ['company_validated'],
//   groupedStats: { company_validated: [...] },
//   totalCompanies: 1
// }
```

### Test 2: Verify API Response

Test endpoint directly:
```bash
curl http://localhost:8000/api/neon/v_phase_stats
```

Expected response:
```json
{
  "success": true,
  "data": [
    {
      "phase": "company_validated",
      "status": "pending",
      "count": 1,
      "last_updated": "2025-10-24T18:15:56.339798"
    }
  ],
  "count": 1,
  "timestamp": "2025-10-26T..."
}
```

### Test 3: Check CORS

If you see CORS errors in console:

1. Backend (`src/main.py`) should have:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # For development
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. Restart backend: `python start_server.py`

---

## 🚨 Troubleshooting

### Issue: "Failed to fetch"

**Solution:**
1. Check backend is running: `http://localhost:8000/health`
2. Check CORS is enabled
3. Use correct base URL in fetch

### Issue: "undefined is not an object"

**Solution:**
1. Check data structure matches expected format
2. Add fallbacks:
   ```javascript
   stats: state.groupedStats?.['Company Discovery'] || []
   ```

### Issue: "No data showing"

**Solution:**
1. Check Data tab has code
2. Click **Preview** to refresh data
3. Check browser console for errors

---

## 📚 Advanced Examples

### Example 1: Total Count Header

Add a **Text** block with:
```
Total Companies: {{state.totalCompanies}}
```

### Example 2: Company List Table

Data binding:
```javascript
async function getCompanies() {
  const res = await fetch('http://localhost:8000/api/neon/company_master?limit=10');
  const data = await res.json();
  return { companies: data.data };
}
return await getCompanies();
```

Then use Builder's Table component with `state.companies`

### Example 3: Live Error Count

Data binding:
```javascript
async function getErrorCount() {
  const res = await fetch('http://localhost:8000/api/neon/v_error_recent');
  const data = await res.json();
  return { errorCount: data.count };
}
return await getErrorCount();
```

Display: `{{state.errorCount}} Errors`

---

## ✅ Checklist

Before publishing your Builder page:

- [ ] Data tab has fetch code
- [ ] Fetch URL is correct (`http://localhost:8000/...`)
- [ ] Return shape matches component expectations
- [ ] Props are bound to `state.xxx`
- [ ] Backend is running
- [ ] CORS is enabled
- [ ] Preview shows live data
- [ ] Console has no errors

---

## 🎯 Quick Reference

| Component | Data Needed | Bind To |
|-----------|-------------|---------|
| PhaseCard | `stats: [{status, count, last_updated}]` | `state.groupedStats['PhaseName']` |
| PhaseDetail | Same as PhaseCard + `apifyActorId` | `state.groupedStats['PhaseName']` |
| ErrorConsole | None (auto-fetches) | - |
| AccordionItem | `badge: string/number` | `state.totalCompanies` |

---

**Backend Status:** http://localhost:8000/health
**Frontend:** http://localhost:5174
**Builder.io:** https://builder.io/content

**Happy Data Binding!** 📊
