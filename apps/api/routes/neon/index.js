/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Main Neon router aggregator
 * - Routes: Combines all /neon/* endpoints
 */

import express from 'express';
import dashboardRouter from './dashboard.js';
import errorsRouter from './errors.js';
import integrityRouter from './integrity.js';
import missingRouter from './missing.js';
import messagingRouter from './messaging.js';
import analyticsRouter from './analytics.js';

const router = express.Router();

// Health check endpoint for Neon connectivity
router.get('/health', async (req, res) => {
  try {
    const { sql } = await import('../../utils/neonClient.js');
    const result = await sql`SELECT NOW() as current_time, version() as pg_version`;

    res.json({
      success: true,
      status: 'healthy',
      database: 'neon',
      timestamp: result[0].current_time,
      version: result[0].pg_version
    });
  } catch (error) {
    console.error('❌ Neon health check failed:', error);
    res.status(503).json({
      success: false,
      status: 'unhealthy',
      database: 'neon',
      error: error.message
    });
  }
});

// Mount all Neon sub-routers
router.use('/', dashboardRouter);
router.use('/', errorsRouter);
router.use('/', integrityRouter);
router.use('/', missingRouter);
router.use('/', messagingRouter);
router.use('/', analyticsRouter);

// 404 handler for unknown Neon routes
router.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Neon endpoint not found',
    path: req.path,
    availableEndpoints: [
      'GET /neon/health',
      'GET /neon/dashboard-summary',
      'GET /neon/errors',
      'GET /neon/errors/:errorId',
      'GET /neon/integrity',
      'GET /neon/missing',
      'GET /neon/messaging',
      'GET /neon/analytics/error-trend',
      'GET /neon/analytics/doctrine-compliance',
      'GET /neon/analytics/latency',
      'GET /neon/analytics/data-quality'
    ]
  });
});

export default router;
