# Barton Doctrine Template - Installation Guide

## 🚀 3-Minute Setup

### **Step 1: Copy Template Files**

Copy these directories to your new React project:

```bash
# From template-export/ to your project:
src/lib/template/           → your-project/src/lib/template/
src/components/template/    → your-project/src/components/template/
```

### **Step 2: Install Dependencies**

Ensure you have these packages in your `package.json`:

```bash
npm install react-router-dom lucide-react
npm install @radix-ui/react-dialog @radix-ui/react-select
npm install class-variance-authority clsx tailwind-merge
```

### **Step 3: Create Your Configuration**

Create `src/lib/template/your-app-config.ts`:

```typescript
import { ApplicationConfig } from './application-config';

export const yourAppConfig: ApplicationConfig = {
  application: {
    name: "Your Application Name",
    domain: "Your > Business Domain", 
    description: "Your application description",
    id_prefix: "XX.YY.ZZ", // Your unique prefix
    hero_icon: "Building2"
  },
  altitudes: {
    "30k": { name: "Vision", description: "Strategic overview" },
    "20k": { name: "Categories", description: "Process categories" },
    "10k": { name: "Specialization", description: "Detailed processes" },
    "5k": { name: "Execution", description: "Step-by-step execution" }
  },
  branches: [
    {
      id: "01",
      name: "Your First Process Branch",
      description: "Description of what this branch does",
      route: "/doctrine/first-process",
      tools: ["Tool1", "Tool2", "Tool3"],
      processes: [
        {
          id: "01", 
          name: "First Step",
          description: "What this step accomplishes",
          tool: "Tool1",
          table: "your_table_name",
          unique_id_template: "XX.YY.ZZ.01.05.01"
        },
        {
          id: "02",
          name: "Second Step", 
          description: "What this step accomplishes",
          tool: "Tool2",
          table: "your_table_name",
          unique_id_template: "XX.YY.ZZ.01.05.02"
        }
        // Add more steps...
      ]
    },
    // Add 2 more branches for complete system...
  ]
};
```

### **Step 4: Create Your Pages**

**Main Dashboard** (`src/pages/YourIndex.tsx`):
```typescript
import { BartonTemplate } from '@/components/template/BartonTemplate';
import { yourAppConfig } from '@/lib/template/your-app-config';

export default function YourIndex() {
  return <BartonTemplate config={yourAppConfig} />;
}
```

**Process Triangle** (`src/pages/YourDoctrineMap.tsx`):
```typescript
import { ProcessTriangle } from '@/components/template/ProcessTriangle';
import { yourAppConfig } from '@/lib/template/your-app-config';

export default function YourDoctrineMap() {
  return <ProcessTriangle config={yourAppConfig} />;
}
```

**Branch Pages** (`src/pages/doctrine/FirstProcessPage.tsx`):
```typescript
import { BranchTemplate } from '@/components/template/BranchTemplate';
import { yourAppConfig } from '@/lib/template/your-app-config';

export default function FirstProcessPage() {
  const branch = yourAppConfig.branches.find(b => b.id === '01')!;
  return <BranchTemplate config={yourAppConfig} branch={branch} />;
}
```

### **Step 5: Add Routes**

Update your `src/App.tsx`:

```typescript
import YourIndex from './pages/YourIndex';
import YourDoctrineMap from './pages/YourDoctrineMap';
import FirstProcessPage from './pages/doctrine/FirstProcessPage';
// Import other branch pages...

// Add to your Routes:
<Route path="/your-app" element={<YourIndex />} />
<Route path="/your-app/doctrine-map" element={<YourDoctrineMap />} />
<Route path="/your-app/doctrine/first-process" element={<FirstProcessPage />} />
// Add other branch routes...
```

## ✅ **That's It!**

Your new application is now running with:
- ✅ Dashboard with your branding
- ✅ Christmas tree process visualization
- ✅ Branch detail pages with progressive ID building
- ✅ Professional navigation and UI

## 🎯 **Next Steps**

1. **Customize your configuration** with real processes
2. **Add your brand colors** to Tailwind config
3. **Connect real APIs** for your tools
4. **Deploy** using your preferred platform

## 🆘 **Need Help?**

- Check `EXAMPLES.md` for sample configurations
- See `CONFIGURATION.md` for detailed options
- Reference the working Barton Outreach Core implementation

**Total setup time: ~15 minutes for a complete business application!** 🚀