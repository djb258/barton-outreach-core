/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/api
Barton ID: 04.04.12
Unique ID: CTB-348E6773
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.12
 * - Altitude: 10000 (Execution Layer)
 * - Input: HTTP request (health check)
 * - Output: service status and version
 * - MCP: Composio (Neon integrated)
 */
export default function handler(request, response) {
  response.status(200).json({
    message: 'Hello from Vercel API!',
    url: request.url,
    method: request.method
  });
}