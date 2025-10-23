# Barton Doctrine Template - Example Configurations

## 📋 Ready-to-Use Application Examples

### 🎯 **Marketing > Outreach** (Implemented)
```typescript
export const marketingOutreachConfig: ApplicationConfig = {
  application: {
    name: "Barton Outreach Core",
    domain: "Marketing > Outreach", 
    description: "Powered by the HEIR Agent System",
    id_prefix: "01.04.01",
    hero_icon: "Building2"
  },
  branches: [
    {
      id: "01",
      name: "Lead Intake & Validation",
      description: "Complete lead acquisition, scraping, and validation workflow",
      route: "/doctrine/lead-intake",
      tools: ["Apollo", "Apify", "MillionVerifier", "Neon"],
      processes: [
        {
          id: "01", name: "Acquire Companies",
          description: "Pull company list by state from Apollo API",
          tool: "Apollo", table: "marketing_company_intake",
          unique_id_template: "01.04.01.01.05.01"
        },
        {
          id: "02", name: "Scrape Executives", 
          description: "Extract CEO/CFO/HR contacts via Apify",
          tool: "Apify", table: "staging_executives",
          unique_id_template: "01.04.01.01.05.03"
        },
        {
          id: "03", name: "Validate Contacts",
          description: "Validate email addresses using MillionVerifier", 
          tool: "MillionVerifier", table: "people",
          unique_id_template: "01.04.01.01.05.04"
        }
      ]
    },
    {
      id: "02",
      name: "Message Generation (Agent)",
      description: "AI-powered message composition and personalization",
      route: "/doctrine/message-generation", 
      tools: ["AI Agent", "Templates", "Personalization"],
      processes: [
        {
          id: "01", name: "Compose Outreach Message",
          description: "Generate personalized messages using AI agent",
          tool: "Agent", table: "outreach_message_registry",
          unique_id_template: "01.04.01.02.05.01"
        }
      ]
    },
    {
      id: "03",
      name: "Campaign Execution & Telemetry", 
      description: "Deploy campaigns and track performance metrics",
      route: "/doctrine/campaign-execution",
      tools: ["Instantly", "HeyReach", "Tracking"],
      processes: [
        {
          id: "01", name: "Publish Messages",
          description: "Deploy messages via Instantly/HeyReach APIs",
          tool: "Instantly/HeyReach", table: "campaign_run_log",
          unique_id_template: "01.04.01.03.05.01"
        }
      ]
    }
  ]
};
```

### 💼 **Sales > Pipeline Management**
```typescript
export const salesPipelineConfig: ApplicationConfig = {
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
      description: "Automated lead scoring and routing system",
      route: "/doctrine/lead-qualification",
      tools: ["CRM", "Scoring Engine", "Router", "Database"],
      processes: [
        {
          id: "01", name: "Score Leads", 
          description: "Calculate lead quality score using ML model",
          tool: "Scoring Engine", table: "lead_scores",
          unique_id_template: "02.01.01.01.05.01"
        },
        {
          id: "02", name: "Route to Sales Rep",
          description: "Assign qualified leads to appropriate sales rep",
          tool: "Router", table: "lead_assignments", 
          unique_id_template: "02.01.01.01.05.02"
        },
        {
          id: "03", name: "Update CRM",
          description: "Sync lead data and status with CRM system",
          tool: "CRM", table: "crm_sync_log",
          unique_id_template: "02.01.01.01.05.03"
        }
      ]
    },
    {
      id: "02",
      name: "Proposal Generation", 
      description: "AI-powered proposal creation and customization",
      route: "/doctrine/proposal-generation",
      tools: ["AI Engine", "Templates", "Legal Review", "E-signature"],
      processes: [
        {
          id: "01", name: "Generate Proposal",
          description: "Create customized proposal using AI and templates",
          tool: "AI Engine", table: "proposals",
          unique_id_template: "02.01.01.02.05.01"
        },
        {
          id: "02", name: "Legal Review",
          description: "Automated legal compliance check",
          tool: "Legal Review", table: "legal_approvals",
          unique_id_template: "02.01.01.02.05.02"
        }
      ]
    },
    {
      id: "03",
      name: "Deal Closing",
      description: "Contract management and deal finalization", 
      route: "/doctrine/deal-closing",
      tools: ["DocuSign", "Payment Gateway", "CRM", "Reporting"],
      processes: [
        {
          id: "01", name: "Send Contract",
          description: "Deploy contract via DocuSign for signatures",
          tool: "DocuSign", table: "contracts",
          unique_id_template: "02.01.01.03.05.01"
        },
        {
          id: "02", name: "Process Payment", 
          description: "Handle payment processing and invoicing",
          tool: "Payment Gateway", table: "transactions",
          unique_id_template: "02.01.01.03.05.02"
        }
      ]
    }
  ]
};
```

### ⚙️ **Operations > Workflow Automation** 
```typescript
export const operationsWorkflowConfig: ApplicationConfig = {
  application: {
    name: "Barton Operations Core",
    domain: "Operations > Workflow Automation",
    description: "Streamlined operations with intelligent automation",
    id_prefix: "03.02.01", 
    hero_icon: "Settings"
  },
  branches: [
    {
      id: "01",
      name: "Task Management",
      description: "Automated task assignment and progress tracking",
      route: "/doctrine/task-management", 
      tools: ["Project Manager", "Scheduler", "Notifications", "Database"],
      processes: [
        {
          id: "01", name: "Create Tasks",
          description: "Generate tasks from project requirements",
          tool: "Project Manager", table: "tasks",
          unique_id_template: "03.02.01.01.05.01"
        },
        {
          id: "02", name: "Assign Resources",
          description: "Auto-assign tasks based on availability and skills", 
          tool: "Scheduler", table: "task_assignments",
          unique_id_template: "03.02.01.01.05.02"
        },
        {
          id: "03", name: "Track Progress",
          description: "Monitor task completion and send status updates",
          tool: "Notifications", table: "progress_tracking", 
          unique_id_template: "03.02.01.01.05.03"
        }
      ]
    },
    {
      id: "02", 
      name: "Quality Control",
      description: "Automated quality assurance and approval workflows",
      route: "/doctrine/quality-control",
      tools: ["QA Engine", "Review System", "Approvals", "Feedback"],
      processes: [
        {
          id: "01", name: "Quality Check",
          description: "Automated quality assessment using predefined criteria",
          tool: "QA Engine", table: "quality_checks",
          unique_id_template: "03.02.01.02.05.01"
        }
      ]
    },
    {
      id: "03",
      name: "Delivery & Reporting", 
      description: "Output delivery and performance analytics",
      route: "/doctrine/delivery-reporting",
      tools: ["Delivery System", "Analytics", "Dashboard", "Alerts"],
      processes: [
        {
          id: "01", name: "Deliver Output",
          description: "Package and deliver completed work to client",
          tool: "Delivery System", table: "deliveries", 
          unique_id_template: "03.02.01.03.05.01"
        },
        {
          id: "02", name: "Generate Reports",
          description: "Create performance and analytics reports",
          tool: "Analytics", table: "reports",
          unique_id_template: "03.02.01.03.05.02"
        }
      ]
    }
  ]
};
```

### 🎓 **Education > Course Management**
```typescript
export const educationCourseConfig: ApplicationConfig = {
  application: {
    name: "Barton Education Core", 
    domain: "Education > Course Management",
    description: "Intelligent course creation and student engagement",
    id_prefix: "04.01.01",
    hero_icon: "GraduationCap"
  },
  branches: [
    {
      id: "01",
      name: "Content Creation",
      description: "AI-assisted course content generation and curation",
      route: "/doctrine/content-creation",
      tools: ["AI Content Generator", "Video Editor", "LMS", "Review"],
      processes: [
        {
          id: "01", name: "Generate Course Outline",
          description: "Create structured course curriculum using AI",
          tool: "AI Content Generator", table: "course_outlines",
          unique_id_template: "04.01.01.01.05.01"
        }
      ]
    },
    {
      id: "02", 
      name: "Student Engagement",
      description: "Personalized learning paths and progress tracking", 
      route: "/doctrine/student-engagement",
      tools: ["LMS", "Analytics", "Messaging", "Gamification"],
      processes: [
        {
          id: "01", name: "Track Progress",
          description: "Monitor student learning progress and engagement",
          tool: "Analytics", table: "student_progress",
          unique_id_template: "04.01.01.02.05.01"
        }
      ]
    },
    {
      id: "03",
      name: "Assessment & Certification",
      description: "Automated testing and certificate generation",
      route: "/doctrine/assessment-certification", 
      tools: ["Testing Engine", "Proctoring", "Certificates", "Blockchain"],
      processes: [
        {
          id: "01", name: "Create Assessments", 
          description: "Generate adaptive assessments based on learning objectives",
          tool: "Testing Engine", table: "assessments",
          unique_id_template: "04.01.01.03.05.01"
        }
      ]
    }
  ]
};
```

## 🎯 **Usage**

Simply copy any of these configurations and customize:
- Change `name`, `domain`, `description`
- Update `id_prefix` to your numbering scheme  
- Modify `branches` with your specific processes
- Adjust `tools` to match your tech stack
- Update `processes` with your workflow steps

**Each example gives you a complete, working business application in minutes!** 🚀