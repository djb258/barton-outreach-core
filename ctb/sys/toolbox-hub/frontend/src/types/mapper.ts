export interface MappingRecipe {
  id: string;
  name: string;
  source_schema: string;
  target_schema: string;
  field_mappings: FieldMapping[];
  created_at: string;
  updated_at: string;
}

export interface FieldMapping {
  source_field: string;
  target_field: string;
  transformation?: string;
  required: boolean;
}

export interface MappingRun {
  id: string;
  recipe_id: string;
  heir_id: string;
  process_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  records_processed: number;
  started_at: string;
  completed_at?: string;
}
