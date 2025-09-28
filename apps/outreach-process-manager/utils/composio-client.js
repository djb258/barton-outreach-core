/**
 * Composio HTTP Client for MCP Integration
 * Handles all Composio API requests with proper authentication and error handling
 */

export async function composioRequest(payload) {
  try {
    const composioConfig = {
      apiKey: process.env.COMPOSIO_API_KEY,
      baseUrl: process.env.COMPOSIO_BASE_URL || 'https://backend.composio.dev/api/v1'
    };

    if (!composioConfig.apiKey) {
      throw new Error('COMPOSIO_API_KEY environment variable is required');
    }

    console.log(`[COMPOSIO-CLIENT] Sending request to ${composioConfig.baseUrl}/execute`);

    const response = await fetch(`${composioConfig.baseUrl}/execute`, {
      method: 'POST',
      headers: {
        'X-API-KEY': composioConfig.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Composio API request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const result = await response.json();

    console.log(`[COMPOSIO-CLIENT] Request completed successfully`);

    return {
      success: true,
      data: result,
      status: response.status
    };

  } catch (error) {
    console.error('[COMPOSIO-CLIENT] Request failed:', error);

    return {
      success: false,
      error: error.message,
      data: null
    };
  }
}