# Firebase Configuration

## Purpose

Firebase integration for Barton Outreach Core, configured per IMO Creator global config.

## Setup

1. **Obtain Firebase credentials** from Firebase Console
2. **Save as** `firebase.json` in this directory
3. **DO NOT commit** `firebase.json` to Git (already in `.gitignore`)

## File: firebase.json

Place your Firebase service account credentials here:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

## Usage

```javascript
const { initializeFirebase, syncToFirebase } = require('./firebase-config');

// Initialize
const firebase = initializeFirebase();

// Sync data
await syncToFirebase('marketing_companies', companyData, companyId);
```

## Collections

Per global-config.yaml:
- `marketing_companies` - Company master records
- `marketing_contacts` - Contact/people records
- `enrichment_logs` - Enrichment job logs
- `system_errors` - Error tracking

## Status

- **Enabled**: Yes (per global-config.yaml)
- **MCP Integration**: Yes
- **Realtime Sync**: No (can be enabled if needed)

## Security

- Firebase credentials are sensitive
- Never commit `firebase.json`
- Use environment variables for production
- Shared with IMO Creator MCP server
