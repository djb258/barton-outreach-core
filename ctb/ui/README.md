# User Interface (ui/)

**Barton ID Range**: 07.01.*
**Enforcement**: None (presentation layer)

## Purpose
Frontend applications, React components, and UI templates.

## Key Directories

### `apps/` - Frontend Applications
- `amplify-client/` - Main React application
- `factory-imo/` - IMO Creator interface  
- `outreach-process-manager/` - Outreach management UI
- `outreach-ui/` - Outreach campaign interface

### `src/` - Shared Components
- Reusable React components
- UI utilities
- Shared styles

### `packages/` - UI Packages
- Shared npm packages
- Component libraries

### `public/` - Static Assets
- Images, fonts, icons
- Favicon, robots.txt

### `templates/` - UI Templates
- Page templates
- Component blueprints

## Common Tasks

### Run Development Server
```bash
cd ctb/ui/apps/amplify-client
npm install
npm run dev
```

### Build for Production
```bash
npm run build
```

### Deploy to Vercel
```bash
cd ctb/ai/scripts
node vercel-mcp-deploy.js --app amplify-client
```

## Dependencies
- **Upstream**: `ctb/sys/api/` for backend data
- **Downstream**: None (top of user-facing stack)

## Owners
- Frontend: UI/UX team
- Component Library: Design System team
