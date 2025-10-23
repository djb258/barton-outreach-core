/**
 * Doctrine Spec:
 * - Barton ID: 01.01.02.07.10000.002
 * - Altitude: 10000 (Execution Layer)
 * - Input: test parameters and configuration
 * - Output: test results and validation status
 * - MCP: Composio (Neon integrated)
 */
export default function handler(req, res) {
  res.status(200).json({ 
    message: 'API is working!', 
    method: req.method,
    timestamp: new Date().toISOString()
  });
}