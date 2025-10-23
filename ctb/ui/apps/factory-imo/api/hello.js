/**
 * Doctrine Spec:
 * - Barton ID: 01.01.01.07.10000.001
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