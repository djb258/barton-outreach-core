/**
 * MCP (Model Context Protocol) Service for HEIR Compliance
 * Integrates with garage-mcp for validation and subagent registry
 */

export interface MCPValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  heir_compliance: {
    schema_version: string;
    unique_id_present: boolean;
    process_id_present: boolean;
    blueprint_version_hash_present: boolean;
  };
}

export interface SubagentDefinition {
  id: string;
  bay: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive' | 'error';
}

export class MCPService {
  private baseUrl: string;
  private token?: string;

  constructor() {
    this.baseUrl = process.env.GARAGE_MCP_URL || 'http://localhost:7001';
    this.token = process.env.GARAGE_MCP_TOKEN;
  }

  /**
   * Validate SSOT manifest for HEIR compliance
   */
  async validateHEIRCompliance(ssotManifest: any): Promise<MCPValidationResult> {
    try {
      const response = await fetch(`${this.baseUrl}/heir/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.token && { 'Authorization': `Bearer ${this.token}` })
        },
        body: JSON.stringify({ ssot: ssotManifest })
      });

      if (!response.ok) {
        throw new Error(`MCP validation failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Transform response to our expected format
      return {
        valid: result.valid || false,
        errors: result.errors || [],
        warnings: result.warnings || [],
        heir_compliance: {
          schema_version: result.heir_compliance?.schema_version || 'unknown',
          unique_id_present: Boolean(result.heir_compliance?.unique_id_present),
          process_id_present: Boolean(result.heir_compliance?.process_id_present),
          blueprint_version_hash_present: Boolean(result.heir_compliance?.blueprint_version_hash_present)
        }
      };
    } catch (error) {
      console.error('MCP validation error:', error);
      
      // Fallback validation for offline mode
      return this.fallbackValidation(ssotManifest);
    }
  }

  /**
   * Get list of available subagents from registry
   */
  async getSubagents(): Promise<SubagentDefinition[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/subagents`, {
        headers: {
          ...(this.token && { 'Authorization': `Bearer ${this.token}` })
        }
      });

      if (!response.ok) {
        throw new Error(`Subagent registry failed: ${response.status}`);
      }

      const result = await response.json();
      return result.items || [];
    } catch (error) {
      console.error('Subagent registry error:', error);
      
      // Fallback subagents
      return this.getFallbackSubagents();
    }
  }

  /**
   * Stamp doctrine IDs on a manifest
   */
  async stampDoctrineIds(manifest: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/ssot/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.token && { 'Authorization': `Bearer ${this.token}` })
        },
        body: JSON.stringify({ ssot: manifest })
      });

      if (!response.ok) {
        throw new Error(`ID stamping failed: ${response.status}`);
      }

      const result = await response.json();
      return result.ssot || manifest;
    } catch (error) {
      console.error('ID stamping error:', error);
      
      // Fallback ID generation
      return this.fallbackIdStamping(manifest);
    }
  }

  /**
   * Log telemetry event to sidecar
   */
  async logEvent(eventType: string, payload: any, tags: Record<string, string> = {}): Promise<void> {
    try {
      const sidecarUrl = this.baseUrl.replace(':7001', ':8000');
      await fetch(`${sidecarUrl}/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: eventType,
          payload,
          tags: {
            source: 'barton-outreach-core',
            timestamp: new Date().toISOString(),
            ...tags
          }
        })
      });
    } catch (error) {
      console.warn('Telemetry logging failed:', error);
    }
  }

  /**
   * Fallback validation when MCP service is unavailable
   */
  private fallbackValidation(ssotManifest: any): MCPValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check basic structure
    if (!ssotManifest.meta) {
      errors.push('Missing meta section');
    } else {
      if (!ssotManifest.meta.app_name) {
        errors.push('Missing app_name in meta');
      }
    }

    if (!ssotManifest.doctrine) {
      warnings.push('Missing doctrine section');
    }

    const heirCompliance = {
      schema_version: ssotManifest.doctrine?.schema_version || 'unknown',
      unique_id_present: Boolean(ssotManifest.doctrine?.unique_id),
      process_id_present: Boolean(ssotManifest.doctrine?.process_id),
      blueprint_version_hash_present: Boolean(ssotManifest.doctrine?.blueprint_version_hash)
    };

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      heir_compliance: heirCompliance
    };
  }

  /**
   * Fallback subagents when registry is unavailable
   */
  private getFallbackSubagents(): SubagentDefinition[] {
    return [
      {
        id: 'database-specialist',
        bay: 'data',
        description: 'Database design and optimization specialist',
        capabilities: ['schema_design', 'query_optimization', 'data_modeling'],
        status: 'active'
      },
      {
        id: 'frontend-architect',
        bay: 'ui',
        description: 'Frontend architecture and component design',
        capabilities: ['react_components', 'ui_design', 'accessibility'],
        status: 'active'
      },
      {
        id: 'devops-engineer',
        bay: 'infrastructure',
        description: 'DevOps and infrastructure automation',
        capabilities: ['deployment', 'monitoring', 'scaling'],
        status: 'active'
      },
      {
        id: 'security-auditor',
        bay: 'security',
        description: 'Security analysis and vulnerability assessment',
        capabilities: ['code_audit', 'vulnerability_scan', 'compliance_check'],
        status: 'active'
      }
    ];
  }

  /**
   * Fallback ID stamping when MCP service is unavailable
   */
  private fallbackIdStamping(manifest: any): any {
    const now = new Date().toISOString();
    const hash = this.generateSimpleHash(`${manifest.meta?.app_name || 'unknown'}-${now}`);
    
    return {
      ...manifest,
      doctrine: {
        ...manifest.doctrine,
        unique_id: `shq-03-imo-1-${hash.substring(0, 8)}`,
        process_id: `proc-${hash.substring(0, 12)}`,
        blueprint_version_hash: hash,
        schema_version: 'HEIR/1.0',
        stamped_at: now
      }
    };
  }

  /**
   * Simple hash generation for fallback scenarios
   */
  private generateSimpleHash(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }
}