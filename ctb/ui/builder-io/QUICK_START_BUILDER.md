# Builder.io Quick Start
## 5-Minute Setup Guide

---

## Step 1: Get Builder.io API Key (2 minutes)

1. Go to **https://builder.io** → Sign up (free)
2. Click **Account** (top right) → **Organization**
3. Go to **API Keys** tab
4. Copy your **Public API Key**

---

## Step 2: Configure API Key (1 minute)

```bash
# In barton-outreach-core/ui/.env
VITE_BUILDER_PUBLIC_KEY=paste_your_key_here
```

**Example:**
```env
VITE_BUILDER_PUBLIC_KEY=bpk-abc123def456ghi789
```

---

## Step 3: Start Dev Server (1 minute)

```bash
cd barton-outreach-core/ui
npm run dev
```

Visit: **http://localhost:5173**

---

## Step 4: Create Your First Builder Page (1 minute)

### In Builder.io Dashboard:

1. Click **Content** → **+ New**
2. Select **Page**
3. Set URL to: `/builder`
4. Click **Create**

### In Visual Editor:

5. Click **+ Insert** → Scroll to **Custom Components**
6. Drag **AccordionItem** onto canvas
7. Set title: "My First Section"
8. Drag **PhaseCard** inside the AccordionItem
9. Click **Publish**

---

## Step 5: View Your Page

Visit: **http://localhost:5173/builder**

🎉 **Done!** You now have a visual editor for your dashboard.

---

## What's Next?

### Bind Live Data
1. In Builder editor, click **Data** tab
2. Add **Custom Code**:
   ```javascript
   async function fetchData() {
     const res = await fetch('http://localhost:8000/api/neon/v_phase_stats');
     const data = await res.json();
     return { stats: data.data };
   }
   return await fetchData();
   ```
3. Use `state.stats` in component props

### Available Components
- ✅ **AccordionItem** - Collapsible sections
- ✅ **PhaseCard** - Phase summary cards
- ✅ **PhaseDetail** - Detailed phase view
- ✅ **ErrorConsole** - Error monitoring

### API Endpoints
- `GET /api/neon/v_phase_stats` - Phase statistics
- `GET /api/neon/company_master` - Company list
- `GET /api/neon/v_error_recent` - Recent errors
- `GET /api/n8n/errors` - n8n workflow errors
- `GET /api/apify/actors` - Apify actors

---

## Troubleshooting

**Can't see components?**
- Restart dev server after adding API key

**No content on /builder?**
- Make sure you published in Builder.io
- Check URL matches exactly

**Data not loading?**
- Start backend: `cd barton-outreach-core && python start_server.py`
- Check backend is at `http://localhost:8000`

---

**Full Documentation:** See `BUILDER_IO_SETUP.md`

**Support:** Check browser console for error messages
