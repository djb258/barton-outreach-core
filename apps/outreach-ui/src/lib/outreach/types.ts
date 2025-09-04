export interface OutreachCompany {
  company_id: number;
  company_name: string;
  ein?: string;
  renewal_month?: number;
  renewal_notice_window_days?: number;
  dot_color: 'green' | 'yellow' | 'red' | 'gray';
  slot_name?: string;
  slot_updated?: string;
  next_renewal?: string;
}

export interface OutreachContact {
  contact_id: number;
  company_id: number;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  title?: string;
  dot_color: 'green' | 'yellow' | 'red' | 'gray';
  verification_status?: string;
  updated_at?: string;
}

export interface OutreachQueue {
  id: string;
  type: 'company_urls' | 'profile_urls' | 'mv_batch';
  company_id?: number;
  url?: string;
  kind?: string;
  priority: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface OutreachStage {
  id: string;
  name: string;
  status: 'todo' | 'wip' | 'done';
  description?: string;
  tasks?: string[];
  queue_count?: number;
}

export interface OutreachBucket {
  id: string;
  name: string;
  stages: OutreachStage[];
  progress?: {
    done: number;
    wip: number;
    todo: number;
    total: number;
  };
}

export interface OutreachManifest {
  meta: {
    app_name: string;
    stage?: string;
    created?: string;
    updated?: string;
  };
  doctrine?: {
    unique_id?: string;
    process_id?: string;
    blueprint_version_hash?: string;
    schema_version?: string;
  };
  buckets: {
    company?: OutreachBucket;
    people?: OutreachBucket;
    campaigns?: OutreachBucket;
  };
  stats?: {
    total_companies: number;
    verified_contacts: number;
    active_campaigns: number;
    queue_items: number;
  };
}

export interface OutreachLLMRequest {
  provider?: 'anthropic' | 'openai';
  model?: string;
  system?: string;
  prompt: string;
  json?: boolean;
  max_tokens?: number;
}

export interface OutreachLLMResponse {
  content: string;
  provider: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface OutreachProvider {
  type: 'anthropic' | 'openai';
  apiKey?: string;
  model?: string;
  available: boolean;
}