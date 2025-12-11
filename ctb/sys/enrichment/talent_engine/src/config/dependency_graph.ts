/**
 * Dependency Graph Configuration
 * ==============================
 * Defines agent execution order and dependencies within each node.
 *
 * This enforces the Hub-and-Spoke architecture principle:
 * - Agents must run in a specific order
 * - Dependencies must be satisfied before an agent can run
 * - Prevents out-of-order execution that could produce invalid data
 *
 * The Golden Rule: company_valid and person_company_valid must be set
 * before email generation can proceed.
 */

import { FailureNode, FailureAgentType } from "../models/FailureRecord";

/**
 * Node dependency graph structure.
 */
export interface NodeDependencies {
  /** Map of agent -> required predecessor agents */
  requiredBefore: Record<string, string[]>;
}

/**
 * Full dependency graph across all nodes.
 */
export const DEPENDENCY_GRAPH: Record<string, NodeDependencies> = {
  /**
   * COMPANY_HUB - Master node (all data anchors here)
   *
   * Execution order:
   * 1. CompanyFuzzyMatchAgent - Must match company to master list first
   * 2. PatternAgent - Discover email pattern after company confirmed
   * 3. EmailGeneratorAgent - Generate email after pattern known
   * 4. EmailVerificationAgent - Verify email after generation
   */
  company_hub: {
    requiredBefore: {
      // PatternAgent requires company to be fuzzy matched first
      PatternAgent: ["CompanyFuzzyMatchAgent"],

      // EmailGeneratorAgent requires:
      // - Company matched (for domain)
      // - Pattern discovered (for email format)
      EmailGeneratorAgent: ["CompanyFuzzyMatchAgent", "PatternAgent"],

      // EmailVerificationAgent requires email to exist
      EmailVerificationAgent: ["EmailGeneratorAgent"],

      // MissingSlotAgent can run after company is matched
      MissingSlotAgent: ["CompanyFuzzyMatchAgent"],
    },
  },

  /**
   * PEOPLE_NODE - Person enrichment spoke
   *
   * Execution order:
   * 1. PeopleFuzzyMatchAgent - Match person to existing records
   * 2. TitleCompanyAgent - Get current title/company from LinkedIn
   * 3. LinkedInFinderAgent - Resolve LinkedIn URL if not known
   * 4. PublicScannerAgent - Check profile accessibility
   * 5. MovementHashAgent - Generate movement detection hash
   */
  people_node: {
    requiredBefore: {
      // PeopleFuzzyMatchAgent requires company to be matched first
      // (Company Hub must complete before People Node)
      PeopleFuzzyMatchAgent: ["CompanyFuzzyMatchAgent"],

      // TitleCompanyAgent requires person matched first
      TitleCompanyAgent: ["PeopleFuzzyMatchAgent"],

      // LinkedInFinderAgent requires title/company check
      LinkedInFinderAgent: ["TitleCompanyAgent"],

      // PublicScannerAgent requires LinkedIn URL
      PublicScannerAgent: ["LinkedInFinderAgent"],

      // MovementHashAgent requires all person data
      MovementHashAgent: ["TitleCompanyAgent", "LinkedInFinderAgent"],
    },
  },

  /**
   * DOL_NODE - Department of Labor data spoke
   *
   * Execution order:
   * 1. DOLSyncAgent - Sync Form 5500 data
   */
  dol_node: {
    requiredBefore: {
      // DOLSyncAgent requires company to be matched first
      DOLSyncAgent: ["CompanyFuzzyMatchAgent"],
    },
  },

  /**
   * BIT_NODE - Buyer Intent Tool spoke
   *
   * Execution order:
   * 1. BITScoreAgent - Calculate buyer intent score
   * 2. ChurnDetectorAgent - Detect potential churn signals
   */
  bit_node: {
    requiredBefore: {
      // BITScoreAgent requires title/company data
      BITScoreAgent: ["TitleCompanyAgent"],

      // ChurnDetectorAgent requires BIT score
      ChurnDetectorAgent: ["BITScoreAgent"],
    },
  },
};

/**
 * Cross-node dependencies.
 * These agents require specific agents from OTHER nodes to complete first.
 */
export const CROSS_NODE_DEPENDENCIES: Record<string, string[]> = {
  // People Node requires Company Hub completion
  PeopleFuzzyMatchAgent: ["CompanyFuzzyMatchAgent"],
  TitleCompanyAgent: ["CompanyFuzzyMatchAgent"],
  LinkedInFinderAgent: ["CompanyFuzzyMatchAgent"],

  // DOL Node requires Company Hub completion
  DOLSyncAgent: ["CompanyFuzzyMatchAgent"],

  // BIT Node requires People Node completion
  BITScoreAgent: ["CompanyFuzzyMatchAgent", "TitleCompanyAgent"],
  ChurnDetectorAgent: ["CompanyFuzzyMatchAgent", "TitleCompanyAgent", "BITScoreAgent"],

  // Email agents require Golden Rule validation
  EmailGeneratorAgent: ["CompanyFuzzyMatchAgent", "PatternAgent", "TitleCompanyAgent"],
  EmailVerificationAgent: ["CompanyFuzzyMatchAgent", "EmailGeneratorAgent"],
};

/**
 * Agent execution order within each node (for sequential processing).
 */
export const AGENT_EXECUTION_ORDER: Record<string, string[]> = {
  company_hub: [
    "CompanyFuzzyMatchAgent",
    "PatternAgent",
    "MissingSlotAgent",
    "EmailGeneratorAgent",
    "EmailVerificationAgent",
  ],

  people_node: [
    "PeopleFuzzyMatchAgent",
    "TitleCompanyAgent",
    "LinkedInFinderAgent",
    "PublicScannerAgent",
    "MovementHashAgent",
  ],

  dol_node: ["DOLSyncAgent"],

  bit_node: ["BITScoreAgent", "ChurnDetectorAgent"],
};

/**
 * Node execution order (which nodes depend on which).
 */
export const NODE_EXECUTION_ORDER: FailureNode[] = [
  "COMPANY_HUB", // Must run first
  "PEOPLE_NODE", // Requires Company Hub
  "DOL_NODE", // Requires Company Hub
  "BIT_NODE", // Requires People Node
];

/**
 * Check if an agent's dependencies are satisfied.
 */
export function validateDependencies(
  nodeName: string,
  agentName: string,
  completedAgents: string[]
): { valid: boolean; missing: string[] } {
  // Check node-level dependencies
  const nodeDeps = DEPENDENCY_GRAPH[nodeName]?.requiredBefore?.[agentName] || [];

  // Check cross-node dependencies
  const crossDeps = CROSS_NODE_DEPENDENCIES[agentName] || [];

  // Combine all dependencies
  const allDeps = [...new Set([...nodeDeps, ...crossDeps])];

  // Find missing dependencies
  const missing = allDeps.filter((dep) => !completedAgents.includes(dep));

  return {
    valid: missing.length === 0,
    missing,
  };
}

/**
 * Get all dependencies for an agent (direct and transitive).
 */
export function getAllDependencies(agentName: string): string[] {
  const visited = new Set<string>();
  const result: string[] = [];

  function collect(agent: string): void {
    if (visited.has(agent)) return;
    visited.add(agent);

    // Get direct dependencies from all nodes
    for (const node of Object.values(DEPENDENCY_GRAPH)) {
      const deps = node.requiredBefore[agent] || [];
      for (const dep of deps) {
        collect(dep);
        if (!result.includes(dep)) {
          result.push(dep);
        }
      }
    }

    // Get cross-node dependencies
    const crossDeps = CROSS_NODE_DEPENDENCIES[agent] || [];
    for (const dep of crossDeps) {
      collect(dep);
      if (!result.includes(dep)) {
        result.push(dep);
      }
    }
  }

  collect(agentName);
  return result;
}

/**
 * Get the next agent to run for a node.
 */
export function getNextAgent(nodeName: string, completedAgents: string[]): string | null {
  const order = AGENT_EXECUTION_ORDER[nodeName];
  if (!order) return null;

  for (const agent of order) {
    // Skip already completed
    if (completedAgents.includes(agent)) continue;

    // Check if dependencies are met
    const { valid } = validateDependencies(nodeName, agent, completedAgents);
    if (valid) {
      return agent;
    }
  }

  return null;
}

/**
 * Check if a node is complete (all agents have run).
 */
export function isNodeComplete(nodeName: string, completedAgents: string[]): boolean {
  const order = AGENT_EXECUTION_ORDER[nodeName];
  if (!order) return true;

  return order.every((agent) => completedAgents.includes(agent));
}

/**
 * Get the node that should run next based on completion status.
 */
export function getNextNode(completedAgents: string[]): FailureNode | null {
  for (const node of NODE_EXECUTION_ORDER) {
    const nodeLower = node.toLowerCase().replace("_", "_") as string;

    // Check if node has any incomplete agents
    if (!isNodeComplete(nodeLower, completedAgents)) {
      return node;
    }
  }

  return null;
}

/**
 * Dependency validation error.
 */
export class DependencyValidationError extends Error {
  constructor(
    public agentName: string,
    public missingDependencies: string[]
  ) {
    super(
      `Agent "${agentName}" cannot run: missing dependencies [${missingDependencies.join(", ")}]`
    );
    this.name = "DependencyValidationError";
  }
}

/**
 * Strict validation that throws on failure.
 */
export function validateDependenciesStrict(
  nodeName: string,
  agentName: string,
  completedAgents: string[]
): void {
  const { valid, missing } = validateDependencies(nodeName, agentName, completedAgents);

  if (!valid) {
    throw new DependencyValidationError(agentName, missing);
  }
}
