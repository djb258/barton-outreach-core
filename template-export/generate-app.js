#!/usr/bin/env node

/**
 * Barton Doctrine Template Generator
 * Quickly scaffold new applications using the template system
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function ask(question) {
  return new Promise(resolve => {
    rl.question(question, resolve);
  });
}

async function generateApp() {
  console.log('🚀 Barton Doctrine Template Generator\n');

  // Collect app details
  const appName = await ask('Application name (e.g., "Barton Sales Core"): ');
  const domain = await ask('Business domain (e.g., "Sales > Pipeline Management"): ');
  const description = await ask('App description: ');
  const idPrefix = await ask('ID prefix (e.g., "02.01.01"): ');
  const routePrefix = await ask('Route prefix (e.g., "sales"): ');

  console.log('\n📋 Creating configuration...');

  // Generate configuration
  const config = generateConfiguration(appName, domain, description, idPrefix, routePrefix);
  
  // Create files
  const targetDir = `./${routePrefix}-app`;
  
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  // Copy template files
  copyTemplateFiles(targetDir);
  
  // Generate configuration file
  fs.writeFileSync(
    path.join(targetDir, 'src/lib/template/app-config.ts'),
    config
  );

  // Generate pages
  generatePages(targetDir, routePrefix, appName);

  console.log('\n✅ Application generated successfully!');
  console.log(`📁 Location: ${targetDir}`);
  console.log('\n🎯 Next steps:');
  console.log('1. Copy the generated files to your React project');
  console.log('2. Install dependencies: npm install react-router-dom lucide-react');
  console.log('3. Add routes to your App.tsx');
  console.log('4. Customize your processes in app-config.ts');
  
  rl.close();
}

function generateConfiguration(appName, domain, description, idPrefix, routePrefix) {
  return `import { ApplicationConfig } from './application-config';

export const ${routePrefix}Config: ApplicationConfig = {
  application: {
    name: "${appName}",
    domain: "${domain}",
    description: "${description}",
    id_prefix: "${idPrefix}",
    hero_icon: "Building2"
  },
  altitudes: {
    "30k": { name: "Vision", description: "Strategic overview and vision statement" },
    "20k": { name: "Categories", description: "Process categorization and horizontal flow" },
    "10k": { name: "Specialization", description: "Detailed vertical process flows" },
    "5k": { name: "Execution", description: "Step-by-step execution with tool integration" }
  },
  branches: [
    {
      id: "01",
      name: "First Process Branch",
      description: "Description of your first process branch",
      route: "/doctrine/first-process",
      tools: ["Tool1", "Tool2", "Tool3"],
      processes: [
        {
          id: "01",
          name: "Step 1",
          description: "Description of what this step does",
          tool: "Tool1",
          table: "your_table_1",
          unique_id_template: "${idPrefix}.01.05.01"
        },
        {
          id: "02", 
          name: "Step 2",
          description: "Description of what this step does",
          tool: "Tool2",
          table: "your_table_2",
          unique_id_template: "${idPrefix}.01.05.02"
        }
      ]
    },
    {
      id: "02",
      name: "Second Process Branch", 
      description: "Description of your second process branch",
      route: "/doctrine/second-process",
      tools: ["Tool4", "Tool5"],
      processes: [
        {
          id: "01",
          name: "Step 1",
          description: "Description of what this step does",
          tool: "Tool4", 
          table: "your_table_3",
          unique_id_template: "${idPrefix}.02.05.01"
        }
      ]
    },
    {
      id: "03",
      name: "Third Process Branch",
      description: "Description of your third process branch", 
      route: "/doctrine/third-process",
      tools: ["Tool6", "Tool7"],
      processes: [
        {
          id: "01",
          name: "Step 1", 
          description: "Description of what this step does",
          tool: "Tool6",
          table: "your_table_4",
          unique_id_template: "${idPrefix}.03.05.01"
        }
      ]
    }
  ]
};`;
}

function copyTemplateFiles(targetDir) {
  const templateFiles = [
    'src/lib/template/application-config.ts',
    'src/components/template/BartonTemplate.tsx',
    'src/components/template/ProcessTriangle.tsx', 
    'src/components/template/BranchTemplate.tsx'
  ];

  templateFiles.forEach(file => {
    const targetPath = path.join(targetDir, file);
    const targetDirPath = path.dirname(targetPath);
    
    if (!fs.existsSync(targetDirPath)) {
      fs.mkdirSync(targetDirPath, { recursive: true });
    }
    
    if (fs.existsSync(file)) {
      fs.copyFileSync(file, targetPath);
    }
  });
}

function generatePages(targetDir, routePrefix, appName) {
  // Generate index page
  const indexPage = `import { BartonTemplate } from '@/components/template/BartonTemplate';
import { ${routePrefix}Config } from '@/lib/template/app-config';

export default function ${capitalize(routePrefix)}Index() {
  return <BartonTemplate config={${routePrefix}Config} />;
}`;

  fs.writeFileSync(
    path.join(targetDir, `src/pages/${capitalize(routePrefix)}Index.tsx`),
    indexPage
  );

  // Generate doctrine map page  
  const doctrineMapPage = `import { ProcessTriangle } from '@/components/template/ProcessTriangle';
import { ${routePrefix}Config } from '@/lib/template/app-config';

export default function ${capitalize(routePrefix)}DoctrineMap() {
  return <ProcessTriangle config={${routePrefix}Config} />;
}`;

  fs.writeFileSync(
    path.join(targetDir, `src/pages/${capitalize(routePrefix)}DoctrineMap.tsx`),
    doctrineMapPage
  );

  // Generate example routes file
  const routesExample = `// Add these routes to your App.tsx:

import ${capitalize(routePrefix)}Index from './pages/${capitalize(routePrefix)}Index';
import ${capitalize(routePrefix)}DoctrineMap from './pages/${capitalize(routePrefix)}DoctrineMap';

// In your Routes component:
<Route path="/${routePrefix}" element={<${capitalize(routePrefix)}Index />} />
<Route path="/${routePrefix}/doctrine-map" element={<${capitalize(routePrefix)}DoctrineMap />} />

// TODO: Add branch detail pages for each process branch`;

  fs.writeFileSync(
    path.join(targetDir, 'ROUTES.txt'),
    routesExample
  );
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Run the generator
generateApp().catch(console.error);`;