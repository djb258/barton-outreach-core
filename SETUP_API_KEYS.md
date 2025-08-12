# API Key Setup Instructions

## Step 1: Decode Your API Keys

You have provided these encoded API keys:

**Instantly**: `ZWFmMmMzN2UtYWRlOS00Y2QxLTlmOTEtZWRlYzY2ZGZjODNiOlFJck5IRm1STHliQw==`

**HeyReach**: `DlMJYGklvEun5I1WMDZO8MzKXkHLk7gLxbLMXsitiVA=`

### Decode them using:
- Online tool: https://www.base64decode.org/
- Command line: `echo "your_encoded_key" | base64 -d`
- Browser console: `atob("your_encoded_key")`

## Step 2: Add Keys to Environment Files

### For Instantly Integration:
1. Open `services/instantly-integration/.env`
2. Find the line: `INSTANTLY_API_KEY=`
3. Replace with: `INSTANTLY_API_KEY=your_decoded_instantly_key`

### For HeyReach Integration:
1. Open `services/heyreach-integration/.env`
2. Find the line: `HEYREACH_API_KEY=`
3. Replace with: `HEYREACH_API_KEY=your_decoded_heyreach_key`

## Step 3: Test Connections

```bash
# Test Instantly
cd services/instantly-integration
node test-connection.js

# Test HeyReach
cd services/heyreach-integration
node test-connection.js
```

## Step 4: Start Services

```bash
# Start Instantly (Terminal 1)
cd services/instantly-integration
npm install
npm run dev

# Start HeyReach (Terminal 2) 
cd services/heyreach-integration
npm install
npm run dev
```

The services will be available at:
- Instantly: http://localhost:3006
- HeyReach: http://localhost:3007