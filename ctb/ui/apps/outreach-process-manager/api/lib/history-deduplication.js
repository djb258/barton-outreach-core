/**
 * History Deduplication and Retrieval Logic
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.XXXXX.XXX
 * - Altitude: 10000 (History Analysis Layer)
 * - Input: historical field values and confidence scores
 * - Output: deduplicated recommendations and retrieval results
 * - MCP: History tracking through Composio integration
 */

import HistoryMCPClient from './history-mcp-client.js';

class HistoryDeduplication {
  constructor() {
    this.historyClient = new HistoryMCPClient();
    this.confidenceThreshold = 0.8;
    this.sourceReliability = {
      'manual_input': 1.0,
      'apollo': 0.95,
      'clearbit': 0.9,
      'millionverify': 0.9,
      'linkedin_scraper': 0.85,
      'hunter_io': 0.85,
      'apify': 0.8,
      'api_integration': 0.8,
      'enrichment_api': 0.75,
      'web_scraper': 0.7,
      'csv_import': 0.6,
      'unknown': 0.5
    };
  }

  /**
   * Main deduplication logic for field values
   */
  async deduplicateFieldValues(entityId, field, entityType = 'company') {
    try {
      // Get all historical values for this field
      const historyTimeline = await this.historyClient.getHistoryTimeline(entityId, entityType, {
        field: field,
        limit: 100
      });

      if (!historyTimeline.success || !historyTimeline.data || historyTimeline.data.length === 0) {
        return {
          success: true,
          recommendation: 'no_history',
          message: 'No historical data found for this field',
          confidence: 0,
          suggested_value: null
        };
      }

      const values = historyTimeline.data;

      // Analyze values for deduplication
      const analysis = this.analyzeValueHistory(values);

      // Generate deduplication recommendation
      const recommendation = this.generateRecommendation(analysis);

      return {
        success: true,
        recommendation: recommendation.type,
        message: recommendation.message,
        confidence: recommendation.confidence,
        suggested_value: recommendation.value,
        analysis: analysis,
        alternatives: recommendation.alternatives
      };

    } catch (error) {
      console.error('Deduplication error:', error);
      return {
        success: false,
        error: error.message,
        recommendation: 'error',
        confidence: 0
      };
    }
  }

  /**
   * Analyze historical values to identify patterns and duplicates
   */
  analyzeValueHistory(values) {
    const analysis = {
      total_entries: values.length,
      unique_values: new Set(),
      value_frequency: {},
      source_breakdown: {},
      confidence_trends: [],
      timeline_analysis: {},
      potential_duplicates: [],
      recommended_action: null
    };

    // Process each historical value
    values.forEach((entry, index) => {
      const value = this.normalizeValue(entry.value_found);
      const source = entry.source;
      const confidence = parseFloat(entry.confidence_score);
      const timestamp = new Date(entry.timestamp_found);

      // Track unique values
      analysis.unique_values.add(value);

      // Count value frequency
      if (!analysis.value_frequency[value]) {
        analysis.value_frequency[value] = {
          count: 0,
          sources: new Set(),
          highest_confidence: 0,
          latest_timestamp: null,
          entries: []
        };
      }

      analysis.value_frequency[value].count++;
      analysis.value_frequency[value].sources.add(source);
      analysis.value_frequency[value].highest_confidence = Math.max(
        analysis.value_frequency[value].highest_confidence,
        confidence
      );

      if (!analysis.value_frequency[value].latest_timestamp ||
          timestamp > analysis.value_frequency[value].latest_timestamp) {
        analysis.value_frequency[value].latest_timestamp = timestamp;
      }

      analysis.value_frequency[value].entries.push(entry);

      // Track sources
      if (!analysis.source_breakdown[source]) {
        analysis.source_breakdown[source] = {
          count: 0,
          avg_confidence: 0,
          values: new Set()
        };
      }
      analysis.source_breakdown[source].count++;
      analysis.source_breakdown[source].values.add(value);

      // Track confidence trends
      analysis.confidence_trends.push({
        timestamp: timestamp,
        confidence: confidence,
        source: source,
        value: value
      });
    });

    // Convert Sets to arrays for JSON serialization
    analysis.unique_values = Array.from(analysis.unique_values);

    Object.keys(analysis.value_frequency).forEach(value => {
      analysis.value_frequency[value].sources = Array.from(analysis.value_frequency[value].sources);
    });

    Object.keys(analysis.source_breakdown).forEach(source => {
      analysis.source_breakdown[source].values = Array.from(analysis.source_breakdown[source].values);
    });

    // Identify potential duplicates
    analysis.potential_duplicates = this.identifyDuplicates(analysis.value_frequency);

    return analysis;
  }

  /**
   * Generate deduplication recommendation based on analysis
   */
  generateRecommendation(analysis) {
    const values = Object.keys(analysis.value_frequency);

    if (values.length === 1) {
      // Only one unique value found
      const value = values[0];
      const valueData = analysis.value_frequency[value];

      return {
        type: 'single_value',
        message: `Single value found across ${valueData.count} entries`,
        confidence: valueData.highest_confidence,
        value: value,
        alternatives: []
      };
    }

    if (values.length === 2) {
      // Two values - check for simple variations
      const [value1, value2] = values;
      const similarity = this.calculateSimilarity(value1, value2);

      if (similarity > 0.9) {
        // High similarity - likely variations of same value
        const bestValue = this.selectBestValue(analysis.value_frequency);
        return {
          type: 'similar_values',
          message: `Two similar values found (${(similarity * 100).toFixed(1)}% similarity)`,
          confidence: bestValue.confidence,
          value: bestValue.value,
          alternatives: [value1, value2].filter(v => v !== bestValue.value)
        };
      }
    }

    // Multiple different values - need human review or confidence-based selection
    const bestValue = this.selectBestValue(analysis.value_frequency);

    if (bestValue.confidence >= this.confidenceThreshold) {
      return {
        type: 'high_confidence_selection',
        message: `Multiple values found, selected highest confidence (${(bestValue.confidence * 100).toFixed(1)}%)`,
        confidence: bestValue.confidence,
        value: bestValue.value,
        alternatives: values.filter(v => v !== bestValue.value)
      };
    }

    return {
      type: 'manual_review_required',
      message: `Multiple values with low confidence - manual review recommended`,
      confidence: bestValue.confidence,
      value: bestValue.value,
      alternatives: values.filter(v => v !== bestValue.value)
    };
  }

  /**
   * Select the best value based on confidence, recency, and source reliability
   */
  selectBestValue(valueFrequency) {
    let bestValue = null;
    let bestScore = 0;

    Object.keys(valueFrequency).forEach(value => {
      const data = valueFrequency[value];

      // Calculate composite score
      const confidenceScore = data.highest_confidence * 0.4;
      const frequencyScore = Math.min(data.count / 10, 1) * 0.2;
      const recencyScore = this.calculateRecencyScore(data.latest_timestamp) * 0.2;
      const sourceScore = this.calculateSourceScore(data.sources) * 0.2;

      const compositeScore = confidenceScore + frequencyScore + recencyScore + sourceScore;

      if (compositeScore > bestScore) {
        bestScore = compositeScore;
        bestValue = {
          value: value,
          confidence: data.highest_confidence,
          score: compositeScore,
          reasoning: {
            confidence: confidenceScore,
            frequency: frequencyScore,
            recency: recencyScore,
            source_reliability: sourceScore
          }
        };
      }
    });

    return bestValue;
  }

  /**
   * Calculate recency score (more recent = higher score)
   */
  calculateRecencyScore(timestamp) {
    if (!timestamp) return 0;

    const now = new Date();
    const ageInDays = (now - timestamp) / (1000 * 60 * 60 * 24);

    // Score decreases with age, 1.0 for today, 0.5 for 30 days ago
    return Math.max(0, 1 - (ageInDays / 60));
  }

  /**
   * Calculate source reliability score
   */
  calculateSourceScore(sources) {
    if (!sources || sources.length === 0) return 0;

    const scores = sources.map(source => this.sourceReliability[source] || 0.5);
    return Math.max(...scores);
  }

  /**
   * Identify potential duplicates with different representations
   */
  identifyDuplicates(valueFrequency) {
    const duplicates = [];
    const values = Object.keys(valueFrequency);

    for (let i = 0; i < values.length; i++) {
      for (let j = i + 1; j < values.length; j++) {
        const similarity = this.calculateSimilarity(values[i], values[j]);

        if (similarity > 0.8) {
          duplicates.push({
            value1: values[i],
            value2: values[j],
            similarity: similarity,
            type: this.identifyDuplicateType(values[i], values[j])
          });
        }
      }
    }

    return duplicates;
  }

  /**
   * Calculate similarity between two values
   */
  calculateSimilarity(value1, value2) {
    if (value1 === value2) return 1.0;

    const norm1 = this.normalizeValue(value1);
    const norm2 = this.normalizeValue(value2);

    if (norm1 === norm2) return 0.95;

    // Check for email variations
    if (this.isEmail(value1) && this.isEmail(value2)) {
      return this.calculateEmailSimilarity(value1, value2);
    }

    // Check for phone variations
    if (this.isPhone(value1) && this.isPhone(value2)) {
      return this.calculatePhoneSimilarity(value1, value2);
    }

    // Check for URL variations
    if (this.isURL(value1) && this.isURL(value2)) {
      return this.calculateURLSimilarity(value1, value2);
    }

    // Generic string similarity (Levenshtein-based)
    return this.calculateStringSimilarity(norm1, norm2);
  }

  /**
   * Normalize value for comparison
   */
  normalizeValue(value) {
    if (!value) return '';
    return String(value).toLowerCase().trim();
  }

  /**
   * Check if value is an email
   */
  isEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  /**
   * Check if value is a phone number
   */
  isPhone(value) {
    return /^[\+]?[\d\s\-\(\)]{10,}$/.test(value);
  }

  /**
   * Check if value is a URL
   */
  isURL(value) {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Calculate email similarity
   */
  calculateEmailSimilarity(email1, email2) {
    const [local1, domain1] = email1.toLowerCase().split('@');
    const [local2, domain2] = email2.toLowerCase().split('@');

    if (domain1 !== domain2) return 0.3; // Different domains

    // Same domain, check local part
    const localSim = this.calculateStringSimilarity(local1, local2);
    return 0.5 + (localSim * 0.5); // Domain match gives base 0.5, local similarity adds up to 0.5
  }

  /**
   * Calculate phone similarity
   */
  calculatePhoneSimilarity(phone1, phone2) {
    const clean1 = phone1.replace(/\D/g, '');
    const clean2 = phone2.replace(/\D/g, '');

    if (clean1 === clean2) return 1.0;

    // Check if one is extension of the other (country codes)
    if (clean1.length !== clean2.length) {
      const shorter = clean1.length < clean2.length ? clean1 : clean2;
      const longer = clean1.length > clean2.length ? clean1 : clean2;

      if (longer.endsWith(shorter)) return 0.9;
    }

    return this.calculateStringSimilarity(clean1, clean2);
  }

  /**
   * Calculate URL similarity
   */
  calculateURLSimilarity(url1, url2) {
    try {
      const u1 = new URL(url1);
      const u2 = new URL(url2);

      if (u1.hostname !== u2.hostname) return 0.2;
      if (u1.pathname === u2.pathname) return 0.95;

      return 0.5 + (this.calculateStringSimilarity(u1.pathname, u2.pathname) * 0.4);
    } catch {
      return this.calculateStringSimilarity(url1, url2);
    }
  }

  /**
   * Calculate string similarity using Levenshtein distance
   */
  calculateStringSimilarity(str1, str2) {
    const matrix = [];
    const len1 = str1.length;
    const len2 = str2.length;

    if (len1 === 0) return len2 === 0 ? 1 : 0;
    if (len2 === 0) return 0;

    // Initialize matrix
    for (let i = 0; i <= len1; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= len2; j++) {
      matrix[0][j] = j;
    }

    // Fill matrix
    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,     // deletion
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j - 1] + cost // substitution
        );
      }
    }

    const distance = matrix[len1][len2];
    const maxLen = Math.max(len1, len2);

    return 1 - (distance / maxLen);
  }

  /**
   * Identify type of duplicate
   */
  identifyDuplicateType(value1, value2) {
    if (this.isEmail(value1) && this.isEmail(value2)) {
      const [, domain1] = value1.split('@');
      const [, domain2] = value2.split('@');
      return domain1 === domain2 ? 'email_local_variation' : 'email_domain_variation';
    }

    if (this.isPhone(value1) && this.isPhone(value2)) {
      return 'phone_format_variation';
    }

    if (this.isURL(value1) && this.isURL(value2)) {
      return 'url_variation';
    }

    return 'text_variation';
  }

  /**
   * Get deduplication recommendation for scraping decision
   */
  async shouldSkipScraping(entityId, field, entityType = 'company', hoursThreshold = 24) {
    try {
      // Check if field was discovered recently
      const recentCheck = await this.historyClient.checkFieldDiscovered(
        entityId, field, entityType, hoursThreshold
      );

      if (!recentCheck.success) {
        return { skip: false, reason: 'check_failed' };
      }

      if (!recentCheck.data.found) {
        return { skip: false, reason: 'no_recent_discovery' };
      }

      // Get the latest value and its confidence
      const latest = await this.historyClient.getLatestFieldValue(entityId, field, entityType);

      if (!latest.success || !latest.data) {
        return { skip: false, reason: 'no_latest_value' };
      }

      const confidence = parseFloat(latest.data.confidence_score);
      const source = latest.data.source;

      // High confidence from reliable source = skip
      if (confidence >= this.confidenceThreshold &&
          this.sourceReliability[source] >= 0.8) {
        return {
          skip: true,
          reason: 'high_confidence_recent',
          details: {
            confidence: confidence,
            source: source,
            discovered_at: latest.data.timestamp_found,
            value: latest.data.value_found
          }
        };
      }

      return {
        skip: false,
        reason: 'low_confidence_or_unreliable_source',
        details: {
          confidence: confidence,
          source: source
        }
      };

    } catch (error) {
      console.error('Skip scraping check error:', error);
      return { skip: false, reason: 'error', error: error.message };
    }
  }
}

export default HistoryDeduplication;