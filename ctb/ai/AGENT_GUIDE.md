<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai
Barton ID: 03.01.00
Unique ID: CTB-1898B0A7
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
-->

# 🤖 Agent Guide: Understanding Barton Outreach Core Data Schema

This guide provides a quick reference for AI agents working with the Barton Outreach Core database schema.

## 🎯 **What This System Does**

Barton Outreach Core is a **cold outreach automation system** that:
1. **Ingests** company data from various sources
2. **Scrapes** additional contact information from LinkedIn/websites  
3. **Verifies** email addresses for deliverability
4. **Manages** renewal-based outreach campaigns
5. **Tracks** all communications and results

## 📊 **Database Quick Reference**

### **5 Main Schemas**
```
🏢 company   - Company data & renewal tracking
👥 people    - Contact info & email verification  
📧 marketing - Campaigns & message tracking
🎯 bit       - Buyer intent signals
🔧 ple       - Pipeline logic (future)
```

### **Core Data Flow**
```
Raw Data → company.company → company.company_slot → people.contact → campaigns
```

## 🔑 **Key Tables Agents Should Know**

### **company.company** (Companies)
- `company_id` - Primary key
- `company_name` - Company name  
- `website_url`, `linkedin_url` - URLs for scraping
- `renewal_month` - When they renew (1-12)
- `last_*_checked_at` - Scraping timestamps

### **company.company_slot** (Role Assignments)
- Each company has exactly **3 slots**: CEO, CFO, HR
- `role_code` - ENUM: 'CEO', 'CFO', 'HR'
- `contact_id` - Which person fills this role (nullable)

### **people.contact** (Contacts)
- `contact_id` - Primary key
- `full_name`, `email`, `title` - Basic info
- `profile_source_url` - LinkedIn profile
- `last_profile_checked_at` - Profile scrape timestamp

### **people.contact_verification** (Email Status)
- `email_status` - 'green' (good), 'yellow' (risky), 'red' (bad), 'gray' (unknown)
- `email_checked_at` - Last verification time
- **Rule**: Only send campaigns to 'green' emails

## 🔍 **Magic Views (Zero-Wandering Queues)**

These views automatically show what needs work:

### **What Needs Scraping?**
```sql
-- Companies with URLs to scrape (30-day TTL)
SELECT * FROM company.next_company_urls_30d;

-- Profiles to scrape
SELECT * FROM people.next_profile_urls_30d;

-- Emails to verify  
SELECT * FROM people.due_email_recheck_30d;
```

### **What's Ready for Campaigns?**
```sql
-- Companies in renewal window with verified contacts
SELECT * FROM company.vw_due_renewals_ready;

-- Complete company + contact view
SELECT * FROM company.vw_company_slots;
```

## 🚀 **Common Agent Tasks**

### **1. Add a New Company**
```sql
-- Insert company
INSERT INTO company.company (company_name, website_url, renewal_month)
VALUES ('Acme Corp', 'https://acme.com', 6);

-- Create 3 role slots
INSERT INTO company.company_slot (company_id, role_code)
SELECT currval('company.company_company_id_seq'), unnest(ARRAY['CEO','CFO','HR']);
```

### **2. Add a Contact**
```sql
-- Create contact
INSERT INTO people.contact (full_name, email, title)
VALUES ('John Smith', 'john@acme.com', 'CEO');

-- Create verification record
INSERT INTO people.contact_verification (contact_id, email_status)
VALUES (currval('people.contact_contact_id_seq'), 'gray');

-- Assign to CEO slot
UPDATE company.company_slot 
SET contact_id = currval('people.contact_contact_id_seq')
WHERE company_id = 1 AND role_code = 'CEO';
```

### **3. Mark Scraping Complete**
```sql
-- After scraping website
UPDATE company.company 
SET last_site_checked_at = now() 
WHERE company_id = $1;

-- After email verification
UPDATE people.contact_verification 
SET email_checked_at = now(), email_status = 'green'
WHERE contact_id = $1;
```

### **4. Find Campaign Targets**
```sql
-- Companies ready for outreach
SELECT cs.company_name, cs.full_name, cs.email, cs.role_code
FROM company.vw_company_slots cs
WHERE cs.email_status = 'green'
  AND cs.company_id IN (
    SELECT company_id FROM company.vw_due_renewals_ready
  );
```

## ⚠️ **Important Rules for Agents**

### **Email Verification Status**
- 🟢 **green**: Safe to send emails
- 🟡 **yellow**: Proceed with caution  
- 🔴 **red**: DO NOT send emails
- ⚪ **gray**: Unknown, verify first

### **Slot Management**
- Every company MUST have exactly 3 slots (CEO, CFO, HR)
- Slots can be empty (`contact_id = NULL`)
- One contact can fill multiple slots across companies
- Cannot have duplicate roles per company

### **Scraping Timestamps**
- Always update timestamps after scraping
- Items disappear from queues when timestamps are updated
- 30-day TTL for all scraped data

### **Campaign Logic**
- Only target companies with `email_status = 'green'` contacts
- Check `vw_due_renewals_ready` for renewal-based campaigns
- Log all messages in `marketing.message_log`

## 📈 **Data Quality Checks**

### **Find Problems**
```sql
-- Companies missing slots
SELECT c.company_name, COUNT(cs.role_code) as slot_count
FROM company.company c
LEFT JOIN company.company_slot cs ON cs.company_id = c.company_id
GROUP BY c.company_id, c.company_name
HAVING COUNT(cs.role_code) < 3;

-- Contacts without verification
SELECT p.full_name, p.email
FROM people.contact p
LEFT JOIN people.contact_verification v ON v.contact_id = p.contact_id
WHERE p.email IS NOT NULL AND v.contact_id IS NULL;

-- Queue sizes
SELECT 'company_urls' as queue, COUNT(*) FROM company.next_company_urls_30d
UNION ALL
SELECT 'profiles', COUNT(*) FROM people.next_profile_urls_30d
UNION ALL  
SELECT 'emails', COUNT(*) FROM people.due_email_recheck_30d;
```

## 🔗 **Pipeline Integration**

### **Complete Flow: Ingestor → Neon → Apify → PLE → Bit**

1. **Ingestor**: Data comes in via `/pipeline/execute` API
2. **Neon**: Stored in this database schema
3. **Apify**: Scrapes using queue views
4. **PLE**: Processes and promotes data
5. **Bit**: Generates reusable components

### **API Endpoints**
- `POST /pipeline/execute` - Run complete pipeline
- `GET /pipeline/health` - Check system health
- `GET /pipeline/status/:jobId` - Track job progress

## 📚 **Documentation Files**

- `DATABASE_SCHEMA.md` - Complete technical documentation
- `SCHEMA_DIAGRAM.md` - Visual relationship diagram  
- `PIPELINE_INTEGRATION.md` - Full pipeline details
- `AGENT_GUIDE.md` - This quick reference
- `PRODUCTION_IMPROVEMENTS.md` - Production-grade enhancements applied
- `SCHEMA_VERIFICATION_REPORT.md` - Current deployment status

## 💡 **Pro Tips for Agents**

1. **Always check email status** before sending campaigns
2. **Use the queue views** to find work that needs doing
3. **Update timestamps** after any scraping/verification
4. **Maintain the 3-slot rule** for all companies
5. **Log all communications** in message_log
6. **Check renewal windows** before starting campaigns
7. **Monitor system health** using new monitoring views
8. **Respect data quality** - duplicate emails are automatically prevented

## 📊 **New Monitoring Capabilities**

### **System Health Checks**
```sql
-- Monitor scraping freshness
SELECT * FROM marketing.vw_health_crawl_staleness;

-- Check profile update status  
SELECT * FROM marketing.vw_health_profile_staleness;

-- View current queue sizes
SELECT * FROM marketing.vw_queue_sizes;
```

### **Data Quality Features**
- ✅ **Email duplicate prevention** - Case-insensitive uniqueness enforced
- ✅ **Format validation** - Email and URL format checking active
- ✅ **Performance indexes** - Fast queries on common patterns

This schema is designed for **zero-wandering automation** - the views tell you exactly what needs to be done, and updating timestamps automatically manages the queues.