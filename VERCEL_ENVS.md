# Vercel Environment Variables

These environment variables must be configured in the Vercel dashboard for production deployment.

## Database Configuration
- `DATABASE_URL`: Neon PostgreSQL connection string
- `NEON_DATABASE_URL`: Alternative Neon database connection string

## MCP Server Configuration
- `COMPOSIO_API_KEY`: Composio.dev API key for MCP orchestration
- `APIFY_TOKEN`: Apify API token for web scraping workflows
- `MILLIONVERIFIER_API_KEY`: MillionVerifier API key for email verification

## LLM Provider Configuration
- `ANTHROPIC_API_KEY`: Anthropic Claude API key (sk-ant-xxx)
- `OPENAI_API_KEY`: OpenAI API key (sk-xxx)

## HEIR Doctrine Configuration
- `DOCTRINE_DB`: Database identifier (default: shq)
- `DOCTRINE_SUBHIVE`: Subhive identifier (default: 03)
- `DOCTRINE_APP`: Application identifier (default: imo)
- `DOCTRINE_VER`: Version identifier (default: 1)

## Garage MCP Configuration
- `GARAGE_MCP_URL`: Garage MCP server base URL
- `GARAGE_MCP_TOKEN`: Authentication token for Garage MCP

## Application Configuration
- `NODE_ENV`: Set to "production"

## UI Builder Configuration
- `VITE_BUILDER_IO_KEY`: Builder.io API key for visual page building
- `VITE_PLASMIC_PROJECT_ID`: Plasmic project ID for design system integration
- `VITE_PLASMIC_PROJECT_TOKEN`: Plasmic project token for API access
- `FIGMA_ACCESS_TOKEN`: Figma API token for design system sync
- `LOVEABLE_API_KEY`: Loveable.dev API key for AI-generated components

## How to Set Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Navigate to Settings > Environment Variables
3. Add each variable with its corresponding value
4. Ensure they are available for Production environment
5. Redeploy your application after adding variables

## UI Builder Setup

### Builder.io
1. Create account at [builder.io](https://builder.io)
2. Create a new space/project
3. Copy the API key from Settings > API Keys
4. Add as `VITE_BUILDER_IO_KEY` in Vercel

### Plasmic
1. Create account at [plasmic.app](https://plasmic.app)
2. Create a new project
3. Go to Settings > API to get Project ID and Token
4. Add as `VITE_PLASMIC_PROJECT_ID` and `VITE_PLASMIC_PROJECT_TOKEN`

### Figma
1. Generate a Personal Access Token in Figma Account Settings
2. Add as `FIGMA_ACCESS_TOKEN` in Vercel
3. Note: This enables design system sync via Composio MCP

### Loveable.dev
1. Create account at [loveable.dev](https://loveable.dev)
2. Generate API key from dashboard
3. Add as `LOVEABLE_API_KEY` in Vercel

## Security Notes

- Never commit these values to your repository
- Use Vercel's encrypted environment variable storage
- Rotate API keys regularly
- Monitor usage and set appropriate rate limits
- UI builder integrations are orchestrated through Composio MCP for enhanced security