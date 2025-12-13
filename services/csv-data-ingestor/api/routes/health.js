const express = require('express');
const router = express.Router();

/**
 * GET /api/v1/health
 * HEIR-compliant health check endpoint
 */
router.get('/', async (req, res) => {
  try {
    // Check service health (HEIR Resilient)
    const healthChecks = await performHealthChecks();
    
    const overallStatus = healthChecks.every(check => check.status === 'healthy') 
      ? 'healthy' 
      : healthChecks.some(check => check.status === 'degraded')
        ? 'degraded'
        : 'unhealthy';

    res.status(overallStatus === 'unhealthy' ? 503 : 200).json({
      status: overallStatus,
      timestamp: new Date().toISOString(),
      service: 'csv-data-ingestor',
      version: '1.0.0',
      architecture: 'HEIR-compliant',
      checks: healthChecks.reduce((acc, check) => {
        acc[check.name] = {
          status: check.status,
          message: check.message,
          responseTime: check.responseTime
        };
        return acc;
      }, {}),
      environment: {
        node: process.version,
        platform: process.platform,
        uptime: process.uptime(),
        memory: {
          used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024)
        }
      }
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString(),
      service: 'csv-data-ingestor'
    });
  }
});

/**
 * GET /api/v1/health/detailed
 * Detailed health check for troubleshooting
 */
router.get('/detailed', async (req, res) => {
  try {
    const detailedChecks = await performDetailedHealthChecks();
    
    res.json({
      status: 'detailed-check',
      timestamp: new Date().toISOString(),
      service: 'csv-data-ingestor',
      checks: detailedChecks,
      dependencies: {
        apolloScraper: process.env.APOLLO_SCRAPER_URL || 'http://localhost:3000',
        renderDB: 'https://render-marketing-db.onrender.com'
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

async function performHealthChecks() {
  const checks = [];
  
  // Memory check
  const memoryUsage = process.memoryUsage();
  const memoryUsedMB = memoryUsage.heapUsed / 1024 / 1024;
  checks.push({
    name: 'memory',
    status: memoryUsedMB > 500 ? 'degraded' : 'healthy',
    message: `Memory usage: ${Math.round(memoryUsedMB)}MB`,
    responseTime: '<1ms'
  });

  // File system check
  const start = Date.now();
  try {
    const fs = require('fs');
    fs.accessSync(__dirname, fs.constants.R_OK);
    checks.push({
      name: 'filesystem',
      status: 'healthy',
      message: 'File system accessible',
      responseTime: `${Date.now() - start}ms`
    });
  } catch (error) {
    checks.push({
      name: 'filesystem',
      status: 'unhealthy',
      message: `File system error: ${error.message}`,
      responseTime: `${Date.now() - start}ms`
    });
  }

  // Parser health
  try {
    const IntelligentParser = require('../../lib/parsers/intelligentParser');
    const parser = new IntelligentParser();
    checks.push({
      name: 'parser',
      status: 'healthy',
      message: 'Intelligent parser initialized',
      responseTime: '<1ms'
    });
  } catch (error) {
    checks.push({
      name: 'parser',
      status: 'unhealthy',
      message: `Parser error: ${error.message}`,
      responseTime: '<1ms'
    });
  }

  return checks;
}

async function performDetailedHealthChecks() {
  const checks = {
    system: await getSystemHealth(),
    dependencies: await getDependencyHealth(),
    performance: await getPerformanceMetrics(),
    features: await getFeatureHealth()
  };
  
  return checks;
}

async function getSystemHealth() {
  return {
    nodejs: process.version,
    platform: process.platform,
    arch: process.arch,
    uptime: Math.round(process.uptime()),
    memory: {
      rss: Math.round(process.memoryUsage().rss / 1024 / 1024),
      heapTotal: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
      heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
      external: Math.round(process.memoryUsage().external / 1024 / 1024)
    },
    cpu: process.cpuUsage()
  };
}

async function getDependencyHealth() {
  const axios = require('axios');
  const dependencies = {};
  
  // Check Apollo Scraper Service
  try {
    const apolloUrl = process.env.APOLLO_SCRAPER_URL || 'http://localhost:3000';
    const start = Date.now();
    const response = await axios.get(`${apolloUrl}/api/v1/health`, { timeout: 5000 });
    dependencies.apolloScraper = {
      status: 'healthy',
      url: apolloUrl,
      responseTime: Date.now() - start,
      version: response.data.version
    };
  } catch (error) {
    dependencies.apolloScraper = {
      status: 'unhealthy',
      url: process.env.APOLLO_SCRAPER_URL || 'http://localhost:3000',
      error: error.message
    };
  }
  
  // Check Render DB
  try {
    const renderUrl = 'https://render-marketing-db.onrender.com';
    const start = Date.now();
    const response = await axios.get(`${renderUrl}/api/health`, { timeout: 10000 });
    dependencies.renderDB = {
      status: 'healthy',
      url: renderUrl,
      responseTime: Date.now() - start,
      service: response.data.service
    };
  } catch (error) {
    dependencies.renderDB = {
      status: 'unhealthy',
      url: 'https://render-marketing-db.onrender.com',
      error: error.message
    };
  }
  
  return dependencies;
}

async function getPerformanceMetrics() {
  return {
    eventLoop: process.hrtime(),
    activeHandles: process._getActiveHandles().length,
    activeRequests: process._getActiveRequests().length
  };
}

async function getFeatureHealth() {
  const features = {};
  
  // Test CSV parsing
  try {
    const Papa = require('papaparse');
    features.csvParsing = { status: 'available', library: 'papaparse' };
  } catch (error) {
    features.csvParsing = { status: 'unavailable', error: error.message };
  }
  
  // Test Excel parsing
  try {
    const XLSX = require('xlsx');
    features.excelParsing = { status: 'available', library: 'xlsx' };
  } catch (error) {
    features.excelParsing = { status: 'unavailable', error: error.message };
  }
  
  // Test file upload
  try {
    const multer = require('multer');
    features.fileUpload = { status: 'available', library: 'multer' };
  } catch (error) {
    features.fileUpload = { status: 'unavailable', error: error.message };
  }
  
  return features;
}

module.exports = router;