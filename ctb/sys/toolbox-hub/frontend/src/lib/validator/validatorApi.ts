import { getToolById } from '@/config/tools.config';
import { ToolApiClient } from '@/lib/api/createToolApiClient';
import { ValidationRule, ValidationRun, ValidationFailure } from '@/types/validator';

class ValidatorApiClient extends ToolApiClient {
  async getRules(): Promise<ValidationRule[]> {
    return this.get('/rules');
  }

  async executeValidation(data: Record<string, any>[]): Promise<ValidationRun> {
    return this.post('/validate', { data });
  }

  async getRun(runId: string): Promise<ValidationRun> {
    return this.get(`/runs/${runId}`);
  }

  async getFailures(runId: string): Promise<ValidationFailure[]> {
    return this.get(`/runs/${runId}/failures`);
  }
}

const tool = getToolById('validator')!;
export const validatorApi = new ValidatorApiClient(tool);
