import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { MappingRecipe, MappingRun } from '@/types/mapper';

class MapperApiClient extends ToolApiClient {
  async getRecipes(): Promise<MappingRecipe[]> {
    return this.get('/recipes');
  }

  async createRecipe(recipe: Omit<MappingRecipe, 'id' | 'created_at' | 'updated_at'>): Promise<MappingRecipe> {
    return this.post('/recipes', recipe);
  }

  async executeMapping(recipeId: string, data: Record<string, any>[]): Promise<MappingRun> {
    return this.post('/execute', { recipeId, data });
  }

  async getRun(runId: string): Promise<MappingRun> {
    return this.get(`/runs/${runId}`);
  }
}

const tool = getToolById('mapper')!;
export const mapperApi = new MapperApiClient(tool);
