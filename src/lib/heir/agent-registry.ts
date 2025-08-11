import { Agent, AgentRole } from './types';

export const agentRegistry: Agent[] = [
  {
    id: 'master-orchestrator',
    name: 'Master Orchestrator',
    role: 'orchestrator',
    category: 'global',
    description: 'Central command and control for all HEIR system operations',
    capabilities: [
      'System-wide coordination',
      'Resource allocation',
      'Task prioritization',
      'Agent lifecycle management'
    ],
    status: 'idle'
  },
  {
    id: 'ceo-orchestrator',
    name: 'CEO Orchestrator',
    role: 'orchestrator',
    category: 'global',
    description: 'High-level strategic decision making and oversight',
    capabilities: [
      'Strategic planning',
      'Performance monitoring',
      'Risk assessment',
      'Executive reporting'
    ],
    status: 'idle'
  },
  {
    id: 'data-orchestrator',
    name: 'Data Orchestrator',
    role: 'orchestrator',
    category: 'global',
    description: 'Manages data flow and processing across the system',
    capabilities: [
      'Data pipeline management',
      'ETL operations',
      'Data validation',
      'Cache management'
    ],
    status: 'idle'
  },
  {
    id: 'integration-orchestrator',
    name: 'Integration Orchestrator',
    role: 'orchestrator',
    category: 'global',
    description: 'Coordinates external service integrations',
    capabilities: [
      'API management',
      'Service discovery',
      'Rate limiting',
      'Authentication handling'
    ],
    status: 'idle'
  },
  {
    id: 'backend-manager',
    name: 'Backend Manager',
    role: 'manager',
    category: 'global',
    description: 'Manages backend infrastructure and services',
    capabilities: [
      'Service health monitoring',
      'Load balancing',
      'Database operations',
      'Cache management'
    ],
    status: 'idle'
  },
  {
    id: 'deployment-manager',
    name: 'Deployment Manager',
    role: 'manager',
    category: 'global',
    description: 'Handles deployment and release management',
    capabilities: [
      'CI/CD pipeline management',
      'Version control',
      'Rollback operations',
      'Environment management'
    ],
    status: 'idle'
  },
  {
    id: 'integration-manager',
    name: 'Integration Manager',
    role: 'manager',
    category: 'global',
    description: 'Manages third-party service integrations',
    capabilities: [
      'Service configuration',
      'Credential management',
      'Webhook handling',
      'Error recovery'
    ],
    status: 'idle'
  },
  {
    id: 'error-analyst',
    name: 'Error Analyst',
    role: 'specialist',
    category: 'global',
    description: 'Analyzes and resolves system errors',
    capabilities: [
      'Error pattern recognition',
      'Root cause analysis',
      'Solution recommendation',
      'Error logging'
    ],
    status: 'idle'
  },
  {
    id: 'neon-integrator',
    name: 'Neon Database Integrator',
    role: 'specialist',
    category: 'global',
    description: 'Specialized in Neon database operations',
    capabilities: [
      'Database provisioning',
      'Query optimization',
      'Backup management',
      'Performance tuning'
    ],
    status: 'idle'
  },
  {
    id: 'stripe-handler',
    name: 'Stripe Payment Handler',
    role: 'specialist',
    category: 'global',
    description: 'Manages Stripe payment processing',
    capabilities: [
      'Payment processing',
      'Subscription management',
      'Invoice generation',
      'Webhook handling'
    ],
    status: 'idle'
  },
  {
    id: 'apify-integrator',
    name: 'Apify Integration Specialist',
    role: 'specialist',
    category: 'global',
    description: 'Handles Apify web scraping operations',
    capabilities: [
      'Actor management',
      'Scraping configuration',
      'Data extraction',
      'Result processing'
    ],
    status: 'idle'
  },
  {
    id: 'firecrawl-scraper',
    name: 'Firecrawl Scraper',
    role: 'specialist',
    category: 'global',
    description: 'Specialized in Firecrawl web scraping',
    capabilities: [
      'Site crawling',
      'Content extraction',
      'Data structuring',
      'Rate limit handling'
    ],
    status: 'idle'
  }
];

export function getAgentById(id: string): Agent | undefined {
  return agentRegistry.find(agent => agent.id === id);
}

export function getAgentsByRole(role: AgentRole): Agent[] {
  return agentRegistry.filter(agent => agent.role === role);
}

export function getAgentsByCategory(category: string): Agent[] {
  return agentRegistry.filter(agent => agent.category === category);
}