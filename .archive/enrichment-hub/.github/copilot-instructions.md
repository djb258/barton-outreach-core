# Enricha-Vision AI Coding Agent Guide

## Project Overview

This is **enricha-vision** — a React-based data enrichment workbench built with Vite, TypeScript, shadcn/ui, and Supabase. The app provides spreadsheet-like interfaces for managing enrichment queues, validating data, and tracking monthly updates for people and companies.

## Architecture Quick Start

### Tech Stack
- **Frontend**: React 18 + TypeScript + Vite
- **UI**: shadcn/ui components + Tailwind CSS + Radix UI primitives
- **State**: TanStack Query (React Query) for server state
- **Database**: Supabase (PostgreSQL) with realtime subscriptions
- **Routing**: React Router v6
- **Special Feature**: CTB (Component-Task-Blueprint) system for project organization

### Key Directory Structure
```
enricha-vision/
├── src/
│   ├── pages/           # Route components (Index, DataOpsDashboard, MonthlyUpdates)
│   ├── components/      # Reusable UI components (EditableGrid, ComponentId, etc.)
│   ├── hooks/          # Custom hooks (useSupabaseTable, useBatchActions, useValidation)
│   ├── integrations/   # External integrations (Supabase client)
│   ├── lib/            # Utilities (auditLogger, n8nClient)
│   └── contexts/       # React contexts (EditModeContext)
├── ctb/                # CTB system structure (sys, ai, data, docs, ui, meta)
├── supabase/           # Supabase config and migrations
└── global-config.yaml  # CTB configuration and enforcement rules
```

## Critical Patterns to Follow

### 1. Supabase Data Management Pattern
All database interactions use `useSupabaseTable` hook:

```typescript
// Standard pattern for table operations
const peopleTable = useSupabaseTable({
  tableName: "people_needs_enrichment",
  pageSize: 500,
  orderBy: "created_at",
  orderAscending: false,
});

// Available methods: updateCell, deleteRow, refresh
await peopleTable.updateCell(recordId, fieldName, newValue, oldValue);
```

**Important**: Tables have realtime subscriptions — changes auto-refresh. The hook includes audit logging via `logEdit()` for all updates.

### 2. ComponentId System (Edit Mode Pattern)
Components wrap elements with `<ComponentId>` for developer mode identification:

```tsx
<ComponentId id="unique-component-id" type="button" path="src/pages/Index.tsx">
  <Button>Action</Button>
</ComponentId>
```

Toggle edit mode with `Ctrl/Cmd + E`. IDs should be kebab-case with context prefix (e.g., `dataops-tab-enrichment`, `monthly-nav-enrichment`).

### 3. EditableGrid Component Usage
The `EditableGrid` component is the primary UI for data manipulation:

```tsx
<EditableGrid
  data={tableData}
  columns={columnDefinitions}
  editableColumns={["field1", "field2"]}
  onCellUpdate={handleUpdate}
  isLoading={isLoading}
/>
```

Supports inline editing, pagination, sorting, filtering, and batch operations.

### 4. Batch Actions Pattern
Use `useBatchActions` hook for bulk operations:

```typescript
const { exportBatch, processBatch, bulkUpdate } = useBatchActions("people", "needs_enrichment");

// Export filtered data
exportBatch(selectedRows);

// Process batch to next state
await processBatch(selectedRows, "validated");
```

## Developer Workflows

### Setup & Running
```bash
npm install              # Install dependencies
npm run dev             # Start dev server (localhost:8080)
npm run build           # Production build
npm run preview         # Preview production build
```

**Environment Setup**: Copy `.env.example` to `.env` and configure:
- `VITE_SUPABASE_URL` — Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY` — Supabase anon key

See `ENV_SETUP.md` for detailed credential setup (Firebase, Gemini, GitHub tokens).

### Testing Changes
1. Run dev server: `npm run dev`
2. Open `http://localhost:8080`
3. Toggle edit mode (`Ctrl/Cmd + E`) to see component IDs
4. Check browser console for errors
5. Verify realtime updates work (open in two tabs, edit in one)

### Adding New Pages
1. Create page in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx` **above** the `*` catch-all route:
```tsx
<Route path="/new-page" element={<NewPage />} />
```
3. Add navigation link with `<ComponentId>` wrapper

## Project-Specific Conventions

### CTB System Integration
This project uses the CTB (Component-Task-Blueprint) architecture:

- **ctb/sys/** — System integrations (Composio, Firebase, Neon, GitHub)
- **ctb/ai/** — AI configuration and prompts
- **ctb/data/** — Database schemas
- **ctb/docs/** — Documentation
- **ctb/ui/** — UI component blueprints
- **ctb/meta/** — Metadata and registry

**CTB Enforcement**: The `global-config.yaml` defines compliance rules (min_score: 70). CTB structure is validated but not strictly enforced during development.

### Component Naming
- **Pages**: PascalCase descriptive names (`DataOpsDashboard`, `MonthlyUpdates`)
- **Components**: PascalCase (`EditableGrid`, `ComponentId`)
- **Hooks**: camelCase with `use` prefix (`useSupabaseTable`, `useBatchActions`)
- **Files**: Match component/hook name exactly

### State Management Philosophy
- **Server state**: TanStack Query via Supabase hooks
- **UI state**: React useState for local component state
- **Shared state**: React Context (e.g., `EditModeContext`)
- **Avoid**: Redux, Zustand, or other global state libraries

### Toast Notifications
Use `sonner` for all user feedback:
```tsx
import { toast } from "sonner";

toast.success("Action completed");
toast.error("Operation failed");
```

## Integration Points

### Supabase Tables
Primary tables in use:
- `people_needs_enrichment` — People records pending enrichment
- `company_needs_enrichment` — Company records pending enrichment
- `enrichment_log` — Audit log of enrichment operations
- `monthly_updates` — Monthly status changes

All tables have `created_at`, `updated_at` timestamps. Use `useSupabaseTable` hook for all interactions.

### N8N Webhooks (Future)
Stub exists in `src/lib/n8nClient.ts` for n8n enrichment webhook integration. Not yet fully implemented — add webhook URLs to `.env` when ready.

### External Tools
- **Obsidian**: Used for CTB documentation (vault = project root)
- **GitKraken**: Git visualization and management
- **Lovable.dev**: Original project generator (see `README.md`)

## Common Tasks

### Adding a New Table/Feature
1. Create Supabase migration in `supabase/migrations/`
2. Create custom hook in `src/hooks/` (follow `useSupabaseTable` pattern)
3. Create page component in `src/pages/`
4. Add route in `src/App.tsx`
5. Add navigation link with `ComponentId` wrapper
6. Test realtime subscriptions work

### Modifying EditableGrid
- Column definitions: array of `{ key, label, width? }`
- Editable columns: string array of field names
- Cell updates: logged automatically via `auditLogger`
- Filtering: handled by `TableToolbar` component

### Working with ComponentId System
- Always wrap interactive elements in edit mode
- Use descriptive IDs: `{page}-{section}-{element}`
- Include `type` prop for clarity: `"button"`, `"link"`, `"tab-trigger"`, etc.
- Toggle edit mode to verify IDs are visible and copyable

### Handling Errors
- Use `try/catch` with toast notifications
- Log to console for debugging
- Supabase errors: `.error` property contains message
- Check Network tab for failed API calls

## Files to Reference First

When working on specific features, check these files:

- **Data operations**: `src/hooks/useSupabaseTable.ts` — core table hook
- **UI patterns**: `src/components/EditableGrid.tsx` — primary data grid
- **Routing**: `src/App.tsx` — all routes and providers
- **Supabase setup**: `src/integrations/supabase/client.ts` — client config
- **CTB config**: `global-config.yaml` — project structure and enforcement
- **Environment**: `ENV_SETUP.md` — credential and API key setup
- **Quick start**: `QUICK_START.md` — full setup in 5 minutes

## Troubleshooting

**Supabase connection fails**: Check `.env` has correct URL/key, verify Supabase project is active  
**Realtime not working**: Check browser console for subscription errors, verify table name matches exactly  
**Edit mode toggle not working**: Check `EditModeContext` is in App.tsx provider tree  
**Build errors**: Run `npm install` to ensure all deps are installed, check TypeScript errors  
**CTB compliance warnings**: Refer to `CTB_README.md` for structure requirements (not critical for development)

## Code Style

- Use TypeScript strictly — avoid `any` except in `useSupabaseTable` generic contexts
- Prefer functional components with hooks over class components
- Use async/await over `.then()` chains
- Import shadcn components from `@/components/ui/*`
- Use Tailwind classes (avoid inline styles)
- Follow ESLint rules (run `npm run lint`)
