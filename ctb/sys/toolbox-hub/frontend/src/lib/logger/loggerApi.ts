import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { AuditLogEntry, ErrorEntry, HealthMetric } from '@/types/logger';

class LoggerApiClient extends ToolApiClient {
  async getAuditLogs(params?: { 
    tool_id?: string; 
    date_from?: string; 
    date_to?: string;
  }): Promise<AuditLogEntry[]> {
    return this.get('/audit', params);
  }

  async getErrors(params?: {
    tool_id?: string;
    severity?: string;
    resolved?: boolean;
  }): Promise<ErrorEntry[]> {
    const queryParams = params ? {
      ...(params.tool_id && { tool_id: params.tool_id }),
      ...(params.severity && { severity: params.severity }),
      ...(params.resolved !== undefined && { resolved: params.resolved.toString() }),
    } : undefined;
    return this.get('/errors', queryParams);
  }

  async getHealthMetrics(): Promise<HealthMetric[]> {
    return this.get('/health');
  }

  async resolveError(errorId: string): Promise<ErrorEntry> {
    return this.put(`/errors/${errorId}/resolve`, {});
  }
}

const tool = getToolById('logger')!;
export const loggerApi = new LoggerApiClient(tool);
