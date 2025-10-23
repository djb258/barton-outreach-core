import { IMOManifest } from './types';

export interface HEIRValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  metadata?: {
    unique_id?: string;
    process_id?: string;
    blueprint_version_hash?: string;
  };
}

export class HEIRIntegration {
  private mcpUrl: string;
  private sidecarUrl: string;

  constructor(
    mcpUrl: string = 'http://localhost:7001',
    sidecarUrl: string = 'http://localhost:8000'
  ) {
    this.mcpUrl = mcpUrl;
    this.sidecarUrl = sidecarUrl;
  }

  async validateManifest(manifest: IMOManifest): Promise<HEIRValidationResult> {
    try {
      const response = await fetch(`${this.mcpUrl}/heir/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ssot: manifest }),
      });

      if (!response.ok) {
        return {
          valid: false,
          errors: [`HEIR validation failed: ${response.statusText}`],
          warnings: [],
        };
      }

      const result = await response.json();
      return {
        valid: result.valid || true,
        errors: result.errors || [],
        warnings: result.warnings || [],
        metadata: result.metadata,
      };
    } catch (error) {
      console.error('HEIR validation error:', error);
      return {
        valid: false,
        errors: ['Failed to connect to HEIR validation service'],
        warnings: ['Running in offline mode - validation skipped'],
      };
    }
  }

  async logEvent(
    eventType: string,
    payload: Record<string, any>,
    tags?: Record<string, string>
  ): Promise<void> {
    try {
      await fetch(`${this.sidecarUrl}/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: eventType,
          payload,
          tags: tags || {},
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Failed to log event to sidecar:', error);
    }
  }

  async getRecentEvents(limit: number = 10): Promise<any[]> {
    try {
      const response = await fetch(`${this.sidecarUrl}/events/recent?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch events: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch recent events:', error);
      return [];
    }
  }

  generateUniqueId(prefix: string = '01.04.01'): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 7);
    return `${prefix}.${timestamp}.${random}`;
  }

  generateProcessId(appName: string, stage?: string): string {
    const cleanAppName = appName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const timestamp = new Date().toISOString().replace(/[^0-9]/g, '').substring(0, 14);
    return stage ? `${cleanAppName}_${stage}_${timestamp}` : `${cleanAppName}_${timestamp}`;
  }

  generateBlueprintHash(manifest: IMOManifest): string {
    const content = JSON.stringify({
      app: manifest.meta.app_name,
      buckets: Object.keys(manifest.buckets),
      stages: Object.values(manifest.buckets).flatMap(b => b?.stages.map(s => s.id) || []),
    });
    
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    
    return Math.abs(hash).toString(16).padStart(8, '0');
  }

  enrichManifestWithDoctrine(manifest: IMOManifest): IMOManifest {
    const enriched = { ...manifest };
    
    if (!enriched.doctrine) {
      enriched.doctrine = {};
    }

    enriched.doctrine = {
      ...enriched.doctrine,
      unique_id: enriched.doctrine.unique_id || this.generateUniqueId(),
      process_id: enriched.doctrine.process_id || this.generateProcessId(manifest.meta.app_name, manifest.meta.stage),
      blueprint_version_hash: enriched.doctrine.blueprint_version_hash || this.generateBlueprintHash(manifest),
      schema_version: enriched.doctrine.schema_version || 'HEIR/1.0',
    };

    return enriched;
  }

  async trackManifestChange(
    manifest: IMOManifest,
    changeType: 'created' | 'updated' | 'deleted',
    details?: Record<string, any>
  ): Promise<void> {
    await this.logEvent(
      `imo.manifest.${changeType}`,
      {
        app_name: manifest.meta.app_name,
        unique_id: manifest.doctrine?.unique_id,
        process_id: manifest.doctrine?.process_id,
        ...details,
      },
      {
        source: 'imo-creator',
        environment: 'production',
      }
    );
  }

  async trackStageChange(
    manifestId: string,
    bucketType: string,
    stageId: string,
    oldStatus: string,
    newStatus: string
  ): Promise<void> {
    await this.logEvent(
      'imo.stage.status_changed',
      {
        manifest_id: manifestId,
        bucket: bucketType,
        stage_id: stageId,
        old_status: oldStatus,
        new_status: newStatus,
        timestamp: new Date().toISOString(),
      },
      {
        source: 'imo-creator',
        action: 'stage_update',
      }
    );
  }
}