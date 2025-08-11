const express = require('express');
const multer = require('multer');
const router = express.Router();
const IntelligentParser = require('../../lib/parsers/intelligentParser');
const { renderClient } = require('../../../apollo-scraper/api/clients/renderClient');

// Configure multer for file uploads (HEIR Resilient - file size limits)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
    files: 1
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/json'
    ];
    
    const allowedExtensions = ['.csv', '.xls', '.xlsx', '.json'];
    const extension = '.' + file.originalname.split('.').pop().toLowerCase();
    
    if (allowedTypes.includes(file.mimetype) || allowedExtensions.includes(extension)) {
      cb(null, true);
    } else {
      cb(new Error('Unsupported file type. Only CSV, Excel, and JSON files are allowed.'));
    }
  }
});

// Initialize intelligent parser
const parser = new IntelligentParser();

/**
 * POST /api/v1/ingest/parse
 * Parse uploaded file with intelligent detection (HEIR Intelligence)
 */
router.post('/parse', upload.single('file'), async (req, res) => {
  try {
    console.log('[CSV-Ingestor] Parse request received');
    
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
    }

    console.log(`[CSV-Ingestor] Processing file: ${req.file.originalname} (${req.file.size} bytes)`);

    // Create file-like object for parser
    const fileObj = {
      name: req.file.originalname,
      buffer: req.file.buffer,
      size: req.file.size
    };

    // Parse with intelligence
    const result = await parser.parseFile(fileObj);

    if (!result.success) {
      return res.status(400).json({
        success: false,
        error: result.error,
        metadata: result.metadata
      });
    }

    // HEIR Event-driven: Publish parsing completion
    publishEvent('data.parsing.completed', {
      fileName: req.file.originalname,
      recordCount: result.data.length,
      dataType: result.metadata.detectedDataType,
      qualityScore: result.metadata.qualityScore
    });

    res.json({
      success: true,
      message: `Successfully parsed ${result.data.length} records`,
      data: result.data.slice(0, 10), // Preview first 10 records
      metadata: {
        ...result.metadata,
        previewNote: result.data.length > 10 ? `Showing first 10 of ${result.data.length} records` : null
      }
    });

  } catch (error) {
    console.error('[CSV-Ingestor] Parse error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to parse file'
    });
  }
});

/**
 * POST /api/v1/ingest/upload-and-process
 * Complete workflow: Parse and ingest to Render DB (HEIR Hierarchical)
 */
router.post('/upload-and-process', upload.single('file'), async (req, res) => {
  try {
    const { targetTable, validateOnly = false } = req.body;
    
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
    }

    console.log(`[CSV-Ingestor] Upload-and-process: ${req.file.originalname}`);

    // Step 1: Parse file intelligently
    const fileObj = {
      name: req.file.originalname,
      buffer: req.file.buffer,
      size: req.file.size
    };

    const parseResult = await parser.parseFile(fileObj);

    if (!parseResult.success) {
      return res.status(400).json({
        success: false,
        error: parseResult.error,
        step: 'parsing'
      });
    }

    // Step 2: Determine target table intelligently if not specified
    const finalTargetTable = targetTable || determineTargetTable(parseResult.metadata.detectedDataType);

    // Step 3: Validate data quality (HEIR Intelligent)
    if (parseResult.metadata.qualityScore < 60) {
      return res.status(422).json({
        success: false,
        error: 'Data quality too low for ingestion',
        qualityScore: parseResult.metadata.qualityScore,
        issues: parseResult.metadata.qualityIssues,
        step: 'validation'
      });
    }

    // Step 4: If validation only, return results
    if (validateOnly) {
      return res.json({
        success: true,
        message: 'Validation completed successfully',
        recordCount: parseResult.data.length,
        targetTable: finalTargetTable,
        qualityScore: parseResult.metadata.qualityScore,
        preview: parseResult.data.slice(0, 5)
      });
    }

    // Step 5: Ingest to Render DB (HEIR Event-driven)
    console.log(`[CSV-Ingestor] Ingesting ${parseResult.data.length} records to ${finalTargetTable}`);
    
    const ingestionResult = await ingestToRenderDB(parseResult.data, finalTargetTable);

    // HEIR Event: Publish ingestion completion
    publishEvent('data.ingestion.completed', {
      fileName: req.file.originalname,
      recordCount: parseResult.data.length,
      targetTable: finalTargetTable,
      inserted: ingestionResult.inserted,
      failed: ingestionResult.failed
    });

    res.json({
      success: true,
      message: `Successfully processed ${req.file.originalname}`,
      parsing: {
        recordCount: parseResult.data.length,
        qualityScore: parseResult.metadata.qualityScore,
        dataType: parseResult.metadata.detectedDataType
      },
      ingestion: {
        targetTable: finalTargetTable,
        inserted: ingestionResult.inserted,
        failed: ingestionResult.failed,
        errors: ingestionResult.errors
      }
    });

  } catch (error) {
    console.error('[CSV-Ingestor] Upload-and-process error:', error);
    
    // HEIR Event: Publish error
    publishEvent('data.ingestion.failed', {
      fileName: req.file?.originalname,
      error: error.message
    });

    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process file',
      step: 'processing'
    });
  }
});

/**
 * POST /api/v1/ingest/batch
 * Batch processing multiple files (HEIR Resilient)
 */
router.post('/batch', upload.array('files', 10), async (req, res) => {
  try {
    const { targetTable } = req.body;
    
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No files uploaded'
      });
    }

    console.log(`[CSV-Ingestor] Batch processing ${req.files.length} files`);

    const results = [];
    let totalInserted = 0;
    let totalFailed = 0;

    // Process each file with resilient error handling
    for (const file of req.files) {
      try {
        const fileObj = {
          name: file.originalname,
          buffer: file.buffer,
          size: file.size
        };

        // Parse file
        const parseResult = await parser.parseFile(fileObj);
        
        if (!parseResult.success) {
          results.push({
            fileName: file.originalname,
            success: false,
            error: parseResult.error,
            step: 'parsing'
          });
          continue;
        }

        // Determine target
        const finalTargetTable = targetTable || determineTargetTable(parseResult.metadata.detectedDataType);

        // Skip low quality data
        if (parseResult.metadata.qualityScore < 50) {
          results.push({
            fileName: file.originalname,
            success: false,
            error: 'Data quality too low',
            qualityScore: parseResult.metadata.qualityScore,
            step: 'validation'
          });
          continue;
        }

        // Ingest
        const ingestionResult = await ingestToRenderDB(parseResult.data, finalTargetTable);
        
        totalInserted += ingestionResult.inserted;
        totalFailed += ingestionResult.failed;

        results.push({
          fileName: file.originalname,
          success: true,
          recordCount: parseResult.data.length,
          inserted: ingestionResult.inserted,
          failed: ingestionResult.failed,
          targetTable: finalTargetTable,
          qualityScore: parseResult.metadata.qualityScore
        });

      } catch (error) {
        results.push({
          fileName: file.originalname,
          success: false,
          error: error.message,
          step: 'processing'
        });
      }
    }

    // HEIR Event: Publish batch completion
    publishEvent('data.batch.completed', {
      fileCount: req.files.length,
      totalInserted,
      totalFailed,
      successRate: results.filter(r => r.success).length / req.files.length
    });

    res.json({
      success: true,
      message: `Batch processing completed`,
      summary: {
        filesProcessed: req.files.length,
        successful: results.filter(r => r.success).length,
        failed: results.filter(r => !r.success).length,
        totalInserted,
        totalFailed
      },
      details: results
    });

  } catch (error) {
    console.error('[CSV-Ingestor] Batch processing error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Batch processing failed'
    });
  }
});

/**
 * GET /api/v1/ingest/supported-formats
 * Get supported file formats and requirements
 */
router.get('/supported-formats', (req, res) => {
  res.json({
    success: true,
    supportedFormats: [
      {
        format: 'CSV',
        extensions: ['.csv'],
        mimeTypes: ['text/csv'],
        description: 'Comma-separated values with header row'
      },
      {
        format: 'Excel',
        extensions: ['.xlsx', '.xls'],
        mimeTypes: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
        description: 'Microsoft Excel files (first sheet will be used)'
      },
      {
        format: 'JSON',
        extensions: ['.json'],
        mimeTypes: ['application/json'],
        description: 'JSON array of objects'
      }
    ],
    limits: {
      maxFileSize: '50MB',
      maxFiles: 10,
      maxRecords: 100000
    },
    dataTypes: {
      companies: {
        requiredFields: ['company_name'],
        optionalFields: ['domain', 'industry', 'location', 'employee_count'],
        targetTable: 'company.marketing_company'
      },
      people: {
        requiredFields: ['email'],
        optionalFields: ['first_name', 'last_name', 'title', 'company'],
        targetTable: 'people.marketing_people'
      }
    }
  });
});

// Helper functions

function determineTargetTable(dataType) {
  const tableMap = {
    'companies': 'company.marketing_company',
    'people': 'people.marketing_people',
    'mixed': 'general.marketing_data'
  };
  
  return tableMap[dataType] || 'general.marketing_data';
}

async function ingestToRenderDB(data, targetTable) {
  try {
    // Use the Render client from Apollo scraper service
    const payload = {
      records: data,
      target_table: targetTable
    };
    
    const result = await renderClient.insertRecords(payload);
    
    return {
      inserted: result.inserted || 0,
      failed: result.failed || 0,
      errors: result.errors || []
    };
    
  } catch (error) {
    console.error('[CSV-Ingestor] Render DB ingestion error:', error);
    throw new Error(`Database ingestion failed: ${error.message}`);
  }
}

function publishEvent(eventType, payload) {
  // HEIR Event-driven pattern
  console.log(`[HEIR-Event] ${eventType}:`, JSON.stringify(payload, null, 2));
  
  // In production, connect to event bus
  // eventBus.publish(eventType, { service: 'csv-data-ingestor', ...payload });
}

module.exports = router;