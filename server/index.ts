// FILE: server/index.ts (Express entrypoint for the worker app)
import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import { bootOrchestration, shutdownOrchestration, getSystemStatus } from './start-orchestrators';
import { buildWebhookRouter } from './webhooks';

const PORT = Number(process.env.PORT || 8080);
const NODE_ENV = process.env.NODE_ENV || 'development';

async function main() {
  console.log(`🚀 Starting Barton Outreach Core worker (${NODE_ENV})`);
  
  // Boot orchestration system
  await bootOrchestration();
  console.log('✅ Orchestration system initialized');

  const app = express();
  
  // Middleware
  app.use(cors({
    origin: process.env.FRONTEND_URL || '*',
    credentials: true
  }));
  app.use(bodyParser.json({ limit: '2mb' }));
  app.use(bodyParser.urlencoded({ extended: true }));

  // Request logging in development
  if (NODE_ENV === 'development') {
    app.use((req, _res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
      next();
    });
  }

  // Routes
  app.use('/webhooks', buildWebhookRouter());

  // Health check with orchestration status
  app.get('/health', (_req, res) => {
    try {
      const status = getSystemStatus();
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        orchestration: {
          overall_status: status.overall_status,
          overall_progress: status.overall_progress,
          active_branches: status.branches.filter(b => b.status !== 'idle').length
        },
        uptime: process.uptime()
      });
    } catch (error) {
      res.status(503).json({
        status: 'unhealthy',
        error: 'Orchestration system not available',
        timestamp: new Date().toISOString()
      });
    }
  });

  // Simple ping endpoint
  app.get('/ping', (_req, res) => res.status(200).send('pong'));

  // 404 handler
  app.use((_req, res) => {
    res.status(404).json({ error: 'Not found' });
  });

  // Global error handler
  app.use((error: any, _req: any, res: any, _next: any) => {
    console.error('❌ Unhandled error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      timestamp: new Date().toISOString()
    });
  });

  // Start server
  const server = app.listen(PORT, () => {
    console.log(`🌐 Worker server listening on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🪝 Webhooks: http://localhost:${PORT}/webhooks/*`);
  });

  // Graceful shutdown
  const shutdown = async (signal: string) => {
    console.log(`\n🛑 Received ${signal}, shutting down gracefully...`);
    
    server.close(async () => {
      try {
        await shutdownOrchestration();
        console.log('✅ Server shutdown complete');
        process.exit(0);
      } catch (error) {
        console.error('❌ Error during shutdown:', error);
        process.exit(1);
      }
    });

    // Force exit after 30 seconds
    setTimeout(() => {
      console.error('❌ Forced shutdown after timeout');
      process.exit(1);
    }, 30000);
  };

  // Handle shutdown signals
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  // Handle uncaught exceptions
  process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
    shutdown('UNCAUGHT_EXCEPTION');
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
    shutdown('UNHANDLED_REJECTION');
  });
}

main().catch((e) => {
  console.error('❌ Failed to start worker:', e);
  process.exit(1);
});