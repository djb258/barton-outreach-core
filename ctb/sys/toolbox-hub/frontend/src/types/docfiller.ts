export interface DocumentTemplate {
  id: string;
  name: string;
  template_type: 'invoice' | 'contract' | 'report' | 'letter' | 'custom';
  template_url: string;
  fields: TemplateField[];
  created_at: string;
  updated_at: string;
}

export interface TemplateField {
  field_id: string;
  field_name: string;
  field_type: 'text' | 'number' | 'date' | 'boolean';
  placeholder: string;
  required: boolean;
}

export interface GenerationJob {
  id: string;
  template_id: string;
  heir_id: string;
  process_id: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  output_url?: string;
  created_at: string;
  completed_at?: string;
}
