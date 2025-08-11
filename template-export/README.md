# Barton Doctrine Template

## 🚀 Rapid Application Deployment Template

This template system enables **rapid deployment** of structured business process applications using the **Barton Doctrine methodology**.

**Deploy Time:** From weeks → **hours**

## 📋 What You Get

### ✅ **4-Page Navigation System**
- **Dashboard** - Configurable homepage
- **Process Triangle** - Christmas tree visualization  
- **Branch Pages** - Detailed workflow pages (3 default)

### ✅ **Christmas Tree Layout**
- **30,000 ft** (TOP - NARROW) - Strategic vision
- **20,000 ft** (EXPANDING) - Process categories
- **10,000 ft** (WIDER) - Specialized processes  
- **5,000 ft** (BASE - WIDEST) - Tactical execution

### ✅ **Auto ID Generation**
- Progressive unique_id building
- Consistent numbering scheme
- Easy tracking and debugging

## 🎯 Proven Use Cases

### ✅ **Marketing > Outreach** (Implemented)
- Lead Intake & Validation
- Message Generation (Agent)
- Campaign Execution & Telemetry

### 🔄 **Sales > Pipeline** (Template Ready)
- Lead Qualification  
- Proposal Generation
- Deal Closing

### 🔄 **Operations > Workflow** (Template Ready)  
- Task Management
- Quality Control
- Delivery & Reporting

## 🚀 Quick Start

### 1. **Copy Template Files**
```bash
# Copy these files to your new project:
src/lib/template/
src/components/template/
```

### 2. **Create Your Configuration**
```typescript
// src/lib/template/your-app-config.ts
export const yourAppConfig: ApplicationConfig = {
  application: {
    name: "Your App Name",
    domain: "Your > Domain", 
    description: "Your app description",
    id_prefix: "XX.XX.XX"
  },
  branches: [
    {
      id: "01",
      name: "Your First Process",
      description: "What this process does",
      route: "/doctrine/your-process",
      tools: ["Tool1", "Tool2"],
      processes: [
        {
          id: "01",
          name: "Step Name",
          description: "What this step does", 
          unique_id_template: "XX.XX.XX.01.05.01"
        }
      ]
    }
  ]
};
```

### 3. **Create Your Pages**
```typescript
// src/pages/YourIndex.tsx
import { BartonTemplate } from '@/components/template/BartonTemplate';
import { yourAppConfig } from '@/lib/template/your-app-config';

export default function YourIndex() {
  return <BartonTemplate config={yourAppConfig} />;
}
```

### 4. **Add Routes**
```typescript
// src/App.tsx  
<Route path="/your-app" element={<YourIndex />} />
<Route path="/your-app/doctrine-map" element={<YourDoctrineMap />} />
```

## 📁 Template Structure

```
template/
├── lib/template/
│   ├── application-config.ts    # Configuration interface
│   └── example-configs/        # Sample configurations
├── components/template/
│   ├── BartonTemplate.tsx      # Main dashboard  
│   ├── ProcessTriangle.tsx     # Christmas tree view
│   └── BranchTemplate.tsx      # Branch detail pages
├── pages/template/
│   ├── TemplateIndex.tsx       # Dashboard page
│   ├── DoctrineMapPage.tsx     # Triangle page  
│   └── doctrine/              # Branch pages
└── docs/
    ├── QUICK_START.md         # Getting started
    ├── CONFIGURATION.md       # Config reference
    └── EXAMPLES.md           # Sample apps
```

## 🎨 Customization

### **Application Branding**
```typescript
application: {
  name: "Your Brand Name",           // Main title
  domain: "Category > Subcategory",  // Domain description  
  description: "Your tagline",       // Hero subtitle
  id_prefix: "01.02.03",            // Unique ID prefix
  hero_icon: "Building2"            // Lucide icon name
}
```

### **Process Branches**
```typescript
branches: [
  {
    id: "01",                        // Branch number
    name: "Process Name",            // Display name
    description: "What it does",     // Description
    route: "/doctrine/process-name", // URL route
    tools: ["Tool1", "Tool2"],      // Required tools
    processes: [...]                 // Detailed steps
  }
]
```

## 🔧 Advanced Features

- **Dynamic routing** from configuration
- **Configurable altitudes** (30k/20k/10k/5k)
- **Tool integration specs**
- **Database table mapping**
- **Progressive ID building**
- **Responsive design**

## 📖 Documentation

- [Quick Start Guide](./docs/QUICK_START.md)
- [Configuration Reference](./docs/CONFIGURATION.md)
- [Example Applications](./docs/EXAMPLES.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

## 🏗️ Built With

- React + TypeScript
- Tailwind CSS + shadcn/ui
- React Router
- Vite build system

---

**Ready to deploy your next business application in hours, not weeks!** 🚀