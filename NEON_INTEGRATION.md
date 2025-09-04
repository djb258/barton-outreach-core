# 🚀 Neon Database Integration Guide

Complete setup guide for integrating your Neon PostgreSQL database with the Barton Outreach Core system.

## 📊 **Database Architecture**

### **Schema Structure**
```
company/     - Company management (your provided schema)
├── company           - Core company data
└── company_slot      - CEO/CFO/HR role assignments

people/      - Contact management with email verification
└── contact           - Contacts with dot color status indicators  

intake/      - Data ingestion layer
└── raw_loads         - Staging area for all incoming data

vault/       - Processed data layer  
└── contact_promotions - Audit trail for data promotion
```

### **Key Features**
✅ **Row Level Security (RLS)** - Secure multi-tenant access  
✅ **SECURITY DEFINER Functions** - Safe MCP operations  
✅ **Email Verification Status** - Visual dot color indicators  
✅ **Company-Contact Linking** - Automatic relationship management  
✅ **Audit Trail** - Complete data lineage tracking  
✅ **Generated Columns** - Auto-computed full names and status colors  

## 🛠️ **Setup Steps**

### **1. Create Your Neon Project**
```bash
# If you don't have a Neon project yet:
# 1. Go to https://neon.tech
# 2. Create a new project
# 3. Copy the connection string
```

### **2. Set Environment Variable**
```bash
# Add to your .env file or environment:
NEON_DATABASE_URL="postgresql://username:password@host.neon.tech/dbname?sslmode=require"

# Alternative variable names supported:
# DATABASE_URL
# NEON_MARKETING_DB_URL  
# MARKETING_DATABASE_URL
```

### **3. Run Schema Setup**
```bash
# Execute the complete schema (includes your company schema + enhancements):
npm run db:setup-company

# Or manually:
psql $NEON_DATABASE_URL -f infra/neon-company-schema.sql
```

### **4. Verify Schema Installation**
```bash
# Check complete schema structure:
npm run neon:company-schema

# Check original marketing schema:
npm run neon:schema
```

## 🔧 **Schema Details**

### **Your Company Schema (Enhanced)**
```sql
-- Your original schema with enhancements:
company.company - Core company data
  ├── company_id (BIGSERIAL PRIMARY KEY)
  ├── company_name, ein, website_url, linkedin_url
  ├── address fields (address_line1, city, state, etc.)
  ├── renewal_month, renewal_notice_window_days
  └── created_at, updated_at (added)

company.company_slot - Exactly 3 slots per company  
  ├── CEO, CFO, HR role assignments
  ├── Links to people.contact
  └── Audit timestamps (added)
```

### **Enhanced Contact Management**
```sql
people.contact - Full contact management
  ├── email (UNIQUE), first_name, last_name
  ├── full_name (GENERATED COLUMN)
  ├── phone, linkedin_url, title
  ├── company_id (links to company.company)
  ├── email_status ('verified', 'pending', 'invalid', 'bounced')
  ├── email_status_color (GENERATED: 'green', 'yellow', 'red')
  ├── verification_date, source, tags, custom_fields
  └── audit timestamps
```

### **Secure MCP Integration**
```sql
-- SECURITY DEFINER functions for safe operations:

intake.f_ingest_json(rows, source, batch_id) 
  → Secure data ingestion through MCP

vault.f_promote_contacts(load_ids)
  → Secure promotion from staging to contacts
  → Auto-creates companies if needed
  → Links contacts to companies
  → Fills company slots (CEO/CFO/HR)
```

## 🎨 **UI Integration Features**

### **Contact Status Indicators**
The system provides visual status indicators:
- 🟢 **Green dot**: Email verified
- 🟡 **Yellow dot**: Email pending verification  
- 🔴 **Red dot**: Email invalid/bounced
- ⚪ **Gray dot**: Status unknown

### **Company Slot Management**
- Each company has exactly 3 slots: CEO, CFO, HR
- Contacts can be assigned to roles
- Visual indicators show filled vs empty slots
- Role assignment tracking with timestamps

### **Real-time Data Flow**
```mermaid
graph LR
    A[MCP Ingestion] --> B[intake.raw_loads]
    B --> C[vault.f_promote_contacts()]
    C --> D[people.contact]
    C --> E[company.company]
    D --> F[UI Status Dots]
    E --> G[Company Slots View]
```

## 🔒 **Security Model**

### **Role-Based Access**
```sql
mcp_ingest   - Can insert into intake schema only
mcp_promote  - Can promote data from intake to vault/people  
app_user     - Read-only access to company/people/vault
```

### **Row Level Security**
- All tables have RLS enabled
- Policies control access by role
- SECURITY DEFINER functions provide safe escalation
- Complete audit trail for all operations

## 🧪 **Testing Your Setup**

### **1. Test Schema Installation**
```bash
# Check if all schemas exist:
npm run neon:company-schema

# Should show:
# ✅ Found schemas: company, people, intake, vault
# ✅ Tables and relationships
# ✅ SECURITY DEFINER functions
```

### **2. Test MCP Integration**
```bash
# Test secure ingestion:
node packages/mcp-clients/test-neon-secure.mjs

# Should demonstrate:
# - Data ingestion through intake.f_ingest_json()
# - Contact promotion through vault.f_promote_contacts()
# - Company creation and linking
```

### **3. Test Express API**
```bash
# With your Neon connection string in .env:
cd apps/api && npm run dev

# Test endpoints:
curl http://localhost:3000/health        # Should be healthy now
curl http://localhost:3000/contacts      # Should return contact list
```

### **4. Test React UI**
```bash
# Start React app:
cd apps/amplify-client && npm run dev

# Visit http://localhost:3001
# Should show contact vault with dot color indicators
```

## 📈 **Production Deployment**

### **1. Vercel Environment Variables**
```bash
# In Vercel dashboard, add:
NEON_DATABASE_URL=postgresql://...    # Your production Neon URL
DATABASE_URL=postgresql://...         # Fallback variable
COMPOSIO_API_KEY=your_composio_key    # For MCP operations
```

### **2. Database Migration**
```bash
# In production, run schema setup:
vercel env pull .env.production
DATABASE_URL=$(cat .env.production | grep DATABASE_URL | cut -d= -f2) npm run db:setup-company
```

## 🔍 **Monitoring & Maintenance**

### **Schema Analysis**
```bash
npm run neon:company-schema  # Complete schema inspection
npm run neon:schema         # Original marketing schema
```

### **Data Health Checks**
- Monitor contact verification rates
- Track ingestion success rates  
- Monitor company slot assignment rates
- Review RLS policy effectiveness

### **Performance Optimization**
- All key columns have indexes
- Generated columns for computed values
- Efficient foreign key relationships
- Optimized for common query patterns

## 🚀 **Ready for Production!**

Your Neon integration includes:
- ✅ **Your original company schema** (enhanced with audit fields)
- ✅ **Complete contact management** with email verification
- ✅ **Secure MCP integration** through SECURITY DEFINER functions
- ✅ **UI-ready features** (dot colors, real-time status)
- ✅ **Production security** (RLS, role-based access)
- ✅ **Comprehensive audit trail** for compliance

**Next**: Set your `NEON_DATABASE_URL` and run `npm run db:setup-company`!