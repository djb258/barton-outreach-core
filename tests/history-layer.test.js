/**
 * Comprehensive History Layer Testing Suite
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.XXXXX.XXX
 * - Altitude: Testing Layer
 * - Tests: Schema validation, MCP operations, deduplication logic
 * - Coverage: Firebase, Neon, MCP client, deduplication algorithms
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { HistoryValidator, HistoryUtils } from '../firebase/history-schema.js';
import HistoryMCPClient from '../apps/outreach-process-manager/api/lib/history-mcp-client.js';
import HistoryDeduplication from '../apps/outreach-process-manager/api/lib/history-deduplication.js';

// Mock data for testing
const mockCompanyHistoryEntry = {
  company_id: 'CMP-12345',
  field: 'email',
  value_found: 'contact@example.com',
  source: 'apollo',
  confidence_score: 0.95,
  process_id: 'HIST-123456789-ABC123',
  timestamp_found: new Date(),
  metadata: { verification_status: 'verified' }
};

const mockPersonHistoryEntry = {
  person_id: 'PER-67890',
  field: 'linkedin_url',
  value_found: 'https://linkedin.com/in/johndoe',
  source: 'linkedin_scraper',
  confidence_score: 0.85,
  process_id: 'HIST-123456789-DEF456',
  related_company_id: 'CMP-12345',
  timestamp_found: new Date(),
  metadata: { profile_verified: true }
};

describe('History Schema Validation', () => {
  describe('Company History Validation', () => {
    it('should validate valid company history entry', () => {
      const result = HistoryValidator.validateCompanyHistoryEntry(mockCompanyHistoryEntry);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject entry with invalid company_id format', () => {
      const invalidEntry = { ...mockCompanyHistoryEntry, company_id: 'INVALID_ID' };
      const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('company_id must match pattern: CMP- or company_');
    });

    it('should reject entry with invalid field enum', () => {
      const invalidEntry = { ...mockCompanyHistoryEntry, field: 'invalid_field' };
      const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.includes('field must be one of'))).toBe(true);
    });

    it('should reject entry with invalid source enum', () => {
      const invalidEntry = { ...mockCompanyHistoryEntry, source: 'invalid_source' };
      const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.includes('source must be one of'))).toBe(true);
    });

    it('should reject entry with invalid confidence score', () => {
      const invalidEntry = { ...mockCompanyHistoryEntry, confidence_score: 1.5 };
      const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('confidence_score must be a number between 0.0 and 1.0');
    });

    it('should reject entry without required fields', () => {
      const invalidEntry = { field: 'email' }; // Missing required fields
      const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('company_id is required');
      expect(result.errors).toContain('value_found is required');
      expect(result.errors).toContain('source is required');
    });
  });

  describe('Person History Validation', () => {
    it('should validate valid person history entry', () => {
      const result = HistoryValidator.validatePersonHistoryEntry(mockPersonHistoryEntry);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject entry with invalid person_id format', () => {
      const invalidEntry = { ...mockPersonHistoryEntry, person_id: 'INVALID_ID' };
      const result = HistoryValidator.validatePersonHistoryEntry(invalidEntry);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('person_id must match pattern: PER- or person_');
    });

    it('should validate all person field enums', () => {
      const validFields = [
        'email', 'phone', 'linkedin_url', 'first_name', 'last_name', 'full_name',
        'title', 'department', 'seniority_level', 'company_email', 'personal_email'
      ];

      validFields.forEach(field => {
        const entry = { ...mockPersonHistoryEntry, field };
        const result = HistoryValidator.validatePersonHistoryEntry(entry);
        expect(result.isValid).toBe(true);
      });
    });
  });

  describe('History Utils', () => {
    it('should generate valid history ID', () => {
      const id = HistoryUtils.generateHistoryId();
      expect(id).toMatch(/^HIST-\d+-[A-Z0-9]+$/);
    });

    it('should format history entry with defaults', () => {
      const entry = { company_id: 'CMP-123', field: 'email', value_found: 'test@example.com', source: 'apollo' };
      const formatted = HistoryUtils.formatHistoryEntry(entry);

      expect(formatted.confidence_score).toBe(1.0);
      expect(formatted.change_reason).toBe('initial_discovery');
      expect(formatted.metadata).toEqual({});
      expect(formatted.timestamp_found).toBeDefined();
    });

    it('should detect value changes correctly', () => {
      expect(HistoryUtils.isValueChanged('new@example.com', 'old@example.com')).toBe(true);
      expect(HistoryUtils.isValueChanged('same@example.com', 'same@example.com')).toBe(false);
      expect(HistoryUtils.isValueChanged('value', null)).toBe(true);
      expect(HistoryUtils.isValueChanged('  value  ', 'value')).toBe(false); // Trimmed comparison
    });

    it('should calculate confidence scores correctly', () => {
      expect(HistoryUtils.calculateConfidenceScore('manual_input')).toBe(1.0);
      expect(HistoryUtils.calculateConfidenceScore('apollo')).toBe(0.95);
      expect(HistoryUtils.calculateConfidenceScore('unknown_source')).toBe(0.5);

      // With validation results
      const score = HistoryUtils.calculateConfidenceScore('apollo', {
        email_verified: true,
        phone_verified: true
      });
      expect(score).toBe(1.0); // 0.95 + 0.1 + 0.1 = 1.15, capped at 1.0
    });
  });
});

describe('History MCP Client', () => {
  let historyClient;

  beforeEach(() => {
    historyClient = new HistoryMCPClient();
    // Mock the MCP server calls
    historyClient.callMCPServer = jest.fn().mockResolvedValue({
      success: true,
      data: {},
      metadata: {}
    });
  });

  describe('Company History Operations', () => {
    it('should add company history entry', async () => {
      const result = await historyClient.addCompanyHistoryEntry(
        'CMP-12345',
        'email',
        'contact@example.com',
        'apollo',
        { confidenceScore: 0.95 }
      );

      expect(historyClient.callMCPServer).toHaveBeenCalledWith(
        expect.objectContaining({
          tool: 'history.add_company_entry',
          params: expect.objectContaining({
            entry: expect.objectContaining({
              company_id: 'CMP-12345',
              field: 'email',
              value_found: 'contact@example.com',
              source: 'apollo',
              confidence_score: 0.95
            })
          })
        })
      );

      expect(result.success).toBe(true);
    });

    it('should check field discovery', async () => {
      historyClient.callMCPServer.mockResolvedValue({
        success: true,
        data: { found: true, timestamp: new Date() }
      });

      const result = await historyClient.checkFieldDiscovered('CMP-12345', 'email', 'company', 24);

      expect(historyClient.callMCPServer).toHaveBeenCalledWith(
        expect.objectContaining({
          tool: 'history.check_field_discovered',
          params: expect.objectContaining({
            entity_id: 'CMP-12345',
            field: 'email',
            entity_type: 'company',
            hours_threshold: 24
          })
        })
      );

      expect(result.success).toBe(true);
    });
  });

  describe('Person History Operations', () => {
    it('should add person history entry', async () => {
      const result = await historyClient.addPersonHistoryEntry(
        'PER-67890',
        'linkedin_url',
        'https://linkedin.com/in/johndoe',
        'linkedin_scraper',
        { confidenceScore: 0.85, relatedCompanyId: 'CMP-12345' }
      );

      expect(historyClient.callMCPServer).toHaveBeenCalledWith(
        expect.objectContaining({
          tool: 'history.add_person_entry',
          params: expect.objectContaining({
            entry: expect.objectContaining({
              person_id: 'PER-67890',
              field: 'linkedin_url',
              related_company_id: 'CMP-12345'
            })
          })
        })
      );

      expect(result.success).toBe(true);
    });
  });

  describe('Batch Operations', () => {
    it('should handle batch history entries', async () => {
      const entries = [
        { company_id: 'CMP-1', field: 'email', value_found: 'test1@example.com', source: 'apollo' },
        { company_id: 'CMP-2', field: 'email', value_found: 'test2@example.com', source: 'apollo' }
      ];

      const result = await historyClient.batchAddHistoryEntries(entries, 'company');

      expect(historyClient.callMCPServer).toHaveBeenCalledWith(
        expect.objectContaining({
          tool: 'history.batch_add_entries',
          params: expect.objectContaining({
            entity_type: 'company',
            entries: expect.arrayContaining([
              expect.objectContaining({ company_id: 'CMP-1' }),
              expect.objectContaining({ company_id: 'CMP-2' })
            ])
          })
        })
      );

      expect(result.success).toBe(true);
    });
  });

  describe('ID Generation', () => {
    it('should generate valid Barton IDs', () => {
      const id = historyClient.generateBartonId();
      expect(id).toMatch(/^\d{2}\.\d{2}\.\d{2}\.07\.\d{5}\.\d{3}$/);
    });

    it('should generate unique process IDs', () => {
      const id1 = historyClient.generateProcessId();
      const id2 = historyClient.generateProcessId();

      expect(id1).toMatch(/^HIST-\d+-[A-Z0-9]+$/);
      expect(id2).toMatch(/^HIST-\d+-[A-Z0-9]+$/);
      expect(id1).not.toBe(id2);
    });
  });

  describe('Confidence Calculation', () => {
    it('should calculate confidence scores with validation', () => {
      const score = historyClient.calculateConfidenceScore('apollo', {
        email_verified: true,
        phone_verified: false,
        domain_verified: true
      });

      expect(score).toBe(1.0); // 0.95 + 0.1 + 0.05 = 1.1, capped at 1.0
    });
  });
});

describe('History Deduplication', () => {
  let deduplication;

  beforeEach(() => {
    deduplication = new HistoryDeduplication();
    // Mock the history client
    deduplication.historyClient.getHistoryTimeline = jest.fn();
  });

  describe('Value Analysis', () => {
    it('should analyze single value history correctly', () => {
      const values = [
        { value_found: 'test@example.com', source: 'apollo', confidence_score: 0.95, timestamp_found: new Date() }
      ];

      const analysis = deduplication.analyzeValueHistory(values);

      expect(analysis.total_entries).toBe(1);
      expect(analysis.unique_values).toEqual(['test@example.com']);
      expect(analysis.value_frequency['test@example.com'].count).toBe(1);
      expect(analysis.value_frequency['test@example.com'].highest_confidence).toBe(0.95);
    });

    it('should identify duplicate values', () => {
      const values = [
        { value_found: 'test@example.com', source: 'apollo', confidence_score: 0.95, timestamp_found: new Date() },
        { value_found: 'test@example.com', source: 'clearbit', confidence_score: 0.90, timestamp_found: new Date() },
        { value_found: 'other@example.com', source: 'hunter_io', confidence_score: 0.85, timestamp_found: new Date() }
      ];

      const analysis = deduplication.analyzeValueHistory(values);

      expect(analysis.total_entries).toBe(3);
      expect(analysis.unique_values).toHaveLength(2);
      expect(analysis.value_frequency['test@example.com'].count).toBe(2);
      expect(analysis.value_frequency['test@example.com'].sources).toEqual(['apollo', 'clearbit']);
      expect(analysis.value_frequency['test@example.com'].highest_confidence).toBe(0.95);
    });
  });

  describe('Similarity Calculation', () => {
    it('should detect identical values', () => {
      const similarity = deduplication.calculateSimilarity('test@example.com', 'test@example.com');
      expect(similarity).toBe(1.0);
    });

    it('should detect email variations', () => {
      const similarity = deduplication.calculateSimilarity('john.doe@example.com', 'johndoe@example.com');
      expect(similarity).toBeGreaterThan(0.7);
    });

    it('should detect phone number variations', () => {
      const similarity = deduplication.calculateSimilarity('+1-555-123-4567', '(555) 123-4567');
      expect(similarity).toBeGreaterThan(0.8);
    });

    it('should detect URL variations', () => {
      const similarity = deduplication.calculateSimilarity(
        'https://www.example.com/page',
        'http://example.com/page'
      );
      expect(similarity).toBeGreaterThan(0.7);
    });
  });

  describe('Deduplication Recommendations', () => {
    it('should recommend single value when only one exists', async () => {
      deduplication.historyClient.getHistoryTimeline.mockResolvedValue({
        success: true,
        data: [
          { value_found: 'test@example.com', source: 'apollo', confidence_score: 0.95, timestamp_found: new Date() }
        ]
      });

      const result = await deduplication.deduplicateFieldValues('CMP-12345', 'email');

      expect(result.success).toBe(true);
      expect(result.recommendation).toBe('single_value');
      expect(result.suggested_value).toBe('test@example.com');
      expect(result.confidence).toBe(0.95);
    });

    it('should handle no history case', async () => {
      deduplication.historyClient.getHistoryTimeline.mockResolvedValue({
        success: true,
        data: []
      });

      const result = await deduplication.deduplicateFieldValues('CMP-12345', 'email');

      expect(result.success).toBe(true);
      expect(result.recommendation).toBe('no_history');
      expect(result.suggested_value).toBeNull();
    });

    it('should recommend high confidence selection', async () => {
      const now = new Date();
      deduplication.historyClient.getHistoryTimeline.mockResolvedValue({
        success: true,
        data: [
          { value_found: 'high@example.com', source: 'manual_input', confidence_score: 1.0, timestamp_found: now },
          { value_found: 'low@example.com', source: 'web_scraper', confidence_score: 0.6, timestamp_found: new Date(now - 86400000) }
        ]
      });

      const result = await deduplication.deduplicateFieldValues('CMP-12345', 'email');

      expect(result.success).toBe(true);
      expect(result.recommendation).toBe('high_confidence_selection');
      expect(result.suggested_value).toBe('high@example.com');
      expect(result.alternatives).toContain('low@example.com');
    });
  });

  describe('Scraping Decision Logic', () => {
    it('should recommend skipping for high confidence recent discovery', async () => {
      deduplication.historyClient.checkFieldDiscovered.mockResolvedValue({
        success: true,
        data: { found: true }
      });

      deduplication.historyClient.getLatestFieldValue.mockResolvedValue({
        success: true,
        data: {
          confidence_score: 0.95,
          source: 'apollo',
          timestamp_found: new Date(),
          value_found: 'test@example.com'
        }
      });

      const result = await deduplication.shouldSkipScraping('CMP-12345', 'email', 'company', 24);

      expect(result.skip).toBe(true);
      expect(result.reason).toBe('high_confidence_recent');
      expect(result.details.confidence).toBe(0.95);
    });

    it('should not skip for low confidence discovery', async () => {
      deduplication.historyClient.checkFieldDiscovered.mockResolvedValue({
        success: true,
        data: { found: true }
      });

      deduplication.historyClient.getLatestFieldValue.mockResolvedValue({
        success: true,
        data: {
          confidence_score: 0.5,
          source: 'web_scraper',
          timestamp_found: new Date(),
          value_found: 'test@example.com'
        }
      });

      const result = await deduplication.shouldSkipScraping('CMP-12345', 'email', 'company', 24);

      expect(result.skip).toBe(false);
      expect(result.reason).toBe('low_confidence_or_unreliable_source');
    });

    it('should not skip when no recent discovery found', async () => {
      deduplication.historyClient.checkFieldDiscovered.mockResolvedValue({
        success: true,
        data: { found: false }
      });

      const result = await deduplication.shouldSkipScraping('CMP-12345', 'email', 'company', 24);

      expect(result.skip).toBe(false);
      expect(result.reason).toBe('no_recent_discovery');
    });
  });

  describe('Type Detection', () => {
    it('should detect email format', () => {
      expect(deduplication.isEmail('test@example.com')).toBe(true);
      expect(deduplication.isEmail('not-an-email')).toBe(false);
    });

    it('should detect phone format', () => {
      expect(deduplication.isPhone('+1-555-123-4567')).toBe(true);
      expect(deduplication.isPhone('(555) 123-4567')).toBe(true);
      expect(deduplication.isPhone('not-a-phone')).toBe(false);
    });

    it('should detect URL format', () => {
      expect(deduplication.isURL('https://example.com')).toBe(true);
      expect(deduplication.isURL('http://example.com/page')).toBe(true);
      expect(deduplication.isURL('not-a-url')).toBe(false);
    });
  });
});

describe('Integration Tests', () => {
  let historyClient;
  let deduplication;

  beforeEach(() => {
    historyClient = new HistoryMCPClient();
    deduplication = new HistoryDeduplication();
  });

  it('should complete full history workflow', async () => {
    // Mock successful history tracking
    historyClient.callMCPServer = jest.fn().mockResolvedValue({
      success: true,
      data: { id: 'HIST-123' }
    });

    // 1. Add history entry
    const addResult = await historyClient.addCompanyHistoryEntry(
      'CMP-12345',
      'email',
      'contact@example.com',
      'apollo'
    );

    expect(addResult.success).toBe(true);

    // 2. Check if field should be skipped for scraping
    historyClient.checkFieldDiscovered = jest.fn().mockResolvedValue({
      success: true,
      data: { found: true }
    });

    historyClient.getLatestFieldValue = jest.fn().mockResolvedValue({
      success: true,
      data: {
        confidence_score: 0.95,
        source: 'apollo',
        value_found: 'contact@example.com'
      }
    });

    const skipResult = await deduplication.shouldSkipScraping('CMP-12345', 'email');
    expect(skipResult.skip).toBe(true);
  });

  it('should handle validation errors gracefully', () => {
    const invalidEntry = {
      company_id: 'INVALID',
      field: 'invalid_field',
      source: 'invalid_source'
    };

    const result = HistoryValidator.validateCompanyHistoryEntry(invalidEntry);
    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});

describe('Error Handling', () => {
  let historyClient;

  beforeEach(() => {
    historyClient = new HistoryMCPClient();
  });

  it('should handle MCP server errors', async () => {
    historyClient.callMCPServer = jest.fn().mockRejectedValue(new Error('MCP server error'));

    const result = await historyClient.addCompanyHistoryEntry('CMP-12345', 'email', 'test@example.com', 'apollo');

    // The method should catch and wrap the error
    expect(result).toBeUndefined(); // Method throws, doesn't return
  });

  it('should handle deduplication errors', async () => {
    const deduplication = new HistoryDeduplication();
    deduplication.historyClient.getHistoryTimeline = jest.fn().mockRejectedValue(new Error('Database error'));

    const result = await deduplication.deduplicateFieldValues('CMP-12345', 'email');

    expect(result.success).toBe(false);
    expect(result.recommendation).toBe('error');
    expect(result.error).toBe('Database error');
  });
});