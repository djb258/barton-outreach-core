export interface ValidationError {
  field: string;
  error: string;
  value: any;
  severity: 'error' | 'warning';
}

export interface ValidationPayload {
  source: string;
  data: Record<string, any>;
  validation_errors: ValidationError[];
  heir_id: string;
  process_id: string;
  metadata?: Record<string, any>;
}

export interface Recipe {
  id: string;
  name: string;
  description: string;
  source_types: string[];
  sheet_template_id?: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SheetRegistry {
  id: string;
  sheet_id: string;
  sheet_name: string;
  sheet_url: string;
  source: string;
  recipe_id: string;
  status: 'active' | 'completed' | 'archived';
  record_count: number;
  heir_id: string;
  process_id: string;
  created_at: string;
  last_synced_at?: string;
}

export interface RecipeRun {
  id: string;
  recipe_id: string;
  heir_id: string;
  process_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface RunLog {
  id: string;
  run_id: string;
  log_level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ValidationQueueItem {
  id: string;
  source: string;
  payload: ValidationPayload;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  priority: number;
  created_at: string;
  processed_at?: string;
}
