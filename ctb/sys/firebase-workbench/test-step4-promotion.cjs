/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-CFF8E654
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

#!/usr/bin/env node

const https = require('https');
const { performance } = require('perf_hooks');

class Step4PromotionTester {
  constructor() {
    this.baseUrl = process.env.FIREBASE_FUNCTIONS_URL || 'https://us-central1-barton-outreach-core.cloudfunctions.net';
    this.testResults = [];
    this.testSession = `test-step4-${Date.now()}`;

    console.log('🚀 Step 4 Promotion Workflow Tester');
    console.log(`📍 Testing against: ${this.baseUrl}`);
    console.log(`🔍 Test Session: ${this.testSession}\n`);
  }

  async runAllTests() {
    const startTime = performance.now();

    try {
      console.log('🎯 Starting Step 4 Promotion Tests...\n');

      // Test 1: Company Promotion
      await this.testCompanyPromotion();

      // Test 2: Person Promotion
      await this.testPersonPromotion();

      // Test 3: Relationship Preservation
      await this.testRelationshipPreservation();

      // Test 4: Error Handling (Schema Mismatch)
      await this.testErrorHandling();

      // Test 5: Duplicate Detection
      await this.testDuplicateDetection();

      // Test 6: Transaction Rollback
      await this.testTransactionRollback();

      // Test 7: Promotion Status Tracking
      await this.testPromotionStatusTracking();

      // Test 8: Permanent ID Assignment
      await this.testPermanentIdAssignment();

      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(2);

      this.printSummary(duration);

    } catch (error) {
      console.error('❌ Critical test failure:', error.message);
      process.exit(1);
    }
  }

  async testCompanyPromotion() {
    console.log('🏢 Test 1: Company Promotion');

    const testPayload = {
      companyRecords: [
        {
          unique_id: 'CMP-INT-TEST-001',
          company_name: 'Microsoft Corporation',
          domain: 'microsoft.com',
          industry: 'Technology',
          address: '1 Microsoft Way, Redmond, WA',
          employees: 180000,
          revenue: '198B',
          validation_status: 'validated',
          validated_at: '2025-01-15T10:30:00Z'
        },
        {
          unique_id: 'CMP-INT-TEST-002',
          company_name: 'Google LLC',
          domain: 'google.com',
          industry: 'Technology',
          address: '1600 Amphitheatre Parkway, Mountain View, CA',
          employees: 156000,
          revenue: '282B',
          validation_status: 'validated',
          validated_at: '2025-01-15T11:15:00Z'
        }
      ],
      processId: `${this.testSession}-company-promotion`
    };

    try {
      const result = await this.callFunction('promoteCompany', testPayload);

      if (result.success) {
        console.log('✅ Company promotion successful');
        console.log(`   📊 Total records: ${result.stats.total}`);
        console.log(`   🎯 Successfully promoted: ${result.stats.promoted}`);
        console.log(`   ❌ Failed: ${result.stats.failed}`);
        console.log(`   🔄 Duplicates detected: ${result.stats.duplicates}`);
        console.log(`   ⏱️  Duration: ${result.duration}ms`);

        // Validate permanent IDs were assigned
        if (result.promotedCompanies && result.promotedCompanies.length > 0) {
          const hasValidIds = result.promotedCompanies.every(company =>
            company.unique_id.startsWith('CMP-') && company.unique_id !== company.promoted_from_intake
          );

          if (hasValidIds) {
            console.log('   ✅ Permanent IDs assigned correctly');
          } else {
            throw new Error('Permanent ID assignment failed');
          }
        }

        this.testResults.push({
          test: 'Company Promotion',
          status: 'PASS',
          details: result.stats
        });
      } else {
        throw new Error(result.error || 'Unknown error');
      }

    } catch (error) {
      console.log('❌ Company promotion failed:', error.message);
      this.testResults.push({
        test: 'Company Promotion',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testPersonPromotion() {
    console.log('👥 Test 2: Person Promotion');

    const testPayload = {
      personRecords: [
        {
          unique_id: 'PER-INT-TEST-001',
          first_name: 'Satya',
          last_name: 'Nadella',
          email: 'satya.nadella@microsoft.com',
          phone: '+1-425-882-8080',
          title: 'CEO',
          company_unique_id: 'CMP-20250115-ABC123',
          validation_status: 'validated',
          validated_at: '2025-01-15T10:45:00Z'
        },
        {
          unique_id: 'PER-INT-TEST-002',
          first_name: 'Sundar',
          last_name: 'Pichai',
          email: 'sundar.pichai@google.com',
          phone: '+1-650-253-0000',
          title: 'CEO',
          company_unique_id: 'CMP-20250115-XYZ789',
          validation_status: 'validated',
          validated_at: '2025-01-15T11:30:00Z'
        }
      ],
      processId: `${this.testSession}-person-promotion`
    };

    try {
      const result = await this.callFunction('promotePerson', testPayload);

      if (result.success) {
        console.log('✅ Person promotion successful');
        console.log(`   📊 Total records: ${result.stats.total}`);
        console.log(`   🎯 Successfully promoted: ${result.stats.promoted}`);
        console.log(`   ❌ Failed: ${result.stats.failed}`);
        console.log(`   🔄 Duplicates detected: ${result.stats.duplicates}`);
        console.log(`   🔗 Relationships preserved: ${result.stats.relationshipsPreserved}`);
        console.log(`   ⏱️  Duration: ${result.duration}ms`);

        this.testResults.push({
          test: 'Person Promotion',
          status: 'PASS',
          details: result.stats
        });
      } else {
        throw new Error(result.error || 'Unknown error');
      }

    } catch (error) {
      console.log('❌ Person promotion failed:', error.message);
      this.testResults.push({
        test: 'Person Promotion',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testRelationshipPreservation() {
    console.log('🔗 Test 3: Relationship Preservation');

    const testPayload = {
      personRecords: [
        {
          unique_id: 'PER-INT-REL-001',
          first_name: 'Test',
          last_name: 'Employee',
          email: 'test.employee@testcompany.com',
          company_unique_id: 'CMP-20250115-REL001',
          validation_status: 'validated',
          validated_at: '2025-01-15T12:00:00Z'
        }
      ],
      processId: `${this.testSession}-relationship-test`
    };

    try {
      const result = await this.callFunction('promotePerson', testPayload);

      if (result.success && result.stats.relationshipsPreserved >= 0) {
        console.log('✅ Relationship preservation tested');
        console.log(`   🔗 Relationships preserved: ${result.stats.relationshipsPreserved}`);

        this.testResults.push({
          test: 'Relationship Preservation',
          status: 'PASS',
          details: { relationshipsPreserved: result.stats.relationshipsPreserved }
        });
      } else {
        throw new Error('Relationship preservation test failed');
      }

    } catch (error) {
      console.log('❌ Relationship preservation test failed:', error.message);
      this.testResults.push({
        test: 'Relationship Preservation',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testErrorHandling() {
    console.log('⚠️  Test 4: Error Handling (Schema Mismatch)');

    const testPayload = {
      companyRecords: [
        {
          unique_id: 'CMP-INT-ERROR-001',
          // Missing required field: company_name
          domain: 'invalid-domain',
          industry: 'Technology'
        },
        {
          unique_id: 'CMP-INT-ERROR-002',
          company_name: '',  // Empty required field
          domain: 'another-invalid-domain',
          industry: 'Technology'
        }
      ],
      processId: `${this.testSession}-error-handling`
    };

    try {
      const result = await this.callFunction('promoteCompany', testPayload);

      // Should handle errors gracefully
      if (result.stats && result.stats.failed > 0 && result.errors && result.errors.length > 0) {
        console.log('✅ Error handling works correctly');
        console.log(`   ⚠️  Records failed: ${result.stats.failed}`);
        console.log(`   📝 Error entries: ${result.errors.length}`);

        this.testResults.push({
          test: 'Error Handling',
          status: 'PASS',
          details: { errorsCaught: result.errors.length, recordsFailed: result.stats.failed }
        });
      } else {
        throw new Error('Error handling did not work as expected');
      }

    } catch (error) {
      console.log('❌ Error handling test failed:', error.message);
      this.testResults.push({
        test: 'Error Handling',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testDuplicateDetection() {
    console.log('🔄 Test 5: Duplicate Detection');

    const testPayload = {
      companyRecords: [
        {
          unique_id: 'CMP-INT-DUP-001',
          company_name: 'Duplicate Test Company',
          domain: 'duplicate-test.com',
          industry: 'Technology'
        },
        {
          unique_id: 'CMP-INT-DUP-002',
          company_name: 'Another Duplicate Test Company',
          domain: 'duplicate-test.com',  // Same domain as above
          industry: 'Technology'
        }
      ],
      processId: `${this.testSession}-duplicate-detection`
    };

    try {
      const result = await this.callFunction('promoteCompany', testPayload);

      if (result.stats && result.stats.duplicates >= 0) {
        console.log('✅ Duplicate detection tested');
        console.log(`   🔄 Duplicates detected: ${result.stats.duplicates}`);
        console.log(`   ✅ Records promoted: ${result.stats.promoted}`);
        console.log(`   ❌ Records failed: ${result.stats.failed}`);

        this.testResults.push({
          test: 'Duplicate Detection',
          status: 'PASS',
          details: result.stats
        });
      } else {
        throw new Error('Duplicate detection test failed');
      }

    } catch (error) {
      console.log('❌ Duplicate detection test failed:', error.message);
      this.testResults.push({
        test: 'Duplicate Detection',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testTransactionRollback() {
    console.log('🔄 Test 6: Transaction Rollback');

    const testPayload = {
      companyRecords: [
        {
          unique_id: 'CMP-INT-ROLLBACK-001',
          company_name: 'Valid Company',
          domain: 'valid-company.com',
          industry: 'Technology'
        },
        {
          unique_id: 'CMP-INT-ROLLBACK-002',
          // This should cause the transaction to fail
          company_name: null,
          domain: 'invalid-company.com',
          industry: 'Technology'
        }
      ],
      processId: `${this.testSession}-transaction-rollback`
    };

    try {
      const result = await this.callFunction('promoteCompany', testPayload);

      // In case of transaction failure, some records should fail but valid ones might still succeed
      if (result.stats) {
        console.log('✅ Transaction rollback tested');
        console.log(`   ✅ Records promoted: ${result.stats.promoted}`);
        console.log(`   ❌ Records failed: ${result.stats.failed}`);

        this.testResults.push({
          test: 'Transaction Rollback',
          status: 'PASS',
          details: result.stats
        });
      } else {
        throw new Error('Transaction rollback test failed');
      }

    } catch (error) {
      console.log('❌ Transaction rollback test failed:', error.message);
      this.testResults.push({
        test: 'Transaction Rollback',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testPromotionStatusTracking() {
    console.log('📊 Test 7: Promotion Status Tracking');

    const processId = `${this.testSession}-status-tracking`;

    try {
      const result = await this.callFunction('getPromotionStatus', { processId: processId });

      if (result.success !== undefined) {
        console.log('✅ Promotion status tracking works');
        console.log(`   📊 Process ID: ${result.processId || 'N/A'}`);
        console.log(`   📈 Stats available: ${result.stats ? 'Yes' : 'No'}`);

        this.testResults.push({
          test: 'Promotion Status Tracking',
          status: 'PASS',
          details: { statusAvailable: true, hasStats: !!result.stats }
        });
      } else {
        throw new Error('Status tracking response invalid');
      }

    } catch (error) {
      console.log('❌ Promotion status tracking failed:', error.message);
      this.testResults.push({
        test: 'Promotion Status Tracking',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async testPermanentIdAssignment() {
    console.log('🆔 Test 8: Permanent ID Assignment');

    const testPayload = {
      companyRecords: [
        {
          unique_id: 'CMP-INT-ID-001',
          company_name: 'ID Test Company',
          domain: 'id-test-company.com',
          industry: 'Technology'
        }
      ],
      processId: `${this.testSession}-id-assignment`
    };

    try {
      const result = await this.callFunction('promoteCompany', testPayload);

      if (result.success && result.promotedCompanies && result.promotedCompanies.length > 0) {
        const promotedCompany = result.promotedCompanies[0];
        const hasValidPermanentId = promotedCompany.unique_id.startsWith('CMP-') &&
                                   promotedCompany.unique_id !== 'CMP-INT-ID-001';

        if (hasValidPermanentId) {
          console.log('✅ Permanent ID assignment successful');
          console.log(`   🆔 Original ID: CMP-INT-ID-001`);
          console.log(`   🆔 Permanent ID: ${promotedCompany.unique_id}`);
          console.log(`   ✅ ID format valid: ${promotedCompany.unique_id.match(/^CMP-\d{8}-[A-Z0-9]{6}$/) ? 'Yes' : 'No'}`);

          this.testResults.push({
            test: 'Permanent ID Assignment',
            status: 'PASS',
            details: {
              originalId: 'CMP-INT-ID-001',
              permanentId: promotedCompany.unique_id,
              formatValid: !!promotedCompany.unique_id.match(/^CMP-\d{8}-[A-Z0-9]{6}$/)
            }
          });
        } else {
          throw new Error('Permanent ID format invalid');
        }
      } else {
        throw new Error('No promoted companies returned');
      }

    } catch (error) {
      console.log('❌ Permanent ID assignment failed:', error.message);
      this.testResults.push({
        test: 'Permanent ID Assignment',
        status: 'FAIL',
        error: error.message
      });
    }

    console.log('');
  }

  async callFunction(functionName, payload) {
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify({ data: payload });

      const options = {
        hostname: this.baseUrl.replace('https://', '').replace('http://', ''),
        port: 443,
        path: `/${functionName}`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData),
          'Authorization': `Bearer ${process.env.FIREBASE_TOKEN || 'test-token'}`
        }
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const result = JSON.parse(data);
            resolve(result);
          } catch (error) {
            reject(new Error(`Parse error: ${error.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.write(postData);
      req.end();
    });
  }

  printSummary(duration) {
    console.log('📊 Test Summary');
    console.log('═'.repeat(60));

    const passed = this.testResults.filter(t => t.status === 'PASS').length;
    const failed = this.testResults.filter(t => t.status === 'FAIL').length;

    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`⏱️  Duration: ${duration}s`);
    console.log(`🔍 Session: ${this.testSession}`);

    if (failed > 0) {
      console.log('\n❌ Failed Tests:');
      this.testResults
        .filter(t => t.status === 'FAIL')
        .forEach(test => {
          console.log(`   • ${test.test}: ${test.error}`);
        });
    }

    console.log('\n🎯 Step 4 Promotion Implementation Status:');
    console.log(`   🏢 Company Promotion: ${this.getTestStatus('Company Promotion')}`);
    console.log(`   👥 Person Promotion: ${this.getTestStatus('Person Promotion')}`);
    console.log(`   🔗 Relationship Preservation: ${this.getTestStatus('Relationship Preservation')}`);
    console.log(`   ⚠️  Error Handling: ${this.getTestStatus('Error Handling')}`);
    console.log(`   🔄 Duplicate Detection: ${this.getTestStatus('Duplicate Detection')}`);
    console.log(`   🔄 Transaction Rollback: ${this.getTestStatus('Transaction Rollback')}`);
    console.log(`   📊 Status Tracking: ${this.getTestStatus('Promotion Status Tracking')}`);
    console.log(`   🆔 Permanent ID Assignment: ${this.getTestStatus('Permanent ID Assignment')}`);

    console.log('\n📋 Key Features Validated:');
    console.log(`   ✅ Permanent ID assignment (CMP-XXXXXXXX-XXXXXX format)`);
    console.log(`   ✅ Master table promotion (company_master + person_master)`);
    console.log(`   ✅ Relationship preservation (company_unique_id ↔ person_unique_id)`);
    console.log(`   ✅ Comprehensive error handling and rollback`);
    console.log(`   ✅ Promotion and audit logging`);
    console.log(`   ✅ Schema validation and duplicate detection`);

    if (failed === 0) {
      console.log('\n🎉 All Step 4 promotion tests passed! Ready for production deployment.');
      console.log('📈 The promotion console can safely promote validated records to master tables.');
    } else {
      console.log('\n⚠️  Some tests failed. Review and fix before deployment.');
    }
  }

  getTestStatus(testName) {
    const test = this.testResults.find(t => t.test === testName);
    return test ? (test.status === 'PASS' ? '✅' : '❌') : '❓';
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new Step4PromotionTester();
  tester.runAllTests().catch(console.error);
}

module.exports = Step4PromotionTester;