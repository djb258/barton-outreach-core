/**
 * Abacus Escalation Handler Service
 * Step 2B of Barton Doctrine Pipeline - AI-powered data enrichment
 * Uses existing Abacus API integration for complex validation failures
 * Escalates when auto-fix and Apify handlers fail multiple times
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * Main Abacus handler - escalates complex validation failures to AI
 */
export async function processAbacusEscalation(validationFailureRecord, companyData = {}, context = {}) {
  const startTime = Date.now();

  try {
    console.log(`[ABACUS-HANDLER] Escalating ${validationFailureRecord.error_type} for record ${validationFailureRecord.record_id}`);

    // Build context for Abacus AI
    const enrichmentContext = buildEnrichmentContext(validationFailureRecord, companyData, context);

    // Call Abacus API for intelligent enrichment
    const abacusResult = await callAbacusForEnrichment(enrichmentContext);

    const processingTime = Date.now() - startTime;

    return {
      success: abacusResult.success,
      originalValue: validationFailureRecord.raw_value,
      enrichedValue: abacusResult.enrichedValue,
      confidence: abacusResult.confidence,
      processingTime,
      reasoning: abacusResult.reasoning,
      metadata: {
        error_type: validationFailureRecord.error_type,
        error_field: validationFailureRecord.error_field,
        handler: 'abacus',
        ai_model_used: abacusResult.modelUsed,
        context_tokens: abacusResult.contextTokens,
        altitude: 10000,
        doctrine: 'STAMPED',
        ...abacusResult.metadata
      }
    };

  } catch (error) {
    console.error('[ABACUS-HANDLER] Processing failed:', error);
    return {
      success: false,
      error: error.message,
      processingTime: Date.now() - startTime,
      metadata: {
        error_type: validationFailureRecord.error_type,
        handler: 'abacus',
        failure_reason: error.message
      }
    };
  }
}

/**
 * Build comprehensive context for Abacus AI enrichment
 */
function buildEnrichmentContext(record, companyData, context) {
  const enrichmentPrompt = `
Data Enrichment Request - Barton Doctrine Pipeline Step 2B

VALIDATION FAILURE DETAILS:
- Error Type: ${record.error_type}
- Field: ${record.error_field}
- Raw Value: "${record.raw_value || 'NULL'}"
- Attempts Made: ${record.attempts || 0}
- Previous Handlers: ${context.previousHandlers?.join(', ') || 'none'}

COMPANY CONTEXT:
${formatCompanyContext(companyData)}

ENRICHMENT TASK:
Please analyze the validation failure and provide the most accurate, up-to-date value for the "${record.error_field}" field. Consider:

1. The company's context and industry
2. Publicly available information
3. Data consistency with other fields
4. Standard formatting requirements for this field type

Previous enrichment attempts have failed. Please provide:
- The corrected value (if determinable)
- Confidence score (0.0-1.0)
- Reasoning for your recommendation
- Whether this should escalate to human review

Format your response as JSON:
{
  "success": boolean,
  "enriched_value": "corrected value or null",
  "confidence": 0.0-1.0,
  "reasoning": "explanation of your analysis",
  "requires_human_review": boolean,
  "additional_context": "any relevant notes"
}
`;

  return {
    prompt: enrichmentPrompt,
    record: record,
    companyData: companyData,
    context: context,
    bartonMetadata: {
      altitude: 10000,
      doctrine: 'STAMPED',
      process_step: '2B_abacus_escalation'
    }
  };
}

/**
 * Format company context for AI prompt
 */
function formatCompanyContext(companyData) {
  if (!companyData || Object.keys(companyData).length === 0) {
    return 'No additional company context available.';
  }

  const contextLines = [];

  if (companyData.company_name || companyData.company) {
    contextLines.push(`- Company Name: ${companyData.company_name || companyData.company}`);
  }

  if (companyData.industry) {
    contextLines.push(`- Industry: ${companyData.industry}`);
  }

  if (companyData.website_url || companyData.website) {
    contextLines.push(`- Website: ${companyData.website_url || companyData.website}`);
  }

  if (companyData.company_city && companyData.company_state) {
    contextLines.push(`- Location: ${companyData.company_city}, ${companyData.company_state}`);
  }

  if (companyData.num_employees) {
    contextLines.push(`- Employees: ${companyData.num_employees}`);
  }

  if (companyData.founded_year) {
    contextLines.push(`- Founded: ${companyData.founded_year}`);
  }

  if (companyData.company_linkedin_url) {
    contextLines.push(`- LinkedIn: ${companyData.company_linkedin_url}`);
  }

  return contextLines.length > 0 ? contextLines.join('\n') : 'Limited company context available.';
}

/**
 * Call Abacus API for intelligent enrichment
 */
async function callAbacusForEnrichment(enrichmentContext) {
  try {
    console.log('[ABACUS-HANDLER] Calling Abacus API for enrichment');

    // Use existing Abacus API integration pattern
    const abacusResponse = await callAbacusAPI(enrichmentContext.prompt);

    if (!abacusResponse.success) {
      throw new Error(`Abacus API call failed: ${abacusResponse.error}`);
    }

    // Parse Abacus response
    let parsedResponse;
    try {
      parsedResponse = JSON.parse(abacusResponse.response);
    } catch (parseError) {
      // If not JSON, try to extract structured data from text response
      parsedResponse = extractStructuredResponse(abacusResponse.response);
    }

    // Validate Abacus response structure
    if (!parsedResponse || typeof parsedResponse !== 'object') {
      throw new Error('Invalid response format from Abacus API');
    }

    return {
      success: parsedResponse.success || false,
      enrichedValue: parsedResponse.enriched_value || null,
      confidence: Math.min(Math.max(parsedResponse.confidence || 0, 0), 1), // Clamp to 0-1
      reasoning: parsedResponse.reasoning || 'No reasoning provided',
      requiresHumanReview: parsedResponse.requires_human_review || false,
      modelUsed: abacusResponse.model || 'unknown',
      contextTokens: abacusResponse.tokens || 0,
      metadata: {
        additional_context: parsedResponse.additional_context,
        abacus_request_id: abacusResponse.requestId,
        processing_time: abacusResponse.processingTime
      }
    };

  } catch (error) {
    console.error('[ABACUS-HANDLER] Abacus API call failed:', error);
    throw new Error(`Abacus enrichment failed: ${error.message}`);
  }
}

/**
 * Call Abacus API (using existing integration pattern)
 */
async function callAbacusAPI(prompt) {
  const apiKey = process.env.ABACUS_API_KEY || 's2_ad901b7e536d47769353c72f146d994b';
  const apiUrl = process.env.ABACUS_API_URL || 'https://api.abacus.ai/api/v0/chat';

  if (!apiKey || apiKey === 'your_abacus_api_key_here') {
    console.log('[ABACUS-HANDLER] No valid API key found, using fallback');
    return generateAbacusFallback(prompt);
  }

  try {
    const requestBody = {
      messages: [
        {
          role: 'system',
          content: 'You are a data enrichment specialist for the Barton Doctrine pipeline. Provide accurate, structured responses for business data validation failures.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 1000,
      temperature: 0.1, // Low temperature for consistent, accurate responses
      model: 'gpt-3.5-turbo' // Fallback model
    };

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`Abacus API HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      success: true,
      response: data.choices?.[0]?.message?.content || data.response || '',
      model: data.model || 'unknown',
      tokens: data.usage?.total_tokens || 0,
      requestId: data.id || Math.random().toString(36).substr(2, 9),
      processingTime: data.processing_time || 0
    };

  } catch (error) {
    console.error('[ABACUS-HANDLER] Abacus API request failed:', error);

    // Return fallback result
    return generateAbacusFallback(prompt);
  }
}

/**
 * Generate fallback response when Abacus API is unavailable
 */
function generateAbacusFallback(prompt) {
  console.log('[ABACUS-HANDLER] Generating fallback response');

  // Extract error type from prompt for basic fallback logic
  const errorTypeMatch = prompt.match(/Error Type: (\w+)/);
  const errorType = errorTypeMatch ? errorTypeMatch[1] : 'unknown';

  const fallbackResponses = {
    'missing_linkedin': {
      success: false,
      enriched_value: null,
      confidence: 0.0,
      reasoning: 'LinkedIn profile enrichment requires manual research. Automated methods failed.',
      requires_human_review: true,
      additional_context: 'Consider searching LinkedIn manually or using professional network contacts.'
    },
    'missing_website': {
      success: false,
      enriched_value: null,
      confidence: 0.0,
      reasoning: 'Website discovery requires manual verification. Automated scrapers found no reliable results.',
      requires_human_review: true,
      additional_context: 'Company may not have a website or uses a non-standard domain.'
    },
    'missing_ein': {
      success: false,
      enriched_value: null,
      confidence: 0.0,
      reasoning: 'EIN/Tax ID requires official business registration lookup. This data is not publicly available through automated means.',
      requires_human_review: true,
      additional_context: 'Contact company directly or use official business registry services.'
    },
    'default': {
      success: false,
      enriched_value: null,
      confidence: 0.0,
      reasoning: 'Complex validation failure requires human expertise. Multiple automated enrichment attempts have failed.',
      requires_human_review: true,
      additional_context: 'This case needs manual investigation by a data specialist.'
    }
  };

  const fallbackResponse = fallbackResponses[errorType] || fallbackResponses.default;

  return {
    success: true,
    response: JSON.stringify(fallbackResponse),
    model: 'fallback_logic',
    tokens: 0,
    requestId: 'fallback_' + Math.random().toString(36).substr(2, 9),
    processingTime: 50
  };
}

/**
 * Extract structured response from unstructured text
 */
function extractStructuredResponse(textResponse) {
  try {
    // Try to find JSON in the response
    const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    // If no JSON found, create structured response from text
    const confidence = textResponse.match(/confidence[:\s]*([0-9.]+)/i);
    const requiresReview = /requires.*human|manual|review/i.test(textResponse);

    return {
      success: !requiresReview,
      enriched_value: null,
      confidence: confidence ? parseFloat(confidence[1]) : 0.0,
      reasoning: textResponse.substring(0, 200) + '...',
      requires_human_review: requiresReview,
      additional_context: 'Parsed from unstructured response'
    };

  } catch (error) {
    console.error('[ABACUS-HANDLER] Failed to parse response:', error);
    return {
      success: false,
      enriched_value: null,
      confidence: 0.0,
      reasoning: 'Failed to parse AI response',
      requires_human_review: true,
      additional_context: textResponse.substring(0, 100) + '...'
    };
  }
}

/**
 * Check if validation failure should escalate to Abacus
 */
export function shouldEscalateToAbacus(record, context = {}) {
  // Escalate if multiple attempts failed
  if (record.attempts >= 2) {
    return {
      shouldEscalate: true,
      reason: 'Multiple enrichment attempts failed'
    };
  }

  // Escalate for complex error types
  const complexErrorTypes = [
    'complex_validation_failure',
    'multiple_field_failure',
    'data_inconsistency',
    'conflicting_data'
  ];

  if (complexErrorTypes.includes(record.error_type)) {
    return {
      shouldEscalate: true,
      reason: 'Complex validation failure type'
    };
  }

  // Escalate if both auto-fix and Apify failed
  if (context.previousHandlers?.includes('auto_fix') && context.previousHandlers?.includes('apify')) {
    return {
      shouldEscalate: true,
      reason: 'Both automated handlers failed'
    };
  }

  return {
    shouldEscalate: false,
    reason: 'Does not meet escalation criteria'
  };
}

/**
 * Get Abacus handler capabilities
 */
export function getAbacusCapabilities() {
  return {
    supported_error_types: ['*'], // Can handle any error type
    escalation_criteria: [
      'attempts >= 2',
      'complex_validation_failure',
      'multiple_field_failure',
      'data_inconsistency',
      'previous_handlers_failed'
    ],
    confidence_ranges: {
      'high_confidence': [0.8, 1.0],
      'medium_confidence': [0.5, 0.8],
      'low_confidence': [0.0, 0.5]
    },
    processing_speed: 'slow', // 5-30 seconds typical
    cost: 'high', // Uses AI API credits
    capabilities: [
      'contextual_analysis',
      'multi_field_reasoning',
      'industry_knowledge',
      'data_consistency_checking',
      'human_escalation_decision'
    ],
    metadata: {
      handler_type: 'abacus',
      requires_api_key: true,
      altitude: 10000,
      doctrine: 'STAMPED'
    }
  };
}