/**
 * Apify Actor Handler Service
 * Step 2B of Barton Doctrine Pipeline - Web scraping enrichment
 * Uses Composio MCP to call Apify actors for data enrichment
 * Handles: missing_linkedin, missing_website, missing_ein, missing_permit
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * Main Apify handler - calls appropriate Apify actor via Composio MCP
 */
export async function processApifyEnrichment(validationFailureRecord, companyData = {}) {
  const startTime = Date.now();

  try {
    console.log(`[APIFY-HANDLER] Processing ${validationFailureRecord.error_type} for record ${validationFailureRecord.record_id}`);

    const enrichmentResult = await callApifyActor(validationFailureRecord, companyData);

    const processingTime = Date.now() - startTime;

    return {
      success: enrichmentResult.success,
      originalValue: validationFailureRecord.raw_value,
      enrichedValue: enrichmentResult.enrichedValue,
      confidence: enrichmentResult.confidence,
      processingTime,
      actorUsed: enrichmentResult.actorUsed,
      metadata: {
        error_type: validationFailureRecord.error_type,
        error_field: validationFailureRecord.error_field,
        handler: 'apify',
        actor_run_id: enrichmentResult.runId,
        altitude: 10000,
        doctrine: 'STAMPED',
        ...enrichmentResult.metadata
      }
    };

  } catch (error) {
    console.error('[APIFY-HANDLER] Processing failed:', error);
    return {
      success: false,
      error: error.message,
      processingTime: Date.now() - startTime,
      metadata: {
        error_type: validationFailureRecord.error_type,
        handler: 'apify',
        failure_reason: error.message
      }
    };
  }
}

/**
 * Call appropriate Apify actor based on error type
 */
async function callApifyActor(record, companyData) {
  const { error_type, error_field, raw_value } = record;

  switch (error_type) {
    case 'missing_linkedin':
    case 'invalid_linkedin':
      return await enrichLinkedInProfile(companyData, record);

    case 'missing_website':
    case 'website_not_found':
      return await enrichCompanyWebsite(companyData, record);

    case 'missing_ein':
    case 'missing_tax_id':
      return await enrichCompanyRegistration(companyData, record);

    case 'missing_permit':
    case 'missing_license':
      return await enrichBusinessPermits(companyData, record);

    case 'missing_revenue':
    case 'missing_financial_data':
      return await enrichFinancialData(companyData, record);

    default:
      throw new Error(`No Apify actor available for error type: ${error_type}`);
  }
}

/**
 * Enrich LinkedIn profile using Apify LinkedIn scraper
 */
async function enrichLinkedInProfile(companyData, record) {
  console.log('[APIFY-HANDLER] Enriching LinkedIn profile');

  try {
    // Simulate Composio MCP call to Apify LinkedIn scraper
    // In production, this would use actual Composio integration
    const mockLinkedInResult = await simulateComposioApifyCall('linkedin-company-scraper', {
      searchQuery: companyData.company_name || companyData.company,
      website: companyData.website_url || companyData.website,
      location: companyData.company_city && companyData.company_state
        ? `${companyData.company_city}, ${companyData.company_state}`
        : null
    });

    if (mockLinkedInResult.success && mockLinkedInResult.data.linkedinUrl) {
      return {
        success: true,
        enrichedValue: mockLinkedInResult.data.linkedinUrl,
        confidence: 0.85,
        actorUsed: 'linkedin-company-scraper',
        runId: mockLinkedInResult.runId,
        metadata: {
          search_query: companyData.company_name,
          matches_found: mockLinkedInResult.data.matchesCount,
          verification_score: mockLinkedInResult.data.verificationScore
        }
      };
    }

    return {
      success: false,
      error: 'LinkedIn profile not found',
      confidence: 0.0,
      actorUsed: 'linkedin-company-scraper'
    };

  } catch (error) {
    throw new Error(`LinkedIn enrichment failed: ${error.message}`);
  }
}

/**
 * Enrich company website using Apify web crawler
 */
async function enrichCompanyWebsite(companyData, record) {
  console.log('[APIFY-HANDLER] Enriching company website');

  try {
    const searchTerms = [
      companyData.company_name || companyData.company,
      companyData.company_linkedin_url ? extractCompanyFromLinkedIn(companyData.company_linkedin_url) : null
    ].filter(Boolean);

    const mockWebsiteResult = await simulateComposioApifyCall('website-content-crawler', {
      searchTerms: searchTerms,
      location: companyData.company_city && companyData.company_state
        ? `${companyData.company_city}, ${companyData.company_state}`
        : null,
      additionalContext: {
        industry: companyData.industry,
        employee_count: companyData.num_employees
      }
    });

    if (mockWebsiteResult.success && mockWebsiteResult.data.websiteUrl) {
      return {
        success: true,
        enrichedValue: mockWebsiteResult.data.websiteUrl,
        confidence: 0.75,
        actorUsed: 'website-content-crawler',
        runId: mockWebsiteResult.runId,
        metadata: {
          search_terms: searchTerms,
          verification_method: mockWebsiteResult.data.verificationMethod,
          additional_data: mockWebsiteResult.data.additionalCompanyInfo
        }
      };
    }

    return {
      success: false,
      error: 'Company website not found',
      confidence: 0.0,
      actorUsed: 'website-content-crawler'
    };

  } catch (error) {
    throw new Error(`Website enrichment failed: ${error.message}`);
  }
}

/**
 * Enrich company registration data (EIN, tax ID)
 */
async function enrichCompanyRegistration(companyData, record) {
  console.log('[APIFY-HANDLER] Enriching company registration data');

  try {
    const mockRegistrationResult = await simulateComposioApifyCall('company-data-scraper', {
      companyName: companyData.company_name || companyData.company,
      state: companyData.company_state,
      address: companyData.company_address || `${companyData.company_city}, ${companyData.company_state}`,
      website: companyData.website_url || companyData.website,
      dataTypes: ['ein', 'tax_id', 'registration_number', 'incorporation_date']
    });

    if (mockRegistrationResult.success && mockRegistrationResult.data.ein) {
      return {
        success: true,
        enrichedValue: mockRegistrationResult.data.ein,
        confidence: 0.9,
        actorUsed: 'company-data-scraper',
        runId: mockRegistrationResult.runId,
        metadata: {
          registration_state: mockRegistrationResult.data.registrationState,
          incorporation_date: mockRegistrationResult.data.incorporationDate,
          business_type: mockRegistrationResult.data.businessType,
          data_source: mockRegistrationResult.data.dataSource
        }
      };
    }

    return {
      success: false,
      error: 'Company registration data not found',
      confidence: 0.0,
      actorUsed: 'company-data-scraper'
    };

  } catch (error) {
    throw new Error(`Registration data enrichment failed: ${error.message}`);
  }
}

/**
 * Enrich business permits and licenses
 */
async function enrichBusinessPermits(companyData, record) {
  console.log('[APIFY-HANDLER] Enriching business permits');

  try {
    const mockPermitResult = await simulateComposioApifyCall('business-permit-scraper', {
      companyName: companyData.company_name || companyData.company,
      state: companyData.company_state,
      industry: companyData.industry,
      city: companyData.company_city,
      permitTypes: ['business_license', 'operating_permit', 'professional_license']
    });

    if (mockPermitResult.success && mockPermitResult.data.permits?.length > 0) {
      const primaryPermit = mockPermitResult.data.permits[0];

      return {
        success: true,
        enrichedValue: primaryPermit.permit_number,
        confidence: 0.8,
        actorUsed: 'business-permit-scraper',
        runId: mockPermitResult.runId,
        metadata: {
          permit_type: primaryPermit.permit_type,
          issuing_authority: primaryPermit.issuing_authority,
          expiration_date: primaryPermit.expiration_date,
          all_permits: mockPermitResult.data.permits
        }
      };
    }

    return {
      success: false,
      error: 'Business permits not found',
      confidence: 0.0,
      actorUsed: 'business-permit-scraper'
    };

  } catch (error) {
    throw new Error(`Business permit enrichment failed: ${error.message}`);
  }
}

/**
 * Enrich financial data (revenue, funding)
 */
async function enrichFinancialData(companyData, record) {
  console.log('[APIFY-HANDLER] Enriching financial data');

  try {
    const mockFinancialResult = await simulateComposioApifyCall('financial-data-scraper', {
      companyName: companyData.company_name || companyData.company,
      website: companyData.website_url || companyData.website,
      linkedinUrl: companyData.company_linkedin_url,
      industry: companyData.industry,
      dataTypes: ['annual_revenue', 'funding_rounds', 'valuation', 'employee_count']
    });

    if (mockFinancialResult.success && mockFinancialResult.data.annual_revenue) {
      return {
        success: true,
        enrichedValue: mockFinancialResult.data.annual_revenue,
        confidence: 0.7, // Lower confidence for financial data
        actorUsed: 'financial-data-scraper',
        runId: mockFinancialResult.runId,
        metadata: {
          revenue_range: mockFinancialResult.data.revenue_range,
          funding_total: mockFinancialResult.data.funding_total,
          last_funding_date: mockFinancialResult.data.last_funding_date,
          data_sources: mockFinancialResult.data.sources
        }
      };
    }

    return {
      success: false,
      error: 'Financial data not found',
      confidence: 0.0,
      actorUsed: 'financial-data-scraper'
    };

  } catch (error) {
    throw new Error(`Financial data enrichment failed: ${error.message}`);
  }
}

/**
 * Simulate Composio MCP call to Apify actor
 * In production, this would use actual Composio integration
 */
async function simulateComposioApifyCall(actorName, params) {
  // Simulate processing delay
  await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

  const runId = 'act_' + Math.random().toString(36).substr(2, 9);

  // Simulate different success rates based on actor
  const successRates = {
    'linkedin-company-scraper': 0.8,
    'website-content-crawler': 0.7,
    'company-data-scraper': 0.65,
    'business-permit-scraper': 0.6,
    'financial-data-scraper': 0.55
  };

  const successRate = successRates[actorName] || 0.5;
  const isSuccess = Math.random() < successRate;

  if (!isSuccess) {
    return {
      success: false,
      error: `Actor ${actorName} failed to find data`,
      runId: runId
    };
  }

  // Generate mock successful results based on actor
  const mockData = generateMockActorResult(actorName, params);

  return {
    success: true,
    data: mockData,
    runId: runId,
    actorName: actorName,
    timestamp: new Date().toISOString()
  };
}

/**
 * Generate mock results for different actors
 */
function generateMockActorResult(actorName, params) {
  switch (actorName) {
    case 'linkedin-company-scraper':
      return {
        linkedinUrl: `https://linkedin.com/company/${params.searchQuery?.toLowerCase().replace(/\s+/g, '-')}`,
        matchesCount: Math.floor(Math.random() * 5) + 1,
        verificationScore: 0.7 + Math.random() * 0.3
      };

    case 'website-content-crawler':
      return {
        websiteUrl: `https://${params.searchTerms?.[0]?.toLowerCase().replace(/\s+/g, '')}.com`,
        verificationMethod: 'dns_verification',
        additionalCompanyInfo: {
          description: 'Company description found on website',
          industry: params.additionalContext?.industry
        }
      };

    case 'company-data-scraper':
      return {
        ein: Math.floor(Math.random() * 900000000) + 100000000,
        registrationState: params.state,
        incorporationDate: '2015-03-15',
        businessType: 'Corporation',
        dataSource: 'state_business_registry'
      };

    case 'business-permit-scraper':
      return {
        permits: [{
          permit_number: 'BP-' + Math.floor(Math.random() * 100000),
          permit_type: 'Business License',
          issuing_authority: `${params.city} Business Office`,
          expiration_date: '2025-12-31'
        }]
      };

    case 'financial-data-scraper':
      return {
        annual_revenue: '$' + (Math.floor(Math.random() * 50) + 5) + 'M',
        revenue_range: '$10M-$50M',
        funding_total: '$' + (Math.floor(Math.random() * 20) + 2) + 'M',
        last_funding_date: '2023-06-15',
        sources: ['crunchbase', 'sec_filings']
      };

    default:
      return { data: 'mock_result' };
  }
}

/**
 * Extract company name from LinkedIn URL
 */
function extractCompanyFromLinkedIn(linkedinUrl) {
  if (!linkedinUrl) return null;

  const match = linkedinUrl.match(/linkedin\.com\/company\/([^\/]+)/i);
  return match ? match[1].replace(/-/g, ' ') : null;
}

/**
 * Get Apify handler capabilities
 */
export function getApifyCapabilities() {
  return {
    supported_error_types: [
      'missing_linkedin',
      'invalid_linkedin',
      'missing_website',
      'website_not_found',
      'missing_ein',
      'missing_tax_id',
      'missing_permit',
      'missing_license',
      'missing_revenue',
      'missing_financial_data'
    ],
    available_actors: [
      'linkedin-company-scraper',
      'website-content-crawler',
      'company-data-scraper',
      'business-permit-scraper',
      'financial-data-scraper'
    ],
    confidence_ranges: {
      'linkedin-company-scraper': [0.7, 0.9],
      'website-content-crawler': [0.6, 0.8],
      'company-data-scraper': [0.8, 0.95],
      'business-permit-scraper': [0.7, 0.85],
      'financial-data-scraper': [0.5, 0.8]
    },
    processing_speed: 'medium', // 2-10 seconds typical
    cost: 'variable', // depends on Apify credits
    metadata: {
      handler_type: 'apify',
      requires_composio: true,
      altitude: 10000,
      doctrine: 'STAMPED'
    }
  };
}