require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

// Import routes
const ingestionRoutes = require('./routes/ingestion');
const processingRoutes = require('./routes/processing');
const healthRoutes = require('./routes/health');
const apolloSyncRoutes = require('./routes/apollo-sync');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:5173',
    'https://*.lovable.dev',
    'https://*.lovableproject.com'
  ],
  credentials: true
}));
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// API Routes
app.use('/api/v1/ingest', ingestionRoutes);
app.use('/api/v1/process', processingRoutes);
app.use('/api/v1/health', healthRoutes);
app.use('/api/v1/apollo-sync', apolloSyncRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'CSV Data Ingestor Service',
    version: '1.0.0',
    status: 'active',
    architecture: 'HEIR-compliant',
    capabilities: [
      'csv-parsing',
      'excel-processing', 
      'data-validation',
      'batch-ingestion',
      'apollo-integration'
    ],
    endpoints: {
      health: '/api/v1/health',
      ingestion: '/api/v1/ingest',
      processing: '/api/v1/process',
      apolloSync: '/api/v1/apollo-sync',
      documentation: '/api/v1/docs'
    }
  });
});

// OpenAPI documentation endpoint
app.get('/api/v1/docs', (req, res) => {
  res.json(require('./openapi.json'));
});

// HEIR Event Publishing Middleware
app.use((req, res, next) => {
  // Store original json method
  const originalJson = res.json;
  
  res.json = function(data) {
    // Publish events for HEIR orchestration
    if (req.method === 'POST' && req.path.includes('/ingest')) {
      publishEvent('data.ingestion.completed', {
        endpoint: req.path,
        recordCount: data.processed || 0,
        success: data.success || false,
        timestamp: new Date().toISOString()
      });
    }
    
    return originalJson.call(this, data);
  };
  
  next();
});

// Error handling middleware (HEIR Resilient pattern)
app.use((err, req, res, next) => {
  console.error(`[CSV-Ingestor] Error:`, err.stack);
  
  // Publish error event for HEIR monitoring
  publishEvent('service.error', {
    service: 'csv-data-ingestor',
    error: err.message,
    endpoint: req.path,
    timestamp: new Date().toISOString()
  });
  
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal Server Error',
      status: err.status || 500,
      timestamp: new Date().toISOString(),
      service: 'csv-data-ingestor'
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: {
      message: 'Endpoint not found',
      status: 404,
      path: req.path,
      timestamp: new Date().toISOString(),
      service: 'csv-data-ingestor'
    }
  });
});

// HEIR Event Publishing Function (Event-driven pattern)
function publishEvent(eventType, payload) {
  // In production, this would connect to event bus/message queue
  console.log(`[HEIR-Event] ${eventType}:`, JSON.stringify(payload, null, 2));
  
  // Example: Send to main orchestrator
  // eventBus.publish(eventType, payload);
}

// Graceful shutdown (HEIR Resilient pattern)
process.on('SIGTERM', () => {
  console.log('[CSV-Ingestor] Received SIGTERM, shutting down gracefully');
  publishEvent('service.shutdown', {
    service: 'csv-data-ingestor',
    timestamp: new Date().toISOString()
  });
  process.exit(0);
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 CSV Data Ingestor Service running on port ${PORT}`);
  console.log(`📍 Local: http://localhost:${PORT}`);
  console.log(`🏗️  Architecture: HEIR-compliant microservice`);
  console.log(`📚 API Docs: http://localhost:${PORT}/api/v1/docs`);
  
  // Publish service startup event
  publishEvent('service.started', {
    service: 'csv-data-ingestor',
    port: PORT,
    capabilities: ['csv-parsing', 'excel-processing', 'data-validation'],
    timestamp: new Date().toISOString()
  });
});