import { OutreachManifest, OutreachBucket, OutreachStage, OutreachLLMRequest, OutreachLLMResponse, OutreachCompany, OutreachContact, OutreachQueue } from './types';

export class OutreachService {
  private baseUrl: string;
  
  constructor(baseUrl: string = '/api/outreach') {
    this.baseUrl = baseUrl;
  }

  async loadManifest(blueprintId: string = 'default'): Promise<OutreachManifest> {
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

  async saveManifest(manifest: OutreachManifest, blueprintId: string = 'default'): Promise<void> {
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

  async getCompanies(limit: number = 50): Promise<OutreachCompany[]> {
    try {
      const response = await fetch(`${this.baseUrl}/companies?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`Failed to load companies: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error loading companies:', error);
      return [];
    }
  }

  async getContacts(companyId?: number, limit: number = 50): Promise<OutreachContact[]> {
    try {
      const url = companyId 
        ? `${this.baseUrl}/contacts?company_id=${companyId}&limit=${limit}`
        : `${this.baseUrl}/contacts?limit=${limit}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to load contacts: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error loading contacts:', error);
      return [];
    }
  }

  async getQueues(): Promise<OutreachQueue[]> {
    try {
      const response = await fetch(`${this.baseUrl}/queues`);
      if (!response.ok) {
        throw new Error(`Failed to load queues: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error loading queues:', error);
      return [];
    }
  }

  async processQueue(queueType: string, limit: number = 10): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/queues/${queueType}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ limit }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to process queue: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error processing queue:', error);
      throw error;
    }
  }

  async generateWithLLM(request: OutreachLLMRequest): Promise<OutreachLLMResponse> {
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

  calculateProgress(bucket: OutreachBucket): OutreachBucket['progress'] {
    const stages = bucket.stages || [];
    const done = stages.filter(s => s.status === 'done').length;
    const wip = stages.filter(s => s.status === 'wip').length;
    const todo = stages.filter(s => s.status === 'todo').length;
    const total = stages.length;
    
    return { done, wip, todo, total };
  }

  updateStageStatus(manifest: OutreachManifest, bucketId: 'company' | 'people' | 'campaigns', stageId: string, status: OutreachStage['status']): OutreachManifest {
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

  private getDefaultManifest(): OutreachManifest {
    return {
      meta: {
        app_name: 'Barton Outreach Core',
        stage: 'planning',
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
      },
      doctrine: {
        schema_version: 'HEIR/1.0',
      },
      buckets: {
        company: {
          id: 'company',
          name: 'Company Management',
          stages: [
            { id: 'discovery', name: 'Company Discovery', status: 'todo', queue_count: 0 },
            { id: 'verification', name: 'Data Verification', status: 'todo', queue_count: 0 },
            { id: 'enrichment', name: 'Profile Enrichment', status: 'todo', queue_count: 0 },
          ],
        },
        people: {
          id: 'people',
          name: 'Contact Management',
          stages: [
            { id: 'scraping', name: 'Contact Scraping', status: 'todo', queue_count: 0 },
            { id: 'verification', name: 'Email Verification', status: 'todo', queue_count: 0 },
            { id: 'enrichment', name: 'Profile Enrichment', status: 'todo', queue_count: 0 },
          ],
        },
        campaigns: {
          id: 'campaigns',
          name: 'Campaign Management',
          stages: [
            { id: 'planning', name: 'Campaign Planning', status: 'todo', queue_count: 0 },
            { id: 'execution', name: 'Campaign Execution', status: 'todo', queue_count: 0 },
            { id: 'tracking', name: 'Performance Tracking', status: 'todo', queue_count: 0 },
          ],
        },
      },
      stats: {
        total_companies: 0,
        verified_contacts: 0,
        active_campaigns: 0,
        queue_items: 0,
      },
    };
  }
}