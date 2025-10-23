/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-BAD33609
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2C Apify Scraping Cloud Functions for fresh data collection
 * - Input: Target URLs/domains and actor specifications
 * - Output: Scraped company/people data inserted into staging intake tables
 * - MCP: Firebase (Composio-only scraping operations)
 */

import { onCall } from 'firebase-functions/v2/https';
import { getFirestore } from 'firebase-admin/firestore';
import { logger } from 'firebase-functions';

// Initialize Firestore
const db = getFirestore();

/**
 * Apify client utility for actor management
 */
class ApifyClient {
  constructor() {
    this.apiKey = process.env.APIFY_API_KEY;
    this.baseUrl = 'https://api.apify.com/v2';
    this.supportedActors = {
      'linkedin-company': 'apify/linkedin-company-scraper',
      'linkedin-people': 'apify/linkedin-people-scraper',
      'email-scraper': 'apify/email-scraper'
    };
  }

  /**
   * Run Apify actor with input parameters
   */
  async runActor(actorId, input, options = {}) {
    try {
      logger.info(`Starting Apify actor: ${actorId}`, { input });

      const runResponse = await fetch(`${this.baseUrl}/acts/${actorId}/runs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...input,
          timeout: options.timeout || 300, // 5 minutes default
          memory: options.memory || 512
        })
      });

      if (!runResponse.ok) {
        throw new Error(`Apify actor start failed: ${runResponse.statusText}`);
      }

      const runData = await runResponse.json();
      const runId = runData.data.id;

      logger.info(`Apify actor started: ${runId}`);

      // Wait for completion
      const result = await this.waitForCompletion(runId, options.maxWaitTime || 600);

      return {
        success: true,
        runId: runId,
        status: result.status,
        data: result.data,
        stats: result.stats
      };

    } catch (error) {
      logger.error('Apify actor execution failed:', error);
      return {
        success: false,
        error: error.message,
        runId: null,
        data: []
      };
    }
  }

  /**
   * Wait for actor run completion
   */
  async waitForCompletion(runId, maxWaitTime = 600) {
    const startTime = Date.now();
    const pollInterval = 5000; // 5 seconds

    while (Date.now() - startTime < maxWaitTime * 1000) {
      try {
        const statusResponse = await fetch(`${this.baseUrl}/actor-runs/${runId}`, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        });

        if (!statusResponse.ok) {
          throw new Error(`Status check failed: ${statusResponse.statusText}`);
        }

        const statusData = await statusResponse.json();
        const status = statusData.data.status;

        logger.info(`Actor ${runId} status: ${status}`);

        if (status === 'SUCCEEDED') {
          // Get results
          const resultsResponse = await fetch(`${this.baseUrl}/datasets/${statusData.data.defaultDatasetId}/items`, {
            headers: {
              'Authorization': `Bearer ${this.apiKey}`
            }
          });

          const results = await resultsResponse.json();

          return {
            status: 'SUCCEEDED',
            data: results || [],
            stats: statusData.data.stats
          };
        }

        if (status === 'FAILED' || status === 'ABORTED' || status === 'TIMED-OUT') {
          return {
            status: status,
            data: [],
            error: statusData.data.exitCode || 'Actor failed',
            stats: statusData.data.stats
          };
        }

        // Still running, wait and check again
        await new Promise(resolve => setTimeout(resolve, pollInterval));

      } catch (error) {
        logger.error(`Error checking actor status: ${error.message}`);
        throw error;
      }
    }

    throw new Error(`Actor timeout after ${maxWaitTime} seconds`);
  }

  /**
   * Get supported actor ID from type
   */
  getActorId(actorType) {
    const actorId = this.supportedActors[actorType];
    if (!actorId) {
      throw new Error(`Unsupported actor type: ${actorType}`);
    }
    return actorId;
  }
}

/**
 * Data normalization utility for scraped data
 */
class ScrapingDataNormalizer {
  constructor() {
    this.phoneNormalizer = new PhoneNormalizer();
  }

  /**
   * Normalize scraped company data
   */
  normalizeCompanyData(rawData) {
    try {
      const normalized = {
        // Basic company information
        company_name: this.normalizeString(rawData.name || rawData.companyName || rawData.title),
        website_url: this.normalizeUrl(rawData.website || rawData.websiteUrl || rawData.url),

        // Contact information
        phone_number: this.normalizePhone(rawData.phone || rawData.phoneNumber),
        email: this.normalizeEmail(rawData.email || rawData.contactEmail),

        // Location data
        address: this.normalizeString(rawData.address || rawData.location),
        city: this.normalizeString(rawData.city),
        state: this.normalizeString(rawData.state || rawData.region),
        country: this.normalizeString(rawData.country || 'US'),

        // Company details
        employee_count: this.normalizeEmployeeCount(rawData.employeeCount || rawData.employees || rawData.size),
        industry: this.normalizeString(rawData.industry || rawData.sector),
        description: this.normalizeString(rawData.description || rawData.about),

        // Social media
        linkedin_url: this.normalizeUrl(rawData.linkedinUrl || rawData.linkedin),
        twitter_url: this.normalizeUrl(rawData.twitterUrl || rawData.twitter),

        // Scraping metadata
        scraped_at: new Date().toISOString(),
        scrape_source: 'apify',
        data_quality_score: this.calculateDataQuality(rawData)
      };

      // Remove null/undefined values
      return this.cleanObject(normalized);

    } catch (error) {
      logger.error('Company data normalization error:', error);
      throw error;
    }
  }

  /**
   * Normalize scraped person data
   */
  normalizePersonData(rawData) {
    try {
      const normalized = {
        // Basic person information
        first_name: this.normalizeString(rawData.firstName || this.extractFirstName(rawData.name || rawData.fullName)),
        last_name: this.normalizeString(rawData.lastName || this.extractLastName(rawData.name || rawData.fullName)),
        full_name: this.normalizeString(rawData.name || rawData.fullName || `${rawData.firstName} ${rawData.lastName}`),

        // Contact information
        email: this.normalizeEmail(rawData.email || rawData.contactEmail),
        phone_number: this.normalizePhone(rawData.phone || rawData.phoneNumber),

        // Professional information
        job_title: this.normalizeString(rawData.title || rawData.jobTitle || rawData.position),
        company_name: this.normalizeString(rawData.company || rawData.companyName || rawData.currentCompany),

        // Location data
        location: this.normalizeString(rawData.location || rawData.city),
        city: this.normalizeString(rawData.city),
        state: this.normalizeString(rawData.state || rawData.region),
        country: this.normalizeString(rawData.country || 'US'),

        // Social media
        linkedin_url: this.normalizeUrl(rawData.linkedinUrl || rawData.linkedin || rawData.profileUrl),
        twitter_url: this.normalizeUrl(rawData.twitterUrl || rawData.twitter),

        // Experience and education
        experience_summary: this.normalizeString(rawData.experience || rawData.summary),
        education: this.normalizeString(rawData.education || rawData.school),

        // Scraping metadata
        scraped_at: new Date().toISOString(),
        scrape_source: 'apify',
        data_quality_score: this.calculateDataQuality(rawData)
      };

      // Remove null/undefined values
      return this.cleanObject(normalized);

    } catch (error) {
      logger.error('Person data normalization error:', error);
      throw error;
    }
  }

  /**
   * Normalize string values
   */
  normalizeString(value) {
    if (!value || typeof value !== 'string') return null;
    return value.trim().replace(/\s+/g, ' ') || null;
  }

  /**
   * Normalize URL values
   */
  normalizeUrl(value) {
    if (!value || typeof value !== 'string') return null;

    let url = value.trim();
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    try {
      new URL(url);
      return url;
    } catch (error) {
      return null;
    }
  }

  /**
   * Normalize email addresses
   */
  normalizeEmail(value) {
    if (!value || typeof value !== 'string') return null;

    const email = value.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return emailRegex.test(email) ? email : null;
  }

  /**
   * Normalize phone numbers to E.164 format
   */
  normalizePhone(value) {
    if (!value) return null;

    // Use the phone normalizer from enrichment operations
    const result = this.phoneNormalizer.normalizePhone(value);
    return result.normalized_phone;
  }

  /**
   * Normalize employee count
   */
  normalizeEmployeeCount(value) {
    if (!value) return null;

    if (typeof value === 'number') return Math.max(0, Math.floor(value));
    if (typeof value === 'string') {
      // Handle ranges like "50-100", "1000+"
      const match = value.match(/(\d+)/);
      return match ? Math.max(0, parseInt(match[1])) : null;
    }

    return null;
  }

  /**
   * Extract first name from full name
   */
  extractFirstName(fullName) {
    if (!fullName) return null;
    return fullName.split(' ')[0] || null;
  }

  /**
   * Extract last name from full name
   */
  extractLastName(fullName) {
    if (!fullName) return null;
    const parts = fullName.split(' ');
    return parts.length > 1 ? parts[parts.length - 1] : null;
  }

  /**
   * Calculate data quality score
   */
  calculateDataQuality(data) {
    if (!data || typeof data !== 'object') return 0;

    const totalFields = Object.keys(data).length;
    const filledFields = Object.values(data).filter(value =>
      value !== null && value !== undefined && value !== ''
    ).length;

    return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) / 100 : 0;
  }

  /**
   * Remove null/undefined values from object
   */
  cleanObject(obj) {
    const cleaned = {};
    for (const [key, value] of Object.entries(obj)) {
      if (value !== null && value !== undefined) {
        cleaned[key] = value;
      }
    }
    return cleaned;
  }
}

/**
 * Phone normalizer utility (simplified version)
 */
class PhoneNormalizer {
  normalizePhone(phoneNumber, defaultCountry = 'US') {
    if (!phoneNumber || typeof phoneNumber !== 'string') {
      return { normalized_phone: null };
    }

    try {
      const cleaned = phoneNumber.replace(/[^\d+]/g, '');

      if (cleaned.startsWith('+') && cleaned.length >= 10 && cleaned.length <= 15) {
        return { normalized_phone: cleaned };
      }

      if (defaultCountry === 'US' && cleaned.length === 10) {
        return { normalized_phone: `+1${cleaned}` };
      }

      if (defaultCountry === 'US' && cleaned.length === 11 && cleaned.startsWith('1')) {
        return { normalized_phone: `+${cleaned}` };
      }

      return { normalized_phone: null };

    } catch (error) {
      return { normalized_phone: null };
    }
  }
}

/**
 * Barton ID generator for scraped records
 */
class BartonIdGenerator {
  constructor() {
    // Step 2C scraping IDs: 15.01.02.10.XXXXX.XXX
    this.baseId = '15.01.02.10';
  }

  /**
   * Generate company Barton ID
   */
  generateCompanyId() {
    const sequence = Math.floor(Math.random() * 99999).toString().padStart(5, '0');
    const version = Math.floor(Math.random() * 999).toString().padStart(3, '0');
    return `${this.baseId}.${sequence}.${version}`;
  }

  /**
   * Generate person Barton ID
   */
  generatePersonId() {
    const sequence = Math.floor(Math.random() * 99999).toString().padStart(5, '0');
    const version = Math.floor(Math.random() * 999).toString().padStart(3, '0');
    return `${this.baseId}.${sequence}.${version}`;
  }

  /**
   * Generate process ID for tracking
   */
  generateProcessId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `PRC-SCR-${timestamp}-${random}`;
  }
}

/**
 * MCP access validation
 */
async function validateMCPAccess(context, operation) {
  const auth = context.auth;

  if (!auth || !auth.uid) {
    throw new Error('MCP_ACCESS_DENIED: Authentication required');
  }

  const mcpToken = context.rawRequest?.headers?.['x-composio-key'];
  if (!mcpToken) {
    throw new Error('MCP_ACCESS_DENIED: Composio MCP access required');
  }

  logger.info(`MCP access validated for scraping operation: ${operation}`, {
    uid: auth.uid,
    operation: operation,
    timestamp: new Date().toISOString()
  });
}

/**
 * Create unified audit log entry
 */
async function createUnifiedAuditLog(operation, result, context) {
  const auditEntry = {
    operation_type: 'scraping',
    operation_subtype: operation.actorType,
    unique_id: result.processId || 'unknown',
    actor_type: operation.actorType,
    target_urls: operation.targetUrls || [],
    domains: operation.domains || [],

    // Results summary
    total_scraped: result.totalScraped || 0,
    successful_inserts: result.successfulInserts || 0,
    failed_inserts: result.failedInserts || 0,
    data_quality_average: result.averageDataQuality || 0,

    // Apify specific data
    apify_run_id: result.apifyRunId,
    apify_status: result.apifyStatus,
    apify_stats: result.apifyStats,

    // Timing
    scrape_duration_ms: result.scrapeDuration || 0,
    processing_duration_ms: result.processingDuration || 0,

    // Error information
    errors: result.errors || [],
    warnings: result.warnings || [],

    // MCP tracking
    mcp_trace: {
      scraping_endpoint: 'scraping',
      scraping_operation: operation.functionName,
      request_id: context.requestId || 'unknown',
      user_id: context.auth?.uid || 'system',
      composio_session: context.composioSession || null
    },

    created_at: new Date().toISOString(),
    operation_started_at: new Date(context.startTime).toISOString(),
    operation_completed_at: new Date().toISOString()
  };

  try {
    await db.collection('unified_audit_log').add(auditEntry);
    logger.info(`Unified audit log created for ${operation.actorType} scraping:`, {
      processId: result.processId,
      totalScraped: result.totalScraped
    });
  } catch (error) {
    logger.error('Failed to create unified audit log:', error);
  }
}

/**
 * Create error log entry
 */
async function createErrorLog(operation, error, context) {
  const errorEntry = {
    error_type: 'scraping_error',
    operation_type: 'scraping',
    operation_subtype: operation.actorType,
    actor_type: operation.actorType,
    target_urls: operation.targetUrls || [],

    // Error details
    error_code: error.code || 'SCRAPING_ERROR',
    error_message: error.message,
    error_stack: error.stack,

    // Apify specific error data
    apify_run_id: error.runId || null,
    apify_status: error.status || null,

    // Context
    process_id: context.processId,
    mcp_trace: {
      request_id: context.requestId || 'unknown',
      user_id: context.auth?.uid || 'system'
    },

    created_at: new Date().toISOString(),
    retry_possible: true,
    severity: 'error'
  };

  try {
    await db.collection('error_log').add(errorEntry);
    logger.info('Error log created for scraping failure:', {
      processId: context.processId,
      errorType: error.code
    });
  } catch (logError) {
    logger.error('Failed to create error log:', logError);
  }
}

/**
 * Insert company data into staging intake
 */
async function insertCompanyToStaging(companyData, processId) {
  try {
    const docRef = await db.collection('company_raw_intake')
      .doc(companyData.company_unique_id)
      .set({
        ...companyData,
        intake_status: 'staging',
        process_id: processId,
        inserted_at: new Date().toISOString()
      });

    return { success: true, documentId: companyData.company_unique_id };

  } catch (error) {
    logger.error('Failed to insert company to staging:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Insert person data into staging intake
 */
async function insertPersonToStaging(personData, processId) {
  try {
    const docRef = await db.collection('people_raw_intake')
      .doc(personData.person_unique_id)
      .set({
        ...personData,
        intake_status: 'staging',
        process_id: processId,
        inserted_at: new Date().toISOString()
      });

    return { success: true, documentId: personData.person_unique_id };

  } catch (error) {
    logger.error('Failed to insert person to staging:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Cloud Function: Scrape Company Data
 */
export const scrapeCompany = onCall({
  memory: '2GiB',
  timeoutSeconds: 600, // 10 minutes for scraping
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'scrapeCompany');

    logger.info('Starting company scraping:', {
      actorType: data.actorType,
      targetUrls: data.targetUrls?.length || 0
    });

    // Initialize utilities
    const apifyClient = new ApifyClient();
    const normalizer = new ScrapingDataNormalizer();
    const idGenerator = new BartonIdGenerator();
    const processId = idGenerator.generateProcessId();

    const context = {
      startTime,
      auth,
      requestId: data.request_id,
      processId,
      composioSession: data.composio_session
    };

    // Validate input
    if (!data.actorType || !data.targetUrls || !Array.isArray(data.targetUrls)) {
      throw new Error('Invalid input: actorType and targetUrls array required');
    }

    // Get actor ID
    const actorId = apifyClient.getActorId(data.actorType);

    // Prepare actor input
    const actorInput = {
      startUrls: data.targetUrls.map(url => ({ url })),
      maxItems: data.maxItems || 100,
      proxyConfiguration: { useApifyProxy: true },
      includeUnlistedCompanies: false
    };

    // Run Apify actor
    const scrapeStartTime = Date.now();
    const actorResult = await apifyClient.runActor(actorId, actorInput, {
      timeout: data.timeout || 300,
      maxWaitTime: data.maxWaitTime || 480
    });

    const scrapeDuration = Date.now() - scrapeStartTime;

    if (!actorResult.success) {
      throw new Error(`Apify scraping failed: ${actorResult.error}`);
    }

    // Process and normalize scraped data
    const processingStartTime = Date.now();
    const results = {
      totalScraped: 0,
      successfulInserts: 0,
      failedInserts: 0,
      errors: [],
      warnings: [],
      companies: []
    };

    for (const rawCompany of actorResult.data) {
      try {
        results.totalScraped++;

        // Normalize company data
        const normalizedCompany = normalizer.normalizeCompanyData(rawCompany);

        // Assign Barton ID
        normalizedCompany.company_unique_id = idGenerator.generateCompanyId();

        // Insert to staging
        const insertResult = await insertCompanyToStaging(normalizedCompany, processId);

        if (insertResult.success) {
          results.successfulInserts++;
          results.companies.push(normalizedCompany.company_unique_id);
        } else {
          results.failedInserts++;
          results.errors.push({
            company: normalizedCompany.company_name || 'unknown',
            error: insertResult.error
          });
        }

      } catch (error) {
        results.failedInserts++;
        results.errors.push({
          rawData: rawCompany,
          error: error.message
        });
        logger.error('Company processing error:', error);
      }
    }

    const processingDuration = Date.now() - processingStartTime;

    // Calculate average data quality
    const averageDataQuality = results.totalScraped > 0
      ? actorResult.data.reduce((sum, company) => sum + normalizer.calculateDataQuality(company), 0) / results.totalScraped
      : 0;

    const finalResult = {
      processId,
      apifyRunId: actorResult.runId,
      apifyStatus: actorResult.status,
      apifyStats: actorResult.stats,
      totalScraped: results.totalScraped,
      successfulInserts: results.successfulInserts,
      failedInserts: results.failedInserts,
      scrapeDuration,
      processingDuration,
      averageDataQuality,
      errors: results.errors,
      warnings: results.warnings,
      companies: results.companies
    };

    // Create unified audit log
    await createUnifiedAuditLog({
      actorType: data.actorType,
      targetUrls: data.targetUrls,
      functionName: 'scrapeCompany'
    }, finalResult, context);

    logger.info('Company scraping completed:', {
      processId,
      totalScraped: results.totalScraped,
      successfulInserts: results.successfulInserts
    });

    return {
      success: true,
      process_id: processId,
      total_scraped: results.totalScraped,
      successful_inserts: results.successfulInserts,
      failed_inserts: results.failedInserts,
      companies: results.companies,
      apify_run_id: actorResult.runId,
      processing_time_ms: Date.now() - startTime,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Company scraping error:', error);

    // Create error log
    await createErrorLog({
      actorType: data.actorType,
      targetUrls: data.targetUrls,
      functionName: 'scrapeCompany'
    }, error, {
      processId: data.process_id || 'unknown',
      requestId: data.request_id,
      auth
    });

    throw error;
  }
});

/**
 * Cloud Function: Scrape Person Data
 */
export const scrapePerson = onCall({
  memory: '2GiB',
  timeoutSeconds: 600, // 10 minutes for scraping
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'scrapePerson');

    logger.info('Starting person scraping:', {
      actorType: data.actorType,
      targetUrls: data.targetUrls?.length || 0
    });

    // Initialize utilities
    const apifyClient = new ApifyClient();
    const normalizer = new ScrapingDataNormalizer();
    const idGenerator = new BartonIdGenerator();
    const processId = idGenerator.generateProcessId();

    const context = {
      startTime,
      auth,
      requestId: data.request_id,
      processId,
      composioSession: data.composio_session
    };

    // Validate input
    if (!data.actorType || !data.targetUrls || !Array.isArray(data.targetUrls)) {
      throw new Error('Invalid input: actorType and targetUrls array required');
    }

    // Get actor ID
    const actorId = apifyClient.getActorId(data.actorType);

    // Prepare actor input
    const actorInput = {
      startUrls: data.targetUrls.map(url => ({ url })),
      maxItems: data.maxItems || 100,
      proxyConfiguration: { useApifyProxy: true },
      includeContactInfo: true
    };

    // Run Apify actor
    const scrapeStartTime = Date.now();
    const actorResult = await apifyClient.runActor(actorId, actorInput, {
      timeout: data.timeout || 300,
      maxWaitTime: data.maxWaitTime || 480
    });

    const scrapeDuration = Date.now() - scrapeStartTime;

    if (!actorResult.success) {
      throw new Error(`Apify scraping failed: ${actorResult.error}`);
    }

    // Process and normalize scraped data
    const processingStartTime = Date.now();
    const results = {
      totalScraped: 0,
      successfulInserts: 0,
      failedInserts: 0,
      errors: [],
      warnings: [],
      people: []
    };

    for (const rawPerson of actorResult.data) {
      try {
        results.totalScraped++;

        // Normalize person data
        const normalizedPerson = normalizer.normalizePersonData(rawPerson);

        // Assign Barton ID
        normalizedPerson.person_unique_id = idGenerator.generatePersonId();

        // Insert to staging
        const insertResult = await insertPersonToStaging(normalizedPerson, processId);

        if (insertResult.success) {
          results.successfulInserts++;
          results.people.push(normalizedPerson.person_unique_id);
        } else {
          results.failedInserts++;
          results.errors.push({
            person: normalizedPerson.full_name || 'unknown',
            error: insertResult.error
          });
        }

      } catch (error) {
        results.failedInserts++;
        results.errors.push({
          rawData: rawPerson,
          error: error.message
        });
        logger.error('Person processing error:', error);
      }
    }

    const processingDuration = Date.now() - processingStartTime;

    // Calculate average data quality
    const averageDataQuality = results.totalScraped > 0
      ? actorResult.data.reduce((sum, person) => sum + normalizer.calculateDataQuality(person), 0) / results.totalScraped
      : 0;

    const finalResult = {
      processId,
      apifyRunId: actorResult.runId,
      apifyStatus: actorResult.status,
      apifyStats: actorResult.stats,
      totalScraped: results.totalScraped,
      successfulInserts: results.successfulInserts,
      failedInserts: results.failedInserts,
      scrapeDuration,
      processingDuration,
      averageDataQuality,
      errors: results.errors,
      warnings: results.warnings,
      people: results.people
    };

    // Create unified audit log
    await createUnifiedAuditLog({
      actorType: data.actorType,
      targetUrls: data.targetUrls,
      functionName: 'scrapePerson'
    }, finalResult, context);

    logger.info('Person scraping completed:', {
      processId,
      totalScraped: results.totalScraped,
      successfulInserts: results.successfulInserts
    });

    return {
      success: true,
      process_id: processId,
      total_scraped: results.totalScraped,
      successful_inserts: results.successfulInserts,
      failed_inserts: results.failedInserts,
      people: results.people,
      apify_run_id: actorResult.runId,
      processing_time_ms: Date.now() - startTime,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Person scraping error:', error);

    // Create error log
    await createErrorLog({
      actorType: data.actorType,
      targetUrls: data.targetUrls,
      functionName: 'scrapePerson'
    }, error, {
      processId: data.process_id || 'unknown',
      requestId: data.request_id,
      auth
    });

    throw error;
  }
});

/**
 * Export utilities for testing
 */
export {
  ApifyClient,
  ScrapingDataNormalizer,
  BartonIdGenerator
};