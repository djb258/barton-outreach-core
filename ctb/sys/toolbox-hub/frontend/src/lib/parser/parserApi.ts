import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { ParseJob, ParseTemplate } from '@/types/parser';

class ParserApiClient extends ToolApiClient {
  async getTemplates(): Promise<ParseTemplate[]> {
    return this.get('/templates');
  }

  async parseDocument(file: File, templateId?: string): Promise<ParseJob> {
    const formData = new FormData();
    formData.append('file', file);
    if (templateId) formData.append('template_id', templateId);
    
    return this.post('/parse', formData);
  }

  async getJob(jobId: string): Promise<ParseJob> {
    return this.get(`/jobs/${jobId}`);
  }

  async getJobs(status?: string): Promise<ParseJob[]> {
    return this.get('/jobs', status ? { status } : undefined);
  }
}

const tool = getToolById('parser')!;
export const parserApi = new ParserApiClient(tool);
