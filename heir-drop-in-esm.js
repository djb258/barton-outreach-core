#!/usr/bin/env node

/**
 * HEIR Agent System - Drop-in Setup (ES Module Version)
 * 
 * Usage: Just drop this file into any existing project and run:
 * node heir-drop-in-esm.js
 * 
 * This will:
 * 1. Create the .claude/agents structure
 * 2. Generate project-config.json template
 * 3. Set up HEIR system without disrupting existing code
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🏗️ Setting up HEIR Agent System - Skyscraper Construction Model...');

// Create skyscraper directory structure
const dirs = [
  '.claude',
  '.claude/agents',
  '.claude/agents/meta_system',
  '.claude/agents/domain_orchestrators',
  '.claude/agents/specialist_library',
  '.heir',
  '.heir/institutional_knowledge',
  '.heir/orbt_logs',
  '.heir/project_configs'
];

dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`✅ Created ${dir}/`);
  }
});

// Create skyscraper project config template
const configTemplate = {
  "// PROJECT OVERVIEW": "=== FILL THIS OUT FIRST ===",
  "project_name": path.basename(process.cwd()),
  "project_description": "Barton Outreach Core - A modern React application with HEIR agent system integration",
  "project_type": "complex",
  "architecture_model": "skyscraper_construction",
  
  "// WHAT TO BUILD": "=== PROJECT REQUIREMENTS ===",
  "what_you_want": "A comprehensive outreach platform with HEIR agent system integration for automated operations, data management, and intelligent coordination",
  "success_looks_like": [
    "Users can access outreach tools and resources",
    "HEIR agents coordinate data collection and processing",
    "System provides intelligent insights and automation",
    "Seamless integration between React frontend and HEIR backend"
  ],
  "constraints": {
    "budget": "Cost-effective with scalable architecture",
    "timeline": "Iterative development with continuous improvement",
    "must_use_technologies": ["React", "TypeScript", "Vite", "HEIR Agent System"],
    "cannot_use": ["Legacy frameworks", "Proprietary lock-in solutions"]
  },

  "// DPR SYSTEM INTEGRATION": "=== YOUR DOCTRINE SYSTEM ===",
  "dpr_system": {
    "unique_id_format": "[DB].[SUBHIVE].[MICROPROCESS].[TOOL].[ALTITUDE].[STEP]",
    "section_number_format": "[database].[subhive].[subsubhive].[section].[sequence]",
    "process_id_style": "Verb + Object (e.g., Load CSV, Generate Report)",
    "orbt_enabled": true,
    "orbt_protocol": "3_strike_escalation_with_institutional_knowledge",
    "schema_enforcement": "STAMPED/SPVPET/STACKED",
    "doctrine_enforcement_level": "strict",
    "institutional_knowledge_enabled": true,
    "cross_project_learning": true
  },

  "// SKYSCRAPER CONSTRUCTION AGENTS": "=== AGENT ACTIVATION (set to true for needed agents) ===",
  "agents_needed": {
    "// LEVEL 0: Meta-System (Always Required)": "",
    "master_orchestrator": {
      "use_this_agent": true,
      "role": "building_superintendent",
      "why": "Always needed - coordinates all domain orchestrators like a construction superintendent"
    },
    
    "system_orchestrator": {
      "use_this_agent": true,
      "role": "dpr_doctrine_enforcement",
      "why": "Always needed - enforces your DPR doctrine system across all agents"
    },

    "heir_claude_code_specialist": {
      "use_this_agent": true,
      "role": "claude_code_automation", 
      "why": "Always needed - automates all Claude Code operations and HEIR system setup"
    },

    "// LEVEL 1: Domain Orchestrators (Floor Managers)": "",
    
    "project_planner": {
      "use_this_agent": true,
      "why": "Complex outreach platform with multiple phases and features"
    },

    "backend_manager": {
      "use_this_agent": true,
      "why": "Need APIs, databases, and server logic for outreach operations",
      "what_to_build": "Backend services for data management, user authentication, and outreach coordination"
    },
    
    "integration_manager": {
      "use_this_agent": true,
      "why": "Need external APIs, data pipelines, and outreach tools integration",
      "what_to_integrate": "Email services, CRM systems, analytics platforms, and outreach automation tools"
    },
    
    "deployment_manager": {
      "use_this_agent": true,
      "why": "Need hosting, CI/CD, and infrastructure for production deployment",
      "where_to_deploy": "Vercel, Netlify, or similar modern hosting platform"
    },

    "neon_database": {
      "use_this_agent": true,
      "why": "Need PostgreSQL database for user data, outreach records, and analytics",
      "database_needs": "User profiles, outreach campaigns, contact lists, analytics data, and system logs"
    },
    
    "stripe_payments": {
      "use_this_agent": false,
      "why": "May need payment processing for premium features",
      "payment_details": "Subscription tiers for advanced outreach tools and features"
    },
    
    "web_scraping": {
      "use_this_agent": true,
      "why": "Need to collect outreach data and contact information",
      "scraping_targets": "Professional networks, business directories, and outreach platforms"
    },
    
    "orbt_monitor": {
      "use_this_agent": true,
      "why": "Production systems need real-time monitoring and error logging",
      "monitoring_requirements": "Real-time dashboard, global error logging, automated escalation"
    },
    
    "error_handling": {
      "use_this_agent": true,
      "why": "Need advanced error handling and monitoring for outreach operations",
      "error_requirements": "API failures, data validation errors, outreach delivery issues, and system performance problems"
    }
  },

  "// TECHNICAL DETAILS": "=== FILL OUT FOR ACTIVE AGENTS ONLY ===",
  "technical_specs": {
    "backend_details": {
      "database_schema": "Users, campaigns, contacts, analytics, outreach_logs, system_config",
      "api_endpoints": ["/api/users", "/api/campaigns", "/api/contacts", "/api/analytics", "/api/outreach"],
      "authentication": "Email/password with optional OAuth (Google, LinkedIn)"
    },
    
    "integration_details": {
      "external_apis": ["Email services (SendGrid, Mailgun)", "CRM systems", "Analytics platforms", "Social media APIs"],
      "data_flows": "Real-time data synchronization between frontend, backend, and external services",
      "rate_limits": "Respect API rate limits for all external services"
    },
    
    "deployment_details": {
      "hosting_platform": "Vercel for frontend, Render for backend services",
      "environment_variables": "Database URLs, API keys, service credentials, monitoring endpoints",
      "monitoring_needs": "Application performance, error rates, user engagement, outreach success metrics"
    },
    
    "database_details": {
      "tables_needed": ["users", "campaigns", "contacts", "outreach_logs", "analytics", "system_config"],
      "relationships": "Users have campaigns, campaigns have contacts, all activities are logged",
      "performance_needs": "Fast query response for real-time dashboard updates"
    },
    
    "payment_details": {
      "payment_types": ["subscription", "usage-based"],
      "pricing_tiers": "Free tier, Pro tier with advanced features, Enterprise tier with custom limits",
      "webhook_handling": "Subscription management, usage tracking, and billing notifications"
    },
    
    "scraping_details": {
      "target_websites": ["LinkedIn", "Professional directories", "Business databases"],
      "data_to_extract": "Contact information, professional details, company information",
      "scraping_frequency": "Scheduled daily/weekly based on campaign needs",
      "ethical_limits": "Respect robots.txt, rate limiting, and data privacy regulations"
    },
    
    "monitoring_details": {
      "dashboard_enabled": true,
      "error_log_retention": "90 days",
      "escalation_channels": ["email", "slack"],
      "orbt_compliance": true,
      "performance_tracking": true,
      "training_logs": true
    }
  },

  "system": {
    "entry_point": "system-orchestrator",
    "user_interface": "heir-claude-code-specialist",
    "project_coordination": "master-orchestrator",
    "auto_repair": true,
    "orbt_enabled": true,
    "dpr_compliant": true,
    "session_tracking": true,
    "created_timestamp": new Date().toISOString(),
    "project_root": process.cwd(),
    "heir_version": "2.0.0"
  }
};

// Write config file
const configPath = 'heir-project-config.json';
if (!fs.existsSync(configPath)) {
  fs.writeFileSync(configPath, JSON.stringify(configTemplate, null, 2));
  console.log(`✅ Created ${configPath}`);
} else {
  console.log(`⚠️  ${configPath} already exists, skipping...`);
}

// Create .gitignore entry if needed
const gitignorePath = '.gitignore';
const gitignoreEntry = '\n# HEIR Agent System\n.claude/\nheir-project-config.json\n';

if (fs.existsSync(gitignorePath)) {
  const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
  if (!gitignoreContent.includes('HEIR Agent System')) {
    fs.appendFileSync(gitignorePath, gitignoreEntry);
    console.log('✅ Updated .gitignore');
  }
} else {
  fs.writeFileSync(gitignorePath, gitignoreEntry);
  console.log('✅ Created .gitignore');
}

console.log('\n🏗️ HEIR Skyscraper Construction System setup complete!');
console.log('\n📋 Skyscraper Configuration Template Created:');
console.log('✅ Master Orchestrator (Building Superintendent) enabled');
console.log('✅ DPR doctrine system with 3-Strike ORBT protocol');
console.log('✅ Institutional knowledge system for cross-project learning');
console.log('✅ Domain Orchestrators (Floor Managers) ready for assignment');
console.log('✅ Specialist Library (Reusable Workforce Pool) configured');
console.log('✅ Complete technical specification templates');
console.log('\n🚀 Next steps:');
console.log('1. Review heir-project-config.json and customize for your specific needs');
console.log('2. Activate needed Domain Orchestrators (Data, Payment, Integration, Platform)');
console.log('3. Specialists will be assigned automatically by Domain Orchestrators'); 
console.log('4. Bring completed config to Claude Code with HEIR Claude Code Specialist');
console.log('5. Say "Set up my HEIR project" - complete skyscraper construction automated!');
console.log('\n🏗️ Project:', path.basename(process.cwd()));
console.log('🏗️ HEIR Version: 2.0.0 Skyscraper Construction Model');
console.log('🧠 Features: Master Orchestrator + Domain Orchestrators + Specialist Library');
console.log('⚡ Protocol: 3-Strike ORBT with Institutional Knowledge');
console.log('🔄 Learning: Cross-project expertise that compounds over time');
