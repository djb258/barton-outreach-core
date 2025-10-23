/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-2D54C41A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2B Enrichment Cloud Functions for data enhancement operations
 * - Input: Company and people records requiring enrichment
 * - Output: Enriched records with normalized data and audit logs
 * - MCP: Firebase (Composio-only enrichment operations)
 */

import { onCall } from 'firebase-functions/v2/https';
import { getFirestore } from 'firebase-admin/firestore';
import { logger } from 'firebase-functions';

// Initialize Firestore
const db = getFirestore();

/**
 * Domain normalization utility
 */
class DomainNormalizer {
  constructor() {
    this.validProtocols = ['http:', 'https:'];
    this.commonDomainPatterns = [
      /^(www\.)(.+)$/i,
      /^(m\.)(.+)$/i,
      /^(mobile\.)(.+)$/i
    ];
  }

  /**
   * Normalize domain/website URL
   */
  normalizeDomain(websiteUrl) {
    if (!websiteUrl || typeof websiteUrl !== 'string') {
      return {
        normalized_url: null,
        domain: null,
        status: 'invalid',
        error: 'Invalid or empty URL'
      };
    }

    try {
      // Clean the URL
      let cleanUrl = websiteUrl.trim().toLowerCase();

      // Add protocol if missing
      if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
        cleanUrl = 'https://' + cleanUrl;
      }

      const url = new URL(cleanUrl);

      // Validate protocol
      if (!this.validProtocols.includes(url.protocol)) {
        return {
          normalized_url: null,
          domain: null,
          status: 'invalid_protocol',
          error: 'Invalid protocol'
        };
      }

      // Extract and normalize domain
      let domain = url.hostname;

      // Remove common prefixes
      for (const pattern of this.commonDomainPatterns) {
        const match = domain.match(pattern);
        if (match) {
          domain = match[2];
          break;
        }
      }

      // Construct normalized URL
      const normalizedUrl = `https://${domain}${url.pathname === '/' ? '' : url.pathname}`;

      return {
        normalized_url: normalizedUrl,
        domain: domain,
        status: 'valid',
        error: null
      };

    } catch (error) {
      return {
        normalized_url: null,
        domain: null,
        status: 'parse_error',
        error: error.message
      };
    }
  }
}

/**
 * Phone repair and normalization utility
 */
class PhoneRepairer {
  constructor() {
    this.countryPatterns = {
      US: {
        code: '+1',
        patterns: [
          /^(?:\+?1[-.\s]?)?(?:\(?([0-9]{3})\)?[-.\s]?)?([0-9]{3})[-.\s]?([0-9]{4})$/,
          /^([0-9]{3})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$/
        ],
        format: (matches) => `+1${matches[1]}${matches[2]}${matches[3]}`
      }
    };
  }

  /**
   * Repair and normalize phone number
   */
  repairPhone(phoneNumber, defaultCountry = 'US') {
    if (!phoneNumber || typeof phoneNumber !== 'string') {
      return {
        normalized_phone: null,
        phone_country: null,
        phone_type: null,
        status: 'invalid',
        error: 'Invalid or empty phone number'
      };
    }

    try {
      // Clean the input
      const cleaned = phoneNumber.replace(/[^\d+]/g, '');

      // If already in E.164 format, validate and return
      if (cleaned.startsWith('+') && cleaned.length >= 10 && cleaned.length <= 15) {
        return {
          normalized_phone: cleaned,
          phone_country: this.detectCountry(cleaned),
          phone_type: 'mobile', // Default assumption
          status: 'valid',
          error: null
        };
      }

      // Try country-specific patterns
      const countryConfig = this.countryPatterns[defaultCountry];
      if (countryConfig) {
        for (const pattern of countryConfig.patterns) {
          const match = phoneNumber.match(pattern);
          if (match) {
            const normalized = countryConfig.format(match);
            return {
              normalized_phone: normalized,
              phone_country: defaultCountry,
              phone_type: 'mobile',
              status: 'repaired',
              error: null
            };
          }
        }
      }

      return {
        normalized_phone: null,
        phone_country: null,
        phone_type: null,
        status: 'unrepairable',
        error: 'Could not normalize phone number'
      };

    } catch (error) {
      return {
        normalized_phone: null,
        phone_country: null,
        phone_type: null,
        status: 'error',
        error: error.message
      };
    }
  }

  /**
   * Detect country from E.164 format
   */
  detectCountry(e164Number) {
    if (e164Number.startsWith('+1')) return 'US';
    if (e164Number.startsWith('+44')) return 'UK';
    if (e164Number.startsWith('+33')) return 'FR';
    if (e164Number.startsWith('+49')) return 'DE';
    return 'UNKNOWN';
  }
}

/**
 * Address geocoding utility (mock implementation)
 */
class AddressGeocoder {
  constructor() {
    // In production, this would integrate with Google Places API
    this.mockCoordinates = {
      'san francisco': { lat: 37.7749, lng: -122.4194, timezone: 'America/Los_Angeles' },
      'new york': { lat: 40.7128, lng: -74.0060, timezone: 'America/New_York' },
      'london': { lat: 51.5074, lng: -0.1278, timezone: 'Europe/London' }
    };
  }

  /**
   * Geocode address to coordinates
   */
  async geocodeAddress(address, city, state, country) {
    try {
      if (!address && !city) {
        return {
          latitude: null,
          longitude: null,
          formatted_address: null,
          timezone: null,
          status: 'insufficient_data',
          error: 'Address or city required'
        };
      }

      // Mock geocoding logic
      const searchKey = (city || address || '').toLowerCase();
      const coords = this.mockCoordinates[searchKey];

      if (coords) {
        const formattedAddress = this.formatAddress(address, city, state, country);
        return {
          latitude: coords.lat,
          longitude: coords.lng,
          formatted_address: formattedAddress,
          timezone: coords.timezone,
          status: 'geocoded',
          error: null
        };
      }

      return {
        latitude: null,
        longitude: null,
        formatted_address: null,
        timezone: null,
        status: 'not_found',
        error: 'Location not found'
      };

    } catch (error) {
      return {
        latitude: null,
        longitude: null,
        formatted_address: null,
        timezone: null,
        status: 'error',
        error: error.message
      };
    }
  }

  /**
   * Format address components
   */
  formatAddress(address, city, state, country) {
    const components = [address, city, state, country].filter(Boolean);
    return components.join(', ');
  }
}

/**
 * Person slot type inference utility
 */
class SlotTypeInferrer {
  constructor() {
    this.slotTypePatterns = {
      'CEO': { slot_type: 'executive', role_category: 'c-suite', department: 'executive' },
      'CTO': { slot_type: 'executive', role_category: 'c-suite', department: 'technology' },
      'CFO': { slot_type: 'executive', role_category: 'c-suite', department: 'finance' },
      'VP': { slot_type: 'executive', role_category: 'vice-president', department: 'management' },
      'Director': { slot_type: 'management', role_category: 'director', department: 'management' },
      'Manager': { slot_type: 'management', role_category: 'manager', department: 'management' },
      'Engineer': { slot_type: 'individual_contributor', role_category: 'technical', department: 'engineering' },
      'Developer': { slot_type: 'individual_contributor', role_category: 'technical', department: 'engineering' },
      'Sales': { slot_type: 'individual_contributor', role_category: 'sales', department: 'sales' },
      'Marketing': { slot_type: 'individual_contributor', role_category: 'marketing', department: 'marketing' }
    };
  }

  /**
   * Infer slot type from job title
   */
  inferSlotType(jobTitle, companyName = null) {
    if (!jobTitle || typeof jobTitle !== 'string') {
      return {
        slot_type: null,
        role_category: null,
        department: null,
        status: 'invalid',
        error: 'Invalid job title'
      };
    }

    try {
      const titleUpper = jobTitle.toUpperCase();

      // Check exact matches first
      for (const [pattern, classification] of Object.entries(this.slotTypePatterns)) {
        if (titleUpper.includes(pattern.toUpperCase())) {
          return {
            ...classification,
            status: 'classified',
            error: null,
            confidence: 0.9
          };
        }
      }

      // Default classification for unmatched titles
      return {
        slot_type: 'individual_contributor',
        role_category: 'general',
        department: 'other',
        status: 'default',
        error: null,
        confidence: 0.3
      };

    } catch (error) {
      return {
        slot_type: null,
        role_category: null,
        department: null,
        status: 'error',
        error: error.message
      };
    }
  }
}

/**
 * Seniority determination utility
 */
class SeniorityDeterminer {
  constructor() {
    this.seniorityPatterns = {
      'C-LEVEL': { seniority_level: 'executive', management_level: 'c-suite', years_experience_estimate: 15 },
      'VP': { seniority_level: 'senior', management_level: 'vice-president', years_experience_estimate: 12 },
      'SENIOR VP': { seniority_level: 'executive', management_level: 'senior-vice-president', years_experience_estimate: 15 },
      'DIRECTOR': { seniority_level: 'senior', management_level: 'director', years_experience_estimate: 10 },
      'SENIOR DIRECTOR': { seniority_level: 'senior', management_level: 'senior-director', years_experience_estimate: 12 },
      'MANAGER': { seniority_level: 'mid', management_level: 'manager', years_experience_estimate: 7 },
      'SENIOR MANAGER': { seniority_level: 'senior', management_level: 'senior-manager', years_experience_estimate: 10 },
      'SENIOR': { seniority_level: 'senior', management_level: 'individual-contributor', years_experience_estimate: 8 },
      'LEAD': { seniority_level: 'mid', management_level: 'team-lead', years_experience_estimate: 6 },
      'JUNIOR': { seniority_level: 'junior', management_level: 'individual-contributor', years_experience_estimate: 2 }
    };
  }

  /**
   * Determine seniority from job title
   */
  determineSeniority(jobTitle, companySize = null) {
    if (!jobTitle || typeof jobTitle !== 'string') {
      return {
        seniority_level: null,
        management_level: null,
        years_experience_estimate: null,
        status: 'invalid',
        error: 'Invalid job title'
      };
    }

    try {
      const titleUpper = jobTitle.toUpperCase();

      // Check for C-level first
      if (titleUpper.match(/^C[A-Z]{2}$/) || titleUpper.includes('CHIEF')) {
        return {
          ...this.seniorityPatterns['C-LEVEL'],
          status: 'classified',
          error: null,
          confidence: 0.95
        };
      }

      // Check other patterns
      for (const [pattern, classification] of Object.entries(this.seniorityPatterns)) {
        if (titleUpper.includes(pattern)) {
          return {
            ...classification,
            status: 'classified',
            error: null,
            confidence: 0.8
          };
        }
      }

      // Default for unmatched titles
      return {
        seniority_level: 'mid',
        management_level: 'individual-contributor',
        years_experience_estimate: 5,
        status: 'default',
        error: null,
        confidence: 0.3
      };

    } catch (error) {
      return {
        seniority_level: null,
        management_level: null,
        years_experience_estimate: null,
        status: 'error',
        error: error.message
      };
    }
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

  logger.info(`MCP access validated for enrichment operation: ${operation}`, {
    uid: auth.uid,
    operation: operation,
    timestamp: new Date().toISOString()
  });
}

/**
 * Create enrichment audit log entry
 */
async function createEnrichmentAuditLog(uniqueId, action, beforeValues, afterValues, status, errorLog, operation, context) {
  const auditEntry = {
    unique_id: uniqueId,
    action: action,
    record_type: beforeValues.company_name ? 'company' : 'person',
    enrichment_operation: operation,
    before_values: beforeValues,
    after_values: afterValues,
    fields_changed: getChangedFields(beforeValues, afterValues),
    status: status,
    error_log: errorLog || null,
    performance_metrics: {
      processing_time_ms: Date.now() - context.startTime,
      api_calls_made: 1,
      data_quality_score: calculateDataQualityScore(afterValues)
    },
    mcp_trace: {
      enrichment_endpoint: 'enrichment',
      enrichment_operation: operation.operation_type,
      request_id: context.requestId || 'unknown',
      user_id: context.auth?.uid || 'system',
      composio_session: context.composioSession || null
    },
    created_at: new Date().toISOString(),
    operation_started_at: new Date(context.startTime).toISOString(),
    operation_completed_at: new Date().toISOString()
  };

  try {
    await db.collection('enrichment_audit_log').add(auditEntry);
    logger.info(`Enrichment audit log created for ${operation.operation_type}:`, { uniqueId });
  } catch (error) {
    logger.error('Failed to create enrichment audit log:', error);
  }
}

/**
 * Get changed fields between before and after values
 */
function getChangedFields(beforeValues, afterValues) {
  const changed = [];
  const allKeys = new Set([...Object.keys(beforeValues), ...Object.keys(afterValues)]);

  for (const key of allKeys) {
    if (beforeValues[key] !== afterValues[key]) {
      changed.push(key);
    }
  }

  return changed;
}

/**
 * Calculate data quality score
 */
function calculateDataQualityScore(data) {
  let totalFields = 0;
  let filledFields = 0;

  for (const [key, value] of Object.entries(data)) {
    totalFields++;
    if (value !== null && value !== undefined && value !== '') {
      filledFields++;
    }
  }

  return totalFields > 0 ? filledFields / totalFields : 0;
}

/**
 * Cloud Function: Enrich Company
 */
export const enrichCompany = onCall({
  memory: '1GiB',
  timeoutSeconds: 120,
  maxInstances: 20
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'enrichCompany');

    logger.info('Starting company enrichment:', { companyId: data.company_unique_id });

    // Get company document from intake collection
    const companyDoc = await db.collection('company_raw_intake')
      .doc(data.company_unique_id)
      .get();

    if (!companyDoc.exists) {
      throw new Error(`Company document not found: ${data.company_unique_id}`);
    }

    const originalData = companyDoc.data();
    const enrichedData = { ...originalData };
    const enrichmentResults = {};

    // Initialize enrichment utilities
    const domainNormalizer = new DomainNormalizer();
    const phoneRepairer = new PhoneRepairer();
    const addressGeocoder = new AddressGeocoder();

    // 1. Normalize domain
    if (originalData.website_url) {
      const domainResult = domainNormalizer.normalizeDomain(originalData.website_url);
      if (domainResult.status === 'valid' || domainResult.status === 'repaired') {
        enrichedData.website_url = domainResult.normalized_url;
        enrichedData.domain = domainResult.domain;
        enrichmentResults.normalize_domain = domainResult;
      }
    }

    // 2. Repair phone number
    if (originalData.phone_number) {
      const phoneResult = phoneRepairer.repairPhone(originalData.phone_number);
      if (phoneResult.status === 'valid' || phoneResult.status === 'repaired') {
        enrichedData.phone_number = phoneResult.normalized_phone;
        enrichedData.phone_country = phoneResult.phone_country;
        enrichedData.phone_type = phoneResult.phone_type;
        enrichmentResults.repair_phone = phoneResult;
      }
    }

    // 3. Geocode address
    if (originalData.address || originalData.city) {
      const geocodeResult = await addressGeocoder.geocodeAddress(
        originalData.address,
        originalData.city,
        originalData.state,
        originalData.country
      );
      if (geocodeResult.status === 'geocoded') {
        enrichedData.latitude = geocodeResult.latitude;
        enrichedData.longitude = geocodeResult.longitude;
        enrichedData.formatted_address = geocodeResult.formatted_address;
        enrichedData.timezone = geocodeResult.timezone;
        enrichmentResults.geocode_address = geocodeResult;
      }
    }

    // Add enrichment metadata
    enrichedData.enriched_at = new Date().toISOString();
    enrichedData.enrichment_status = 'enriched';
    enrichedData.enrichment_results = enrichmentResults;

    // Update the company document
    await db.collection('company_raw_intake')
      .doc(data.company_unique_id)
      .update(enrichedData);

    // Create audit log
    await createEnrichmentAuditLog(
      data.company_unique_id,
      'enrich',
      originalData,
      enrichedData,
      'success',
      null,
      { operation_type: 'enrich_company' },
      { startTime, auth, requestId: data.request_id }
    );

    logger.info('Company enrichment successful:', { companyId: data.company_unique_id });

    return {
      success: true,
      company_unique_id: data.company_unique_id,
      enrichment_status: 'enriched',
      enriched_fields: Object.keys(enrichmentResults),
      processing_time_ms: Date.now() - startTime,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Company enrichment error:', error);

    // Create error audit log
    await createEnrichmentAuditLog(
      data.company_unique_id,
      'enrich',
      {},
      {},
      'failed',
      {
        error_code: 'ENRICHMENT_ERROR',
        error_message: error.message,
        error_type: 'system_error',
        retry_possible: true
      },
      { operation_type: 'enrich_company' },
      { startTime, auth, requestId: data.request_id }
    );

    throw error;
  }
});

/**
 * Cloud Function: Enrich Person
 */
export const enrichPerson = onCall({
  memory: '1GiB',
  timeoutSeconds: 120,
  maxInstances: 20
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'enrichPerson');

    logger.info('Starting person enrichment:', { personId: data.person_unique_id });

    // Get person document from intake collection
    const personDoc = await db.collection('people_raw_intake')
      .doc(data.person_unique_id)
      .get();

    if (!personDoc.exists) {
      throw new Error(`Person document not found: ${data.person_unique_id}`);
    }

    const originalData = personDoc.data();
    const enrichedData = { ...originalData };
    const enrichmentResults = {};

    // Initialize enrichment utilities
    const phoneRepairer = new PhoneRepairer();
    const slotTypeInferrer = new SlotTypeInferrer();
    const seniorityDeterminer = new SeniorityDeterminer();

    // 1. Infer slot type
    if (originalData.job_title) {
      const slotResult = slotTypeInferrer.inferSlotType(originalData.job_title, originalData.company_name);
      if (slotResult.status === 'classified' || slotResult.status === 'default') {
        enrichedData.slot_type = slotResult.slot_type;
        enrichedData.role_category = slotResult.role_category;
        enrichedData.department = slotResult.department;
        enrichmentResults.infer_slot_type = slotResult;
      }
    }

    // 2. Determine seniority
    if (originalData.job_title) {
      const seniorityResult = seniorityDeterminer.determineSeniority(originalData.job_title);
      if (seniorityResult.status === 'classified' || seniorityResult.status === 'default') {
        enrichedData.seniority_level = seniorityResult.seniority_level;
        enrichedData.management_level = seniorityResult.management_level;
        enrichedData.years_experience_estimate = seniorityResult.years_experience_estimate;
        enrichmentResults.determine_seniority = seniorityResult;
      }
    }

    // 3. Normalize phone number
    if (originalData.phone_number) {
      const phoneResult = phoneRepairer.repairPhone(originalData.phone_number);
      if (phoneResult.status === 'valid' || phoneResult.status === 'repaired') {
        enrichedData.phone_number = phoneResult.normalized_phone;
        enrichedData.phone_country = phoneResult.phone_country;
        enrichedData.phone_type = phoneResult.phone_type;
        enrichmentResults.normalize_phone = phoneResult;
      }
    }

    // 4. Normalize email (basic validation)
    if (originalData.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (emailRegex.test(originalData.email)) {
        enrichedData.email = originalData.email.toLowerCase().trim();
        enrichedData.email_domain = originalData.email.split('@')[1];
        enrichedData.email_status = 'valid';
        enrichmentResults.normalize_email = {
          status: 'normalized',
          error: null
        };
      }
    }

    // Add enrichment metadata
    enrichedData.enriched_at = new Date().toISOString();
    enrichedData.enrichment_status = 'enriched';
    enrichedData.enrichment_results = enrichmentResults;

    // Update the person document
    await db.collection('people_raw_intake')
      .doc(data.person_unique_id)
      .update(enrichedData);

    // Create audit log
    await createEnrichmentAuditLog(
      data.person_unique_id,
      'enrich',
      originalData,
      enrichedData,
      'success',
      null,
      { operation_type: 'enrich_person' },
      { startTime, auth, requestId: data.request_id }
    );

    logger.info('Person enrichment successful:', { personId: data.person_unique_id });

    return {
      success: true,
      person_unique_id: data.person_unique_id,
      enrichment_status: 'enriched',
      enriched_fields: Object.keys(enrichmentResults),
      processing_time_ms: Date.now() - startTime,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Person enrichment error:', error);

    // Create error audit log
    await createEnrichmentAuditLog(
      data.person_unique_id,
      'enrich',
      {},
      {},
      'failed',
      {
        error_code: 'ENRICHMENT_ERROR',
        error_message: error.message,
        error_type: 'system_error',
        retry_possible: true
      },
      { operation_type: 'enrich_person' },
      { startTime, auth, requestId: data.request_id }
    );

    throw error;
  }
});

/**
 * Export enrichment utilities for testing
 */
export {
  DomainNormalizer,
  PhoneRepairer,
  AddressGeocoder,
  SlotTypeInferrer,
  SeniorityDeterminer
};