/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/api
Barton ID: 04.04.12
Unique ID: CTB-A9B2995E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

export default function handler(req, res) {
  res.status(200).json({ 
    message: 'API is working!', 
    method: req.method,
    timestamp: new Date().toISOString()
  });
}