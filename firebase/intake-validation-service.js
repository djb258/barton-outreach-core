/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.07.10000.008
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2 validation and enforcement service for intake operations
 * - Input: Intake data validation and enforcement requests
 * - Output: Comprehensive validation results and enforcement actions
 * - MCP: Firebase (Composio-only validation)
 */

import { STEP_2_SCHEMAS, validateIntakeDocument, INTAKE_STATUS, INTAKE_ACTIONS } from './intake-schema.js';

class IntakeValidationService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.validationRules = this.initializeValidationRules();
    this.enforcementPolicies = this.initializeEnforcementPolicies();
  }

  /**
   * Initialize validation rules for intake operations
   */
  initializeValidationRules() {
    return {
      company: {
        required_fields: ['company_name', 'website_url', 'industry', 'company_size', 'headquarters_location'],
        optional_fields: ['linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url'],
        validation_patterns: {
          company_name: /^.{1,500}$/,
          website_url: /^https?:\/\/.+/,
          industry: /^.{1,200}$/,
          headquarters_location: /^.{1,200}$/,
          linkedin_url: /^https:\/\/(www\.)?linkedin\.com\/company\/.+$/,
          twitter_url: /^https:\/\/(www\.)?(twitter\.com|x\.com)\/.+$/,
          facebook_url: /^https:\/\/(www\.)?facebook\.com\/.+$/,
          instagram_url: /^https:\/\/(www\.)?instagram\.com\/.+$/
        },
        business_rules: {
          duplicate_detection: true,
          domain_validation: true,
          social_profile_validation: true,
          company_size_validation: true
        }
      },
      person: {
        required_fields: ['full_name', 'email_address', 'job_title', 'company_name', 'location'],
        optional_fields: ['linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url', 'associated_company_id'],
        validation_patterns: {
          full_name: /^.{1,300}$/,
          email_address: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
          job_title: /^.{1,200}$/,
          company_name: /^.{1,500}$/,
          location: /^.{1,200}$/,
          linkedin_url: /^https:\/\/(www\.)?linkedin\.com\/in\/.+$/,
          twitter_url: /^https:\/\/(www\.)?(twitter\.com|x\.com)\/.+$/,
          facebook_url: /^https:\/\/(www\.)?facebook\.com\/.+$/,
          instagram_url: /^https:\/\/(www\.)?instagram\.com\/.+$/,
          associated_company_id: /^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$/
        },
        business_rules: {
          duplicate_detection: true,
          email_validation: true,
          social_profile_validation: true,
          company_association_validation: true
        }
      }
    };
  }

  /**
   * Initialize enforcement policies
   */
  initializeEnforcementPolicies() {
    return {
      mcp_only_access: {
        enabled: true,
        strict_mode: true,
        allowed_sources: ['composio_mcp_ingestion', 'composio_mcp_endpoint', 'composio_mcp_service'],
        blocked_sources: ['direct_client', 'sdk_access', 'manual_insert']
      },
      data_quality_enforcement: {
        enabled: true,
        reject_invalid_data: true,
        quarantine_suspicious_data: true,
        auto_clean_data: false
      },
      duplicate_prevention: {
        enabled: true,
        check_email_duplicates: true,
        check_domain_duplicates: true,
        check_social_profile_duplicates: true,
        fuzzy_name_matching: true
      },
      rate_limiting: {
        enabled: true,
        max_intake_per_minute: 100,
        max_batch_size: 100,
        cool_down_period_seconds: 60
      },
      security_enforcement: {
        enabled: true,
        scan_for_malicious_content: true,
        validate_external_urls: true,
        check_domain_reputation: false,
        pii_detection: true
      }
    };
  }

  /**
   * Comprehensive company intake validation
   */
  async validateCompanyIntake(companyData, context = {}) {
    console.log('[INTAKE-VALIDATION] Validating company intake...');

    const validationResult = {
      valid: true,
      errors: [],
      warnings: [],
      recommendations: [],
      enforcement_actions: [],
      data_quality_score: 0,
      validation_timestamp: new Date().toISOString()
    };

    try {
      // 1. Schema Validation
      await this.validateCompanySchema(companyData, validationResult);

      // 2. Business Rules Validation
      await this.validateCompanyBusinessRules(companyData, validationResult, context);

      // 3. Data Quality Assessment
      await this.assessCompanyDataQuality(companyData, validationResult);

      // 4. Security Validation
      await this.validateCompanySecurity(companyData, validationResult);

      // 5. Duplicate Detection
      await this.detectCompanyDuplicates(companyData, validationResult, context);

      // 6. MCP Access Enforcement
      await this.enforceCompanyMCPAccess(context, validationResult);

      // Calculate overall validation score
      validationResult.data_quality_score = this.calculateDataQualityScore(validationResult);

      // Apply enforcement policies
      await this.applyCompanyEnforcementPolicies(companyData, validationResult, context);

      return validationResult;

    } catch (error) {
      validationResult.valid = false;
      validationResult.errors.push(`Validation system error: ${error.message}`);
      return validationResult;
    }
  }

  /**
   * Comprehensive person intake validation
   */
  async validatePersonIntake(personData, context = {}) {
    console.log('[INTAKE-VALIDATION] Validating person intake...');

    const validationResult = {
      valid: true,
      errors: [],
      warnings: [],
      recommendations: [],
      enforcement_actions: [],
      data_quality_score: 0,
      validation_timestamp: new Date().toISOString()
    };

    try {
      // 1. Schema Validation
      await this.validatePersonSchema(personData, validationResult);

      // 2. Business Rules Validation
      await this.validatePersonBusinessRules(personData, validationResult, context);

      // 3. Data Quality Assessment
      await this.assessPersonDataQuality(personData, validationResult);

      // 4. Security Validation
      await this.validatePersonSecurity(personData, validationResult);

      // 5. Duplicate Detection
      await this.detectPersonDuplicates(personData, validationResult, context);

      // 6. MCP Access Enforcement
      await this.enforcePersonMCPAccess(context, validationResult);

      // Calculate overall validation score
      validationResult.data_quality_score = this.calculateDataQualityScore(validationResult);

      // Apply enforcement policies
      await this.applyPersonEnforcementPolicies(personData, validationResult, context);

      return validationResult;

    } catch (error) {
      validationResult.valid = false;
      validationResult.errors.push(`Validation system error: ${error.message}`);
      return validationResult;
    }
  }

  /**
   * Validate company schema
   */
  async validateCompanySchema(companyData, validationResult) {
    try {
      // Use schema validation from intake-schema.js
      const schemaValidation = validateIntakeDocument('company_raw_intake', companyData);

      if (!schemaValidation.valid) {
        validationResult.valid = false;
        validationResult.errors.push(...schemaValidation.errors);
      }

      validationResult.warnings.push(...schemaValidation.warnings);

      // Additional custom validations
      const rules = this.validationRules.company;

      // Required fields validation
      for (const field of rules.required_fields) {
        if (!companyData[field] || companyData[field].trim() === '') {
          validationResult.valid = false;
          validationResult.errors.push(`Required field missing or empty: ${field}`);
        }
      }

      // Pattern validation
      for (const [field, pattern] of Object.entries(rules.validation_patterns)) {
        if (companyData[field] && !pattern.test(companyData[field])) {
          validationResult.valid = false;
          validationResult.errors.push(`Invalid format for ${field}: ${companyData[field]}`);
        }
      }

    } catch (error) {
      validationResult.valid = false;
      validationResult.errors.push(`Schema validation error: ${error.message}`);
    }
  }

  /**
   * Validate person schema
   */
  async validatePersonSchema(personData, validationResult) {
    try {
      // Use schema validation from intake-schema.js
      const schemaValidation = validateIntakeDocument('people_raw_intake', personData);

      if (!schemaValidation.valid) {
        validationResult.valid = false;
        validationResult.errors.push(...schemaValidation.errors);
      }

      validationResult.warnings.push(...schemaValidation.warnings);

      // Additional custom validations
      const rules = this.validationRules.person;

      // Required fields validation
      for (const field of rules.required_fields) {
        if (!personData[field] || personData[field].trim() === '') {
          validationResult.valid = false;
          validationResult.errors.push(`Required field missing or empty: ${field}`);
        }
      }

      // Pattern validation
      for (const [field, pattern] of Object.entries(rules.validation_patterns)) {
        if (personData[field] && !pattern.test(personData[field])) {
          validationResult.valid = false;
          validationResult.errors.push(`Invalid format for ${field}: ${personData[field]}`);
        }
      }

    } catch (error) {
      validationResult.valid = false;
      validationResult.errors.push(`Schema validation error: ${error.message}`);
    }
  }

  /**
   * Validate company business rules
   */
  async validateCompanyBusinessRules(companyData, validationResult, context) {
    try {
      const rules = this.validationRules.company.business_rules;

      // Company size validation
      if (rules.company_size_validation) {
        const validSizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+'];
        if (!validSizes.includes(companyData.company_size)) {
          validationResult.valid = false;
          validationResult.errors.push(`Invalid company size: ${companyData.company_size}`);
        }
      }

      // Domain validation
      if (rules.domain_validation && companyData.website_url) {
        const domainValidation = await this.validateDomain(companyData.website_url);
        if (!domainValidation.valid) {
          validationResult.warnings.push(`Domain validation warning: ${domainValidation.message}`);
        }
      }

      // Social profile validation
      if (rules.social_profile_validation) {
        await this.validateCompanySocialProfiles(companyData, validationResult);
      }

    } catch (error) {
      validationResult.warnings.push(`Business rules validation error: ${error.message}`);
    }
  }

  /**
   * Validate person business rules
   */
  async validatePersonBusinessRules(personData, validationResult, context) {
    try {
      const rules = this.validationRules.person.business_rules;

      // Email validation
      if (rules.email_validation && personData.email_address) {
        const emailValidation = await this.validateEmailAddress(personData.email_address);
        if (!emailValidation.valid) {
          validationResult.valid = false;
          validationResult.errors.push(`Email validation failed: ${emailValidation.message}`);
        }
      }

      // Company association validation
      if (rules.company_association_validation && personData.associated_company_id) {
        const associationValidation = await this.validateCompanyAssociation(personData.associated_company_id);
        if (!associationValidation.valid) {
          validationResult.warnings.push(`Company association warning: ${associationValidation.message}`);
        }
      }

      // Social profile validation
      if (rules.social_profile_validation) {
        await this.validatePersonSocialProfiles(personData, validationResult);
      }

    } catch (error) {
      validationResult.warnings.push(`Business rules validation error: ${error.message}`);
    }
  }

  /**
   * Assess company data quality
   */
  async assessCompanyDataQuality(companyData, validationResult) {
    let qualityScore = 100;
    const qualityChecks = [];

    // Completeness check
    const allFields = [...this.validationRules.company.required_fields, ...this.validationRules.company.optional_fields];
    const providedFields = allFields.filter(field => companyData[field] && companyData[field].trim() !== '');
    const completenessScore = (providedFields.length / allFields.length) * 100;

    qualityChecks.push({
      check: 'completeness',
      score: completenessScore,
      details: `${providedFields.length}/${allFields.length} fields provided`
    });

    // Content quality check
    const contentScore = await this.assessContentQuality(companyData);
    qualityChecks.push({
      check: 'content_quality',
      score: contentScore,
      details: 'Content richness and validity assessment'
    });

    // Social presence check
    const socialFields = ['linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url'];
    const socialPresence = socialFields.filter(field => companyData[field]).length;
    const socialScore = (socialPresence / socialFields.length) * 100;

    qualityChecks.push({
      check: 'social_presence',
      score: socialScore,
      details: `${socialPresence}/${socialFields.length} social profiles provided`
    });

    // Calculate weighted average
    qualityScore = (completenessScore * 0.5) + (contentScore * 0.3) + (socialScore * 0.2);

    validationResult.quality_assessment = {
      overall_score: Math.round(qualityScore),
      checks: qualityChecks,
      recommendations: this.generateQualityRecommendations(qualityChecks)
    };
  }

  /**
   * Assess person data quality
   */
  async assessPersonDataQuality(personData, validationResult) {
    let qualityScore = 100;
    const qualityChecks = [];

    // Completeness check
    const allFields = [...this.validationRules.person.required_fields, ...this.validationRules.person.optional_fields];
    const providedFields = allFields.filter(field => personData[field] && personData[field].trim() !== '');
    const completenessScore = (providedFields.length / allFields.length) * 100;

    qualityChecks.push({
      check: 'completeness',
      score: completenessScore,
      details: `${providedFields.length}/${allFields.length} fields provided`
    });

    // Content quality check
    const contentScore = await this.assessContentQuality(personData);
    qualityChecks.push({
      check: 'content_quality',
      score: contentScore,
      details: 'Content richness and validity assessment'
    });

    // Professional information check
    const professionalScore = this.assessProfessionalInformation(personData);
    qualityChecks.push({
      check: 'professional_information',
      score: professionalScore,
      details: 'Job title and company information quality'
    });

    // Calculate weighted average
    qualityScore = (completenessScore * 0.4) + (contentScore * 0.4) + (professionalScore * 0.2);

    validationResult.quality_assessment = {
      overall_score: Math.round(qualityScore),
      checks: qualityChecks,
      recommendations: this.generateQualityRecommendations(qualityChecks)
    };
  }

  /**
   * Validate security aspects
   */
  async validateCompanySecurity(companyData, validationResult) {
    const securityPolicies = this.enforcementPolicies.security_enforcement;

    if (!securityPolicies.enabled) return;

    try {
      // Scan for malicious content
      if (securityPolicies.scan_for_malicious_content) {
        const maliciousCheck = this.scanForMaliciousContent(companyData);
        if (!maliciousCheck.clean) {
          validationResult.valid = false;
          validationResult.errors.push('Potentially malicious content detected');
          validationResult.enforcement_actions.push('quarantine_record');
        }
      }

      // Validate external URLs
      if (securityPolicies.validate_external_urls) {
        await this.validateExternalURLs(companyData, validationResult);
      }

      // PII detection
      if (securityPolicies.pii_detection) {
        const piiCheck = this.detectPII(companyData);
        if (piiCheck.detected) {
          validationResult.warnings.push('Potential PII detected in company data');
          validationResult.enforcement_actions.push('pii_review_required');
        }
      }

    } catch (error) {
      validationResult.warnings.push(`Security validation error: ${error.message}`);
    }
  }

  /**
   * Validate person security
   */
  async validatePersonSecurity(personData, validationResult) {
    const securityPolicies = this.enforcementPolicies.security_enforcement;

    if (!securityPolicies.enabled) return;

    try {
      // Scan for malicious content
      if (securityPolicies.scan_for_malicious_content) {
        const maliciousCheck = this.scanForMaliciousContent(personData);
        if (!maliciousCheck.clean) {
          validationResult.valid = false;
          validationResult.errors.push('Potentially malicious content detected');
          validationResult.enforcement_actions.push('quarantine_record');
        }
      }

      // Validate external URLs
      if (securityPolicies.validate_external_urls) {
        await this.validateExternalURLs(personData, validationResult);
      }

      // PII detection (expected for person data)
      if (securityPolicies.pii_detection) {
        const piiCheck = this.detectPII(personData);
        if (piiCheck.detected) {
          validationResult.warnings.push('PII detected (expected for person data)');
          validationResult.enforcement_actions.push('pii_handling_protocol');
        }
      }

    } catch (error) {
      validationResult.warnings.push(`Security validation error: ${error.message}`);
    }
  }

  /**
   * Detect company duplicates
   */
  async detectCompanyDuplicates(companyData, validationResult, context) {
    const duplicatePolicies = this.enforcementPolicies.duplicate_prevention;

    if (!duplicatePolicies.enabled) return;

    try {
      const duplicateChecks = [];

      // Check domain duplicates
      if (duplicatePolicies.check_domain_duplicates && companyData.website_url) {
        const domainCheck = await this.checkDomainDuplicates(companyData.website_url);
        if (domainCheck.found) {
          duplicateChecks.push({
            type: 'domain',
            found: true,
            details: domainCheck.details
          });
          validationResult.warnings.push(`Potential domain duplicate: ${companyData.website_url}`);
        }
      }

      // Check social profile duplicates
      if (duplicatePolicies.check_social_profile_duplicates) {
        const socialCheck = await this.checkCompanySocialDuplicates(companyData);
        if (socialCheck.found) {
          duplicateChecks.push({
            type: 'social_profiles',
            found: true,
            details: socialCheck.details
          });
          validationResult.warnings.push('Potential social profile duplicates detected');
        }
      }

      // Fuzzy name matching
      if (duplicatePolicies.fuzzy_name_matching && companyData.company_name) {
        const nameCheck = await this.checkFuzzyNameMatch(companyData.company_name, 'company');
        if (nameCheck.found) {
          duplicateChecks.push({
            type: 'fuzzy_name',
            found: true,
            details: nameCheck.details
          });
          validationResult.warnings.push('Potential name duplicate (fuzzy match)');
        }
      }

      validationResult.duplicate_analysis = {
        checks_performed: duplicateChecks.length,
        duplicates_found: duplicateChecks.filter(check => check.found).length,
        details: duplicateChecks
      };

    } catch (error) {
      validationResult.warnings.push(`Duplicate detection error: ${error.message}`);
    }
  }

  /**
   * Detect person duplicates
   */
  async detectPersonDuplicates(personData, validationResult, context) {
    const duplicatePolicies = this.enforcementPolicies.duplicate_prevention;

    if (!duplicatePolicies.enabled) return;

    try {
      const duplicateChecks = [];

      // Check email duplicates
      if (duplicatePolicies.check_email_duplicates && personData.email_address) {
        const emailCheck = await this.checkEmailDuplicates(personData.email_address);
        if (emailCheck.found) {
          duplicateChecks.push({
            type: 'email',
            found: true,
            details: emailCheck.details
          });
          validationResult.valid = false;
          validationResult.errors.push(`Email already exists: ${personData.email_address}`);
        }
      }

      // Check social profile duplicates
      if (duplicatePolicies.check_social_profile_duplicates) {
        const socialCheck = await this.checkPersonSocialDuplicates(personData);
        if (socialCheck.found) {
          duplicateChecks.push({
            type: 'social_profiles',
            found: true,
            details: socialCheck.details
          });
          validationResult.warnings.push('Potential social profile duplicates detected');
        }
      }

      // Fuzzy name matching
      if (duplicatePolicies.fuzzy_name_matching && personData.full_name) {
        const nameCheck = await this.checkFuzzyNameMatch(personData.full_name, 'person');
        if (nameCheck.found) {
          duplicateChecks.push({
            type: 'fuzzy_name',
            found: true,
            details: nameCheck.details
          });
          validationResult.warnings.push('Potential name duplicate (fuzzy match)');
        }
      }

      validationResult.duplicate_analysis = {
        checks_performed: duplicateChecks.length,
        duplicates_found: duplicateChecks.filter(check => check.found).length,
        details: duplicateChecks
      };

    } catch (error) {
      validationResult.warnings.push(`Duplicate detection error: ${error.message}`);
    }
  }

  /**
   * Enforce MCP access for company operations
   */
  async enforceCompanyMCPAccess(context, validationResult) {
    const mcpPolicies = this.enforcementPolicies.mcp_only_access;

    if (!mcpPolicies.enabled) return;

    try {
      // Check if request comes from allowed MCP source
      const source = context.intake_source || context.source || 'unknown';
      const isAllowedSource = mcpPolicies.allowed_sources.includes(source);
      const isBlockedSource = mcpPolicies.blocked_sources.includes(source);

      if (isBlockedSource || (!isAllowedSource && mcpPolicies.strict_mode)) {
        validationResult.valid = false;
        validationResult.errors.push('MCP-only access required. Direct client access denied.');
        validationResult.enforcement_actions.push('block_non_mcp_access');
      }

      // Validate MCP context markers
      const mcpVerified = context.mcp_verified ||
                         context.user_agent?.includes('mcp') ||
                         context.composio_key_present ||
                         false;

      if (!mcpVerified && mcpPolicies.strict_mode) {
        validationResult.valid = false;
        validationResult.errors.push('MCP verification required');
        validationResult.enforcement_actions.push('require_mcp_verification');
      }

    } catch (error) {
      validationResult.warnings.push(`MCP access enforcement error: ${error.message}`);
    }
  }

  /**
   * Enforce MCP access for person operations
   */
  async enforcePersonMCPAccess(context, validationResult) {
    // Same logic as company MCP access enforcement
    await this.enforceCompanyMCPAccess(context, validationResult);
  }

  /**
   * Apply company enforcement policies
   */
  async applyCompanyEnforcementPolicies(companyData, validationResult, context) {
    const policies = this.enforcementPolicies;

    // Data quality enforcement
    if (policies.data_quality_enforcement.enabled) {
      if (validationResult.quality_assessment?.overall_score < 50 && policies.data_quality_enforcement.reject_invalid_data) {
        validationResult.valid = false;
        validationResult.errors.push('Data quality below acceptable threshold');
        validationResult.enforcement_actions.push('reject_low_quality_data');
      }

      if (validationResult.quality_assessment?.overall_score < 70 && policies.data_quality_enforcement.quarantine_suspicious_data) {
        validationResult.enforcement_actions.push('quarantine_for_review');
      }
    }

    // Rate limiting enforcement
    if (policies.rate_limiting.enabled) {
      const rateLimitCheck = await this.checkRateLimit(context);
      if (!rateLimitCheck.allowed) {
        validationResult.valid = false;
        validationResult.errors.push('Rate limit exceeded');
        validationResult.enforcement_actions.push('rate_limit_exceeded');
      }
    }
  }

  /**
   * Apply person enforcement policies
   */
  async applyPersonEnforcementPolicies(personData, validationResult, context) {
    // Same logic as company enforcement policies
    await this.applyCompanyEnforcementPolicies(personData, validationResult, context);
  }

  /**
   * Helper validation methods
   */
  async validateDomain(url) {
    try {
      const urlObj = new URL(url);
      return {
        valid: true,
        domain: urlObj.hostname,
        message: 'Domain validation passed'
      };
    } catch {
      return {
        valid: false,
        message: 'Invalid URL format'
      };
    }
  }

  async validateEmailAddress(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return {
      valid: emailPattern.test(email),
      message: emailPattern.test(email) ? 'Email format valid' : 'Invalid email format'
    };
  }

  async validateCompanyAssociation(companyId) {
    // In production, would check if company ID exists in company_raw_intake
    return {
      valid: true,
      message: 'Company association validation passed'
    };
  }

  async validateCompanySocialProfiles(companyData, validationResult) {
    const socialFields = ['linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url'];

    for (const field of socialFields) {
      if (companyData[field]) {
        const urlValid = this.isValidURL(companyData[field]);
        if (!urlValid) {
          validationResult.warnings.push(`Invalid social URL format: ${field}`);
        }
      }
    }
  }

  async validatePersonSocialProfiles(personData, validationResult) {
    const socialFields = ['linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url'];

    for (const field of socialFields) {
      if (personData[field]) {
        const urlValid = this.isValidURL(personData[field]);
        if (!urlValid) {
          validationResult.warnings.push(`Invalid social URL format: ${field}`);
        }
      }
    }
  }

  async assessContentQuality(data) {
    let score = 100;

    // Check for meaningful content (not just placeholder text)
    const placeholderPatterns = [/test/i, /sample/i, /example/i, /placeholder/i, /dummy/i];

    Object.values(data).forEach(value => {
      if (typeof value === 'string') {
        for (const pattern of placeholderPatterns) {
          if (pattern.test(value)) {
            score -= 10;
            break;
          }
        }
      }
    });

    return Math.max(score, 0);
  }

  assessProfessionalInformation(personData) {
    let score = 100;

    // Check for meaningful job titles
    if (personData.job_title) {
      const genericTitles = ['employee', 'worker', 'staff', 'person'];
      if (genericTitles.some(title => personData.job_title.toLowerCase().includes(title))) {
        score -= 20;
      }
    }

    // Check for company information richness
    if (personData.company_name && personData.company_name.length < 5) {
      score -= 15;
    }

    return Math.max(score, 0);
  }

  scanForMaliciousContent(data) {
    const maliciousPatterns = [
      /<script/i,
      /javascript:/i,
      /eval\(/i,
      /onclick=/i,
      /onerror=/i,
      /onload=/i,
      /alert\(/i,
      /document\./i,
      /window\./i
    ];

    const dataString = JSON.stringify(data);

    for (const pattern of maliciousPatterns) {
      if (pattern.test(dataString)) {
        return {
          clean: false,
          threat_detected: pattern.toString()
        };
      }
    }

    return { clean: true };
  }

  async validateExternalURLs(data, validationResult) {
    const urlFields = ['website_url', 'linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url'];

    for (const field of urlFields) {
      if (data[field]) {
        try {
          new URL(data[field]);
        } catch {
          validationResult.warnings.push(`Invalid URL format: ${field}`);
        }
      }
    }
  }

  detectPII(data) {
    const piiPatterns = [
      /\b\d{3}-\d{2}-\d{4}\b/, // SSN
      /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/, // Credit card
      /\b\d{3}-\d{3}-\d{4}\b/, // Phone number
    ];

    const dataString = JSON.stringify(data);

    for (const pattern of piiPatterns) {
      if (pattern.test(dataString)) {
        return {
          detected: true,
          pattern: pattern.toString()
        };
      }
    }

    return { detected: false };
  }

  async checkDomainDuplicates(domain) {
    // In production, would query existing company records
    return {
      found: false,
      details: []
    };
  }

  async checkEmailDuplicates(email) {
    // In production, would query existing person records
    return {
      found: false,
      details: []
    };
  }

  async checkCompanySocialDuplicates(companyData) {
    // In production, would check social URLs against existing records
    return {
      found: false,
      details: []
    };
  }

  async checkPersonSocialDuplicates(personData) {
    // In production, would check social URLs against existing records
    return {
      found: false,
      details: []
    };
  }

  async checkFuzzyNameMatch(name, type) {
    // In production, would implement fuzzy string matching
    return {
      found: false,
      details: []
    };
  }

  async checkRateLimit(context) {
    // In production, would implement rate limiting logic
    return {
      allowed: true,
      remaining: 100,
      reset_time: new Date(Date.now() + 60000).toISOString()
    };
  }

  calculateDataQualityScore(validationResult) {
    if (validationResult.quality_assessment) {
      return validationResult.quality_assessment.overall_score;
    }

    // Fallback calculation based on errors and warnings
    let score = 100;
    score -= validationResult.errors.length * 20;
    score -= validationResult.warnings.length * 5;

    return Math.max(score, 0);
  }

  generateQualityRecommendations(qualityChecks) {
    const recommendations = [];

    qualityChecks.forEach(check => {
      if (check.score < 70) {
        switch (check.check) {
          case 'completeness':
            recommendations.push('Consider providing more complete information');
            break;
          case 'content_quality':
            recommendations.push('Improve content quality and avoid placeholder text');
            break;
          case 'social_presence':
            recommendations.push('Add social media profiles for better verification');
            break;
          case 'professional_information':
            recommendations.push('Provide more detailed professional information');
            break;
        }
      }
    });

    return recommendations;
  }

  isValidURL(url) {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }
}

export default IntakeValidationService;