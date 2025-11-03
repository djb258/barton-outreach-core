# n8n Hosted Account Setup - Complete Guide

Step-by-step setup for sending messages from your Neon database via Instantly & HeyReach.

---

## 🎯 What You're Setting Up

Your hosted n8n will:
- ✅ Connect to your Neon Marketing Database
- ✅ Pull contacts with assigned message templates
- ✅ Send emails via Instantly (90 CEOs, 67 CFOs, 12 HR contacts)
- ✅ Send LinkedIn messages via HeyReach
- ✅ Track all sends in your database
- ✅ Record engagement signals for BIT scoring

---

## 📋 STEP-BY-STEP SETUP

### **STEP 1: Add Neon Database Credential in n8n**

1. Log into your **hosted n8n account**
2. Click **"Credentials"** in the left sidebar
3. Click **"Add Credential"** button
4. Search for and select **"Postgres"**
5. Fill in these **exact values**:

```
Name: Neon Marketing DB
Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Database: Marketing DB
User: Marketing DB_owner
Password: npg_OsE4Z2oPCpiT
Port: 5432
SSL: Enable (toggle ON)
```

6. Click **"Test"** - should show "Connection successful"
7. Click **"Save"**

---

### **STEP 2: Import Workflow #1 (Instantly - Email)**

1. In n8n, click **"Workflows"** → **"+ Add Workflow"**
2. Click the **three dots menu** (⋮) → **"Import from File"**
3. Upload: `workflows/06-send-messages-instantly.json`
4. The workflow will open showing 5 nodes
5. Click **each Postgres node** and verify it's using **"Neon Marketing DB"** credential
6. Click **"Save"** (top right)
7. Toggle **"Active"** to ON (top right)

---

### **STEP 3: Import Workflow #2 (HeyReach - LinkedIn)**

1. Click **"+ Add Workflow"** again
2. Import: `workflows/07-send-messages-heyreach.json`
3. Verify all Postgres nodes use **"Neon Marketing DB"** credential
4. Click **"Save"**
5. Toggle **"Active"** to ON

---

### **STEP 4: Assign Messages to Your 170 Contacts**

Run this Python script I created for you:

```bash
python assign_messages_to_contacts.py
```

This will:
- Assign `MSG.CEO.001.A` to 90 CEOs
- Assign `MSG.CFO.005.A` to 67 CFOs  
- Assign `MSG.HR.001.B` to 12 HR contacts
- Total: 169 messages scheduled

---

### **STEP 5: Verify n8n is Sending**

After 15-20 minutes, check:

1. **In n8n**: Click on each workflow → "Executions" tab
   - Should show successful runs
   - Green checkmarks on all nodes

2. **In your database** (run this Python script):
   ```bash
   python check_message_status.py
   ```

3. **In Instantly.ai**: Check your campaign "WV_OUTREACH_2025"
   - Should see leads being added
   - Emails queued/sent

4. **In HeyReach**: Check campaign "WV_LINKEDIN_OUTREACH_2025"
   - Should see LinkedIn messages sent

---

## 🔑 API Keys Reference

Your workflows are pre-configured with these keys:

| Service | API Key | Location in n8n |
|---------|---------|-----------------|
| **Instantly** | `eaf2c37e-ade9-4cd1-9f91-edec66dfc83b:gpeymGNltHfI` | In HTTP Request node headers |
| **HeyReach** | `30l4vmMccKZvGnjsCgMdUb6W4m1qpgt6oSBjwrASV+c=` | In HTTP Request node headers |

These are hardcoded in the workflow JSON, so they'll work immediately after import.

---

## 📊 What Each Workflow Does

### **Workflow 06: Instantly (Email)**

```
Schedule: Every 15 minutes
    ↓
Get Contacts Ready for Email (SQL query)
  → Pulls 50 contacts with message_key_scheduled
  → Only verified emails
  → Only 'email' or 'both' channels
    ↓
Send to Instantly (API call)
  → POST to Instantly.ai
  → Adds lead with custom variables
  → Campaign: WV_OUTREACH_2025
    ↓
Update Message Status (SQL)
  → Clears message_key_scheduled
  → Logs to pipeline_events
    ↓
Track BIT Signal (SQL)
  → Inserts 'email_sent' signal
  → Source: 'instantly'
```

### **Workflow 07: HeyReach (LinkedIn)**

```
Schedule: Every 20 minutes
    ↓
Get Contacts Ready for LinkedIn (SQL query)
  → Pulls 30 contacts with message_key_scheduled
  → Only contacts with linkedin_url
  → Only 'linkedin' or 'both' channels
    ↓
Send to HeyReach (API call)
  → POST to HeyReach API
  → Sends LinkedIn message
  → Campaign: WV_LINKEDIN_OUTREACH_2025
    ↓
Update Message Status (SQL)
  → Clears message_key_scheduled
  → Logs to pipeline_events
    ↓
Track BIT Signal (SQL)
  → Inserts 'linkedin_message_sent' signal
  → Source: 'heyreach'
```

---

## 🎛️ Controls & Monitoring

### **Pause Sending**
In n8n workflow, toggle **"Active"** to OFF

### **Change Frequency**
Edit the Schedule trigger:
- Click the "Schedule" node
- Change interval (default: 15 min for email, 20 min for LinkedIn)

### **Adjust Batch Size**
Edit the SQL query LIMIT:
- Click "Get Contacts" node
- Change `LIMIT 50` to any number (1-100 recommended)

### **Monitor Executions**
- Click workflow name → "Executions" tab
- See all runs with timestamps
- Click any execution to see node-by-node results

---

## 🚀 READY TO LAUNCH

Once you:
1. ✅ Add Neon credential in n8n
2. ✅ Import both workflows
3. ✅ Activate both workflows
4. ✅ Run `assign_messages_to_contacts.py`

Then **automatically within 15-20 minutes**, your first messages will send via Instantly and HeyReach!

---

## 📞 Need Help?

If you need help with:
- n8n credential setup
- Workflow import
- Testing a single send
- Checking results

Just let me know and I'll guide you through it!

**Everything is ready on GitHub - just need to import to your hosted n8n!** 🚀

