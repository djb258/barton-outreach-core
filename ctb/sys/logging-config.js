/**
 * CTB Logging Configuration - Barton Outreach Core
 * Pulled from: imo-creator global-config.yaml
 * Last Synced: 2025-11-07
 */

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

// Logging configuration from global-config.yaml
const LOGGING_CONFIG = {
  directory: 'logs/',
  audit_enabled: true,
  retention_days: 90,
  levels: ['audit', 'error', 'info', 'debug'],
  database_logging: {
    enabled: true,
    table: 'public.shq_error_log',
    severity_levels: ['info', 'warning', 'error', 'critical']
  }
};

// Barton Doctrine ID format for error logs
const ERROR_ID_PREFIX = '04.04.02.04.40000.';

// Database connection pool
let dbPool = null;

/**
 * Initialize database connection for logging
 */
function initializeDatabase() {
  if (dbPool) return dbPool;

  dbPool = new Pool({
    host: process.env.NEON_HOST,
    port: 5432,
    database: process.env.NEON_DATABASE,
    user: process.env.NEON_USER,
    password: process.env.NEON_PASSWORD,
    ssl: { rejectUnauthorized: false },
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  });

  return dbPool;
}

/**
 * Generate Barton Doctrine error ID
 */
function generateErrorId() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `${ERROR_ID_PREFIX}${timestamp.toString().slice(-5)}.${random}`;
}

/**
 * Ensure logs directory exists
 */
function ensureLogsDirectory() {
  const logsDir = path.join(process.cwd(), LOGGING_CONFIG.directory);
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }
  return logsDir;
}

/**
 * Write log to file
 */
function writeToFile(level, message, metadata = {}) {
  const logsDir = ensureLogsDirectory();
  const timestamp = new Date().toISOString();
  const logFile = path.join(logsDir, `${level}.log`);

  const logEntry = {
    timestamp,
    level,
    message,
    metadata
  };

  fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
}

/**
 * Write log to database (shq_error_log table)
 */
async function writeToDatabase(level, message, metadata = {}) {
  if (!LOGGING_CONFIG.database_logging.enabled) return;

  const severityMap = {
    'debug': 'info',
    'info': 'info',
    'audit': 'info',
    'error': 'error',
    'critical': 'critical',
    'warning': 'warning'
  };

  const severity = severityMap[level] || 'info';

  if (!LOGGING_CONFIG.database_logging.severity_levels.includes(severity)) {
    return; // Skip if severity not configured for database logging
  }

  try {
    const pool = initializeDatabase();
    const errorId = metadata.error_id || generateErrorId();

    await pool.query(`
      INSERT INTO public.shq_error_log (
        error_id,
        error_code,
        error_message,
        severity,
        component,
        stack_trace,
        user_id,
        request_id,
        resolution_status,
        created_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW()
      )
    `, [
      errorId,
      metadata.error_code || 'LOG',
      message,
      severity,
      metadata.component || 'system',
      metadata.stack_trace || null,
      metadata.user_id || null,
      metadata.request_id || null,
      'unresolved'
    ]);
  } catch (dbError) {
    // Fallback to file logging if database fails
    console.error('Database logging failed:', dbError.message);
    writeToFile('error', `Database logging failed: ${dbError.message}`, { originalMessage: message });
  }
}

/**
 * Main logging function
 */
async function log(level, message, metadata = {}) {
  // Validate level
  if (!LOGGING_CONFIG.levels.includes(level)) {
    throw new Error(`Invalid log level: ${level}`);
  }

  // Write to file
  writeToFile(level, message, metadata);

  // Write to database if error/critical
  if (['error', 'critical', 'warning'].includes(level)) {
    await writeToDatabase(level, message, metadata);
  }

  // Console output for development
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[${level.toUpperCase()}] ${message}`, metadata);
  }
}

/**
 * Convenience methods
 */
const logger = {
  audit: (message, metadata) => log('audit', message, metadata),
  error: (message, metadata) => log('error', message, metadata),
  info: (message, metadata) => log('info', message, metadata),
  debug: (message, metadata) => log('debug', message, metadata),
  critical: (message, metadata) => log('critical', message, metadata),
  warning: (message, metadata) => log('warning', message, metadata),
};

/**
 * Clean up old logs (retention policy)
 */
function cleanOldLogs() {
  const logsDir = ensureLogsDirectory();
  const retentionMs = LOGGING_CONFIG.retention_days * 24 * 60 * 60 * 1000;
  const cutoffDate = Date.now() - retentionMs;

  fs.readdirSync(logsDir).forEach(file => {
    const filePath = path.join(logsDir, file);
    const stats = fs.statSync(filePath);

    if (stats.mtimeMs < cutoffDate) {
      fs.unlinkSync(filePath);
      console.log(`Deleted old log file: ${file}`);
    }
  });
}

/**
 * Shutdown handler
 */
async function shutdown() {
  if (dbPool) {
    await dbPool.end();
  }
}

module.exports = {
  logger,
  log,
  cleanOldLogs,
  shutdown,
  LOGGING_CONFIG,
  generateErrorId
};
