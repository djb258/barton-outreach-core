import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { DocumentTemplate, GenerationJob } from '@/types/docfiller';

class DocFillerApiClient extends ToolApiClient {
  async getTemplates(): Promise<DocumentTemplate[]> {
    return this.get('/templates');
  }

  async generateDocument(
    templateId: string, 
    data: Record<string, any>,
    heir_id: string,
    process_id: string
  ): Promise<GenerationJob> {
    return this.post('/generate', { templateId, data, heir_id, process_id });
  }

  async getJob(jobId: string): Promise<GenerationJob> {
    return this.get(`/jobs/${jobId}`);
  }

  async getJobs(status?: string): Promise<GenerationJob[]> {
    return this.get('/jobs', status ? { status } : undefined);
  }
}

const tool = getToolById('docfiller')!;
export const docfillerApi = new DocFillerApiClient(tool);
