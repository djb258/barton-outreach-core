# Contact Slot System Architecture

## 🎯 Overview

The Barton Outreach Core system implements a **3-Slot Contact System** for each company, ensuring targeted and strategic contact collection for maximum outreach effectiveness.

## 📊 Slot Definition

Each company in the system has **exactly 3 contact slots** that must be filled:

### Slot 1: CEO (Chief Executive Officer)
- **Target Titles**: CEO, Chief Executive Officer, President, Founder, Managing Director
- **Priority**: Highest decision-making authority
- **Outreach Purpose**: Strategic partnerships, high-level business decisions
- **Search Patterns**: `CEO`, `Chief Executive`, `President`, `Founder`, `Managing Director`

### Slot 2: CFO (Chief Financial Officer)
- **Target Titles**: CFO, Chief Financial Officer, VP Finance, Finance Director, Controller
- **Priority**: Financial decision-making authority
- **Outreach Purpose**: Budget approvals, financial planning discussions
- **Search Patterns**: `CFO`, `Chief Financial`, `VP Finance`, `Finance Director`, `Controller`, `Treasurer`

### Slot 3: HR/Benefits (Human Resources Manager)
- **Target Titles**: HR Director, HR Manager, Benefits Manager, People Operations, Chief People Officer
- **Priority**: Employee benefits and HR decision-making
- **Outreach Purpose**: Employee benefits, HR solutions, workforce management
- **Search Patterns**: `HR`, `Human Resources`, `Benefits`, `People Operations`, `CPO`, `Chief People Officer`

## 🏗️ Database Schema

### Company Contact Slots Table
```sql
CREATE TABLE company_contact_slots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES marketing_company_intake(id),
  
  -- Slot 1: CEO
  ceo_contact_id UUID REFERENCES contacts(id),
  ceo_status ENUM('empty', 'in_progress', 'filled', 'not_found') DEFAULT 'empty',
  ceo_scraped_at TIMESTAMP,
  ceo_last_attempt TIMESTAMP,
  
  -- Slot 2: CFO
  cfo_contact_id UUID REFERENCES contacts(id),
  cfo_status ENUM('empty', 'in_progress', 'filled', 'not_found') DEFAULT 'empty',
  cfo_scraped_at TIMESTAMP,
  cfo_last_attempt TIMESTAMP,
  
  -- Slot 3: HR/Benefits
  hr_contact_id UUID REFERENCES contacts(id),
  hr_status ENUM('empty', 'in_progress', 'filled', 'not_found') DEFAULT 'empty',
  hr_scraped_at TIMESTAMP,
  hr_last_attempt TIMESTAMP,
  
  -- Overall tracking
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  completion_percentage INTEGER GENERATED ALWAYS AS (
    CASE 
      WHEN ceo_status = 'filled' THEN 33 ELSE 0 END +
    CASE 
      WHEN cfo_status = 'filled' THEN 33 ELSE 0 END +
    CASE 
      WHEN hr_status = 'filled' THEN 34 ELSE 0 END
  ) STORED,
  
  -- Indexing for performance
  UNIQUE(company_id)
);

-- Indexes for efficient querying
CREATE INDEX idx_company_slots_completion ON company_contact_slots(completion_percentage);
CREATE INDEX idx_company_slots_status ON company_contact_slots(ceo_status, cfo_status, hr_status);
```

### Enhanced Contacts Table
```sql
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Basic information
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  phone VARCHAR(50),
  
  -- Company association
  company_id UUID REFERENCES marketing_company_intake(id),
  company_name VARCHAR(255),
  
  -- Position information
  title VARCHAR(255),
  slot_type ENUM('ceo', 'cfo', 'hr_benefits') NOT NULL,
  seniority_level INTEGER, -- 1-10 scale for ranking within slot
  
  -- Contact details
  linkedin_url TEXT,
  location VARCHAR(255),
  
  -- Scraping metadata
  source VARCHAR(50) DEFAULT 'apollo',
  scraped_at TIMESTAMP DEFAULT NOW(),
  confidence_score INTEGER, -- 1-100, how confident we are this is the right person
  
  -- Quality metrics
  email_verified BOOLEAN DEFAULT FALSE,
  linkedin_verified BOOLEAN DEFAULT FALSE,
  
  UNIQUE(email, company_id)
);

-- Indexes
CREATE INDEX idx_contacts_company_slot ON contacts(company_id, slot_type);
CREATE INDEX idx_contacts_confidence ON contacts(confidence_score DESC);
```

## 🤖 Apollo Scraper Enhancement

### Slot-Specific Filtering
```typescript
interface SlotFilterConfig {
  ceo: {
    titlePatterns: string[];
    exclusions: string[];
    confidenceThreshold: number;
  };
  cfo: {
    titlePatterns: string[];
    exclusions: string[];
    confidenceThreshold: number;
  };
  hr_benefits: {
    titlePatterns: string[];
    exclusions: string[];
    confidenceThreshold: number;
  };
}

class SlotBasedContactFilter {
  private config: SlotFilterConfig = {
    ceo: {
      titlePatterns: [
        'CEO', 'Chief Executive Officer', 'President', 'Founder', 
        'Managing Director', 'Executive Director', 'General Manager'
      ],
      exclusions: ['Assistant', 'Associate', 'Junior', 'Intern'],
      confidenceThreshold: 80
    },
    cfo: {
      titlePatterns: [
        'CFO', 'Chief Financial Officer', 'VP Finance', 'Vice President Finance',
        'Finance Director', 'Financial Director', 'Controller', 'Treasurer'
      ],
      exclusions: ['Assistant', 'Associate', 'Junior', 'Analyst'],
      confidenceThreshold: 75
    },
    hr_benefits: {
      titlePatterns: [
        'HR Director', 'HR Manager', 'Human Resources', 'Benefits Manager',
        'People Operations', 'Chief People Officer', 'CPO', 'VP People',
        'Employee Benefits', 'Benefits Director', 'Benefits Coordinator'
      ],
      exclusions: ['Assistant', 'Coordinator', 'Specialist'],
      confidenceThreshold: 70
    }
  };
  
  filterContactsForSlots(contacts: Contact[]): SlotAssignments {
    const slots = {
      ceo: this.findBestMatch(contacts, 'ceo'),
      cfo: this.findBestMatch(contacts, 'cfo'), 
      hr_benefits: this.findBestMatch(contacts, 'hr_benefits')
    };
    
    return slots;
  }
  
  private findBestMatch(contacts: Contact[], slotType: keyof SlotFilterConfig): Contact | null {
    const config = this.config[slotType];
    
    // Filter candidates
    const candidates = contacts.filter(contact => {
      const title = contact.title?.toLowerCase() || '';
      
      // Must match at least one pattern
      const hasMatch = config.titlePatterns.some(pattern => 
        title.includes(pattern.toLowerCase())
      );
      
      // Must not match exclusions
      const hasExclusion = config.exclusions.some(exclusion =>
        title.includes(exclusion.toLowerCase())
      );
      
      return hasMatch && !hasExclusion;
    });
    
    if (candidates.length === 0) return null;
    
    // Score candidates by relevance
    const scored = candidates.map(contact => ({
      contact,
      score: this.calculateSlotScore(contact, slotType)
    }));
    
    // Sort by score and return best match
    scored.sort((a, b) => b.score - a.score);
    
    const best = scored[0];
    return best.score >= config.confidenceThreshold ? best.contact : null;
  }
  
  private calculateSlotScore(contact: Contact, slotType: string): number {
    const title = contact.title?.toLowerCase() || '';
    let score = 0;
    
    // Exact title matches get highest scores
    if (slotType === 'ceo') {
      if (title.includes('ceo') || title.includes('chief executive')) score += 50;
      if (title.includes('president') && !title.includes('vice')) score += 45;
      if (title.includes('founder')) score += 40;
    } else if (slotType === 'cfo') {
      if (title.includes('cfo') || title.includes('chief financial')) score += 50;
      if (title.includes('vp finance') || title.includes('vice president finance')) score += 45;
      if (title.includes('finance director')) score += 40;
    } else if (slotType === 'hr_benefits') {
      if (title.includes('hr director') || title.includes('human resources director')) score += 50;
      if (title.includes('benefits manager') || title.includes('benefits director')) score += 45;
      if (title.includes('people operations') || title.includes('chief people')) score += 40;
    }
    
    // Seniority indicators
    if (title.includes('senior') || title.includes('principal')) score += 10;
    if (title.includes('director') || title.includes('manager')) score += 8;
    if (title.includes('head of')) score += 6;
    
    // Confidence boosters
    if (contact.email && contact.email.includes(contact.company_name?.toLowerCase())) score += 15;
    if (contact.linkedin_url) score += 10;
    
    return Math.min(score, 100);
  }
}
```

## 🔄 Enhanced Data Flow

### 1. CSV Ingestor Enhancement
```typescript
class CompanySlotInitializer {
  async initializeCompanySlots(companyId: string): Promise<void> {
    await this.neonClient.query(`
      INSERT INTO company_contact_slots (company_id) 
      VALUES ($1) 
      ON CONFLICT (company_id) DO NOTHING
    `, [companyId]);
    
    // Publish event for slot initialization
    this.publishEvent('company.slots.initialized', {
      companyId,
      slots: ['ceo', 'cfo', 'hr_benefits'],
      status: 'ready_for_scraping'
    });
  }
}
```

### 2. Apollo Scraper Slot Processing
```typescript
class SlotBasedScraper {
  async scrapeCompanySlots(companyId: string): Promise<SlotScrapeResult> {
    console.log(`[Slot-Scraper] Processing slots for company ${companyId}`);
    
    // Get company data and current slot status
    const company = await this.getCompanyData(companyId);
    const currentSlots = await this.getCurrentSlotStatus(companyId);
    
    // Determine which slots need filling
    const slotsToFill = this.determineSlotsToFill(currentSlots);
    
    if (slotsToFill.length === 0) {
      return { message: 'All slots already filled', completionRate: 100 };
    }
    
    // Scrape contacts from Apollo
    const apolloContacts = await this.scrapeApolloContacts(company);
    
    // Filter and assign to slots
    const slotAssignments = this.slotFilter.filterContactsForSlots(apolloContacts);
    
    // Update database with assignments
    const updateResult = await this.updateCompanySlots(companyId, slotAssignments);
    
    // Publish completion event
    this.publishEvent('company.slots.updated', {
      companyId,
      filledSlots: Object.keys(slotAssignments).filter(slot => slotAssignments[slot]),
      completionRate: this.calculateCompletionRate(currentSlots, slotAssignments)
    });
    
    return updateResult;
  }
  
  private async updateCompanySlots(
    companyId: string, 
    assignments: SlotAssignments
  ): Promise<SlotUpdateResult> {
    const updates: string[] = [];
    const contacts: Contact[] = [];
    
    // Process each slot assignment
    for (const [slotType, contact] of Object.entries(assignments)) {
      if (contact) {
        // Insert contact
        const contactId = await this.insertContact(contact, slotType as SlotType);
        contacts.push({ ...contact, id: contactId });
        
        // Update slot status
        updates.push(`
          ${slotType}_contact_id = '${contactId}',
          ${slotType}_status = 'filled',
          ${slotType}_scraped_at = NOW()
        `);
      } else {
        // Mark as not found
        updates.push(`
          ${slotType}_status = 'not_found',
          ${slotType}_last_attempt = NOW()
        `);
      }
    }
    
    // Update company slots table
    if (updates.length > 0) {
      await this.neonClient.query(`
        UPDATE company_contact_slots 
        SET ${updates.join(', ')}, updated_at = NOW()
        WHERE company_id = $1
      `, [companyId]);
    }
    
    return {
      companyId,
      contactsAdded: contacts.length,
      slotsProcessed: Object.keys(assignments).length,
      contacts
    };
  }
}
```

### 3. Monitoring and Analytics
```typescript
class SlotAnalytics {
  async getSlotCompletionStats(): Promise<SlotStats> {
    const result = await this.neonClient.query(`
      SELECT 
        COUNT(*) as total_companies,
        COUNT(CASE WHEN ceo_status = 'filled' THEN 1 END) as ceo_filled,
        COUNT(CASE WHEN cfo_status = 'filled' THEN 1 END) as cfo_filled,
        COUNT(CASE WHEN hr_status = 'filled' THEN 1 END) as hr_filled,
        AVG(completion_percentage) as avg_completion,
        COUNT(CASE WHEN completion_percentage = 100 THEN 1 END) as fully_complete
      FROM company_contact_slots
    `);
    
    return {
      totalCompanies: result[0].total_companies,
      slotFillRates: {
        ceo: (result[0].ceo_filled / result[0].total_companies) * 100,
        cfo: (result[0].cfo_filled / result[0].total_companies) * 100,
        hr: (result[0].hr_filled / result[0].total_companies) * 100
      },
      averageCompletion: result[0].avg_completion,
      fullyCompleteCompanies: result[0].fully_complete
    };
  }
  
  async getPriorityScrapingQueue(): Promise<Company[]> {
    // Companies with lowest completion rates get priority
    return await this.neonClient.query(`
      SELECT 
        c.id,
        c.company_name,
        c.apollo_url,
        s.completion_percentage,
        s.ceo_status,
        s.cfo_status,
        s.hr_status
      FROM marketing_company_intake c
      JOIN company_contact_slots s ON c.id = s.company_id
      WHERE s.completion_percentage < 100
      AND c.apollo_url IS NOT NULL
      ORDER BY s.completion_percentage ASC, c.created_at DESC
      LIMIT 50
    `);
  }
}
```

## 📊 API Enhancements

### New Endpoints for Slot Management
```typescript
// GET /api/v1/companies/{id}/slots
router.get('/companies/:id/slots', async (req, res) => {
  const slots = await getCompanySlots(req.params.id);
  res.json({
    companyId: req.params.id,
    slots,
    completionRate: calculateCompletionRate(slots)
  });
});

// POST /api/v1/scraper/fill-slots
router.post('/scraper/fill-slots', async (req, res) => {
  const { companyIds, priority } = req.body;
  const results = [];
  
  for (const companyId of companyIds) {
    const result = await slotScraper.scrapeCompanySlots(companyId);
    results.push(result);
  }
  
  res.json({
    success: true,
    processed: results.length,
    results
  });
});

// GET /api/v1/analytics/slot-completion
router.get('/analytics/slot-completion', async (req, res) => {
  const stats = await slotAnalytics.getSlotCompletionStats();
  res.json(stats);
});
```

## 🎯 Benefits of the 3-Slot System

1. **Targeted Outreach**: Each slot serves a specific business purpose
2. **Quality over Quantity**: Focus on key decision-makers rather than mass collection
3. **Completion Tracking**: Clear metrics on data collection progress
4. **Scalable Architecture**: Easy to add more slot types in the future
5. **Strategic Alignment**: Supports different outreach strategies per role

This 3-slot system ensures that every company in the Barton Outreach Core has the exact contacts needed for effective, targeted business outreach campaigns.