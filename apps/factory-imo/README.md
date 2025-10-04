# 🏗️ Factory IMO - Doctrine Tracker with Builder.io Integration

## Overview

Factory IMO contains the **Doctrine Tracker**, a React-based shell that enforces Barton Doctrine while remaining fully editable in Builder.io. This system provides altitude-based process organization and MCP-first integration for scalable process management.

## 🎯 Barton Doctrine Compliance

### Altitude System
- **30,000 ft (Vision)**: Strategic planning and blueprint design
- **20,000 ft (Category)**: Process definition and validation
- **10,000 ft (Execution)**: Implementation and data operations

### ID Format
All processes use Barton ID format: `XX.XX.XX.XX.ALTITUDE.SEQUENCE`
- Example: `02.03.07.04.30000.001` (Vision level process)
- Example: `02.03.07.04.10000.003` (Execution level process)

## 🏗️ Builder.io Integration

### Setup Instructions

1. **Install Builder.io Extension in VS Code**
2. **Configure Extension:**
   - **Dev Server URL:** `http://localhost:8081`
   - **Dev Command:** `npm run dev`

3. **Start Development Server:**
   ```bash
   cd apps/factory-imo
   npm run dev
   ```

4. **Register Components with Builder.io:**
   ```bash
   # Ensure Composio MCP server is running on localhost:3001
   npm run builderio:register
   ```

### Available Components

#### 1. PhaseGroup
- **Purpose**: Groups process steps by altitude level
- **Props**:
  - `altitude` (number): 30000, 20000, or 10000
  - `title` (string): Display title for phase
  - `steps` (Step[]): Array of process steps
- **Visual**: Colored sections with altitude badges

#### 2. StepCard
- **Purpose**: Individual process step display
- **Props**:
  - `process_id` (string): Human-readable description
  - `unique_id` (string): Barton ID format
  - `tool_id?` (string): MCP tool identifier
  - `table_reference?` (string): Database table reference
- **Visual**: Clickable cards with status indicators

#### 3. StepModal
- **Purpose**: Detailed process step view
- **Props**:
  - `step` (Step): Complete step object
  - `onClose` (function): Modal close handler
- **Features**: Focus trapping, ESC key support, accessibility

#### 4. ProcessDetailView
- **Purpose**: Complete process management dashboard
- **Features**: Altitude-based grouping, demo data integration, responsive design

## 📁 Project Structure

```
src/
├── components/
│   └── doctrine/           # Doctrine Tracker components
│       ├── PhaseGroup.tsx  # Altitude-based grouping
│       ├── StepCard.tsx    # Individual step cards
│       └── StepModal.tsx   # Detailed step view
├── data/
│   └── demo_processes.json # Sample process data
├── pages/
│   └── process-detail-view/
│       └── index.tsx       # Main dashboard page
├── types.ts               # TypeScript definitions
└── scripts/
    └── register-builderio-components.js # Builder.io registration
```

## 🔧 Development Workflow

### 1. Standard Development
```bash
# Start development server
npm run dev

# Open http://localhost:8081 in browser
# Components are viewable at /process-detail-view
```

### 2. MCP Data Integration
```bash
# 1. Ensure Composio MCP server is running with doctrine routes
curl http://localhost:3001/doctrine/health

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 3. Test dynamic data fetching
# ProcessDetailView will automatically fetch from MCP server
# Falls back to demo data if MCP server is unavailable
```

### 3. Builder.io Visual Editing
```bash
# 1. Ensure MCP server is running
curl http://localhost:3001/health

# 2. Register components with Builder.io
npm run builderio:register

# 3. Open Builder.io visual editor
# 4. Find "Process Management" category
# 5. Drag and drop components
# 6. Configure properties visually
```

### 3. Component Customization

#### Adding New Process Steps
```typescript
// Edit src/data/demo_processes.json
{
  "unique_id": "02.03.07.07.20000.010",
  "process_id": "Your new process",
  "altitude": 20000,
  "tool_id": "07",
  "table_reference": "your_table"
}
```

#### Customizing Altitude Levels
```typescript
// Edit src/types.ts - ALTITUDE_CONFIG
export const ALTITUDE_CONFIG = {
  40000: { label: 'Strategy', color: 'purple', ... }, // Add new level
  30000: { label: 'Vision', color: 'red', ... },
  // ... existing levels
}
```

#### Using Dynamic Data Hook
```typescript
// Use useDoctrineSteps hook in your components
import { useDoctrineSteps } from '../hooks/useDoctrineSteps';

function MyComponent() {
  const { steps, loading, error, stepsByAltitude } = useDoctrineSteps({
    microprocess_id: 'my-process',
    blueprint_id: 'my-blueprint'
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Vision Steps: {stepsByAltitude(30000).length}</h2>
      <h2>Category Steps: {stepsByAltitude(20000).length}</h2>
      <h2>Execution Steps: {stepsByAltitude(10000).length}</h2>
    </div>
  );
}
```

## 🔗 MCP Integration

### Composio MCP Server
- **URL**: `http://localhost:3001`
- **Health Check**: `curl http://localhost:3001/health`
- **Required for**: Builder.io component registration, process data validation

### Builder.io Registration
The registration script (`scripts/register-builderio-components.js`) automatically:
1. Connects to Composio MCP server
2. Registers each component with metadata
3. Sets up input/output schemas
4. Creates Builder.io component library entries

## 🎨 Styling System

### Tailwind Classes
- **Altitude Colors**: Red (Vision), Yellow (Category), Green (Execution)
- **Component States**: Hover effects, focus management, responsive breakpoints
- **Accessibility**: ARIA labels, focus trapping, keyboard navigation

### Customization
```css
/* Add custom Barton Doctrine styles */
.barton-altitude-30000 { @apply bg-red-100 border-red-300 text-red-800; }
.barton-altitude-20000 { @apply bg-yellow-100 border-yellow-300 text-yellow-800; }
.barton-altitude-10000 { @apply bg-green-100 border-green-300 text-green-800; }
```

## 🧪 Testing

### Component Testing
```bash
# Lint components
npm run lint

# Visual testing in browser
npm run dev
# Navigate to: http://localhost:8081/process-detail-view
```

### Builder.io Testing
1. Register components: `npm run builderio:register`
2. Open Builder.io visual editor
3. Test drag-and-drop functionality
4. Verify property configuration
5. Preview in Builder.io preview mode

## 📊 Data Flow

```
Demo Data (JSON) → ProcessDetailView → PhaseGroup → StepCard → StepModal
                                    ↓
                           Builder.io Visual Editor
                                    ↓
                              MCP Integration
                                    ↓
                           Composio Tool Execution
```

## 🔒 Barton Doctrine Enforcement

### ID Validation
- All processes must have valid Barton ID format
- Altitude must match process classification
- Sequential numbering enforced

### MCP-First Execution
- All operations go through Composio MCP server
- No direct database connections allowed
- Process reference validation against `shq_process_key_reference`

### Audit Compliance
- Every component interaction logged
- Process changes tracked with unique IDs
- Builder.io edits maintain doctrine compliance

## 🚀 Deployment

### Development
```bash
npm run dev          # Local development server
npm run builderio:register  # Register with Builder.io
```

### Production
```bash
npm run build        # Build for production
npm run preview      # Preview production build
```

### Builder.io Integration
1. Components are automatically available in Builder.io component library
2. Visual editing preserves Barton Doctrine compliance
3. Changes sync back to codebase via MCP integration

## 📖 Next Steps

1. **Expand Component Library**: Add more Doctrine-compliant components
2. **Enhanced MCP Integration**: Real-time data synchronization
3. **Advanced Builder.io Features**: Custom property editors, validation rules
4. **Process Automation**: Workflow triggers via Builder.io visual editor

---

**🎯 Builder.io Configuration Summary:**
- **Dev Server URL**: `http://localhost:8081`
- **Dev Command**: `npm run dev`
- **Registration**: `npm run builderio:register`
- **Component Category**: "Process Management"