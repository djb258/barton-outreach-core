import { ToolConfig } from '@/config/tools.config';

const MASTER_HUB_URL = import.meta.env.VITE_MASTER_HUB_API_URL || 'https://master-hub.barton.com';

export interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string>;
}

export class ToolApiClient {
  private baseUrl: string;
  private apiPrefix: string;

  constructor(tool: ToolConfig) {
    this.baseUrl = MASTER_HUB_URL;
    this.apiPrefix = tool.apiPrefix;
  }

  async request<T>(
    endpoint: string,
    options?: ApiRequestOptions
  ): Promise<T> {
    const url = new URL(`${this.apiPrefix}${endpoint}`, this.baseUrl);
    
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const response = await fetch(url.toString(), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', params });
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const createToolApiClient = (tool: ToolConfig): ToolApiClient => {
  return new ToolApiClient(tool);
};
