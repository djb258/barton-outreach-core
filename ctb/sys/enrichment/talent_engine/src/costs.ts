/**
 * Cost Metadata
 * =============
 * Per-agent cost definitions for the Talent Engine.
 * Used by cost guardrails to track and limit spend.
 */

/**
 * Per-agent cost in USD.
 */
export const agentCosts = {
  LinkedInFinderAgent: 0.01,       // Proxycurl
  PublicScannerAgent: 0.005,       // ScraperAPI/Firecrawl normalized
  PatternAgent: 0,                 // Hunter patterns (flat fee)
  EmailGeneratorAgent: 0.001,      // VitaMail verification
  TitleCompanyAgent: 0.01,         // Proxycurl person lookup
  HashAgent: 0                     // Free internal operation
} as const;

/**
 * Agent names as a type.
 */
export type AgentName = keyof typeof agentCosts;

/**
 * Get the cost for a specific agent.
 * @param agentName - Name of the agent
 * @returns Cost in USD
 */
export function getAgentCost(agentName: AgentName): number {
  return agentCosts[agentName];
}

/**
 * Check if an agent name is valid.
 * @param name - Name to check
 * @returns true if valid agent name
 */
export function isValidAgentName(name: string): name is AgentName {
  return name in agentCosts;
}
