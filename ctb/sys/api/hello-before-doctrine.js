/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/api
Barton ID: 04.04.12
Unique ID: CTB-1D2748D3
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

export default function handler(request, response) {
  response.status(200).json({
    message: 'Hello from Vercel API!',
    url: request.url,
    method: request.method
  });
}