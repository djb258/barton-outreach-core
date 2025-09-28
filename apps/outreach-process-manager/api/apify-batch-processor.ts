/**
 * Doctrine Spec:
 * - Barton ID: 07.01.01.07.10000.016
 * - Altitude: 10000 (Execution Layer)
 * - Input: Apify batch job configuration and data
 * - Output: batch processing results and status
 * - MCP: Composio (Neon integrated)
 */
/**
 * Apify Batch Processor API - Barton Doctrine Pipeline
 * Handles complete Apify data processing workflow from staging to validation
 * Uses Standard Composio MCP Pattern for all database operations
 *
 * Workflow:
 * 1. Create batch → 2. Prepare data → 3. Quality check → 4. Process → 5. Validate
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface ApifyBatchRequest {
  actorId: string;
  runId: string;
  batchType: 'companies' | 'people' | 'mixed';
  rawData: any;
  validationMode?: 'strict' | 'lenient';
}

interface ApifyBatchResponse {
  batchId: string;
  status: 'created' | 'processing' | 'completed' | 'failed';
  summary: {
    totalRecords: number;
    prepared: number;
    processed: number;
    validated: number;
    failed: number;
    duplicates?: number;
  };
  qualityScore?: number;
  recommendations?: string[];
  errors?: string[];
}

/**
 * POST /api/apify-batch-processor
 * Complete Apify batch processing endpoint
 */
export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();
  let batchId: string | null = null;

  try {
    const {
      actorId,
      runId,
      batchType,
      rawData,
      validationMode = 'lenient'
    }: ApifyBatchRequest = req.body;

    // Validate required fields
    if (!actorId || !batchType || !rawData) {
      return res.status(400).json({
        error: 'Missing required fields: actorId, batchType, rawData'
      });
    }

    console.log(`Starting Apify batch processing for ${batchType} from ${actorId}`);

    // Step 1: Create batch log entry
    batchId = await createApifyBatch(bridge, batchType, actorId, runId);
    console.log(`Created batch: ${batchId}`);

    // Step 2: Prepare and stage data
    const preparationResult = await prepareApifyData(
      bridge,
      batchId,
      rawData,
      batchType,
      actorId
    );
    console.log(`Data preparation completed:`, preparationResult);

    // Step 3: Quality assessment
    const qualityResult = await assessDataQuality(bridge, batchId);
    console.log(`Quality assessment completed:`, qualityResult);

    // Step 4: Data enrichment (if quality is acceptable)
    if (qualityResult.quality_score >= 50) {
      if (batchType === 'companies' || batchType === 'mixed') {
        await enrichCompanyData(bridge, batchId);
        console.log(`Company data enrichment completed`);
      }
    }

    // Step 5: Process staged data into main tables
    const processingResult = await processApifyBatch(
      bridge,
      batchId,
      batchType,
      validationMode
    );
    console.log(`Batch processing completed:`, processingResult);

    // Step 6: Run validation if needed
    if (processingResult.processed > 0) {
      const validationResult = await runValidation(bridge, batchType);
      console.log(`Validation completed:`, validationResult);
    }

    // Compile final response
    const response: ApifyBatchResponse = {
      batchId,
      status: processingResult.failed === 0 ? 'completed' : 'failed',
      summary: {
        totalRecords: preparationResult.total_processed || 0,
        prepared: preparationResult.prepared_companies || preparationResult.prepared_people || 0,
        processed: processingResult.processed || 0,
        validated: processingResult.validated || 0,
        failed: processingResult.failed || 0,
        duplicates: processingResult.duplicates || 0
      },
      qualityScore: qualityResult.quality_score,
      recommendations: qualityResult.recommendations || [],
      errors: processingResult.errors || []
    };

    return res.status(200).json(response);

  } catch (error: any) {
    console.error('Apify batch processing error:', error);

    // Log error to batch if we have batch ID
    if (batchId) {
      try {
        await logBatchError(bridge, batchId, error.message);
      } catch (logError) {
        console.error('Failed to log batch error:', logError);
      }
    }

    return res.status(500).json({
      error: 'Batch processing failed',
      message: error.message,
      batchId: batchId
    });
  }
}

/**
 * Create Apify batch log entry
 */
async function createApifyBatch(
  bridge: StandardComposioNeonBridge,
  batchType: string,
  actorId: string,
  runId?: string
): Promise<string> {
  const query = 'SELECT generate_apify_batch_id() as batch_id';
  const batchIdResult = await bridge.query(query);
  const batchId = batchIdResult.rows[0].batch_id;

  const insertQuery = `
    INSERT INTO marketing.apify_batch_log (
      batch_unique_id,
      batch_type,
      source_actor_id,
      source_run_id,
      status,
      processing_mode,
      created_at
    ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
  `;

  await bridge.query(insertQuery, [
    batchId,
    batchType,
    actorId,
    runId || 'unknown',
    'created',
    'api_batch_processor'
  ]);

  return batchId;
}

/**
 * Prepare Apify data using preparation functions
 */
async function prepareApifyData(
  bridge: StandardComposioNeonBridge,
  batchId: string,
  rawData: any,
  batchType: string,
  actorId: string
): Promise<any> {
  if (batchType === 'mixed') {
    const query = 'SELECT prepare_apify_mixed_batch($1, $2, $3) as result';
    const result = await bridge.query(query, [
      batchId,
      JSON.stringify(rawData),
      actorId
    ]);
    return result.rows[0].result;
  }

  if (batchType === 'companies') {
    const companiesArray = Array.isArray(rawData) ? rawData : [rawData];
    const query = 'SELECT prepare_apify_company_data($1, $2, $3) as result';
    const result = await bridge.query(query, [
      batchId,
      JSON.stringify(companiesArray),
      actorId
    ]);
    return result.rows[0].result;
  }

  if (batchType === 'people') {
    const peopleArray = Array.isArray(rawData) ? rawData : [rawData];
    const query = 'SELECT prepare_apify_people_data($1, $2, $3) as result';
    const result = await bridge.query(query, [
      batchId,
      JSON.stringify(peopleArray),
      actorId
    ]);
    return result.rows[0].result;
  }

  throw new Error(`Unknown batch type: ${batchType}`);
}

/**
 * Assess data quality using validation function
 */
async function assessDataQuality(
  bridge: StandardComposioNeonBridge,
  batchId: string
): Promise<any> {
  const query = 'SELECT validate_apify_batch_quality($1) as quality_result';
  const result = await bridge.query(query, [batchId]);
  return result.rows[0].quality_result;
}

/**
 * Enrich company data
 */
async function enrichCompanyData(
  bridge: StandardComposioNeonBridge,
  batchId: string
): Promise<void> {
  const query = 'SELECT enrich_staged_companies($1) as result';
  await bridge.query(query, [batchId]);
}

/**
 * Process staged data into main tables
 */
async function processApifyBatch(
  bridge: StandardComposioNeonBridge,
  batchId: string,
  batchType: string,
  validationMode: string
): Promise<any> {
  const errors: string[] = [];
  let result: any = {
    processed: 0,
    validated: 0,
    failed: 0,
    duplicates: 0,
    errors: []
  };

  try {
    if (batchType === 'companies' || batchType === 'mixed') {
      const companyQuery = 'SELECT * FROM process_apify_company_batch($1, $2)';
      const companyResult = await bridge.query(companyQuery, [batchId, 100]); // Process in batches of 100

      if (companyResult.rows.length > 0) {
        const [processed, validated, failed] = companyResult.rows[0];
        result.processed += processed;
        result.validated += validated;
        result.failed += failed;
      }
    }

    if (batchType === 'people' || batchType === 'mixed') {
      const peopleQuery = 'SELECT * FROM process_apify_people_batch($1, $2)';
      const peopleResult = await bridge.query(peopleQuery, [batchId, 100]);

      if (peopleResult.rows.length > 0) {
        const [processed, validated, failed] = peopleResult.rows[0];
        result.processed += processed;
        result.validated += validated;
        result.failed += failed;
      }
    }

    result.errors = errors;
    return result;

  } catch (error: any) {
    errors.push(`Processing error: ${error.message}`);
    result.errors = errors;
    return result;
  }
}

/**
 * Run validation on processed records
 */
async function runValidation(
  bridge: StandardComposioNeonBridge,
  batchType: string
): Promise<any> {
  try {
    if (batchType === 'companies' || batchType === 'mixed') {
      // Trigger company validation
      const companyValidationQuery = `
        UPDATE marketing.company_raw_intake
        SET validation_status = 'pending'
        WHERE validation_status = 'validated'
        AND source_system = 'apify'
        AND created_at > NOW() - INTERVAL '1 hour'
      `;
      await bridge.query(companyValidationQuery);
    }

    if (batchType === 'people' || batchType === 'mixed') {
      // Trigger people validation
      const peopleValidationQuery = `
        UPDATE marketing.people_raw_intake
        SET validation_status = 'pending'
        WHERE validation_status = 'validated'
        AND source_system = 'apify'
        AND created_at > NOW() - INTERVAL '1 hour'
      `;
      await bridge.query(peopleValidationQuery);
    }

    return { status: 'validation_triggered' };

  } catch (error: any) {
    console.error('Validation trigger error:', error);
    return { status: 'validation_failed', error: error.message };
  }
}

/**
 * Log batch processing error
 */
async function logBatchError(
  bridge: StandardComposioNeonBridge,
  batchId: string,
  errorMessage: string
): Promise<void> {
  const query = `
    UPDATE marketing.apify_batch_log
    SET status = 'failed',
        completed_at = NOW(),
        processing_stats = COALESCE(processing_stats, '{}'::jsonb) || jsonb_build_object(
          'error_message', $2,
          'failed_at', NOW()
        )
    WHERE batch_unique_id = $1
  `;

  await bridge.query(query, [batchId, errorMessage]);
}

/**
 * GET /api/apify-batch-processor?batchId=xxx
 * Check batch processing status
 */
export async function getBatchStatus(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { batchId } = req.query;
  if (!batchId) {
    return res.status(400).json({ error: 'batchId parameter required' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    // Get batch log details
    const batchQuery = `
      SELECT
        batch_unique_id,
        batch_type,
        status,
        total_records,
        prepared_records,
        processed_records,
        validated_records,
        failed_records,
        validation_errors,
        processing_stats,
        created_at,
        completed_at
      FROM marketing.apify_batch_log
      WHERE batch_unique_id = $1
    `;

    const batchResult = await bridge.query(batchQuery, [batchId]);

    if (batchResult.rows.length === 0) {
      return res.status(404).json({ error: 'Batch not found' });
    }

    const batch = batchResult.rows[0];

    // Get import status details
    const statusQuery = `
      SELECT * FROM marketing.apify_import_status
      WHERE batch_unique_id = $1
    `;

    const statusResult = await bridge.query(statusQuery, [batchId]);

    return res.status(200).json({
      batchId: batch.batch_unique_id,
      batchType: batch.batch_type,
      status: batch.status,
      summary: {
        totalRecords: batch.total_records || 0,
        prepared: batch.prepared_records || 0,
        processed: batch.processed_records || 0,
        validated: batch.validated_records || 0,
        failed: batch.failed_records || 0
      },
      processingStats: batch.processing_stats || {},
      importDetails: statusResult.rows,
      createdAt: batch.created_at,
      completedAt: batch.completed_at
    });

  } catch (error: any) {
    console.error('Batch status error:', error);
    return res.status(500).json({
      error: 'Failed to get batch status',
      message: error.message
    });
  }
}