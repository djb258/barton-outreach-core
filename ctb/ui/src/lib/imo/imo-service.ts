import { IMOManifest, IMOBucket, IMOStage, IMOLLMRequest, IMOLLMResponse } from './types';

export class IMOService {
  private baseUrl: string;
  
  constructor(baseUrl: string = '/api/imo') {
    this.baseUrl = baseUrl;
  }

  async loadManifest(blueprintId: string = 'default'): Promise<IMOManifest> {
    try {
      const response = await fetch(`${this.baseUrl}/manifest/${blueprintId}`);
      if (!response.ok) {
        throw new Error(`Failed to load manifest: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error loading manifest:', error);
      return this.getDefaultManifest();
    }
  }

  async saveManifest(manifest: IMOManifest, blueprintId: string = 'default'): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/manifest/${blueprintId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(manifest),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save manifest: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error saving manifest:', error);
      throw error;
    }
  }

  async generateWithLLM(request: IMOLLMRequest): Promise<IMOLLMResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error(`LLM request failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error with LLM request:', error);
      throw error;
    }
  }

  async stampDoctrineIds(manifest: IMOManifest): Promise<IMOManifest> {
    try {
      const response = await fetch(`${this.baseUrl}/ssot/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ssot: manifest }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to stamp doctrine IDs: ${response.statusText}`);
      }
      
      const result = await response.json();
      return result.ssot;
    } catch (error) {
      console.error('Error stamping doctrine IDs:', error);
      return manifest;
    }
  }

  calculateProgress(bucket: IMOBucket): IMOBucket['progress'] {
    const stages = bucket.stages || [];
    const done = stages.filter(s => s.status === 'done').length;
    const wip = stages.filter(s => s.status === 'wip').length;
    const todo = stages.filter(s => s.status === 'todo').length;
    const total = stages.length;
    
    return { done, wip, todo, total };
  }

  updateStageStatus(manifest: IMOManifest, bucketId: 'input' | 'middle' | 'output', stageId: string, status: IMOStage['status']): IMOManifest {
    const bucket = manifest.buckets[bucketId];
    if (!bucket) return manifest;
    
    const stage = bucket.stages.find(s => s.id === stageId);
    if (stage) {
      stage.status = status;
      bucket.progress = this.calculateProgress(bucket);
    }
    
    manifest.meta.updated = new Date().toISOString();
    return manifest;
  }

  private getDefaultManifest(): IMOManifest {
    return {
      meta: {
        app_name: 'Barton Outreach IMO',
        stage: 'planning',
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
      },
      doctrine: {
        schema_version: 'HEIR/1.0',
      },
      buckets: {
        input: {
          id: 'input',
          name: 'Input Phase',
          stages: [
            { id: 'requirements', name: 'Gather Requirements', status: 'todo' },
            { id: 'research', name: 'Research & Analysis', status: 'todo' },
            { id: 'planning', name: 'Planning & Design', status: 'todo' },
          ],
        },
        middle: {
          id: 'middle',
          name: 'Middle Phase',
          stages: [
            { id: 'implementation', name: 'Core Implementation', status: 'todo' },
            { id: 'integration', name: 'System Integration', status: 'todo' },
            { id: 'testing', name: 'Testing & Validation', status: 'todo' },
          ],
        },
        output: {
          id: 'output',
          name: 'Output Phase',
          stages: [
            { id: 'deployment', name: 'Deployment', status: 'todo' },
            { id: 'monitoring', name: 'Monitoring & Metrics', status: 'todo' },
            { id: 'optimization', name: 'Optimization', status: 'todo' },
          ],
        },
      },
    };
  }
}