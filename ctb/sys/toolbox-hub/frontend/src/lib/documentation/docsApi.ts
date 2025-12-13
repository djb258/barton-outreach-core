import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { DocumentationPage, ProcessDiagram, ApiEndpoint } from '@/types/documentation';

class DocumentationApiClient extends ToolApiClient {
  async getPages(category?: string): Promise<DocumentationPage[]> {
    return this.get('/pages', category ? { category } : undefined);
  }

  async getPage(slug: string): Promise<DocumentationPage> {
    return this.get(`/pages/${slug}`);
  }

  async getDiagrams(): Promise<ProcessDiagram[]> {
    return this.get('/diagrams');
  }

  async getEndpoints(toolId?: string): Promise<ApiEndpoint[]> {
    return this.get('/endpoints', toolId ? { tool_id: toolId } : undefined);
  }
}

const tool = getToolById('documentation')!;
export const docsApi = new DocumentationApiClient(tool);
