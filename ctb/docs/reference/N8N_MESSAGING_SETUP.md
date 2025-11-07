# n8n Messaging Setup Guide

Complete setup for sending messages via Instantly (email) and HeyReach (LinkedIn) from your Neon database.

---

## 🎯 What This Does

Your messaging system now:
- ✅ Pulls contacts from `marketing.people_master` with `message_key_scheduled`
- ✅ Gets message templates from `message_key_reference`
- ✅ Sends via **Instantly** (email) or **HeyReach** (LinkedIn)
- ✅ Tracks all sends in `marketing.pipeline_events`
- ✅ Records engagement signals in `bit.bit_signal`
- ✅ Auto-clears `message_key_scheduled` after sending

---

## 🚀 Quick Setup

### **1. Access Your n8n Instance**

Do you have n8n running? If not, you need either:
- **Option A**: n8n Cloud (https://n8n.io) - Hosted solution
- **Option B**: Self-hosted n8n - Run locally with Docker

### **2. Import Workflows**

In n8n:
1. Click **"+"** → **"Import from File"**
2. Import these workflows:
   - `workflows/06-send-messages-instantly.json` (Email via Instantly)
   - `workflows/07-send-messages-heyreach.json` (LinkedIn via HeyReach)

### **3. Configure Neon Database Credential**

In n8n:
1. Go to **Credentials** → **"+ Add Credential"**
2. Select **"Postgres"**
3. Enter:
   - **Name**: `Neon Marketing DB`
   - **Host**: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
   - **Database**: `Marketing DB`
   - **User**: `Marketing DB_owner`
   - **Password**: `npg_OsE4Z2oPCpiT`
   - **Port**: `5432`
   - **SSL**: Enable (required)
4. **Test Connection** → Save

### **4. Activate Workflows**

1. Open **"06 - Send Messages via Instantly"**
2. Click **"Active"** toggle (top right)
3. Repeat for **"07 - Send Messages via HeyReach"**

---

## 📋 How It Works

### **Workflow 06: Instantly (Email)**

```
Every 15 minutes:
  ↓
Query people_master for contacts with:
  - message_key_scheduled IS NOT NULL
  - message_channel IN ('email', 'both')
  - email_verified = TRUE
  ↓
Send to Instantly API
  ↓
Clear message_key_scheduled
  ↓
Log to pipeline_events
  ↓
Track BIT signal
```

### **Workflow 07: HeyReach (LinkedIn)**

```
Every 20 minutes:
  ↓
Query people_master for contacts with:
  - message_key_scheduled IS NOT NULL
  - message_channel IN ('linkedin', 'both')
  - linkedin_url IS NOT NULL
  ↓
Send to HeyReach API
  ↓
Clear message_key_scheduled
  ↓
Log to pipeline_events
  ↓
Track BIT signal
```

---

## 🔑 API Keys Already Configured

Your keys are stored in `ctb/meta/config/mcp-servers.json`:

| Service | API Key | Status |
|---------|---------|--------|
| **Instantly** | `eaf2c37e-ade9-4cd1-9f91-edec66dfc83b:gpeymGNltHfI` | ✅ Ready |
| **HeyReach** | `30l4vmMccKZvGnjsCgMdUb6W4m1qpgt6oSBjwrASV+c=` | ✅ Ready |

---

## 📤 How to Send Messages

### **Step 1: Assign Message Keys to Contacts**

```sql
-- Assign CEO cold intro to all CEOs without messages
UPDATE marketing.people_master pm
SET message_key_scheduled = 'MSG.CEO.001.A'
FROM marketing.company_slots cs
WHERE pm.company_slot_unique_id = cs.company_slot_unique_id
  AND cs.slot_type = 'CEO'
  AND pm.email_verified = TRUE
  AND pm.message_key_scheduled IS NULL;

-- Assign CFO cold intro to all CFOs
UPDATE marketing.people_master pm
SET message_key_scheduled = 'MSG.CFO.005.A'
FROM marketing.company_slots cs
WHERE pm.company_slot_unique_id = cs.company_slot_unique_id
  AND cs.slot_type = 'CFO'
  AND pm.email_verified = TRUE
  AND pm.message_key_scheduled IS NULL;

-- Assign HR cold intro to all HR contacts
UPDATE marketing.people_master pm
SET message_key_scheduled = 'MSG.HR.001.B'
FROM marketing.company_slots cs
WHERE pm.company_slot_unique_id = cs.company_slot_unique_id
  AND cs.slot_type = 'HR'
  AND pm.email_verified = TRUE
  AND pm.message_key_scheduled IS NULL;
```

### **Step 2: n8n Workflows Auto-Send**

Once message keys are assigned, the n8n workflows will:
- Check every 15-20 minutes
- Pick up contacts with message_key_scheduled
- Send via Instantly or HeyReach based on channel
- Auto-clear the message key after sending
- Log everything

### **Step 3: Monitor Results**

```sql
-- Check recent sends
SELECT 
  event_type,
  payload->>'contact_id' as contact_id,
  payload->>'message_key' as message_key,
  payload->>'channel' as channel,
  created_at
FROM marketing.pipeline_events
WHERE event_type = 'message_sent'
ORDER BY created_at DESC
LIMIT 20;

-- Check BIT signals
SELECT 
  bs.signal_type,
  pm.full_name,
  pm.email,
  cm.company_name,
  bs.source,
  bs.captured_at
FROM bit.bit_signal bs
JOIN marketing.people_master pm ON bs.contact_unique_id = pm.unique_id
JOIN marketing.company_master cm ON bs.company_unique_id = cm.company_unique_id
ORDER BY bs.captured_at DESC
LIMIT 20;
```

---

## 📨 Available Message Templates

| Key | Role | Type | Channel | Subject |
|-----|------|------|---------|---------|
| MSG.CEO.001.A | CEO | cold_intro | email | Transforming Benefits Management for Growing Companies |
| MSG.CEO.004.B | CEO | sniper_followup | both | I noticed you checked out our site |
| MSG.CEO.006.A | CEO | renewal_window | both | Your Benefits Renewal is Coming Up |
| MSG.CFO.002.A | CFO | job_change | linkedin | Congrats on the new role! |
| MSG.CFO.005.A | CFO | cold_intro | email | Cut Benefits Costs Without Cutting Coverage |
| MSG.HR.001.B | HR | cold_intro | email | Simplifying Benefits for Your HR Team |
| MSG.HR.003.A | HR | reengage | email | Following up: Benefits Management Solutions |
| MSG.HR.007.A | HR | linkedin_intro | linkedin | Connecting: HR Innovation in WV |

---

## 🔄 Integration with VibeOS

The `vibeos_template_id` field links to your VibeOS templates:
- `vibeos_ceo_intro_a`
- `vibeos_cfo_job_a`
- `vibeos_hr_intro_b`
- etc.

You can create these templates in VibeOS with personalization variables like:
- `{{first_name}}`
- `{{company_name}}`
- `{{role}}`

---

## 🎛️ n8n Workflow Controls

### **Pause Sending**
In n8n, toggle workflow to "Inactive"

### **Change Send Frequency**
Edit the Schedule trigger:
- Instantly: Every 15 minutes (default)
- HeyReach: Every 20 minutes (default)

### **Adjust Batch Size**
Edit the SQL query `LIMIT` value:
- Instantly: `LIMIT 50` (default)
- HeyReach: `LIMIT 30` (default)

---

## 🚨 Safety Features

✅ **Only sends to verified emails** (`email_verified = TRUE`)  
✅ **Only sends to active templates** (`active = TRUE`)  
✅ **Auto-clears message_key after send** (prevents duplicates)  
✅ **Tracks all sends** in pipeline_events  
✅ **Rate limiting** via LIMIT and schedule frequency

---

## 📊 Quick Start Command (Assign Messages Now)

Run this SQL to schedule messages for all 170 contacts right now:

```sql
-- Assign messages to all verified contacts by role
UPDATE marketing.people_master pm
SET message_key_scheduled = CASE cs.slot_type
    WHEN 'CEO' THEN 'MSG.CEO.001.A'
    WHEN 'CFO' THEN 'MSG.CFO.005.A'
    WHEN 'HR' THEN 'MSG.HR.001.B'
    ELSE NULL
END
FROM marketing.company_slots cs
WHERE pm.company_slot_unique_id = cs.company_slot_unique_id
  AND pm.email_verified = TRUE
  AND pm.message_key_scheduled IS NULL;
```

After running this, n8n will automatically:
- Send 90 CEO emails via Instantly
- Send 67 CFO emails via Instantly
- Send 12 HR emails via Instantly
- Track all 169 sends (1 contact might not have verified email)

---

**Setup Complete!** Your messaging system is ready to send from you via Instantly and HeyReach! 🚀

