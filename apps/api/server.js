import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Database connection
const sql = neon(process.env.DATABASE_URL || process.env.NEON_DATABASE_URL);

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173', 'http://localhost:3001'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Validation schemas
const IngestJsonSchema = z.object({
  rows: z.array(z.record(z.any())),
  metadata: z.object({
    source: z.string(),
    timestamp: z.string(),
    count: z.number()
  }).optional()
});

const IngestCsvSchema = z.object({
  csv: z.string(),
  metadata: z.object({
    source: z.string(),
    timestamp: z.string()
  }).optional()
});

const PromoteContactsSchema = z.object({
  filter: z.record(z.any()).optional()
});

const ContactsQuerySchema = z.object({
  limit: z.coerce.number().default(50),
  offset: z.coerce.number().default(0),
  search: z.string().optional(),
  source: z.string().optional()
}).refine(data => data.limit <= 1000, { message: "Limit cannot exceed 1000" });

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await sql`SELECT 1`;
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      database: 'connected'
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Database connection failed'
    });
  }
});

// POST /ingest/json - Ingest JSON data rows
app.post('/ingest/json', async (req, res) => {
  try {
    const { rows, metadata } = IngestJsonSchema.parse(req.body);
    
    if (!rows || rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No data rows provided'
      });
    }

    // Generate batch ID
    const batch_id = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Insert rows into staged_data table
    const insertPromises = rows.map(async (row, index) => {
      const keys = Object.keys(row);
      const values = Object.values(row);
      
      return sql`
        INSERT INTO staged_data (
          batch_id,
          source,
          raw_data,
          created_at
        ) VALUES (
          ${batch_id},
          ${metadata?.source || 'api'},
          ${JSON.stringify(row)},
          NOW()
        )
      `;
    });

    await Promise.all(insertPromises);

    res.json({
      success: true,
      count: rows.length,
      batch_id,
      message: `Successfully ingested ${rows.length} rows`
    });

  } catch (error) {
    console.error('Ingest JSON error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /ingest/csv - Ingest CSV data
app.post('/ingest/csv', async (req, res) => {
  try {
    const { csv, metadata } = IngestCsvSchema.parse(req.body);
    
    if (!csv || csv.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No CSV data provided'
      });
    }

    // Parse CSV data
    const lines = csv.trim().split('\\n');
    if (lines.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'CSV must contain at least a header and one data row'
      });
    }

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      if (values.length === headers.length) {
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index];
        });
        rows.push(row);
      }
    }

    if (rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid data rows found in CSV'
      });
    }

    // Generate batch ID
    const batch_id = `csv_batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Insert rows into staged_data table
    const insertPromises = rows.map(async (row) => {
      return sql`
        INSERT INTO staged_data (
          batch_id,
          source,
          raw_data,
          created_at
        ) VALUES (
          ${batch_id},
          ${metadata?.source || 'csv'},
          ${JSON.stringify(row)},
          NOW()
        )
      `;
    });

    await Promise.all(insertPromises);

    res.json({
      success: true,
      count: rows.length,
      batch_id,
      message: `Successfully ingested ${rows.length} rows from CSV`
    });

  } catch (error) {
    console.error('Ingest CSV error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /promote/contacts - Promote staged data to contacts vault
app.post('/promote/contacts', async (req, res) => {
  try {
    const { filter } = PromoteContactsSchema.parse(req.body);
    
    let whereClause = 'WHERE promoted = false';
    let params = [];
    
    if (filter) {
      // Add filter conditions
      const filterConditions = [];
      Object.entries(filter).forEach(([key, value]) => {
        filterConditions.push(`raw_data->>'${key}' = $${params.length + 1}`);
        params.push(value);
      });
      
      if (filterConditions.length > 0) {
        whereClause += ` AND ${filterConditions.join(' AND ')}`;
      }
    }

    // Get staged data to promote
    const stagedData = await sql`
      SELECT id, raw_data FROM staged_data 
      WHERE promoted = false
      ${filter ? sql.raw(whereClause.replace('WHERE promoted = false', '').replace(' AND ', 'AND '), params) : sql``}
    `;

    if (stagedData.length === 0) {
      return res.json({
        success: true,
        promoted_count: 0,
        message: 'No data found matching criteria'
      });
    }

    // Promote to contacts
    const promotionPromises = stagedData.map(async (record) => {
      const data = record.raw_data;
      
      // Insert into contacts table
      await sql`
        INSERT INTO contacts (
          email,
          name,
          phone,
          company,
          title,
          source,
          tags,
          custom_fields,
          created_at,
          updated_at
        ) VALUES (
          ${data.email || null},
          ${data.name || null},
          ${data.phone || null},
          ${data.company || null},
          ${data.title || null},
          ${data.source || 'promoted'},
          ${data.tags ? JSON.stringify(data.tags) : null},
          ${JSON.stringify(data)},
          NOW(),
          NOW()
        )
        ON CONFLICT (email) DO UPDATE SET
          name = COALESCE(EXCLUDED.name, contacts.name),
          phone = COALESCE(EXCLUDED.phone, contacts.phone),
          company = COALESCE(EXCLUDED.company, contacts.company),
          title = COALESCE(EXCLUDED.title, contacts.title),
          custom_fields = EXCLUDED.custom_fields,
          updated_at = NOW()
      `;
      
      // Mark as promoted
      await sql`UPDATE staged_data SET promoted = true WHERE id = ${record.id}`;
    });

    await Promise.all(promotionPromises);

    res.json({
      success: true,
      promoted_count: stagedData.length,
      message: `Successfully promoted ${stagedData.length} records to contacts`
    });

  } catch (error) {
    console.error('Promote contacts error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /contacts - Retrieve contacts from vault
app.get('/contacts', async (req, res) => {
  try {
    const { limit, offset, search, source } = ContactsQuerySchema.parse(req.query);
    
    let whereConditions = [];
    let params = [];
    
    if (search) {
      whereConditions.push(`(
        name ILIKE $${params.length + 1} OR 
        email ILIKE $${params.length + 1} OR 
        company ILIKE $${params.length + 1}
      )`);
      params.push(`%${search}%`);
    }
    
    if (source) {
      whereConditions.push(`source = $${params.length + 1}`);
      params.push(source);
    }
    
    const whereClause = whereConditions.length > 0 ? 
      `WHERE ${whereConditions.join(' AND ')}` : '';
    
    // Get total count
    const countResult = await sql`
      SELECT COUNT(*) as total FROM contacts
      ${whereClause ? sql.raw(whereClause, params) : sql``}
    `;
    const total = parseInt(countResult[0].total);
    
    // Get contacts
    const contacts = await sql`
      SELECT 
        id,
        email,
        name,
        phone,
        company,
        title,
        source,
        tags,
        custom_fields,
        created_at,
        updated_at
      FROM contacts
      ${whereClause ? sql.raw(whereClause, params) : sql``}
      ORDER BY updated_at DESC
      LIMIT ${limit}
      OFFSET ${offset}
    `;

    res.json({
      contacts,
      total,
      limit,
      offset,
      has_more: offset + contacts.length < total
    });

  } catch (error) {
    console.error('Get contacts error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Default route
app.get('/', (req, res) => {
  res.json({
    name: 'Barton Outreach Core API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: 'GET /health',
      ingest_json: 'POST /ingest/json',
      ingest_csv: 'POST /ingest/csv',
      promote_contacts: 'POST /promote/contacts',
      get_contacts: 'GET /contacts'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Global error handler
app.use((error, req, res, next) => {
  console.error('Global error handler:', error);
  
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Barton Outreach Core API running on port ${PORT}`);
  console.log(`🏥 Health check: http://localhost:${PORT}/health`);
  console.log(`📚 API docs: http://localhost:${PORT}/`);
});

export default app;