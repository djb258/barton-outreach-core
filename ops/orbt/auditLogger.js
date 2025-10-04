/**
 * Barton Doctrine Audit Logger - Full Persistence + Query Layer
 * Writes operation status into marketing.unified_audit_log
 * Supports: Scraping, Email Verification, Outreach Campaigns
 * Dual writes to Firebase and Neon through Composio MCP
 * Features: Query API, Statistics, Retry Logic, CLI Support
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import dotenv from 'dotenv';

dotenv.config();

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const STRICT_MODE = process.env.AUDIT_STRICT_MODE === 'true';
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000; // ms

// Initialize Firebase Admin
let firebaseApp;
let db;

function initFirebase() {
  if (!firebaseApp) {
    firebaseApp = initializeApp({
      projectId: process.env.FIREBASE_PROJECT_ID || "barton-outreach-core",
      credential: process.env.FIREBASE_SERVICE_ACCOUNT_KEY
        ? cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY))
        : null
    });
    db = getFirestore(firebaseApp);
  }
  return db;
}

/**
 * Generate audit log entry ID
 */
function generateAuditId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8).toUpperCase();
  return `AUDIT-${timestamp}-${random}`;
}

/**
 * Validate Barton ID format before writing
 */
function validateBartonId(id) {
  if (!id) return false;

  // Check for basic Barton ID patterns
  const bartonPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  const extendedPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d+\.\d+\.[A-Z0-9]+$/;
  const shortPattern = /^(CMP|PER|CNT|AUDIT)-/;

  return bartonPattern.test(id) || extendedPattern.test(id) || shortPattern.test(id);
}

/**
 * Sleep utility for retry backoff
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry with exponential backoff
 */
async function retryWithBackoff(fn, operation, maxRetries = MAX_RETRIES) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt < maxRetries - 1) {
        const delay = INITIAL_RETRY_DELAY * Math.pow(2, attempt);
        console.warn(`⚠️ ${operation} failed (attempt ${attempt + 1}/${maxRetries}), retrying in ${delay}ms...`);
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

/**
 * Post audit log entry with dual persistence
 * @param {Object} entry - Audit log entry
 * @param {Object} options - Options { strictMode, skipRetry }
 */
export async function postToAuditLog(entry, options = {}) {
  const audit_id = generateAuditId();
  const timestamp = new Date().toISOString();

  // Validate Barton ID
  if (entry.unique_id && !validateBartonId(entry.unique_id)) {
    const error = new Error(`Invalid Barton ID format: ${entry.unique_id}`);
    if (options.strictMode || STRICT_MODE) {
      throw error;
    }
    console.warn(`⚠️ ${error.message} - continuing anyway`);
  }

  // Prepare complete audit entry
  const auditEntry = {
    // Primary identifiers
    audit_id,
    unique_id: entry.unique_id,
    process_id: entry.process_id,
    company_unique_id: entry.company_unique_id,

    // Status tracking
    status: entry.status, // Pending | Success | Failed | Skipped
    source: entry.source || "runner",
    altitude: entry.altitude || 10000,

    // Context (varies by operation type)
    blueprint_id: entry.blueprint_id,
    domain_url: entry.domain_url,
    campaign_id: entry.campaign_id,
    platform: entry.platform,
    skip_reason: entry.skip_reason,

    // Metrics (for successful scrapes)
    records_scraped: entry.records_scraped || 0,
    emails_found: entry.emails_found || 0,
    phones_found: entry.phones_found || 0,
    linkedin_found: entry.linkedin_found || 0,
    names_found: entry.names_found || 0,
    titles_found: entry.titles_found || 0,

    // Outreach metrics
    outreach_status: entry.outreach_status,
    campaign_sequence_id: entry.campaign_sequence_id,
    emails_verified: entry.emails_verified || 0,
    verification_status: entry.verification_status,

    // Error tracking
    error: entry.error || null,
    error_message: entry.error || null,
    error_stack: entry.error_stack || null,

    // Timing
    started_at: entry.started_at || timestamp,
    completed_at: entry.completed_at || timestamp,
    duration_ms: entry.duration_ms || null,
    timestamp: timestamp,
    created_at: timestamp,

    // Additional metadata
    metadata: entry.metadata || {}
  };

  console.log(`📝 AUDIT LOG [${entry.status}]:`, {
    audit_id,
    unique_id: entry.unique_id,
    process_id: entry.process_id,
    company: entry.company_unique_id
  });

  try {
    // Parallel writes to both stores with retry
    const writeWithRetry = async (writeFn, name) => {
      if (options.skipRetry) {
        return await writeFn(auditEntry);
      }
      return await retryWithBackoff(
        () => writeFn(auditEntry),
        `${name} audit write`,
        MAX_RETRIES
      );
    };

    const [neonResult, firebaseResult] = await Promise.allSettled([
      writeWithRetry(writeToNeon, 'Neon'),
      writeWithRetry(writeToFirebase, 'Firebase')
    ]);

    // Check for failures
    const neonFailed = neonResult.status === 'rejected';
    const firebaseFailed = firebaseResult.status === 'rejected';

    // Log any write failures
    if (neonFailed) {
      console.error('⚠️ Neon audit write failed:', neonResult.reason?.message || neonResult.reason);
    }
    if (firebaseFailed) {
      console.error('⚠️ Firebase audit write failed:', firebaseResult.reason?.message || firebaseResult.reason);
    }

    // In strict mode, fail if either write fails
    if ((neonFailed || firebaseFailed) && (options.strictMode || STRICT_MODE)) {
      const errors = [];
      if (neonFailed) errors.push(`Neon: ${neonResult.reason?.message}`);
      if (firebaseFailed) errors.push(`Firebase: ${firebaseResult.reason?.message}`);
      throw new Error(`Audit write failed in strict mode: ${errors.join(', ')}`);
    }

    return {
      success: true,
      audit_id,
      timestamp,
      neon_written: !neonFailed,
      firebase_written: !firebaseFailed,
      warnings: neonFailed || firebaseFailed ? {
        neon_error: neonFailed ? neonResult.reason?.message : null,
        firebase_error: firebaseFailed ? firebaseResult.reason?.message : null
      } : null
    };

  } catch (error) {
    console.error("❌ Audit logging failed:", error);

    // At minimum, log to console for debugging
    console.error("Failed audit entry:", JSON.stringify(auditEntry, null, 2));

    return {
      success: false,
      error: error.message,
      audit_id,
      timestamp
    };
  }
}

/**
 * Write audit entry to Neon through Composio MCP
 */
async function writeToNeon(auditEntry) {
  const mcpPayload = {
    tool: "neon.insert_row",
    params: {
      connection_id: "neon_barton_outreach",
      database: "marketing",
      table: "unified_audit_log",
      row: {
        ...auditEntry,
        // Ensure proper column mapping
        audit_id: auditEntry.audit_id,
        unique_id: auditEntry.unique_id,
        process_id: auditEntry.process_id,
        company_unique_id: auditEntry.company_unique_id,
        status: auditEntry.status,
        source: auditEntry.source,
        error_message: auditEntry.error_message,
        created_at: auditEntry.created_at
      },
      returning: ["audit_id"],
      on_conflict: {
        columns: ["audit_id"],
        action: "do_nothing"
      }
    },
    metadata: {
      unique_id: auditEntry.unique_id,
      process_id: "audit-logger",
      orbt_layer: auditEntry.altitude,
      timestamp: auditEntry.created_at
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Composio MCP Neon write failed: ${response.statusText} - ${errorText}`);
  }

  const result = await response.json();
  console.log(`✅ Audit entry written to Neon: ${auditEntry.audit_id}`);
  return result;
}

/**
 * Write audit entry to Firebase
 */
async function writeToFirebase(auditEntry) {
  const db = initFirebase();

  // Write to audit_log collection
  const docRef = db.collection('audit_log').doc(auditEntry.audit_id);

  await docRef.set({
    ...auditEntry,
    firebase_write_timestamp: new Date().toISOString(),
    collection_type: "unified_audit_log"
  });

  // Also write a summary to company_audit for quick lookups
  if (auditEntry.company_unique_id) {
    const companyAuditRef = db
      .collection('company_audit')
      .doc(`${auditEntry.company_unique_id}_${auditEntry.audit_id}`);

    await companyAuditRef.set({
      audit_id: auditEntry.audit_id,
      company_unique_id: auditEntry.company_unique_id,
      process_id: auditEntry.process_id,
      status: auditEntry.status,
      timestamp: auditEntry.timestamp
    });
  }

  console.log(`✅ Audit entry written to Firebase: ${auditEntry.audit_id}`);
  return { success: true };
}

/**
 * Query audit logs through Composio MCP
 */
export async function queryAuditLogs(filter = {}) {
  const conditions = [];
  const params = [];
  let paramCount = 0;

  // Build WHERE conditions
  if (filter.process_id) {
    conditions.push(`process_id = $${++paramCount}`);
    params.push(filter.process_id);
  }
  if (filter.status) {
    conditions.push(`status = $${++paramCount}`);
    params.push(filter.status);
  }
  if (filter.source) {
    conditions.push(`source = $${++paramCount}`);
    params.push(filter.source);
  }
  if (filter.company_unique_id) {
    conditions.push(`company_unique_id = $${++paramCount}`);
    params.push(filter.company_unique_id);
  }

  const whereClause = conditions.length > 0
    ? `WHERE ${conditions.join(' AND ')}`
    : '';

  const query = `
    SELECT
      audit_id,
      unique_id,
      process_id,
      company_unique_id,
      status,
      source,
      altitude,
      domain_url,
      records_scraped,
      emails_found,
      phones_found,
      linkedin_found,
      error_message,
      duration_ms,
      started_at,
      completed_at,
      created_at
    FROM marketing.unified_audit_log
    ${whereClause}
    ${filter.days_back ? `AND created_at >= NOW() - INTERVAL '${filter.days_back} days'` : ''}
    ORDER BY created_at DESC
    LIMIT ${filter.limit || 100}
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-query",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Audit query failed: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data || [];
}

/**
 * Get audit statistics
 */
export async function getAuditStats(processId = null, daysBack = 7) {
  const conditions = [`created_at >= NOW() - INTERVAL '${daysBack} days'`];
  const params = [];

  if (processId) {
    conditions.push('process_id = $1');
    params.push(processId);
  }

  const whereClause = conditions.join(' AND ');

  const query = `
    SELECT
      status,
      COUNT(*) as count,
      AVG(duration_ms) as avg_duration_ms,
      MIN(duration_ms) as min_duration_ms,
      MAX(duration_ms) as max_duration_ms,
      SUM(records_scraped) as total_records_scraped,
      SUM(emails_found) as total_emails_found,
      SUM(phones_found) as total_phones_found,
      SUM(linkedin_found) as total_linkedin_found
    FROM marketing.unified_audit_log
    WHERE ${whereClause}
    GROUP BY status
    ORDER BY count DESC
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-stats",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Audit stats query failed: ${response.statusText}`);
  }

  const result = await response.json();

  // Calculate summary stats
  const data = result.data || [];
  const summary = {
    total_runs: data.reduce((sum, row) => sum + parseInt(row.count), 0),
    success_rate: 0,
    failure_rate: 0,
    avg_duration_ms: 0,
    total_contacts: data.reduce((sum, row) => sum + parseInt(row.total_records_scraped || 0), 0),
    total_emails: data.reduce((sum, row) => sum + parseInt(row.total_emails_found || 0), 0),
    by_status: data
  };

  const successRow = data.find(r => r.status === 'Success');
  const failedRow = data.find(r => r.status === 'Failed');

  if (summary.total_runs > 0) {
    summary.success_rate = successRow ? (parseInt(successRow.count) / summary.total_runs * 100).toFixed(1) : 0;
    summary.failure_rate = failedRow ? (parseInt(failedRow.count) / summary.total_runs * 100).toFixed(1) : 0;
  }

  return summary;
}

/**
 * Batch post multiple audit entries
 */
export async function batchPostToAuditLog(entries) {
  const results = [];

  for (const entry of entries) {
    try {
      const result = await postToAuditLog(entry);
      results.push(result);
    } catch (error) {
      results.push({
        success: false,
        error: error.message,
        entry
      });
    }
  }

  return {
    success: results.every(r => r.success),
    total: entries.length,
    succeeded: results.filter(r => r.success).length,
    failed: results.filter(r => !r.success).length,
    results
  };
}

/**
 * Query audit logs by date range (ISO strings)
 */
export async function queryAuditLogsByDateRange(startDate, endDate, filters = {}) {
  const conditions = ['created_at >= $1', 'created_at <= $2'];
  const params = [startDate, endDate];
  let paramCount = 2;

  if (filters.process_id) {
    conditions.push(`process_id = $${++paramCount}`);
    params.push(filters.process_id);
  }
  if (filters.status) {
    conditions.push(`status = $${++paramCount}`);
    params.push(filters.status);
  }
  if (filters.company_unique_id) {
    conditions.push(`company_unique_id = $${++paramCount}`);
    params.push(filters.company_unique_id);
  }

  const whereClause = `WHERE ${conditions.join(' AND ')}`;

  const query = `
    SELECT
      audit_id,
      unique_id,
      process_id,
      company_unique_id,
      status,
      source,
      altitude,
      domain_url,
      records_scraped,
      emails_found,
      phones_found,
      linkedin_found,
      error_message,
      duration_ms,
      started_at,
      completed_at,
      created_at
    FROM marketing.unified_audit_log
    ${whereClause}
    ORDER BY created_at DESC
    LIMIT ${filters.limit || 1000}
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-query-date-range",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Date range query failed: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data || [];
}

/**
 * Query audit logs by contact_unique_id
 */
export async function queryAuditLogsByContact(contactUniqueId, filters = {}) {
  const query = `
    SELECT
      audit_id,
      unique_id,
      process_id,
      status,
      source,
      error_message,
      duration_ms,
      verification_status,
      outreach_status,
      created_at
    FROM marketing.unified_audit_log
    WHERE metadata->>'contact_unique_id' = $1
    ORDER BY created_at DESC
    LIMIT ${filters.limit || 100}
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: [contactUniqueId]
    },
    metadata: {
      process_id: "audit-query-contact",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Contact query failed: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data || [];
}

/**
 * Get success rate for a specific process
 */
export async function getSuccessRate(processId, daysBack = 7) {
  const stats = await getAuditStats(processId, daysBack);
  return parseFloat(stats.success_rate || 0);
}

/**
 * Get average runtime for a specific process
 */
export async function getAverageRunTime(processId, daysBack = 7) {
  const conditions = [`created_at >= NOW() - INTERVAL '${daysBack} days'`, 'duration_ms IS NOT NULL'];
  const params = [];

  if (processId) {
    conditions.push('process_id = $1');
    params.push(processId);
  }

  const whereClause = conditions.join(' AND ');

  const query = `
    SELECT
      AVG(duration_ms) as avg_runtime_ms,
      MIN(duration_ms) as min_runtime_ms,
      MAX(duration_ms) as max_runtime_ms,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as median_runtime_ms
    FROM marketing.unified_audit_log
    WHERE ${whereClause}
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-runtime-stats",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Runtime stats query failed: ${response.statusText}`);
  }

  const result = await response.json();
  const data = result.data?.[0] || {};

  return {
    average_ms: Math.round(parseFloat(data.avg_runtime_ms || 0)),
    min_ms: Math.round(parseFloat(data.min_runtime_ms || 0)),
    max_ms: Math.round(parseFloat(data.max_runtime_ms || 0)),
    median_ms: Math.round(parseFloat(data.median_runtime_ms || 0))
  };
}

/**
 * Get contacts processed count for a specific process
 */
export async function getContactsProcessed(processId, daysBack = 7) {
  const conditions = [`created_at >= NOW() - INTERVAL '${daysBack} days'`];
  const params = [];

  if (processId) {
    conditions.push('process_id = $1');
    params.push(processId);
  }

  const whereClause = conditions.join(' AND ');

  const query = `
    SELECT
      SUM(records_scraped) as total_contacts,
      SUM(emails_found) as total_emails,
      SUM(phones_found) as total_phones,
      SUM(linkedin_found) as total_linkedin,
      SUM(emails_verified) as total_verified,
      COUNT(DISTINCT company_unique_id) as unique_companies
    FROM marketing.unified_audit_log
    WHERE ${whereClause}
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-contacts-stats",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Contacts stats query failed: ${response.statusText}`);
  }

  const result = await response.json();
  const data = result.data?.[0] || {};

  return {
    total_contacts: parseInt(data.total_contacts || 0),
    total_emails: parseInt(data.total_emails || 0),
    total_phones: parseInt(data.total_phones || 0),
    total_linkedin: parseInt(data.total_linkedin || 0),
    total_verified: parseInt(data.total_verified || 0),
    unique_companies: parseInt(data.unique_companies || 0)
  };
}

/**
 * Get error analysis for debugging
 */
export async function getErrorAnalysis(processId = null, daysBack = 7) {
  const conditions = [
    `created_at >= NOW() - INTERVAL '${daysBack} days'`,
    `status = 'Failed'`,
    `error_message IS NOT NULL`
  ];
  const params = [];

  if (processId) {
    conditions.push('process_id = $1');
    params.push(processId);
  }

  const whereClause = conditions.join(' AND ');

  const query = `
    SELECT
      error_message,
      COUNT(*) as occurrence_count,
      MAX(created_at) as last_occurred,
      ARRAY_AGG(DISTINCT company_unique_id) FILTER (WHERE company_unique_id IS NOT NULL) as affected_companies
    FROM marketing.unified_audit_log
    WHERE ${whereClause}
    GROUP BY error_message
    ORDER BY occurrence_count DESC
    LIMIT 20
  `;

  const mcpPayload = {
    tool: "neon.query",
    params: {
      connection_id: "neon_barton_outreach",
      query: query,
      params: params
    },
    metadata: {
      process_id: "audit-error-analysis",
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    throw new Error(`Error analysis query failed: ${response.statusText}`);
  }

  const result = await response.json();
  return result.data || [];
}

/**
 * CLI Runner
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  // Parse CLI arguments
  const parseArg = (name, defaultValue = null) => {
    const arg = args.find(a => a.startsWith(`--${name}=`));
    return arg ? arg.split('=')[1] : defaultValue;
  };

  const command = args[0]?.replace('--', '');
  const processId = parseArg('process');
  const status = parseArg('status');
  const company = parseArg('company');
  const contact = parseArg('contact');
  const startDate = parseArg('start');
  const endDate = parseArg('end');
  const days = parseInt(parseArg('days', '7'));
  const limit = parseInt(parseArg('limit', '100'));

  console.log('\n🔍 Barton Audit Logger CLI\n');

  (async () => {
    try {
      switch (command) {
        case 'query':
          console.log('📊 Querying audit logs...\n');
          const logs = await queryAuditLogs({
            process_id: processId,
            status: status,
            company_unique_id: company,
            limit: limit,
            days_back: days
          });
          console.log(`Found ${logs.length} entries:\n`);
          console.table(logs.map(l => ({
            audit_id: l.audit_id,
            process: l.process_id,
            status: l.status,
            duration: l.duration_ms ? `${l.duration_ms}ms` : 'N/A',
            created: l.created_at
          })));
          break;

        case 'query-date':
          if (!startDate || !endDate) {
            console.error('❌ --start and --end dates required (ISO format)');
            process.exit(1);
          }
          console.log(`📊 Querying logs from ${startDate} to ${endDate}...\n`);
          const dateLogs = await queryAuditLogsByDateRange(startDate, endDate, {
            process_id: processId,
            status: status,
            company_unique_id: company,
            limit: limit
          });
          console.log(`Found ${dateLogs.length} entries:\n`);
          console.table(dateLogs);
          break;

        case 'query-contact':
          if (!contact) {
            console.error('❌ --contact required');
            process.exit(1);
          }
          console.log(`📊 Querying logs for contact ${contact}...\n`);
          const contactLogs = await queryAuditLogsByContact(contact, { limit });
          console.log(`Found ${contactLogs.length} entries:\n`);
          console.table(contactLogs);
          break;

        case 'stats':
          console.log(`📈 Getting audit statistics (last ${days} days)...\n`);
          const stats = await getAuditStats(processId, days);
          console.log('Summary:');
          console.table([{
            total_runs: stats.total_runs,
            success_rate: `${stats.success_rate}%`,
            failure_rate: `${stats.failure_rate}%`,
            total_contacts: stats.total_contacts,
            total_emails: stats.total_emails
          }]);
          console.log('\nBy Status:');
          console.table(stats.by_status);
          break;

        case 'success-rate':
          const successRate = await getSuccessRate(processId, days);
          console.log(`✅ Success Rate: ${successRate}%`);
          break;

        case 'runtime':
          console.log(`⏱️ Getting runtime statistics (last ${days} days)...\n`);
          const runtime = await getAverageRunTime(processId, days);
          console.table([runtime]);
          break;

        case 'contacts':
          console.log(`👥 Getting contacts processed (last ${days} days)...\n`);
          const contacts = await getContactsProcessed(processId, days);
          console.table([contacts]);
          break;

        case 'errors':
          console.log(`🐛 Analyzing errors (last ${days} days)...\n`);
          const errors = await getErrorAnalysis(processId, days);
          console.log(`Found ${errors.length} unique error patterns:\n`);
          console.table(errors.map(e => ({
            error: e.error_message?.substring(0, 50) + '...',
            count: e.occurrence_count,
            last_seen: e.last_occurred
          })));
          break;

        default:
          console.log('📖 Usage:');
          console.log('  npm run audit:query -- query --process="Scrape" --status="Success" --days=7 --limit=100');
          console.log('  npm run audit:query -- query-date --start="2025-01-01" --end="2025-01-31"');
          console.log('  npm run audit:query -- query-contact --contact=CNT-12345');
          console.log('  npm run audit:query -- stats --process="Scrape" --days=7');
          console.log('  npm run audit:query -- success-rate --process="Verify Email"');
          console.log('  npm run audit:query -- runtime --process="Scrape" --days=30');
          console.log('  npm run audit:query -- contacts --process="Scrape"');
          console.log('  npm run audit:query -- errors --days=7');
          console.log('\nOptions:');
          console.log('  --process     Filter by process_id');
          console.log('  --status      Filter by status (Pending, Success, Failed)');
          console.log('  --company     Filter by company_unique_id');
          console.log('  --contact     Query by contact_unique_id');
          console.log('  --start       Start date (ISO format)');
          console.log('  --end         End date (ISO format)');
          console.log('  --days        Days back (default: 7)');
          console.log('  --limit       Result limit (default: 100)');
          process.exit(0);
      }

      process.exit(0);
    } catch (error) {
      console.error('\n❌ Error:', error.message);
      process.exit(1);
    }
  })();
}

export default {
  postToAuditLog,
  batchPostToAuditLog,
  queryAuditLogs,
  queryAuditLogsByDateRange,
  queryAuditLogsByContact,
  getAuditStats,
  getSuccessRate,
  getAverageRunTime,
  getContactsProcessed,
  getErrorAnalysis
};