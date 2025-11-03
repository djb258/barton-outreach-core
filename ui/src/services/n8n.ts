/**
 * n8n Workflow Service
 * Handles API calls to n8n workflow endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface N8nExecution {
  id: string;
  finished: boolean;
  mode: string;
  retryOf?: string;
  retrySuccessId?: string;
  startedAt: string;
  stoppedAt?: string;
  workflowId: string;
  workflowName?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  count: number;
  timestamp: string;
}

/**
 * Fetch n8n error executions
 */
export async function fetchN8nErrors(): Promise<N8nExecution[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/n8n/errors`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<N8nExecution[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching n8n errors:', error);
    throw error;
  }
}

/**
 * Fetch recent n8n executions
 */
export async function fetchN8nExecutions(limit: number = 20): Promise<N8nExecution[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/n8n/executions?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<N8nExecution[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching n8n executions:', error);
    throw error;
  }
}
