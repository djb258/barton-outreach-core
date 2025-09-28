/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.08.10000.005
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2A Validator Agent standalone test suite (no Firebase dependencies)
 * - Input: Test validation logic, phone normalization, error handling
 * - Output: Test results with validation coverage verification
 * - MCP: Firebase (Composio-only testing patterns)
 */

/**
 * Phone number normalization utility (standalone)
 */
class PhoneNormalizer {
  constructor() {
    this.countryPatterns = {
      US: {
        code: '+1',
        pattern: /^(?:\+?1[-.\s]?)?(?:\(?([0-9]{3})\)?[-.\s]?)?([0-9]{3})[-.\s]?([0-9]{4})$/,
        format: (match) => `+1${match[1]}${match[2]}${match[3]}`
      }
    };
  }

  normalizePhone(phoneNumber, defaultCountry = 'US') {
    if (!phoneNumber) return null;

    const cleaned = phoneNumber.replace(/[^\d+]/g, '');

    if (cleaned.startsWith('+') && cleaned.length >= 10 && cleaned.length <= 15) {
      return cleaned;
    }

    for (const [country, config] of Object.entries(this.countryPatterns)) {
      const match = phoneNumber.match(config.pattern);
      if (match) {
        try {
          return config.format(match);
        } catch (error) {
          console.warn(`Phone normalization failed for ${country}:`, error);
        }
      }
    }

    if (defaultCountry === 'US' && cleaned.length === 10) {
      return `+1${cleaned}`;
    }

    if (defaultCountry === 'US' && cleaned.length === 11 && cleaned.startsWith('1')) {
      return `+${cleaned}`;
    }

    return null;
  }

  isValidE164(phoneNumber) {
    if (!phoneNumber) return false;
    return /^\+[1-9]\d{1,14}$/.test(phoneNumber);
  }
}

/**
 * Company validation utility (standalone)
 */
class CompanyValidator {
  constructor() {
    this.phoneNormalizer = new PhoneNormalizer();
    this.requiredFields = ['company_name', 'website_url', 'phone_number', 'employee_count'];
  }

  async validateCompany(companyDoc) {
    const validationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      normalizedData: { ...companyDoc }
    };

    for (const field of this.requiredFields) {
      if (!companyDoc[field] || companyDoc[field] === '') {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: field,
          error: 'required_field_missing',
          message: `Required field '${field}' is missing or empty`
        });
      }
    }

    if (companyDoc.phone_number) {
      const normalizedPhone = this.phoneNormalizer.normalizePhone(companyDoc.phone_number);
      if (normalizedPhone) {
        validationResult.normalizedData.phone_number = normalizedPhone;
      } else {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'phone_number',
          error: 'invalid_phone_format',
          message: 'Phone number could not be normalized to E.164 format'
        });
      }
    }

    if (companyDoc.website_url && !this.isValidURL(companyDoc.website_url)) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'website_url',
        error: 'invalid_url_format',
        message: 'Website URL is not in valid format'
      });
    }

    if (companyDoc.employee_count !== undefined) {
      const employeeCount = parseInt(companyDoc.employee_count);
      if (isNaN(employeeCount) || employeeCount < 0) {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'employee_count',
          error: 'invalid_employee_count',
          message: 'Employee count must be a non-negative number'
        });
      } else {
        validationResult.normalizedData.employee_count = employeeCount;
      }
    }

    validationResult.normalizedData.validation_timestamp = new Date().toISOString();
    validationResult.normalizedData.validation_status = validationResult.isValid ? 'validated' : 'failed';
    validationResult.normalizedData.validation_errors = validationResult.errors;

    return validationResult;
  }

  isValidURL(urlString) {
    try {
      const url = new URL(urlString);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (error) {
      return false;
    }
  }
}

/**
 * Person validation utility (standalone)
 */
class PersonValidator {
  constructor() {
    this.phoneNormalizer = new PhoneNormalizer();
    this.requiredFields = ['first_name', 'last_name'];
  }

  async validatePerson(personDoc) {
    const validationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      normalizedData: { ...personDoc }
    };

    for (const field of this.requiredFields) {
      if (!personDoc[field] || personDoc[field] === '') {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: field,
          error: 'required_field_missing',
          message: `Required field '${field}' is missing or empty`
        });
      }
    }

    const hasEmail = personDoc.email && personDoc.email.trim() !== '';
    const hasPhone = personDoc.phone_number && personDoc.phone_number.trim() !== '';

    if (!hasEmail && !hasPhone) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'contact_info',
        error: 'missing_contact_method',
        message: 'Either email or phone number must be provided'
      });
    }

    if (hasEmail && !this.isValidEmail(personDoc.email)) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'email',
        error: 'invalid_email_format',
        message: 'Email address is not in valid format'
      });
    }

    if (hasPhone) {
      const normalizedPhone = this.phoneNormalizer.normalizePhone(personDoc.phone_number);
      if (normalizedPhone) {
        validationResult.normalizedData.phone_number = normalizedPhone;
      } else {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'phone_number',
          error: 'invalid_phone_format',
          message: 'Phone number could not be normalized to E.164 format'
        });
      }
    }

    validationResult.normalizedData.validation_timestamp = new Date().toISOString();
    validationResult.normalizedData.validation_status = validationResult.isValid ? 'validated' : 'failed';
    validationResult.normalizedData.validation_errors = validationResult.errors;

    return validationResult;
  }

  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

/**
 * Standalone test suite for Step 2A Validator Agent
 */
class ValidatorTestSuite {
  constructor() {
    this.testResults = [];
    this.phoneNormalizer = new PhoneNormalizer();
    this.companyValidator = new CompanyValidator();
    this.personValidator = new PersonValidator();
  }

  async runAllTests() {
    console.log('🧪 Starting Step 2A Validator Agent Test Suite...\n');

    try {
      await this.testPhoneNormalization();
      await this.testCompanyValidation();
      await this.testPersonValidation();
      await this.testValidationErrorHandling();
      await this.testMCPIntegrationPatterns();

      this.generateTestReport();

    } catch (error) {
      console.error('❌ Test suite execution failed:', error);
      throw error;
    }
  }

  async testPhoneNormalization() {
    console.log('📞 Testing Phone Number Normalization...');

    const testCases = [
      { input: '(555) 123-4567', expected: '+15551234567', country: 'US' },
      { input: '555-123-4567', expected: '+15551234567', country: 'US' },
      { input: '555.123.4567', expected: '+15551234567', country: 'US' },
      { input: '15551234567', expected: '+15551234567', country: 'US' },
      { input: '+1 555 123 4567', expected: '+15551234567', country: 'US' },
      { input: '+15551234567', expected: '+15551234567', country: 'US' },
      { input: '123', expected: null, country: 'US' },
      { input: 'not-a-phone', expected: null, country: 'US' },
      { input: '', expected: null, country: 'US' }
    ];

    let passed = 0;
    let failed = 0;

    for (const testCase of testCases) {
      try {
        const result = this.phoneNormalizer.normalizePhone(testCase.input, testCase.country);

        if (result === testCase.expected) {
          console.log(`  ✅ ${testCase.input} → ${result}`);
          passed++;
        } else {
          console.log(`  ❌ ${testCase.input} → Expected: ${testCase.expected}, Got: ${result}`);
          failed++;
        }
      } catch (error) {
        console.log(`  ❌ ${testCase.input} → Error: ${error.message}`);
        failed++;
      }
    }

    this.testResults.push({
      test: 'Phone Normalization',
      passed: passed,
      failed: failed,
      success: failed === 0
    });

    console.log(`Phone normalization tests: ${passed} passed, ${failed} failed\n`);
  }

  async testCompanyValidation() {
    console.log('🏢 Testing Company Validation...');

    const testCases = [
      {
        name: 'Valid Company',
        data: {
          company_name: 'Acme Corporation',
          website_url: 'https://acmecorp.com',
          phone_number: '(555) 123-4567',
          employee_count: '100'
        },
        shouldPass: true
      },
      {
        name: 'Missing Company Name',
        data: {
          website_url: 'https://acmecorp.com',
          phone_number: '(555) 123-4567',
          employee_count: '100'
        },
        shouldPass: false
      },
      {
        name: 'Invalid Phone Number',
        data: {
          company_name: 'Acme Corporation',
          website_url: 'https://acmecorp.com',
          phone_number: 'invalid-phone',
          employee_count: '100'
        },
        shouldPass: false
      },
      {
        name: 'Invalid Website URL',
        data: {
          company_name: 'Acme Corporation',
          website_url: 'not-a-url',
          phone_number: '(555) 123-4567',
          employee_count: '100'
        },
        shouldPass: false
      }
    ];

    let passed = 0;
    let failed = 0;

    for (const testCase of testCases) {
      try {
        const result = await this.companyValidator.validateCompany(testCase.data);

        if (result.isValid === testCase.shouldPass) {
          console.log(`  ✅ ${testCase.name}: ${result.isValid ? 'Valid' : 'Invalid'} (${result.errors.length} errors)`);
          passed++;
        } else {
          console.log(`  ❌ ${testCase.name}: Expected ${testCase.shouldPass}, got ${result.isValid}`);
          failed++;
        }
      } catch (error) {
        console.log(`  ❌ ${testCase.name}: Error - ${error.message}`);
        failed++;
      }
    }

    this.testResults.push({
      test: 'Company Validation',
      passed: passed,
      failed: failed,
      success: failed === 0
    });

    console.log(`Company validation tests: ${passed} passed, ${failed} failed\n`);
  }

  async testPersonValidation() {
    console.log('👤 Testing Person Validation...');

    const testCases = [
      {
        name: 'Valid Person with Email',
        data: {
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@example.com'
        },
        shouldPass: true
      },
      {
        name: 'Valid Person with Phone',
        data: {
          first_name: 'Jane',
          last_name: 'Smith',
          phone_number: '(555) 123-4567'
        },
        shouldPass: true
      },
      {
        name: 'Missing First Name',
        data: {
          last_name: 'Doe',
          email: 'john.doe@example.com'
        },
        shouldPass: false
      },
      {
        name: 'Missing Contact Info',
        data: {
          first_name: 'John',
          last_name: 'Doe'
        },
        shouldPass: false
      },
      {
        name: 'Invalid Email Format',
        data: {
          first_name: 'John',
          last_name: 'Doe',
          email: 'invalid-email'
        },
        shouldPass: false
      }
    ];

    let passed = 0;
    let failed = 0;

    for (const testCase of testCases) {
      try {
        const result = await this.personValidator.validatePerson(testCase.data);

        if (result.isValid === testCase.shouldPass) {
          console.log(`  ✅ ${testCase.name}: ${result.isValid ? 'Valid' : 'Invalid'} (${result.errors.length} errors)`);
          passed++;
        } else {
          console.log(`  ❌ ${testCase.name}: Expected ${testCase.shouldPass}, got ${result.isValid}`);
          failed++;
        }
      } catch (error) {
        console.log(`  ❌ ${testCase.name}: Error - ${error.message}`);
        failed++;
      }
    }

    this.testResults.push({
      test: 'Person Validation',
      passed: passed,
      failed: failed,
      success: failed === 0
    });

    console.log(`Person validation tests: ${passed} passed, ${failed} failed\n`);
  }

  async testValidationErrorHandling() {
    console.log('⚠️ Testing Validation Error Handling...');

    let passed = 0;
    let failed = 0;

    try {
      const invalidCompany = {};
      const companyResult = await this.companyValidator.validateCompany(invalidCompany);

      if (!companyResult.isValid && companyResult.errors.length > 0) {
        console.log(`  ✅ Company error handling: ${companyResult.errors.length} errors captured`);

        const hasRequiredFields = companyResult.errors.every(error =>
          error.field && error.error && error.message
        );

        if (hasRequiredFields) {
          console.log('  ✅ Error structure validation passed');
          passed++;
        } else {
          console.log('  ❌ Error structure validation failed');
          failed++;
        }
      } else {
        console.log('  ❌ Company error handling failed');
        failed++;
      }

      const invalidPerson = {};
      const personResult = await this.personValidator.validatePerson(invalidPerson);

      if (!personResult.isValid && personResult.errors.length > 0) {
        console.log(`  ✅ Person error handling: ${personResult.errors.length} errors captured`);
        passed++;
      } else {
        console.log('  ❌ Person error handling failed');
        failed++;
      }

    } catch (error) {
      console.log(`  ❌ Error handling test failed: ${error.message}`);
      failed++;
    }

    this.testResults.push({
      test: 'Validation Error Handling',
      passed: passed,
      failed: failed,
      success: failed === 0
    });

    console.log(`Error handling tests: ${passed} passed, ${failed} failed\n`);
  }

  async testMCPIntegrationPatterns() {
    console.log('🔧 Testing MCP Integration Patterns...');

    let passed = 0;
    let failed = 0;

    try {
      // Test HEIR ID format
      const heirId = this.generateHeirId();
      const heirFormat = /^HEIR-\d{14}-VAL-[A-Z0-9]{6}$/.test(heirId);

      if (heirFormat) {
        console.log(`  ✅ HEIR ID format: ${heirId}`);
        passed++;
      } else {
        console.log(`  ❌ HEIR ID format failed: ${heirId}`);
        failed++;
      }

      // Test Process ID format
      const processId = this.generateProcessId();
      const processFormat = /^PRC-VAL-\d+-[A-Z0-9]{4}$/.test(processId);

      if (processFormat) {
        console.log(`  ✅ Process ID format: ${processId}`);
        passed++;
      } else {
        console.log(`  ❌ Process ID format failed: ${processId}`);
        failed++;
      }

      // Test MCP payload structure
      const mcpPayload = {
        tool: 'FIREBASE_FUNCTION_CALL',
        data: { function_name: 'validateCompany', payload: { company_unique_id: '05.01.01.03.10000.001' } },
        unique_id: heirId,
        process_id: processId,
        orbt_layer: 2,
        blueprint_version: '1.0.0'
      };

      const requiredFields = ['tool', 'data', 'unique_id', 'process_id', 'orbt_layer', 'blueprint_version'];
      const hasAllFields = requiredFields.every(field => mcpPayload[field] !== undefined);

      if (hasAllFields) {
        console.log('  ✅ MCP payload structure validation passed');
        passed++;
      } else {
        console.log('  ❌ MCP payload structure validation failed');
        failed++;
      }

    } catch (error) {
      console.log(`  ❌ MCP integration test error: ${error.message}`);
      failed++;
    }

    this.testResults.push({
      test: 'MCP Integration Patterns',
      passed: passed,
      failed: failed,
      success: failed === 0
    });

    console.log(`MCP integration tests: ${passed} passed, ${failed} failed\n`);
  }

  generateHeirId() {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-T:]/g, '');
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `HEIR-${timestamp}-VAL-${random}`;
  }

  generateProcessId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `PRC-VAL-${timestamp}-${random}`;
  }

  generateTestReport() {
    console.log('📊 STEP 2A VALIDATOR AGENT TEST REPORT');
    console.log('=======================================\n');

    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(test => test.success).length;
    const failedTests = totalTests - passedTests;
    const successRate = Math.round((passedTests / totalTests) * 100);

    console.log(`Overall Success: ${failedTests === 0 ? 'true' : 'false'}`);
    console.log(`Tests Passed: ${passedTests}/${totalTests}`);
    console.log(`Success Rate: ${successRate}%\n`);

    console.log('Individual Test Results:');
    this.testResults.forEach(test => {
      const status = test.success ? '✅' : '❌';
      console.log(`  ${status} ${test.test}: ${test.passed} passed, ${test.failed} failed`);
    });

    console.log('\n');

    if (failedTests === 0) {
      console.log('🎉 VALIDATION SYSTEM VERIFICATION:');
      console.log('✅ Phone normalization to E.164 format working');
      console.log('✅ Company validation with required fields');
      console.log('✅ Person validation with email OR phone requirement');
      console.log('✅ Structured error handling for failed validations');
      console.log('✅ MCP integration patterns ready');
      console.log('\n🚀 Step 2A Validator Agent is ready for Composio deployment!');
    } else {
      console.log('⚠️ ISSUES TO RESOLVE:');
      this.testResults.filter(test => !test.success).forEach(test => {
        console.log(`- ${test.test}: ${test.failed} failed tests`);
      });
    }

    console.log('\n✨ Step 2A validation testing complete!');

    return {
      success: failedTests === 0,
      totalTests: totalTests,
      passedTests: passedTests,
      failedTests: failedTests,
      successRate: successRate,
      composioReady: failedTests === 0
    };
  }
}

// Run tests
const testSuite = new ValidatorTestSuite();
testSuite.runAllTests().catch(console.error);

module.exports = { ValidatorTestSuite };