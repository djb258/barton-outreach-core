# Contact Verification Pipeline Architecture

## 🔄 Complete Data Flow

The Barton Outreach Core implements a comprehensive verification pipeline ensuring all contact data is validated before being used for outreach:

```
1. CSV Ingestor → Processes company data → Stores to Neon
2. Neon Database → Triggers Apollo Scraper → Fills 3 contact slots per company
3. Apollo Scraper → Sends contact data → MillionVerifier API
4. MillionVerifier → Verifies emails/data → Returns verification status
5. Verification Service → Updates Neon → Marks slots as verified/invalid
6. Campaign System → Uses only verified contacts → Executes outreach
```

## 📊 Enhanced Database Schema for Verification

### Updated Company Contact Slots Table
```sql
CREATE TABLE company_contact_slots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES marketing_company_intake(id),
  
  -- Slot 1: CEO
  ceo_contact_id UUID REFERENCES contacts(id),
  ceo_status ENUM('empty', 'scraped', 'verifying', 'verified', 'invalid', 'not_found') DEFAULT 'empty',
  ceo_verification_status JSONB, -- MillionVerifier response
  ceo_scraped_at TIMESTAMP,
  ceo_verified_at TIMESTAMP,
  
  -- Slot 2: CFO  
  cfo_contact_id UUID REFERENCES contacts(id),
  cfo_status ENUM('empty', 'scraped', 'verifying', 'verified', 'invalid', 'not_found') DEFAULT 'empty',
  cfo_verification_status JSONB,
  cfo_scraped_at TIMESTAMP,
  cfo_verified_at TIMESTAMP,
  
  -- Slot 3: HR/Benefits
  hr_contact_id UUID REFERENCES contacts(id), 
  hr_status ENUM('empty', 'scraped', 'verifying', 'verified', 'invalid', 'not_found') DEFAULT 'empty',
  hr_verification_status JSONB,
  hr_scraped_at TIMESTAMP,
  hr_verified_at TIMESTAMP,
  
  -- Overall metrics
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Completion percentages
  scraping_completion INTEGER GENERATED ALWAYS AS (
    CASE WHEN ceo_status IN ('scraped', 'verifying', 'verified', 'invalid') THEN 33 ELSE 0 END +
    CASE WHEN cfo_status IN ('scraped', 'verifying', 'verified', 'invalid') THEN 33 ELSE 0 END +
    CASE WHEN hr_status IN ('scraped', 'verifying', 'verified', 'invalid') THEN 34 ELSE 0 END
  ) STORED,
  
  verification_completion INTEGER GENERATED ALWAYS AS (
    CASE WHEN ceo_status IN ('verified', 'invalid') THEN 33 ELSE 0 END +
    CASE WHEN cfo_status IN ('verified', 'invalid') THEN 33 ELSE 0 END +
    CASE WHEN hr_status IN ('verified', 'invalid') THEN 34 ELSE 0 END
  ) STORED,
  
  verified_slots_count INTEGER GENERATED ALWAYS AS (
    CASE WHEN ceo_status = 'verified' THEN 1 ELSE 0 END +
    CASE WHEN cfo_status = 'verified' THEN 1 ELSE 0 END +
    CASE WHEN hr_status = 'verified' THEN 1 ELSE 0 END
  ) STORED,
  
  UNIQUE(company_id)
);

-- Indexes for verification workflows
CREATE INDEX idx_slots_verification_status ON company_contact_slots(ceo_status, cfo_status, hr_status);
CREATE INDEX idx_slots_verification_completion ON company_contact_slots(verification_completion);
CREATE INDEX idx_slots_ready_for_verification ON company_contact_slots(scraping_completion) 
  WHERE scraping_completion = 100;
```

### Enhanced Contacts Table with Verification
```sql
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Basic information
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  phone VARCHAR(50),
  
  -- Company and role
  company_id UUID REFERENCES marketing_company_intake(id),
  company_name VARCHAR(255),
  title VARCHAR(255),
  slot_type ENUM('ceo', 'cfo', 'hr_benefits') NOT NULL,
  
  -- Verification data
  verification_status ENUM('pending', 'verified', 'invalid', 'catch_all', 'disposable') DEFAULT 'pending',
  verification_response JSONB, -- Full MillionVerifier response
  verification_score INTEGER, -- 0-100 confidence score
  verified_at TIMESTAMP,
  
  -- MillionVerifier specific fields
  result VARCHAR(50), -- result from MV (deliverable, undeliverable, etc.)
  reason VARCHAR(100), -- reason from MV (mailbox_full, invalid_domain, etc.)
  role_account BOOLEAN, -- is it a role-based email (info@, support@, etc.)
  free_email BOOLEAN, -- is it a free email provider
  accept_all BOOLEAN, -- does domain accept all emails
  
  -- Quality metrics
  email_quality_score INTEGER, -- Combined score from multiple factors
  linkedin_verified BOOLEAN DEFAULT FALSE,
  phone_verified BOOLEAN DEFAULT FALSE,
  
  -- Metadata
  source VARCHAR(50) DEFAULT 'apollo',
  scraped_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(email, company_id, slot_type)
);

-- Indexes for verification queries
CREATE INDEX idx_contacts_verification_status ON contacts(verification_status);
CREATE INDEX idx_contacts_pending_verification ON contacts(verification_status) 
  WHERE verification_status = 'pending';
CREATE INDEX idx_contacts_verified ON contacts(verification_status, email_quality_score) 
  WHERE verification_status = 'verified';
```

## 🏗️ MillionVerifier Integration Service

### New Service: Email Verification Service
```typescript
class MillionVerifierService {
  private apiKey: string;
  private baseUrl = 'https://api.millionverifier.com/api/v3';
  private rateLimiter: RateLimiter;
  
  constructor() {
    this.apiKey = process.env.MILLIONVERIFIER_API_KEY;
    this.rateLimiter = new RateLimiter(100, 60000); // 100 requests per minute
  }
  
  async verifyEmail(email: string, contactId: string): Promise<VerificationResult> {
    try {
      await this.rateLimiter.wait();
      
      console.log(`[MillionVerifier] Verifying email: ${email}`);
      
      const response = await axios.get(`${this.baseUrl}`, {
        params: {
          api: this.apiKey,
          email: email,
          timeout: 10
        },
        timeout: 15000
      });
      
      const result = this.processVerificationResult(response.data, contactId);
      
      // Log verification for analytics
      this.logVerification(email, result);
      
      return result;
      
    } catch (error) {
      console.error(`[MillionVerifier] Error verifying ${email}:`, error.message);
      throw new Error(`Verification failed: ${error.message}`);
    }
  }
  
  async batchVerifyContacts(contacts: Contact[]): Promise<BatchVerificationResult> {
    console.log(`[MillionVerifier] Batch verifying ${contacts.length} contacts`);
    
    const results: VerificationResult[] = [];
    const errors: { contactId: string, error: string }[] = [];
    
    // Process in chunks to respect rate limits
    const chunks = this.chunkArray(contacts, 10);
    
    for (const chunk of chunks) {
      const chunkPromises = chunk.map(async contact => {
        try {
          const result = await this.verifyEmail(contact.email, contact.id);
          results.push(result);
          
          // Update contact immediately after verification
          await this.updateContactVerification(contact.id, result);
          
        } catch (error) {
          errors.push({
            contactId: contact.id,
            error: error.message
          });
        }
      });
      
      await Promise.allSettled(chunkPromises);
      
      // Wait between chunks to respect rate limits
      await this.delay(1000);
    }
    
    return {
      totalProcessed: contacts.length,
      successful: results.length,
      failed: errors.length,
      results,
      errors
    };
  }
  
  private processVerificationResult(mvResponse: any, contactId: string): VerificationResult {
    const qualityScore = this.calculateEmailQuality(mvResponse);
    
    return {
      contactId,
      email: mvResponse.email,
      result: mvResponse.result, // deliverable, undeliverable, catch_all, etc.
      reason: mvResponse.reason,
      score: mvResponse.score || 0,
      qualityScore,
      verification: {
        isValid: mvResponse.result === 'deliverable',
        isRoleAccount: mvResponse.role_account || false,
        isFreeEmail: mvResponse.free_email || false,
        acceptsAll: mvResponse.accept_all || false,
        isDisposable: mvResponse.disposable || false
      },
      rawResponse: mvResponse,
      verifiedAt: new Date().toISOString()
    };
  }
  
  private calculateEmailQuality(mvResponse: any): number {
    let score = 0;
    
    // Base score from MillionVerifier
    if (mvResponse.result === 'deliverable') score += 40;
    else if (mvResponse.result === 'risky') score += 20;
    else if (mvResponse.result === 'catch_all') score += 30;
    else score += 0; // undeliverable
    
    // Quality factors
    if (!mvResponse.role_account) score += 15; // Personal emails preferred
    if (!mvResponse.free_email) score += 15; // Business emails preferred  
    if (!mvResponse.disposable) score += 10; // Not temporary email
    if (mvResponse.mx_found) score += 10; // Valid mail server
    if (mvResponse.smtp_check) score += 10; // SMTP validation passed
    
    return Math.min(score, 100);
  }
  
  private async updateContactVerification(
    contactId: string, 
    result: VerificationResult
  ): Promise<void> {
    const status = this.determineVerificationStatus(result);
    
    await this.neonClient.query(`
      UPDATE contacts SET
        verification_status = $1,
        verification_response = $2,
        verification_score = $3,
        result = $4,
        reason = $5,
        role_account = $6,
        free_email = $7,
        accept_all = $8,
        email_quality_score = $9,
        verified_at = NOW(),
        updated_at = NOW()
      WHERE id = $10
    `, [
      status,
      JSON.stringify(result.rawResponse),
      result.score,
      result.result,
      result.reason,
      result.verification.isRoleAccount,
      result.verification.isFreeEmail,
      result.verification.acceptsAll,
      result.qualityScore,
      contactId
    ]);
  }
  
  private determineVerificationStatus(result: VerificationResult): string {
    if (result.result === 'deliverable') return 'verified';
    if (result.result === 'undeliverable') return 'invalid';
    if (result.result === 'catch_all') return 'catch_all';
    if (result.verification.isDisposable) return 'disposable';
    return 'invalid';
  }
}
```

## 🔄 Enhanced Apollo Scraper with Verification Flow

### Updated Scraper Service
```typescript
class EnhancedApolloScraper {
  private verificationService: MillionVerifierService;
  
  async scrapeAndVerifyCompanySlots(companyId: string): Promise<CompanyProcessingResult> {
    console.log(`[Enhanced-Scraper] Processing company ${companyId} with verification`);
    
    try {
      // Step 1: Scrape contacts for all 3 slots
      const scrapeResult = await this.scrapeCompanySlots(companyId);
      
      if (scrapeResult.contactsAdded === 0) {
        return { 
          companyId, 
          stage: 'scraping_failed', 
          message: 'No contacts found for any slot' 
        };
      }
      
      // Step 2: Update slot status to 'scraped'
      await this.updateSlotStatus(companyId, scrapeResult.filledSlots, 'scraped');
      
      // Step 3: Send contacts to MillionVerifier
      console.log(`[Enhanced-Scraper] Sending ${scrapeResult.contactsAdded} contacts for verification`);
      
      // Update status to 'verifying'
      await this.updateSlotStatus(companyId, scrapeResult.filledSlots, 'verifying');
      
      // Batch verify all contacts for this company
      const verificationResult = await this.verificationService.batchVerifyContacts(
        scrapeResult.contacts
      );
      
      // Step 4: Process verification results and update slot statuses
      await this.processVerificationResults(companyId, verificationResult);
      
      // Step 5: Publish completion event
      this.publishEvent('company.verification.completed', {
        companyId,
        totalContacts: scrapeResult.contactsAdded,
        verifiedContacts: verificationResult.successful,
        failedVerifications: verificationResult.failed,
        readyForOutreach: await this.countVerifiedSlots(companyId)
      });
      
      return {
        companyId,
        stage: 'completed',
        scraping: scrapeResult,
        verification: verificationResult,
        message: `Successfully processed ${scrapeResult.contactsAdded} contacts with ${verificationResult.successful} verified`
      };
      
    } catch (error) {
      console.error(`[Enhanced-Scraper] Error processing company ${companyId}:`, error);
      
      // Mark any in-progress slots as failed
      await this.handleProcessingFailure(companyId, error.message);
      
      throw error;
    }
  }
  
  private async processVerificationResults(
    companyId: string, 
    verificationResult: BatchVerificationResult
  ): Promise<void> {
    // Get current slot assignments
    const slotData = await this.getCompanySlotData(companyId);
    
    // Process each verification result
    for (const result of verificationResult.results) {
      const contact = await this.getContactById(result.contactId);
      const slotType = contact.slot_type;
      
      // Determine final slot status based on verification
      const slotStatus = result.verification.isValid ? 'verified' : 'invalid';
      
      // Update the specific slot status
      await this.updateSpecificSlotStatus(companyId, slotType, slotStatus, {
        verification_status: result.rawResponse,
        verified_at: 'NOW()'
      });
      
      console.log(`[Enhanced-Scraper] ${slotType.toUpperCase()} slot for company ${companyId}: ${slotStatus}`);
    }
    
    // Handle failed verifications
    for (const error of verificationResult.errors) {
      const contact = await this.getContactById(error.contactId);
      const slotType = contact.slot_type;
      
      await this.updateSpecificSlotStatus(companyId, slotType, 'invalid', {
        verification_status: JSON.stringify({ error: error.error }),
        verified_at: 'NOW()'
      });
    }
  }
  
  private async updateSpecificSlotStatus(
    companyId: string, 
    slotType: string, 
    status: string, 
    additionalFields: Record<string, any>
  ): Promise<void> {
    const updateFields = [`${slotType}_status = $2`];
    const params = [companyId, status];
    let paramCount = 2;
    
    // Add additional fields to update
    Object.entries(additionalFields).forEach(([key, value]) => {
      paramCount++;
      updateFields.push(`${slotType}_${key} = $${paramCount}`);
      params.push(value);
    });
    
    await this.neonClient.query(`
      UPDATE company_contact_slots 
      SET ${updateFields.join(', ')}, updated_at = NOW()
      WHERE company_id = $1
    `, params);
  }
}
```

## 📊 Verification Analytics and Monitoring

### Verification Dashboard Service
```typescript
class VerificationAnalytics {
  async getVerificationStats(): Promise<VerificationStats> {
    const stats = await this.neonClient.query(`
      SELECT 
        -- Contact verification stats
        COUNT(*) as total_contacts,
        COUNT(CASE WHEN verification_status = 'verified' THEN 1 END) as verified_contacts,
        COUNT(CASE WHEN verification_status = 'invalid' THEN 1 END) as invalid_contacts,
        COUNT(CASE WHEN verification_status = 'pending' THEN 1 END) as pending_verification,
        
        -- Email quality metrics
        AVG(email_quality_score) as avg_quality_score,
        COUNT(CASE WHEN role_account = true THEN 1 END) as role_accounts,
        COUNT(CASE WHEN free_email = true THEN 1 END) as free_emails,
        
        -- Slot-specific stats
        COUNT(CASE WHEN slot_type = 'ceo' AND verification_status = 'verified' THEN 1 END) as verified_ceos,
        COUNT(CASE WHEN slot_type = 'cfo' AND verification_status = 'verified' THEN 1 END) as verified_cfos,
        COUNT(CASE WHEN slot_type = 'hr_benefits' AND verification_status = 'verified' THEN 1 END) as verified_hrs
      FROM contacts
    `);
    
    const slotStats = await this.neonClient.query(`
      SELECT 
        COUNT(*) as total_companies,
        COUNT(CASE WHEN verified_slots_count >= 1 THEN 1 END) as companies_with_1_verified,
        COUNT(CASE WHEN verified_slots_count >= 2 THEN 1 END) as companies_with_2_verified,
        COUNT(CASE WHEN verified_slots_count = 3 THEN 1 END) as companies_fully_verified,
        AVG(verification_completion) as avg_verification_completion
      FROM company_contact_slots
    `);
    
    return {
      contacts: stats[0],
      companies: slotStats[0],
      verificationRate: (stats[0].verified_contacts / stats[0].total_contacts) * 100,
      readyForOutreach: slotStats[0].companies_with_1_verified
    };
  }
  
  async getCompaniesReadyForOutreach(): Promise<Company[]> {
    // Companies with at least one verified contact in each priority slot
    return await this.neonClient.query(`
      SELECT 
        c.id,
        c.company_name,
        c.industry,
        c.location,
        s.verified_slots_count,
        s.ceo_status,
        s.cfo_status,
        s.hr_status
      FROM marketing_company_intake c
      JOIN company_contact_slots s ON c.id = s.company_id
      WHERE s.verified_slots_count >= 1
      AND (s.ceo_status = 'verified' OR s.cfo_status = 'verified')
      ORDER BY s.verified_slots_count DESC, c.created_at DESC
    `);
  }
}
```

## 🚀 API Enhancements for Verification

### New Verification Endpoints
```typescript
// POST /api/v1/verification/verify-company
router.post('/verify-company/:companyId', async (req, res) => {
  try {
    const result = await enhancedScraper.scrapeAndVerifyCompanySlots(req.params.companyId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /api/v1/verification/stats
router.get('/verification/stats', async (req, res) => {
  const stats = await verificationAnalytics.getVerificationStats();
  res.json(stats);
});

// GET /api/v1/verification/ready-for-outreach
router.get('/verification/ready-for-outreach', async (req, res) => {
  const companies = await verificationAnalytics.getCompaniesReadyForOutreach();
  res.json({
    readyCompanies: companies.length,
    companies
  });
});

// POST /api/v1/verification/batch-verify
router.post('/verification/batch-verify', async (req, res) => {
  const { companyIds } = req.body;
  const results = [];
  
  for (const companyId of companyIds) {
    const result = await enhancedScraper.scrapeAndVerifyCompanySlots(companyId);
    results.push(result);
  }
  
  res.json({
    processed: results.length,
    results
  });
});
```

## 🎯 Complete Pipeline Benefits

1. **Data Quality Assurance**: Every email is verified before outreach
2. **Cost Optimization**: Avoid bounced emails and maintain sender reputation  
3. **Completion Tracking**: Clear pipeline from ingestion to verified contacts
4. **Strategic Targeting**: 3-slot system ensures key decision-makers are reached
5. **Automated Workflow**: Minimal manual intervention required
6. **Scalable Architecture**: Handle thousands of companies efficiently

This verification pipeline ensures that the Barton Outreach Core system delivers only high-quality, verified contacts for maximum outreach effectiveness.