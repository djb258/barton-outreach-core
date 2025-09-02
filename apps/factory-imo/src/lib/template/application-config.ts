export interface ProcessStep {
  id: string;
  name: string;
  description: string;
  tool?: string;
  table?: string;
  unique_id_template: string;
}

export interface ApplicationBranch {
  id: string;
  name: string;
  description: string;
  tools: string[];
  processes: ProcessStep[];
  route: string;
  subagents?: string[];
  doctrines?: string[];
}

export interface ApplicationConfig {
  application: {
    name: string;
    domain: string;
    description: string;
    id_prefix: string;
    hero_icon: string;
  };
  branches: ApplicationBranch[];
  altitudes: {
    "30k": { name: string; description: string; };
    "20k": { name: string; description: string; };
    "10k": { name: string; description: string; };
    "5k": { name: string; description: string; };
  };
}

// Outreach Core Configuration - First Template Instance
export const outreachConfig: ApplicationConfig = {
  application: {
    name: "Barton Outreach Core",
    domain: "Marketing > Outreach",
    description: "Powered by the HEIR Agent System - Hierarchical Execution Intelligence & Repair",
    id_prefix: "01.04.01",
    hero_icon: "Building2"
  },
  altitudes: {
    "30k": { 
      name: "Vision", 
      description: "Strategic overview and vision statement" 
    },
    "20k": { 
      name: "Categories", 
      description: "Process categorization and horizontal flow" 
    },
    "10k": { 
      name: "Specialization", 
      description: "Detailed vertical process flows" 
    },
    "5k": { 
      name: "Execution", 
      description: "Step-by-step execution with tool integration" 
    }
  },
  branches: [
    {
      id: "00",
      name: "Company & People Ingestion",
      description: "Initial data ingestion from CSV/Excel files into Neon database",
      route: "/doctrine/data-ingestion",
      tools: ["CSV Parser", "Excel Parser", "Neon", "Render API"],
      subagents: ["File Processing Agent", "Data Validation Agent", "Database Ingestion Agent"],
      doctrines: ["Data Format Validation", "Batch Processing", "Error Handling", "Schema Compliance"],
      processes: [
        {
          id: "01",
          name: "Upload Data Files",
          description: "Upload CSV or Excel files containing company/people data",
          tool: "File Upload",
          table: "staging_upload",
          unique_id_template: "01.04.01.00.05.01"
        },
        {
          id: "02",
          name: "Parse & Validate",
          description: "Parse files and validate data structure",
          tool: "CSV/Excel Parser",
          table: "staging_validation",
          unique_id_template: "01.04.01.00.05.02"
        },
        {
          id: "03",
          name: "Preview Data",
          description: "Preview parsed data before ingestion",
          tool: "Data Preview",
          table: "staging_preview",
          unique_id_template: "01.04.01.00.05.03"
        },
        {
          id: "04",
          name: "Ingest to Database",
          description: "Send validated data to Neon database via Render API",
          tool: "Render API",
          table: "company.marketing_company / people.marketing_people",
          unique_id_template: "01.04.01.00.05.04"
        },
        {
          id: "05",
          name: "Track Results",
          description: "Monitor ingestion success/failure rates",
          tool: "Monitoring",
          table: "ingestion_logs",
          unique_id_template: "01.04.01.00.05.05"
        }
      ]
    },
    {
      id: "01",
      name: "Lead Intake & Validation",
      description: "Complete lead acquisition, scraping, and validation workflow",
      route: "/doctrine/lead-intake",
      tools: ["Apollo", "Apify", "MillionVerifier", "Neon"],
      subagents: ["Data Acquisition Agent", "Validation Agent", "Database Agent"],
      doctrines: ["Lead Qualification", "Data Quality", "GDPR Compliance", "Rate Limiting"],
      processes: [
        {
          id: "01",
          name: "Acquire Companies",
          description: "Pull company list by state from Apollo API",
          tool: "Apollo",
          table: "marketing_company_intake",
          unique_id_template: "01.04.01.01.05.01"
        },
        {
          id: "02", 
          name: "Insert Companies",
          description: "Store company data in Neon database",
          tool: "Neon",
          table: "marketing_company_intake", 
          unique_id_template: "01.04.01.01.05.02"
        },
        {
          id: "03",
          name: "Scrape Executives", 
          description: "Extract CEO/CFO/HR contacts via Apify",
          tool: "Apify",
          table: "staging_executives",
          unique_id_template: "01.04.01.01.05.03"
        },
        {
          id: "04",
          name: "Validate Contacts",
          description: "Validate email addresses using MillionVerifier",
          tool: "MillionVerifier", 
          table: "people",
          unique_id_template: "01.04.01.01.05.04"
        },
        {
          id: "05",
          name: "Insert Validated Contacts",
          description: "Store validated contacts in people table",
          tool: "Neon",
          table: "people",
          unique_id_template: "01.04.01.01.05.05"
        },
        {
          id: "06", 
          name: "Link People to Company",
          description: "Establish relationships between people and companies",
          tool: "Neon",
          table: "people ↔ marketing_company_intake",
          unique_id_template: "01.04.01.01.05.06"
        }
      ]
    },
    {
      id: "02",
      name: "Message Generation (Agent)", 
      description: "AI-powered message composition and personalization",
      route: "/doctrine/message-generation",
      tools: ["AI Agent", "Templates", "Personalization", "Neon"],
      subagents: ["Content Creation Agent", "Personalization Agent", "Template Manager", "Quality Assurance Agent"],
      doctrines: ["Message Personalization", "Brand Voice", "CAN-SPAM Compliance", "A/B Testing"],
      processes: [
        {
          id: "01",
          name: "Compose Outreach Message",
          description: "Generate personalized messages using AI agent",
          tool: "Agent",
          table: "outreach_message_registry",
          unique_id_template: "01.04.01.02.05.01"
        },
        {
          id: "02",
          name: "Apply Generic Template",
          description: "Fallback to generic template if personalization fails", 
          tool: "Agent",
          table: "outreach_message_registry",
          unique_id_template: "01.04.01.02.05.02"
        },
        {
          id: "03",
          name: "Record Message Variant",
          description: "Log message variant, role, and version tag",
          tool: "Neon", 
          table: "outreach_message_registry",
          unique_id_template: "01.04.01.02.05.03"
        },
        {
          id: "04",
          name: "Store Message Payload",
          description: "Store message payload for campaign deployment",
          tool: "Neon",
          table: "outreach_message_registry", 
          unique_id_template: "01.04.01.02.05.04"
        }
      ]
    },
    {
      id: "03", 
      name: "Campaign Execution & Telemetry",
      description: "Deploy campaigns and track performance metrics",
      route: "/doctrine/campaign-execution", 
      tools: ["Instantly", "HeyReach", "Tracking", "Dashboard"],
      subagents: ["Campaign Manager Agent", "Delivery Agent", "Analytics Agent", "Performance Monitor"],
      doctrines: ["Campaign Optimization", "Deliverability", "Performance Tracking", "ROI Analysis"],
      processes: [
        {
          id: "01",
          name: "Publish Messages",
          description: "Deploy messages via Instantly/HeyReach APIs",
          tool: "Instantly/HeyReach",
          table: "campaign_run_log",
          unique_id_template: "01.04.01.03.05.01"
        },
        {
          id: "02", 
          name: "Track Events",
          description: "Monitor sends, opens, replies, bounces",
          tool: "Instantly/HeyReach",
          table: "campaign_run_log", 
          unique_id_template: "01.04.01.03.05.02"
        },
        {
          id: "03",
          name: "Update Lead Status",
          description: "Update lead and campaign status in database",
          tool: "Neon",
          table: "marketing_company_intake / people",
          unique_id_template: "01.04.01.03.05.03"
        },
        {
          id: "04",
          name: "Surface Live Metrics", 
          description: "Display real-time metrics on command center dashboard",
          tool: "Dashboard",
          table: "command_center_metrics",
          unique_id_template: "01.04.01.03.05.04"
        }
      ]
    }
  ]
};