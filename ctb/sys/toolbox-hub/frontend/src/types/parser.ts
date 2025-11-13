export interface ParseJob {
  id: string;
  document_name: string;
  document_type: 'pdf' | 'docx' | 'txt' | 'image';
  status: 'queued' | 'processing' | 'completed' | 'failed';
  heir_id: string;
  process_id: string;
  extracted_data?: Record<string, any>;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface ParseTemplate {
  id: string;
  name: string;
  document_type: string;
  extraction_rules: ExtractionRule[];
  created_at: string;
}

export interface ExtractionRule {
  field_name: string;
  extraction_pattern: string;
  field_type: 'text' | 'number' | 'date' | 'boolean';
  required: boolean;
}
