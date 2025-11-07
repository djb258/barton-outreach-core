/**
 * Apify Actor Service
 * Handles API calls to Apify actor endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApifyRunRequest {
  actor_id: string;
  input_data?: Record<string, any>;
  timeout?: number;
}

export interface ApifyActor {
  id: string;
  name: string;
  username: string;
  description?: string;
  createdAt: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  count?: number;
  timestamp: string;
}

/**
 * Run an Apify actor
 */
export async function runApifyActor(
  actorId: string,
  inputData: Record<string, any> = {},
  timeout: number = 300
): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/apify/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        actor_id: actorId,
        input_data: inputData,
        timeout: timeout,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<any> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error running Apify actor:', error);
    throw error;
  }
}

/**
 * List available Apify actors
 */
export async function listApifyActors(): Promise<ApifyActor[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/apify/actors`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApifyActor[]> = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error listing Apify actors:', error);
    throw error;
  }
}
