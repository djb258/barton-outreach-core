/**
 * Doctrine Spec:
 * - Barton ID: 03.01.03.07.10000.009
 * - Altitude: 10000 (Execution Layer)
 * - Input: outreach API requests and parameters
 * - Output: outreach operation results
 * - MCP: Composio (Neon integrated)
 */
// Outreach-specific endpoints for the UI components
// These endpoints connect to your original schema tables and monitoring views

import { z } from 'zod';

// Validation schemas
const CompaniesQuerySchema = z.object({
  limit: z.coerce.number().default(100),
  offset: z.coerce.number().default(0),
  search: z.string().optional()
});

const ContactsQuerySchema = z.object({
  limit: z.coerce.number().default(50),
  offset: z.coerce.number().default(0),
  company_id: z.coerce.number().optional()
});

// Add outreach endpoints to the app
export function setupOutreachEndpoints(app, executeSecureQuery) {

  // GET /api/outreach/companies - Get companies with status
  app.get('/api/outreach/companies', async (req, res) => {
    try {
      const { limit, offset, search } = CompaniesQuerySchema.parse(req.query);
      
      let whereConditions = ['1=1'];
      let params = [];
      
      if (search) {
        whereConditions.push(`c.name ILIKE $${params.length + 1}`);
        params.push(`%${search}%`);
      }
      
      const whereClause = whereConditions.join(' AND ');
      
      // Query your original company table with contact verification status
      const query = `
        SELECT 
          c.company_id,
          c.name as company_name,
          c.website_url,
          c.last_url_refresh_at,
          -- Add derived dot color based on contact verification status
          CASE 
            WHEN COUNT(cv.contact_id) = 0 THEN 'gray'
            WHEN COUNT(CASE WHEN cv.status = 'green' THEN 1 END) > 0 THEN 'green'
            WHEN COUNT(CASE WHEN cv.status = 'yellow' THEN 1 END) > 0 THEN 'yellow'
            WHEN COUNT(CASE WHEN cv.status = 'red' THEN 1 END) > 0 THEN 'red'
            ELSE 'gray'
          END as dot_color,
          COUNT(contact.contact_id) as contact_count,
          COUNT(CASE WHEN cv.status = 'green' THEN 1 END) as verified_contacts
        FROM company c
        LEFT JOIN contact ON c.company_id = contact.company_id
        LEFT JOIN contact_verification cv ON contact.contact_id = cv.contact_id
        WHERE ${whereClause}
        GROUP BY c.company_id, c.name, c.website_url, c.last_url_refresh_at
        ORDER BY c.company_id DESC
        LIMIT $${params.length + 1} OFFSET $${params.length + 2}
      `;
      
      params.push(limit, offset);
      
      const companies = await executeSecureQuery(query, params);
      
      res.json(companies);
      
    } catch (error) {
      console.error('Get companies error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch companies',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /api/outreach/contacts - Get contacts for a company
  app.get('/api/outreach/contacts', async (req, res) => {
    try {
      const { limit, offset, company_id } = ContactsQuerySchema.parse(req.query);
      
      let whereConditions = ['1=1'];
      let params = [];
      
      if (company_id) {
        whereConditions.push(`c.company_id = $${params.length + 1}`);
        params.push(company_id);
      }
      
      const whereClause = whereConditions.join(' AND ');
      
      // Query your original contact table with verification status
      const query = `
        SELECT 
          c.contact_id,
          c.company_id,
          c.full_name,
          c.title,
          c.email,
          c.last_profile_fetch_at,
          -- Get verification status and convert to dot color
          COALESCE(cv.status, 'gray') as verification_status,
          COALESCE(cv.status, 'gray') as dot_color,
          cv.last_checked_at,
          -- Split full_name for compatibility
          SPLIT_PART(c.full_name, ' ', 1) as first_name,
          CASE 
            WHEN POSITION(' ' IN c.full_name) > 0 
            THEN SUBSTRING(c.full_name FROM POSITION(' ' IN c.full_name) + 1)
            ELSE ''
          END as last_name,
          co.name as company_name
        FROM contact c
        LEFT JOIN contact_verification cv ON c.contact_id = cv.contact_id
        LEFT JOIN company co ON c.company_id = co.company_id
        WHERE ${whereClause}
        ORDER BY c.contact_id DESC
        LIMIT $${params.length + 1} OFFSET $${params.length + 2}
      `;
      
      params.push(limit, offset);
      
      const contacts = await executeSecureQuery(query, params);
      
      res.json(contacts);
      
    } catch (error) {
      console.error('Get contacts error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch contacts',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /api/outreach/queues/company-urls - Get companies needing URL refresh
  app.get('/api/outreach/queues/company-urls', async (req, res) => {
    try {
      // Use your monitoring view
      const query = `
        SELECT 
          company_id,
          website_url as url,
          'website' as kind
        FROM next_company_urls_30d
        ORDER BY company_id
        LIMIT 100
      `;
      
      const items = await executeSecureQuery(query);
      
      res.json(items);
      
    } catch (error) {
      console.error('Get company URLs queue error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch company URLs queue',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /api/outreach/queues/profile-urls - Get contacts needing profile refresh
  app.get('/api/outreach/queues/profile-urls', async (req, res) => {
    try {
      // Use your monitoring view
      const query = `
        SELECT 
          contact_id,
          email as url,
          'profile' as kind,
          -- Get company_id for the contact
          (SELECT company_id FROM contact WHERE contact.contact_id = next_profile_urls_30d.contact_id) as company_id
        FROM next_profile_urls_30d
        ORDER BY contact_id
        LIMIT 100
      `;
      
      const items = await executeSecureQuery(query);
      
      res.json(items);
      
    } catch (error) {
      console.error('Get profile URLs queue error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch profile URLs queue',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /api/outreach/queues/mv-batch - Get contacts needing email verification
  app.get('/api/outreach/queues/mv-batch', async (req, res) => {
    try {
      // Use your monitoring view
      const query = `
        SELECT 
          contact_id,
          email,
          -- Get company_id for the contact
          (SELECT company_id FROM contact WHERE contact.contact_id = due_email_recheck_30d.contact_id) as company_id
        FROM due_email_recheck_30d
        ORDER BY contact_id
        LIMIT 100
      `;
      
      const items = await executeSecureQuery(query);
      
      res.json(items);
      
    } catch (error) {
      console.error('Get MV batch queue error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch email verification queue',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // POST /api/outreach/queues/:type/process - Process queue items
  app.post('/api/outreach/queues/:type/process', async (req, res) => {
    try {
      const { type } = req.params;
      const { limit = 10 } = req.body;
      
      // For demo purposes, just mark some items as processed
      let processed = 0;
      
      switch (type) {
        case 'company-urls':
          // Update last_url_refresh_at for companies
          const companyUpdateQuery = `
            UPDATE company 
            SET last_url_refresh_at = NOW() 
            WHERE company_id IN (
              SELECT company_id FROM next_company_urls_30d LIMIT $1
            )
          `;
          await executeSecureQuery(companyUpdateQuery, [limit]);
          processed = limit;
          break;
          
        case 'profile-urls':
          // Update last_profile_fetch_at for contacts
          const contactUpdateQuery = `
            UPDATE contact 
            SET last_profile_fetch_at = NOW() 
            WHERE contact_id IN (
              SELECT contact_id FROM next_profile_urls_30d LIMIT $1
            )
          `;
          await executeSecureQuery(contactUpdateQuery, [limit]);
          processed = limit;
          break;
          
        case 'mv-batch':
          // Update last_checked_at for contact verification
          const verificationUpdateQuery = `
            UPDATE contact_verification 
            SET last_checked_at = NOW(),
                status = CASE 
                  WHEN status = 'gray' THEN 'yellow'
                  ELSE status 
                END
            WHERE contact_id IN (
              SELECT contact_id FROM due_email_recheck_30d LIMIT $1
            )
          `;
          await executeSecureQuery(verificationUpdateQuery, [limit]);
          processed = limit;
          break;
          
        default:
          return res.status(400).json({
            success: false,
            error: `Unknown queue type: ${type}`
          });
      }
      
      res.json({
        success: true,
        processed,
        message: `Processed ${processed} items from ${type} queue`
      });
      
    } catch (error) {
      console.error('Process queue error:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to process queue',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  console.log('✅ Outreach endpoints configured:');
  console.log('   • GET /api/outreach/companies - Company list with status');
  console.log('   • GET /api/outreach/contacts - Contact list with verification');
  console.log('   • GET /api/outreach/queues/company-urls - Companies needing refresh');
  console.log('   • GET /api/outreach/queues/profile-urls - Contacts needing refresh');
  console.log('   • GET /api/outreach/queues/mv-batch - Emails needing verification');
  console.log('   • POST /api/outreach/queues/:type/process - Process queue items');
}