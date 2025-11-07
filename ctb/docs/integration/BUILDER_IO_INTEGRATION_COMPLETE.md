# ✅ Builder.io Integration Complete
## Outreach Command Center - Visual Editor Ready

---

## 🎉 Summary

The Outreach Command Center frontend has been successfully integrated with **Builder.io**, enabling drag-and-drop visual editing of your dashboard in the cloud.

---

## 📦 What Was Installed

```bash
npm install @builder.io/react
```

**Version:** `^8.2.8`
**Package:** Visual CMS SDK for React

---

## 📁 Files Created

### Core Configuration
```
ui/
├── src/
│   ├── builder.config.ts          ✅ NEW - Builder SDK initialization & component registration
│   ├── main.tsx                   ✅ UPDATED - Initialize Builder on startup
│   ├── App.tsx                    ✅ UPDATED - Hybrid mode (Builder + Default)
│   ├── AppDefault.tsx             ✅ NEW - Original dashboard (preserved)
│   │
│   ├── pages/
│   │   └── BuilderPage.tsx        ✅ NEW - Builder.io content renderer
│   │
│   └── utils/
│       └── builderData.ts         ✅ NEW - Helper functions for API data
│
├── .env                           ✅ UPDATED - Added VITE_BUILDER_PUBLIC_KEY
├── .env.example                   ✅ UPDATED - Template for API key
├── BUILDER_IO_SETUP.md            ✅ NEW - Complete integration guide
└── QUICK_START_BUILDER.md         ✅ NEW - 5-minute quick start
```

---

## 🎨 Registered Components

All components are now available in the Builder.io visual editor:

| Component | Description | Props |
|-----------|-------------|-------|
| **AccordionItem** | Collapsible section | title, defaultOpen, badge, children |
| **PhaseCard** | Phase summary metrics | phase, stats[] |
| **PhaseDetail** | Detailed phase view | phase, stats[], apifyActorId |
| **ErrorConsole** | Error monitoring | (auto-fetches data) |

---

## 🔧 Configuration

### Environment Variables

**File:** `ui/.env`

```env
# API Backend URL
VITE_API_URL=http://localhost:8000

# Builder.io Public API Key
# Get from: https://builder.io/account/organization
VITE_BUILDER_PUBLIC_KEY=YOUR_BUILDER_PUBLIC_KEY_HERE
```

### Component Registration

**File:** `ui/src/builder.config.ts`

```typescript
import { Builder } from '@builder.io/react';

// All 4 components registered with full prop definitions
Builder.registerComponent(AccordionItem, { ... });
Builder.registerComponent(PhaseCard, { ... });
Builder.registerComponent(PhaseDetail, { ... });
Builder.registerComponent(ErrorConsole, { ... });
```

### Hybrid App Router

**File:** `ui/src/App.tsx`

- **Default Mode:** Shows original dashboard when no Builder content exists
- **Builder Mode:** Shows Builder.io content when available
- **Force Builder:** Add `?builder=true` to any URL

---

## 🚀 How to Use

### Quick Start (5 Minutes)

1. **Get API Key**
   ```
   Go to: https://builder.io → Sign up → Get Public API Key
   ```

2. **Add to .env**
   ```bash
   # ui/.env
   VITE_BUILDER_PUBLIC_KEY=bpk-your-actual-key-here
   ```

3. **Start Dev Server**
   ```bash
   cd ui
   npm run dev
   ```
   Visit: `http://localhost:5173`

4. **Create Page in Builder.io**
   - Go to builder.io dashboard
   - Create new "Page" model
   - Set URL: `/builder`
   - Drag components onto canvas
   - Publish

5. **View Result**
   ```
   Visit: http://localhost:5173/builder
   ```

---

## 📖 Documentation

### Quick Reference

- **Quick Start Guide:** `ui/QUICK_START_BUILDER.md` (5-minute setup)
- **Full Documentation:** `ui/BUILDER_IO_SETUP.md` (complete guide)

### Key Topics Covered

1. ✅ Getting Builder.io API key
2. ✅ Component registration explained
3. ✅ Creating pages in Builder.io
4. ✅ Binding live API data
5. ✅ Data fetching utilities
6. ✅ Advanced examples
7. ✅ Troubleshooting guide
8. ✅ Production deployment

---

## 🔗 Integration Points

### API Endpoints Available for Data Binding

All FastAPI endpoints can be used in Builder.io:

```javascript
// In Builder.io Data tab - Custom Code

// Neon Database
fetch('http://localhost:8000/api/neon/v_phase_stats')
fetch('http://localhost:8000/api/neon/v_error_recent')
fetch('http://localhost:8000/api/neon/company_master?limit=50')

// n8n Workflows
fetch('http://localhost:8000/api/n8n/errors')
fetch('http://localhost:8000/api/n8n/executions')

// Apify
fetch('http://localhost:8000/api/apify/actors')
```

### Data Utilities

Global helpers exposed on `window.builderData`:

```javascript
// Use in Builder.io custom code
const data = await window.builderData.fetchOutreachData();
// Returns: { phaseStats, neonErrors, companyMaster, n8nErrors, apifyActors }

const grouped = window.builderData.groupPhaseStats(stats);
// Groups stats by phase name

const total = window.builderData.calculateTotalCompanies(stats);
// Calculates total company count
```

---

## 🎯 Use Cases

### Example 1: Custom Dashboard Page

Create `/my-dashboard` with:
- Header with live company count
- Grid of PhaseCard components
- ErrorConsole at bottom

### Example 2: Phase-Specific Page

Create `/phases/discovery` with:
- PhaseDetail component
- Bound to "Company Discovery" phase
- Live stats from API

### Example 3: Error Monitoring Page

Create `/errors` with:
- ErrorConsole component
- Custom header
- Auto-refreshing data

---

## 🔍 How It Works

### App Flow

```
User visits URL
      ↓
App.tsx checks for Builder content
      ↓
  ┌───────────┴───────────┐
  │                       │
Builder content       No Builder content
  exists                 found
  │                       │
  ↓                       ↓
BuilderPage.tsx      AppDefault.tsx
(Visual editor)      (Original dashboard)
```

### Component Registration

```
main.tsx
  ↓
initializeBuilder()
  ↓
Builder.set({ apiKey })
Builder.registerComponent(AccordionItem, {...})
Builder.registerComponent(PhaseCard, {...})
Builder.registerComponent(PhaseDetail, {...})
Builder.registerComponent(ErrorConsole, {...})
```

---

## 🚦 Testing the Integration

### 1. Verify Installation

```bash
cd ui
npm list @builder.io/react
# Should show: @builder.io/react@8.2.8
```

### 2. Check Console Logs

Start dev server and look for:
```
[Builder.io] SDK initialized with API key: bpk-...
[Builder.io] Registered components: [
  'AccordionItem',
  'PhaseCard',
  'PhaseDetail',
  'ErrorConsole'
]
```

### 3. Test Default Mode

Visit `http://localhost:5173/` - Should show original dashboard

### 4. Test Builder Mode

Visit `http://localhost:5173/?builder=true` - Should show Builder check

### 5. Create Test Page

1. Go to builder.io
2. Create page at URL `/test`
3. Add a PhaseCard
4. Publish
5. Visit `http://localhost:5173/test`

---

## 🎨 Builder.io Dashboard Access

### Where to Edit Content

1. **Login:** https://builder.io/login
2. **Content:** https://builder.io/content
3. **Models:** https://builder.io/models
4. **Account:** https://builder.io/account

### Visual Editor Features

- ✅ Drag & drop components
- ✅ Live preview
- ✅ Responsive design tools
- ✅ Custom CSS
- ✅ Data binding
- ✅ A/B testing
- ✅ Scheduling
- ✅ Version history

---

## 📊 Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| Builder.io SDK | ✅ Installed | v8.2.8 |
| Component Registration | ✅ Complete | 4 components |
| Environment Config | ⚠️ Needs API Key | Add to .env |
| Hybrid Mode | ✅ Working | Default + Builder |
| Data Utilities | ✅ Ready | Global helpers |
| Documentation | ✅ Complete | 2 guides |
| Production Ready | ⚠️ Needs Deploy | Set env vars |

---

## 🔒 Security Notes

### API Keys

- ✅ `VITE_BUILDER_PUBLIC_KEY` - Safe to expose in client
- ❌ Never commit `.env` to git
- ✅ Use `.env.example` for templates

### CORS

Update `src/main.py` for production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 Deployment

### Frontend (Vercel/Netlify)

```bash
cd ui
npm run build

# Set environment variable in deployment platform:
VITE_BUILDER_PUBLIC_KEY=bpk-your-key
```

### Backend (Railway/Render)

```bash
cd barton-outreach-core
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Update CORS for production domain
```

---

## 📞 Support & Resources

### Documentation

- **Quick Start:** `ui/QUICK_START_BUILDER.md`
- **Full Guide:** `ui/BUILDER_IO_SETUP.md`
- **Builder.io Docs:** https://www.builder.io/c/docs/intro

### Troubleshooting

Common issues and solutions in `BUILDER_IO_SETUP.md` → Troubleshooting section

### Console Debugging

Check browser console for:
- `[Builder.io]` initialization logs
- Component registration confirmations
- API fetch errors
- Data binding issues

---

## ✅ Next Steps

1. [ ] Get Builder.io API key from https://builder.io
2. [ ] Add key to `ui/.env`
3. [ ] Restart dev server
4. [ ] Create your first page in Builder.io
5. [ ] Drag components onto canvas
6. [ ] Bind live API data
7. [ ] Publish and test
8. [ ] Deploy to production

---

## 🎉 Congratulations!

Your Outreach Command Center now supports **visual editing with Builder.io**!

You can now:
- ✅ Edit layouts without coding
- ✅ Drag and drop components
- ✅ Bind live API data
- ✅ A/B test variations
- ✅ Schedule content changes
- ✅ Collaborate with non-technical team members

**Happy Building!** 🚀

---

**Integration completed:** 2025-10-26
**Builder.io SDK version:** 8.2.8
**Components registered:** 4
**Status:** ✅ Production Ready (pending API key)
