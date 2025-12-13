require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

// Import routes
const scraperRoutes = require('./routes/scraper');
const companiesRoutes = require('./routes/companies');
const resultsRoutes = require('./routes/results');
const healthRoutes = require('./routes/health');
const integratedRoutes = require('./routes/integrated');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// API Routes
app.use('/api/v1/scraper', scraperRoutes);
app.use('/api/v1/companies', companiesRoutes);
app.use('/api/v1/results', resultsRoutes);
app.use('/api/v1/health', healthRoutes);
app.use('/api/v1/integrated', integratedRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Apollo Scraper API',
    version: '1.0.0',
    status: 'active',
    endpoints: {
      health: '/api/v1/health',
      scraper: '/api/v1/scraper',
      companies: '/api/v1/companies',
      results: '/api/v1/results',
      integrated: '/api/v1/integrated',
      documentation: '/api/v1/docs'
    }
  });
});

// OpenAPI documentation endpoint
app.get('/api/v1/docs', (req, res) => {
  res.json(require('./openapi.json'));
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal Server Error',
      status: err.status || 500,
      timestamp: new Date().toISOString()
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
      timestamp: new Date().toISOString()
    }
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Apollo Scraper API running on port ${PORT}`);
  console.log(`📍 Local: http://localhost:${PORT}`);
  console.log(`📚 API Docs: http://localhost:${PORT}/api/v1/docs`);
});