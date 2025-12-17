# Environment Configuration Guide

This guide will help you set up all required environment variables for the enricha-vision application.

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in the required values in `.env` (see sections below)

3. Never commit `.env` to version control (it's in `.gitignore`)

## Required Environment Variables

### Database Configuration

#### Neon PostgreSQL
```bash
DATABASE_URL="postgresql://user:password@host/database?sslmode=require"
```

**How to get:**
1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string from the dashboard

### Firebase Configuration

```bash
FIREBASE_API_KEY="your-api-key"
FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
FIREBASE_PROJECT_ID="your-project-id"
FIREBASE_STORAGE_BUCKET="your-project.appspot.com"
FIREBASE_MESSAGING_SENDER_ID="your-sender-id"
FIREBASE_APP_ID="your-app-id"
```

**How to get:**
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project or select existing
3. Go to Project Settings → General
4. Scroll to "Your apps" section
5. Click "Web app" and register your app
6. Copy the config values

### AI Provider Configuration

#### Gemini (Primary Provider)
```bash
GEMINI_API_KEY="your-gemini-api-key"
```

**How to get:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

#### OpenAI (Fallback Provider)
```bash
OPENAI_API_KEY="sk-your-openai-key"
```

**How to get:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key

### Integration Services

#### Composio MCP
```bash
COMPOSIO_API_KEY="your-composio-key"
COMPOSIO_USER_ID="your-user-id"
```

**How to get:**
1. Sign up at [Composio](https://composio.dev)
2. Get your API key from the dashboard
3. Copy your user ID

#### GitHub Integration
```bash
GITHUB_TOKEN="ghp_your-token-here"
GITHUB_OWNER="your-username-or-org"
GITHUB_REPO="your-repo-name"
```

**How to get:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `workflow`, `read:org`
4. Copy the token

### Supabase Configuration (Optional)

If you're using Supabase alongside Firebase:

```bash
VITE_SUPABASE_PROJECT_ID="your-project-id"
VITE_SUPABASE_PUBLISHABLE_KEY="your-anon-key"
VITE_SUPABASE_URL="https://your-project.supabase.co"
```

## Environment-Specific Configuration

### Development
```bash
NODE_ENV="development"
```

### Production
```bash
NODE_ENV="production"
```

### Testing
```bash
NODE_ENV="test"
```

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use different keys for dev/prod** - Keep environments separate
3. **Rotate keys regularly** - Update credentials periodically
4. **Limit key permissions** - Only grant necessary scopes
5. **Use secret management** - Consider using secret managers in production

## Verification

After setting up your environment variables, verify the configuration:

```bash
npm run dev
```

Check the console for any missing environment variable warnings.

## Troubleshooting

### Missing Environment Variables
If you see errors about missing environment variables:
1. Check that `.env` file exists
2. Verify all required variables are set
3. Restart the development server

### Invalid Credentials
If authentication fails:
1. Verify API keys are correct
2. Check that keys haven't expired
3. Ensure proper permissions/scopes are set

### Connection Issues
If database or service connections fail:
1. Check network connectivity
2. Verify URLs and endpoints
3. Check firewall settings
4. Ensure services are running

## Support

For additional help:
- Check the [documentation](./ctb/docs/)
- Review [troubleshooting guide](./ctb/docs/guides/README.md)
- Open an issue on GitHub
