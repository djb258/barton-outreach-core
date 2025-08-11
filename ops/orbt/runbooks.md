# ORBT Runbooks - Marketing Outreach

## Operation Runbooks

### Company Intake Operations
- **unique_id**: [____]
- **process_id**: Manage Company Intake
- **steps**:
  1. Configure Apollo API connection
  2. Set state parameters for company search
  3. Execute company pull with rate limiting
  4. Validate company data structure
  5. Store in marketing_company_intake table

### People Scraping Operations
- **unique_id**: [____]
- **process_id**: Execute People Scraping
- **steps**:
  1. Configure Apify scraping parameters
  2. Target CEO/CFO/HR roles per company
  3. Extract contact information
  4. Stage data for validation
  5. Queue for email validation

### Message Generation Operations
- **unique_id**: [____]
- **process_id**: Generate Outreach Messages
- **steps**:
  1. Load validated contacts from Neon
  2. Apply role-specific message templates
  3. Personalize based on company/role data
  4. Store message variants in registry
  5. Queue for campaign deployment

### Campaign Execution Operations
- **unique_id**: [____]
- **process_id**: Execute Outreach Campaigns
- **steps**:
  1. Configure Instantly/HeyReach API credentials
  2. Deploy message batches with rate limits
  3. Monitor delivery status
  4. Update campaign logs
  5. Surface metrics to dashboard