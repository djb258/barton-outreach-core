const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Phase statistics from pipeline
export interface PhaseStats {
  phase: string;
  status: string;
  count: number;
  last_updated: string;
}

// Recent error entry
export interface RecentError {
  error_id: string;
  phase: string;
  error_type: string;
  error_message: string;
  company_id?: string;
  created_at: string;
}

// Company master record
export interface CompanyMaster {
  barton_id: string;
  company_name: string;
  website: string;
  phase: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// API response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  count: number;
  timestamp: string;
}

// Fetch phase statistics
export async function fetchPhaseStats(): Promise<PhaseStats[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/neon/v_phase_stats`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<PhaseStats[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching phase stats:', error);
    throw error;
  }
}

// Fetch recent errors
export async function fetchRecentErrors(): Promise<RecentError[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/neon/v_error_recent`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<RecentError[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching recent errors:', error);
    throw error;
  }
}

// Fetch company master data
export async function fetchCompanyMaster(limit: number = 100): Promise<CompanyMaster[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/neon/company_master?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<CompanyMaster[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching company master:', error);
    throw error;
  }
}
