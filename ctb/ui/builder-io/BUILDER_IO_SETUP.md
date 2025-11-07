# Builder.io Integration Guide
## Outreach Command Center - Visual Editor Setup

---

## Overview

The Outreach Command Center now supports **Builder.io visual editing**, allowing you to create and edit dashboard layouts with drag-and-drop functionality in the Builder.io cloud editor.

### Features

- ✅ All components registered with Builder.io
- ✅ Live data binding from FastAPI backend
- ✅ Drag-and-drop visual editing
- ✅ Hybrid mode (Builder.io + Default Dashboard)
- ✅ Custom data utilities for API integration

---

## Quick Start

### 1. Get Your Builder.io API Key

1. Go to [builder.io](https://www.builder.io) and create a free account
2. Create a new organization or select an existing one
3. Navigate to **Account** → **Organization** → **API Keys**
4. Copy your **Public API Key**

### 2. Configure Environment Variables

Add your API key to `.env`:

```bash
# In /ui/.env
VITE_BUILDER_PUBLIC_KEY=your_actual_public_key_here
```

### 3. Start the Development Server

```bash
cd ui
npm run dev
```

Your app will run at `http://localhost:5173`

---

## Registered Components

The following components are available in the Builder.io visual editor:

### 1. **AccordionItem**
Expandable accordion section with toggle functionality.

**Props:**
- `title` (string, required) - Section title
- `defaultOpen` (boolean) - Whether accordion starts open
- `badge` (string/number) - Optional badge text
- `children` (blocks) - Nested content

**Example Use Case:** Organize dashboard sections

---

### 2. **PhaseCard**
Display summary metrics for a pipeline phase.

**Props:**
- `phase` (string, required) - Phase name (e.g., "Company Discovery")
- `stats` (array) - Array of status objects:
  ```typescript
  {
    status: 'completed' | 'processing' | 'pending' | 'failed',
    count: number,
    last_updated: string (ISO date)
  }
  ```

**Example Use Case:** Show overview of companies in each phase

---

### 3. **PhaseDetail**
Detailed phase view with Apify actor integration.

**Props:**
- `phase` (string, required) - Phase name
- `stats` (array) - Status breakdown (same as PhaseCard)
- `apifyActorId` (string, optional) - Apify actor to run

**Example Use Case:** Detailed drill-down for a specific phase

---

### 4. **ErrorConsole**
Display recent errors from Neon database and n8n workflows.

**Props:** None (fetches data automatically)

**Example Use Case:** Monitor system errors in real-time

---

## Creating Your First Builder.io Page

### Step 1: Create a Page Model

1. Go to [builder.io/models](https://builder.io/models)
2. Click **+ New** → **Page**
3. Name it "Outreach Dashboard"
4. Set URL pattern: `/builder` (or any custom path)

### Step 2: Add Components

1. Open the visual editor
2. Drag components from the **Custom Components** section:
   - AccordionItem
   - PhaseCard
   - PhaseDetail
   - ErrorConsole

### Step 3: Bind Live Data

#### Option A: Use Component Props (Static)

For `PhaseCard`, set props manually in the Builder UI:
```json
{
  "phase": "Company Discovery",
  "stats": [
    { "status": "completed", "count": 10, "last_updated": "2025-10-26T12:00:00Z" },
    { "status": "pending", "count": 5, "last_updated": "2025-10-26T12:00:00Z" }
  ]
}
```

#### Option B: Use Data Tab (Dynamic)

1. Click **Data** in the Builder sidebar
2. Add a **Custom Code** data source:

```javascript
async function fetchData() {
  const response = await fetch('http://localhost:8000/api/neon/v_phase_stats');
  const result = await response.json();

  return {
    phaseStats: result.data || []
  };
}

return await fetchData();
```

3. Bind to components via `state.phaseStats`

#### Option C: Use Global Data Utilities

The app exposes `window.builderData` with helper functions:

```javascript
// In Builder.io custom code
async function loadDashboardData() {
  const data = await window.builderData.fetchOutreachData();
  return data;
}

return await loadDashboardData();
```

### Step 4: Publish

Click **Publish** in Builder.io, then visit `http://localhost:5173/builder`

---

## Hybrid Mode Explained

The app supports **two modes**:

### Default Dashboard Mode
- URL: `http://localhost:5173/`
- Uses: Original accordion dashboard (`AppDefault.tsx`)
- When: No Builder.io content found for route

### Builder.io Mode
- URL: Any route with Builder.io content (e.g., `/builder`)
- Uses: `BuilderPage.tsx` with visual editor content
- When: Builder.io content exists for URL path

### Force Builder Mode
Add `?builder=true` to any URL:
```
http://localhost:5173/?builder=true
```

---

## Advanced: API Data Integration

### Fetching Phase Stats

Create a data binding in Builder.io:

```javascript
// Data Tab → Custom Code
async function getPhaseStats() {
  try {
    const res = await fetch('http://localhost:8000/api/neon/v_phase_stats');
    const data = await res.json();

    // Group by phase
    const grouped = {};
    data.data.forEach(stat => {
      if (!grouped[stat.phase]) grouped[stat.phase] = [];
      grouped[stat.phase].push(stat);
    });

    return { phases: Object.keys(grouped), stats: grouped };
  } catch (error) {
    console.error('Failed to fetch phase stats:', error);
    return { phases: [], stats: {} };
  }
}

return await getPhaseStats();
```

Then bind to components:
- PhaseCard: `state.stats[phaseName]`
- Total count: `state.phases.length`

### Fetching Company Master

```javascript
async function getCompanies() {
  const res = await fetch('http://localhost:8000/api/neon/company_master?limit=10');
  const data = await res.json();
  return { companies: data.data };
}

return await getCompanies();
```

### Fetching n8n Errors

```javascript
async function getN8nErrors() {
  const res = await fetch('http://localhost:8000/api/n8n/errors');
  const data = await res.json();
  return { errors: data.data };
}

return await getN8nErrors();
```

---

## File Structure

```
ui/
├── src/
│   ├── builder.config.ts        # Builder.io configuration & component registration
│   ├── main.tsx                 # Initializes Builder.io SDK
│   ├── App.tsx                  # Hybrid router (Builder + Default)
│   ├── AppDefault.tsx           # Original dashboard
│   ├── pages/
│   │   └── BuilderPage.tsx      # Builder.io content renderer
│   ├── components/              # All components (registered with Builder)
│   │   ├── AccordionItem.tsx
│   │   ├── PhaseCard.tsx
│   │   ├── PhaseDetail.tsx
│   │   └── ErrorConsole.tsx
│   ├── services/                # API client layer
│   │   ├── neon.ts
│   │   ├── n8n.ts
│   │   └── apify.ts
│   └── utils/
│       └── builderData.ts       # Helper functions for Builder.io data
├── .env                         # Environment variables (API keys)
└── BUILDER_IO_SETUP.md          # This file
```

---

## Development Workflow

### 1. Local Development
```bash
# Terminal 1: Backend
cd barton-outreach-core
python start_server.py

# Terminal 2: Frontend
cd ui
npm run dev
```

### 2. Edit in Builder.io
1. Go to [builder.io](https://builder.io)
2. Open your page model
3. Edit visually
4. Publish changes
5. Refresh `localhost:5173/builder`

### 3. Production Deployment

**Backend:**
```bash
# Deploy to Railway, Render, or AWS
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
# Deploy to Vercel/Netlify
npm run build
# Set VITE_BUILDER_PUBLIC_KEY in deployment env vars
```

Update CORS in backend `main.py` for production domain.

---

## Troubleshooting

### Builder.io API Key Not Working
- Ensure `VITE_BUILDER_PUBLIC_KEY` is set in `.env`
- Check it's the **Public** key, not Private
- Restart dev server after changing `.env`

### Components Not Showing in Builder
- Check console for initialization logs: `[Builder.io] Registered components`
- Ensure `initializeBuilder()` is called in `main.tsx`
- Clear browser cache

### Data Not Loading
- Check FastAPI backend is running: `http://localhost:8000/health`
- Check CORS settings in `main.py`
- Open browser console for fetch errors

### "No Builder.io Content Found"
- Create content in Builder.io dashboard
- Match URL pattern exactly
- Publish the content
- Or use `?builder=true` query param

---

## Examples

### Example 1: Simple Dashboard Page

Create a page at `/dashboard` with:
1. **AccordionItem** (title: "System Overview")
   - Inside: **PhaseCard** × 3 (for different phases)
2. **AccordionItem** (title: "Errors")
   - Inside: **ErrorConsole**

### Example 2: Phase Detail Page

Create a page at `/phase/:phaseName` with:
1. **PhaseDetail** component
2. Bind `phase` prop to URL parameter
3. Fetch stats from API in Data tab

### Example 3: Custom Header with Live Data

1. Add a **Text** block
2. Set text to: `Total Companies: {{state.totalCompanies}}`
3. In Data tab:
   ```javascript
   async function getTotals() {
     const res = await fetch('http://localhost:8000/api/neon/v_phase_stats');
     const data = await res.json();
     const total = data.data.reduce((sum, s) => sum + s.count, 0);
     return { totalCompanies: total };
   }
   return await getTotals();
   ```

---

## Next Steps

1. ✅ Set up your Builder.io API key
2. ✅ Create your first page in Builder.io
3. ✅ Drag and drop components
4. ✅ Bind live API data
5. ✅ Publish and test
6. 🚀 Deploy to production

---

## Resources

- [Builder.io Docs](https://www.builder.io/c/docs/intro)
- [Component Registration Guide](https://www.builder.io/c/docs/custom-components)
- [Data Binding](https://www.builder.io/c/docs/data-models)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

**Need Help?** Check the console logs or create an issue on GitHub.

**Happy Building!** 🎨
