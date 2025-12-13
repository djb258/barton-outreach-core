# Barton Outreach Core - Integration Setup Guide

This guide will help you set up and test the **Instantly** and **HeyReach** integrations for email and LinkedIn outreach.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Instantly account with API access
- HeyReach account with API access  
- Neon PostgreSQL database

### 1. Environment Configuration

#### Instantly Integration
```bash
cd services/instantly-integration
cp .env.example .env
```

Edit `.env` file:
```env
# Required
INSTANTLY_API_KEY=your_instantly_api_key_here
NEON_DATABASE_URL=postgresql://user:password@host/database

# Optional (defaults provided)
PORT=3006
NODE_ENV=development
DEFAULT_EMAILS_PER_DAY=50
DEFAULT_FROM_NAME=Your Company
```

#### HeyReach Integration  
```bash
cd services/heyreach-integration
cp .env.example .env
```

Edit `.env` file:
```env
# Required
HEYREACH_API_KEY=your_heyreach_api_key_here
NEON_DATABASE_URL=postgresql://user:password@host/database

# Optional (defaults provided)
PORT=3007
NODE_ENV=development
DEFAULT_DAILY_CONNECTION_LIMIT=20
DEFAULT_DAILY_MESSAGE_LIMIT=30
```

### 2. Install Dependencies

For **both** services:
```bash
# Instantly Integration
cd services/instantly-integration
npm install

# HeyReach Integration  
cd services/heyreach-integration
npm install
```

### 3. Test API Connections

#### Test Instantly
```bash
cd services/instantly-integration
node test-connection.js
```

Expected output:
```
🔌 Testing Instantly API Connection...

✅ Connection successful!
   Account Email: your@email.com
   Plan: Pro
   Status: Active

📊 Account limits retrieved:
   Daily email limit: 1000
   Emails sent today: 45
   Remaining today: 955
   Active campaigns: 3
   
🚀 Ready to create and run campaigns!
```

#### Test HeyReach
```bash
cd services/heyreach-integration  
node test-connection.js
```

Expected output:
```
🔌 Testing HeyReach API Connection...

✅ Connection successful!
   Account Email: your@email.com
   Plan: Growth
   Status: Active
   LinkedIn Accounts: 2

📊 Account limits retrieved:
   Daily connection limit: 100
   Daily message limit: 150
   Connections sent today: 12
   Messages sent today: 8
   
💼 LinkedIn accounts connected:
   1. John Doe (active)
   2. Jane Smith (active)
   
🚀 Ready to create and run LinkedIn campaigns!
```

### 4. Start the Services

#### Start Instantly Service
```bash
cd services/instantly-integration
npm run dev
```
Service runs on: http://localhost:3006

#### Start HeyReach Service  
```bash
cd services/heyreach-integration
npm run dev
```
Service runs on: http://localhost:3007

### 5. Health Checks

Test that services are running:

**Instantly**: http://localhost:3006/health
```json
{
  "service": "instantly-integration",
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "connection": {
    "success": true,
    "connected": true,
    "accountEmail": "your@email.com"
  },
  "architecture": "HEIR",
  "version": "1.0.0"
}
```

**HeyReach**: http://localhost:3007/health  
```json
{
  "service": "heyreach-integration", 
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "connection": {
    "success": true,
    "connected": true,
    "accountEmail": "your@email.com"
  },
  "architecture": "HEIR",
  "version": "1.0.0"
}
```

## 📡 API Endpoints

### Instantly Integration (Port 3006)

#### Campaign Management
- `POST /api/campaigns/create` - Create new email campaign
- `POST /api/campaigns/:id/contacts` - Add contacts to campaign  
- `POST /api/campaigns/:id/launch` - Launch campaign
- `POST /api/campaigns/:id/pause` - Pause campaign
- `GET /api/campaigns/:id/stats` - Get campaign statistics

#### Contact Management
- `GET /api/contacts/:email/status` - Get email delivery status
- `GET /api/contacts/:contactId/engagement` - Get engagement score

#### Outcome Tracking
- `GET /api/outcomes/company/:companyId` - Get company outcomes
- `GET /api/outcomes/slot-performance` - Get slot performance metrics
- `GET /api/outcomes/export?format=csv` - Export outcomes data
- `POST /api/campaigns/webhook` - Webhook for Instantly events

### HeyReach Integration (Port 3007)

#### Campaign Management  
- `POST /api/campaigns/create` - Create new LinkedIn campaign
- `POST /api/campaigns/:id/leads` - Add leads to campaign
- `POST /api/campaigns/:id/start` - Start campaign
- `POST /api/campaigns/:id/pause` - Pause campaign  
- `GET /api/campaigns/:id/stats` - Get campaign statistics

#### Connection & Messaging
- `GET /api/connections/:leadId/status` - Get lead status
- `POST /api/messages/:leadId/send` - Send direct message
- `POST /api/messages/sequences/create` - Create message sequence
- `GET /api/connections/network-growth` - Get network growth data

#### Outcome Tracking
- `GET /api/outcomes/company/:companyId` - Get company outcomes
- `GET /api/outcomes/slot-performance` - Get slot performance metrics  
- `GET /api/outcomes/export?format=csv` - Export LinkedIn outcomes
- `POST /api/campaigns/webhook` - Webhook for HeyReach events

## 🧪 Testing Integration

### Create Test Email Campaign

```bash
curl -X POST http://localhost:3006/api/campaigns/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test CEO Outreach",
    "fromName": "John Doe", 
    "fromEmail": "john@company.com",
    "replyTo": "replies@company.com",
    "subject": "Quick question about {{companyName}}",
    "bodyHtml": "<p>Hi {{firstName}},</p><p>I noticed your role as CEO at {{companyName}}...</p>",
    "bodyText": "Hi {{firstName}}, I noticed your role as CEO at {{companyName}}...",
    "schedule": {
      "emails_per_day": 20,
      "timezone": "America/New_York"
    }
  }'
```

### Create Test LinkedIn Campaign

```bash
curl -X POST http://localhost:3007/api/campaigns/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test CEO LinkedIn Outreach",
    "type": "connection_request",
    "dailyLimit": 15,
    "connectionMessage": "Hi {{firstName}}, I came across {{companyName}} and was impressed by your leadership...",
    "followUpMessages": [
      {
        "content": "Thanks for connecting! Would love to learn more about your experience in {{industry}}.",
        "delayDays": 3
      }
    ]
  }'
```

## 🔧 Troubleshooting

### Common Issues

#### ❌ "Connection test failed"
- Check your API keys in `.env` files
- Verify API keys have proper permissions
- Ensure accounts are active and not suspended

#### ❌ "Missing environment variables"  
- Copy `.env.example` to `.env` 
- Fill in all required variables
- Restart the service after changes

#### ❌ "Daily limits reached"
- Check account limits in your platform dashboards
- Wait for limits to reset (usually midnight in account timezone)
- Consider upgrading your plan for higher limits

#### ❌ "No LinkedIn accounts connected" (HeyReach)
- Log into HeyReach dashboard
- Connect your LinkedIn accounts
- Verify accounts are active and not restricted

### Getting API Keys

#### Instantly API Key
1. Log into your Instantly dashboard
2. Go to Settings → API Keys
3. Generate new API key
4. Copy the key to your `.env` file

#### HeyReach API Key  
1. Log into your HeyReach dashboard
2. Go to Settings → API & Integrations
3. Generate new API key
4. Copy the key to your `.env` file

## 📊 Monitoring & Analytics

Both services include comprehensive outcome tracking:

- **Real-time campaign metrics**
- **Contact engagement scoring** 
- **Slot-specific performance** (CEO, CFO, HR)
- **Company-level analytics**
- **Export functionality** (CSV/JSON)

Access analytics via the API endpoints or integrate with your dashboard.

## 🚀 Production Deployment

### Environment Variables for Production

```env
NODE_ENV=production
LOG_LEVEL=warn

# Security
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=1000

# Webhook Security  
WEBHOOK_SECRET=your_secure_webhook_secret

# Monitoring
OUTCOME_SYNC_INTERVAL_MS=30000
```

### Process Management

Use PM2 for production deployment:

```bash
# Install PM2
npm install -g pm2

# Start services
cd services/instantly-integration
pm2 start src/index.js --name instantly-integration

cd services/heyreach-integration  
pm2 start src/index.js --name heyreach-integration

# Monitor
pm2 list
pm2 logs
```

## 🎯 Integration with 3-Slot System

Both integrations support the **3-slot contact system**:

- **CEO Slot**: Executive-level messaging
- **CFO Slot**: Finance-focused messaging  
- **HR Slot**: Benefits and HR messaging

When adding contacts, specify the `slotType` field:

```json
{
  "contacts": [
    {
      "email": "ceo@company.com",
      "firstName": "John", 
      "lastName": "Smith",
      "companyName": "Acme Corp",
      "title": "CEO",
      "slotType": "CEO",
      "contactId": "uuid-here",
      "companyId": "company-uuid"
    }
  ]
}
```

This enables slot-specific analytics and personalized messaging strategies.

---

✅ **Both integrations are now fully configured and ready for production use!**

The system provides complete email + LinkedIn outreach automation with comprehensive outcome tracking and analytics.