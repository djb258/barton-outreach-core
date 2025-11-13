import type { 
  ValidationPayload, 
  Recipe, 
  RecipeRun, 
  SheetRegistry,
  RunLog 
} from '@/types/router';

const API_BASE_URL = import.meta.env.VITE_MASTER_HUB_API_URL || 'https://master-hub.barton.com';

class RouterApiClient {
  async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Route invalid data to Messyflow
  async validateData(payload: ValidationPayload): Promise<{
    success: boolean;
    sheetUrl?: string;
    sheetId?: string;
    heir_id: string;
    process_id: string;
  }> {
    return this.request('/api/messyflow/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Get all recipes
  async getRecipes(): Promise<Recipe[]> {
    return this.request('/api/recipes');
  }

  // Execute a recipe
  async executeRecipe(
    recipeId: string,
    data: Record<string, any>,
    heir_id: string,
    process_id: string
  ): Promise<RecipeRun> {
    return this.request('/api/recipes/execute', {
      method: 'POST',
      body: JSON.stringify({ recipeId, data, heir_id, process_id }),
    });
  }

  // Get recipe run details
  async getRun(runId: string): Promise<RecipeRun> {
    return this.request(`/api/runs/${runId}`);
  }

  // Get run logs
  async getRunLogs(runId: string): Promise<RunLog[]> {
    return this.request(`/api/runs/${runId}/logs`);
  }

  // Get all sheets
  async getSheets(): Promise<SheetRegistry[]> {
    return this.request('/api/sheets');
  }

  // Create a new sheet
  async createSheet(payload: {
    source: string;
    recipe_id: string;
    heir_id: string;
    process_id: string;
    data: Record<string, any>[];
  }): Promise<SheetRegistry> {
    return this.request('/api/sheets/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Get sheets by source
  async getSheetsBySource(source: string): Promise<SheetRegistry[]> {
    return this.request(`/api/sheets?source=${encodeURIComponent(source)}`);
  }
}

export const routerApi = new RouterApiClient();
