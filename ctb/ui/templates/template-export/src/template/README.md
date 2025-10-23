# Barton Doctrine Template System

## Overview

This template system provides a **reusable framework** for building structured business process applications. The Barton Outreach Core serves as the first implementation, establishing the pattern for all future applications.

## Template Structure

### 1. **4-Page Navigation Pattern**
- **Page 1**: Dashboard (configurable homepage)
- **Page 2**: Process Triangle (Christmas tree overview)
- **Page 3-5**: Branch Details (3 main process branches)

### 2. **Christmas Tree Layout**
- **30,000 ft** (TOP - NARROW): Strategic vision
- **20,000 ft** (EXPANDING): Process categories  
- **10,000 ft** (WIDER): Specialized processes
- **5,000 ft** (BASE - WIDEST): Tactical execution steps

### 3. **Configurable Components**
- `BartonTemplate.tsx` - Main dashboard template
- `ProcessTriangle.tsx` - Christmas tree visualization
- `BranchTemplate.tsx` - Branch detail pages
- `application-config.ts` - Configuration system

## Quick Start - New Application

### Step 1: Create Application Config
```typescript
// src/lib/template/sales-config.ts
export const salesConfig: ApplicationConfig = {
  application: {
    name: "Barton Sales Core",
    domain: "Sales > Pipeline Management",
    description: "Automated sales pipeline with AI assistance",
    id_prefix: "02.01.01",
    hero_icon: "TrendingUp"
  },
  branches: [
    {
      id: "01",
      name: "Lead Qualification",
      description: "Automated lead scoring and routing",
      route: "/doctrine/lead-qualification",
      tools: ["CRM", "Scoring Engine", "Router"],
      processes: [
        {
          id: "01",
          name: "Score Leads",
          description: "Calculate lead quality score",
          tool: "Scoring Engine",
          unique_id_template: "02.01.01.01.05.01"
        }
        // ... more processes
      ]
    }
    // ... more branches
  ]
};
```

### Step 2: Create Pages Using Templates
```typescript
// src/pages/SalesIndex.tsx
import { BartonTemplate } from '@/components/template/BartonTemplate';
import { salesConfig } from '@/lib/template/sales-config';

export default function SalesIndex() {
  return <BartonTemplate config={salesConfig} />;
}
```

### Step 3: Add Routes
```typescript
// src/App.tsx
<Route path="/sales" element={<SalesIndex />} />
<Route path="/sales/doctrine-map" element={<SalesDoctrineMap />} />
<Route path="/sales/doctrine/lead-qualification" element={<LeadQualificationPage />} />
```

## Template Benefits

### ✅ **Rapid Deployment**
- New application in hours, not days
- Consistent structure across all apps
- Proven navigation patterns

### ✅ **Configurable Content**
- Swap out processes, tools, descriptions
- Maintain same user experience
- Easy to customize branding

### ✅ **Scalable Architecture**
- Add unlimited process branches
- Support complex workflows
- Maintain performance

### ✅ **ID Management System**
- Auto-generated unique IDs
- Consistent numbering scheme
- Easy tracking and debugging

## Example Applications

### Marketing > Outreach (Implemented)
- Lead Intake & Validation
- Message Generation (Agent)
- Campaign Execution & Telemetry

### Sales > Pipeline Management (Future)
- Lead Qualification
- Proposal Generation
- Deal Closing

### Operations > Workflow Automation (Future)
- Task Management
- Quality Control
- Delivery & Reporting

## Template Components Reference

### ApplicationConfig Interface
```typescript
interface ApplicationConfig {
  application: {
    name: string;           // "Barton Sales Core"
    domain: string;         // "Sales > Pipeline"
    description: string;    // Hero subtitle
    id_prefix: string;      // "02.01.01"
    hero_icon: string;      // Lucide icon name
  };
  branches: ApplicationBranch[];
  altitudes: { ... };       // 30k/20k/10k/5k descriptions
}
```

### Branch Configuration
```typescript
interface ApplicationBranch {
  id: string;               // "01", "02", "03"
  name: string;             // "Lead Qualification"
  description: string;      // Branch overview
  route: string;            // "/doctrine/lead-qualification"
  tools: string[];          // ["CRM", "Scoring"]
  processes: ProcessStep[]; // Detailed steps
}
```

### Process Steps
```typescript
interface ProcessStep {
  id: string;               // "01", "02", "03"
  name: string;             // "Score Leads"
  description: string;      // Step details
  tool?: string;            // "Scoring Engine"
  table?: string;           // "lead_scores"
  unique_id_template: string; // "02.01.01.01.05.01"
}
```

## Best Practices

1. **Start with Configuration** - Define your processes first
2. **Use Consistent Naming** - Follow established patterns
3. **Keep Branches Balanced** - ~3-6 processes per branch
4. **Document Tools** - List all required integrations
5. **Test Navigation** - Verify all routes work correctly

## Future Enhancements

- Dynamic route generation from config
- Visual process flow editor
- Template marketplace
- Multi-tenant configurations
- Real-time collaboration features

---

**Built with the Barton Doctrine methodology - from strategic vision to tactical execution.**