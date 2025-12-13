export interface ValidationRule {
  id: string;
  field: string;
  condition: string;
  action: 'reject' | 'flag' | 'warn';
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ValidationRun {
  id: string;
  heir_id: string;
  process_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  records_total: number;
  records_passed: number;
  records_failed: number;
  started_at: string;
  completed_at?: string;
}

export interface ValidationFailure {
  record_id: string;
  field: string;
  rule_id: string;
  error_message: string;
  severity: 'error' | 'warning';
}
