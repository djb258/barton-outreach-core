/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-F9711C7F
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * History Layer Schema Definitions for Barton Doctrine Pipeline
 *
 * Purpose: Track when, where, and what information was discovered to prevent
 * redundant enrichment/scraping cycles and maintain data provenance.
 *
 * Architecture: Firestore (working memory) + Neon (vault) dual storage
 */

import { Timestamp } from 'firebase/firestore';

/**
 * Company History Schema (Firestore Collection: company_history)
 * Tracks all data discovery events for companies
 */
export const COMPANY_HISTORY_SCHEMA = {
  collection: 'company_history',

  fields: {
    company_id: {
      type: 'string',
      required: true,
      description: 'Foreign key to company intake/master record',
      validation: {
        pattern: /^(CMP-|company_).+/,
        maxLength: 100
      }
    },

    field: {
      type: 'string',
      required: true,
      description: 'Field name that was enriched/discovered',
      enum: [
        'domain',
        'email',
        'phone',
        'linkedin_url',
        'company_size',
        'industry',
        'address',
        'description',
        'logo_url',
        'website',
        'founded_year',
        'revenue',
        'employees',
        'technologies',
        'funding',
        'headquarters',
        'subsidiaries',
        'social_media',
        'contact_email',
        'sales_email',
        'support_email'
      ],
      validation: {
        maxLength: 50
      }
    },

    value_found: {
      type: 'string',
      required: true,
      description: 'The actual value that was discovered',
      validation: {
        maxLength: 5000
      }
    },

    source: {
      type: 'string',
      required: true,
      description: 'Source of the information discovery',
      enum: [
        'apify',
        'millionverify',
        'lindy',
        'manual_adjust',
        'apollo',
        'clearbit',
        'hunter_io',
        'enrichment_api',
        'linkedin_scraper',
        'company_scraper',
        'domain_analyzer',
        'email_finder',
        'web_scraper',
        'manual_input',
        'csv_import',
        'api_integration'
      ],
      validation: {
        maxLength: 50
      }
    },

    timestamp_found: {
      type: 'timestamp',
      required: true,
      description: 'When this information was discovered',
      default: () => Timestamp.now()
    },

    confidence_score: {
      type: 'number',
      required: true,
      description: 'Confidence level of the discovered information (0.0 - 1.0)',
      validation: {
        min: 0.0,
        max: 1.0
      },
      default: 1.0
    },

    // Additional metadata fields
    process_id: {
      type: 'string',
      required: false,
      description: 'Process ID that discovered this information',
      validation: {
        maxLength: 100
      }
    },

    session_id: {
      type: 'string',
      required: false,
      description: 'Session ID for grouping related discoveries',
      validation: {
        maxLength: 100
      }
    },

    previous_value: {
      type: 'string',
      required: false,
      description: 'Previous value if this is an update',
      validation: {
        maxLength: 5000
      }
    },

    change_reason: {
      type: 'string',
      required: false,
      description: 'Reason for value change if applicable',
      enum: [
        'initial_discovery',
        'enrichment_update',
        'correction',
        'verification',
        'manual_override',
        'data_refresh',
        'source_upgrade'
      ]
    },

    metadata: {
      type: 'object',
      required: false,
      description: 'Additional source-specific metadata'
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['company_id', 'field'] },
    { fields: ['company_id', 'timestamp_found'] },
    { fields: ['source', 'timestamp_found'] },
    { fields: ['field', 'confidence_score'] },
    { fields: ['company_id', 'field', 'timestamp_found'] }
  ],

  // Security rules
  security: {
    read: ['authenticated'],
    write: ['mcp_service_only'],
    create: ['mcp_service_only'],
    update: ['mcp_service_only'],
    delete: ['admin_only']
  }
};

/**
 * Person History Schema (Firestore Collection: person_history)
 * Tracks all data discovery events for people
 */
export const PERSON_HISTORY_SCHEMA = {
  collection: 'person_history',

  fields: {
    person_id: {
      type: 'string',
      required: true,
      description: 'Foreign key to person intake/master record',
      validation: {
        pattern: /^(PER-|person_).+/,
        maxLength: 100
      }
    },

    field: {
      type: 'string',
      required: true,
      description: 'Field name that was enriched/discovered',
      enum: [
        'email',
        'phone',
        'linkedin_url',
        'first_name',
        'last_name',
        'full_name',
        'title',
        'department',
        'seniority_level',
        'company_email',
        'personal_email',
        'work_phone',
        'mobile_phone',
        'social_profiles',
        'bio',
        'skills',
        'education',
        'experience',
        'location',
        'timezone',
        'profile_picture',
        'contact_preference',
        'email_status',
        'phone_status',
        'engagement_score',
        'lead_score'
      ],
      validation: {
        maxLength: 50
      }
    },

    value_found: {
      type: 'string',
      required: true,
      description: 'The actual value that was discovered',
      validation: {
        maxLength: 5000
      }
    },

    source: {
      type: 'string',
      required: true,
      description: 'Source of the information discovery',
      enum: [
        'apify',
        'millionverify',
        'lindy',
        'manual_adjust',
        'apollo',
        'clearbit',
        'hunter_io',
        'enrichment_api',
        'linkedin_scraper',
        'people_scraper',
        'email_verifier',
        'phone_verifier',
        'social_scraper',
        'manual_input',
        'csv_import',
        'api_integration',
        'lead_scoring_engine'
      ],
      validation: {
        maxLength: 50
      }
    },

    timestamp_found: {
      type: 'timestamp',
      required: true,
      description: 'When this information was discovered',
      default: () => Timestamp.now()
    },

    confidence_score: {
      type: 'number',
      required: true,
      description: 'Confidence level of the discovered information (0.0 - 1.0)',
      validation: {
        min: 0.0,
        max: 1.0
      },
      default: 1.0
    },

    // Additional metadata fields
    process_id: {
      type: 'string',
      required: false,
      description: 'Process ID that discovered this information',
      validation: {
        maxLength: 100
      }
    },

    session_id: {
      type: 'string',
      required: false,
      description: 'Session ID for grouping related discoveries',
      validation: {
        maxLength: 100
      }
    },

    previous_value: {
      type: 'string',
      required: false,
      description: 'Previous value if this is an update',
      validation: {
        maxLength: 5000
      }
    },

    change_reason: {
      type: 'string',
      required: false,
      description: 'Reason for value change if applicable',
      enum: [
        'initial_discovery',
        'enrichment_update',
        'correction',
        'verification',
        'manual_override',
        'data_refresh',
        'source_upgrade'
      ]
    },

    related_company_id: {
      type: 'string',
      required: false,
      description: 'Associated company ID if applicable',
      validation: {
        maxLength: 100
      }
    },

    metadata: {
      type: 'object',
      required: false,
      description: 'Additional source-specific metadata'
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['person_id', 'field'] },
    { fields: ['person_id', 'timestamp_found'] },
    { fields: ['source', 'timestamp_found'] },
    { fields: ['field', 'confidence_score'] },
    { fields: ['person_id', 'field', 'timestamp_found'] },
    { fields: ['related_company_id', 'field'] }
  ],

  // Security rules
  security: {
    read: ['authenticated'],
    write: ['mcp_service_only'],
    create: ['mcp_service_only'],
    update: ['mcp_service_only'],
    delete: ['admin_only']
  }
};

/**
 * Validation functions for history entries
 */
export class HistoryValidator {

  static validateCompanyHistoryEntry(entry) {
    const errors = [];

    // Required fields validation
    if (!entry.company_id) {
      errors.push('company_id is required');
    } else if (!COMPANY_HISTORY_SCHEMA.fields.company_id.validation.pattern.test(entry.company_id)) {
      errors.push('company_id must match pattern: CMP- or company_');
    }

    if (!entry.field) {
      errors.push('field is required');
    } else if (!COMPANY_HISTORY_SCHEMA.fields.field.enum.includes(entry.field)) {
      errors.push(`field must be one of: ${COMPANY_HISTORY_SCHEMA.fields.field.enum.join(', ')}`);
    }

    if (!entry.value_found) {
      errors.push('value_found is required');
    } else if (entry.value_found.length > COMPANY_HISTORY_SCHEMA.fields.value_found.validation.maxLength) {
      errors.push('value_found exceeds maximum length');
    }

    if (!entry.source) {
      errors.push('source is required');
    } else if (!COMPANY_HISTORY_SCHEMA.fields.source.enum.includes(entry.source)) {
      errors.push(`source must be one of: ${COMPANY_HISTORY_SCHEMA.fields.source.enum.join(', ')}`);
    }

    // Confidence score validation
    if (entry.confidence_score !== undefined) {
      if (typeof entry.confidence_score !== 'number' ||
          entry.confidence_score < 0 ||
          entry.confidence_score > 1) {
        errors.push('confidence_score must be a number between 0.0 and 1.0');
      }
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  static validatePersonHistoryEntry(entry) {
    const errors = [];

    // Required fields validation
    if (!entry.person_id) {
      errors.push('person_id is required');
    } else if (!PERSON_HISTORY_SCHEMA.fields.person_id.validation.pattern.test(entry.person_id)) {
      errors.push('person_id must match pattern: PER- or person_');
    }

    if (!entry.field) {
      errors.push('field is required');
    } else if (!PERSON_HISTORY_SCHEMA.fields.field.enum.includes(entry.field)) {
      errors.push(`field must be one of: ${PERSON_HISTORY_SCHEMA.fields.field.enum.join(', ')}`);
    }

    if (!entry.value_found) {
      errors.push('value_found is required');
    } else if (entry.value_found.length > PERSON_HISTORY_SCHEMA.fields.value_found.validation.maxLength) {
      errors.push('value_found exceeds maximum length');
    }

    if (!entry.source) {
      errors.push('source is required');
    } else if (!PERSON_HISTORY_SCHEMA.fields.source.enum.includes(entry.source)) {
      errors.push(`source must be one of: ${PERSON_HISTORY_SCHEMA.fields.source.enum.join(', ')}`);
    }

    // Confidence score validation
    if (entry.confidence_score !== undefined) {
      if (typeof entry.confidence_score !== 'number' ||
          entry.confidence_score < 0 ||
          entry.confidence_score > 1) {
        errors.push('confidence_score must be a number between 0.0 and 1.0');
      }
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }
}

/**
 * History utility functions
 */
export class HistoryUtils {

  static generateHistoryId() {
    return `HIST-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  }

  static formatHistoryEntry(entry, type = 'company') {
    return {
      ...entry,
      timestamp_found: entry.timestamp_found || Timestamp.now(),
      confidence_score: entry.confidence_score || 1.0,
      change_reason: entry.change_reason || 'initial_discovery',
      metadata: entry.metadata || {}
    };
  }

  static isValueChanged(newValue, oldValue) {
    if (!oldValue) return true;
    return String(newValue).trim() !== String(oldValue).trim();
  }

  static calculateConfidenceScore(source, validationResults = {}) {
    const sourceConfidence = {
      'manual_input': 1.0,
      'csv_import': 0.9,
      'apollo': 0.95,
      'clearbit': 0.9,
      'linkedin_scraper': 0.85,
      'apify': 0.8,
      'hunter_io': 0.85,
      'millionverify': 0.9,
      'enrichment_api': 0.75,
      'web_scraper': 0.7,
      'api_integration': 0.8
    };

    let baseScore = sourceConfidence[source] || 0.5;

    // Adjust based on validation results
    if (validationResults.email_verified === true) baseScore += 0.1;
    if (validationResults.phone_verified === true) baseScore += 0.1;
    if (validationResults.domain_verified === true) baseScore += 0.05;

    return Math.min(baseScore, 1.0);
  }
}

export default {
  COMPANY_HISTORY_SCHEMA,
  PERSON_HISTORY_SCHEMA,
  HistoryValidator,
  HistoryUtils
};