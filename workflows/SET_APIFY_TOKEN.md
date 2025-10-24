# Setting APIFY_TOKEN in n8n

## ⚠️ Important Note

The APIFY_TOKEN cannot be set via the n8n REST API. It must be configured manually in the n8n UI.

## 📋 Steps to Set APIFY_TOKEN

### Method 1: Via n8n UI (Recommended)

1. **Open n8n Cloud**
   - Navigate to: https://dbarton.app.n8n.cloud
   - Log in to your account

2. **Go to Settings**
   - Click on **Settings** (gear icon) in the left sidebar
   - Select **Environment Variables**

3. **Add APIFY_TOKEN**
   - Click **"Add Variable"**
   - Name: `APIFY_TOKEN`
   - Value: `<your-apify-api-key-here>`
   - Click **Save**

4. **Verify**
   - The variable should now appear in the list
   - Any workflow can access it via `{{$env.APIFY_TOKEN}}`

### Method 2: Via Workflow Credentials (Alternative)

If environment variables are not available, you can create an Apify credential:

1. Go to **Credentials** in n8n
2. Click **"Add Credential"**
3. Search for "Apify"
4. Select **"Apify API"**
5. Name: `Apify Account`
6. API Token: `<your-apify-api-key-here>`
7. Click **"Create"**

Then update the Apify Enrichment workflow to use this credential instead of the environment variable.

## 🔑 Getting Your Apify API Key

1. Go to: https://console.apify.com/
2. Log in to your Apify account
3. Click on **Settings** → **Integrations**
4. Under **API tokens**, click **"Create new token"**
5. Name it: `n8n-integration`
6. Copy the token

## ✅ Verification

After setting the token, verify it works:

```bash
# Test the Apify API with your token
curl -X GET "https://api.apify.com/v2/actor-tasks?token=YOUR_TOKEN"
```

Expected: HTTP 200 with list of your Apify actors/tasks

## 🚨 Security Notes

- Never commit the APIFY_TOKEN to git
- Never share the token via email or chat
- Rotate the token every 90 days
- Use different tokens for dev/staging/prod environments

---

**Status:** Manual configuration required before running Apify Enrichment workflow
