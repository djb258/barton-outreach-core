export interface AuditLogEntry {
  id: string;
  tool_id: string;
  process_id: string;
  heir_id?: string;
  action: string;
  status: 'success' | 'warning' | 'error';
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ErrorEntry {
  id: string;
  tool_id: string;
  error_type: string;
  error_message: string;
  stack_trace?: string;
  process_id?: string;
  heir_id?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
  created_at: string;
}

export interface HealthMetric {
  tool_id: string;
  last_run: string;
  success_rate_24h: number;
  active_processes: number;
  avg_response_time: number;
  status: 'healthy' | 'degraded' | 'down';
}
