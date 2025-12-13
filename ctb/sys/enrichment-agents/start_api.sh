#!/bin/bash
# Start Enrichment API for n8n Integration

echo "🚀 Starting Enrichment API..."

# Check if .env exists
if [ ! -f "../../../.env" ]; then
    echo "❌ .env file not found in project root"
    echo "   Please create .env with DATABASE_URL and API keys"
    exit 1
fi

# Load .env
export $(grep -v '^#' ../../../.env | xargs)

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env"
    exit 1
fi

# Check API keys
if [ -z "$APIFY_API_KEY" ] || [ "$APIFY_API_KEY" == "your_apify_api_key_here" ]; then
    echo "⚠️  APIFY_API_KEY not set - Apify agent will be disabled"
fi

if [ -z "$ABACUS_API_KEY" ] || [ "$ABACUS_API_KEY" == "your_abacus_api_key_here" ]; then
    echo "⚠️  ABACUS_API_KEY not set - Abacus agent will be disabled"
fi

if [ -z "$FIRECRAWL_API_KEY" ] || [ "$FIRECRAWL_API_KEY" == "your_firecrawl_api_key_here" ]; then
    echo "⚠️  FIRECRAWL_API_KEY not set - Firecrawl agent will be disabled"
fi

# Set default port
if [ -z "$ENRICHMENT_API_PORT" ]; then
    export ENRICHMENT_API_PORT=8001
fi

echo ""
echo "✅ Configuration loaded"
echo "   API Port: $ENRICHMENT_API_PORT"
echo "   Database: Connected"
echo ""
echo "📖 API Documentation: http://localhost:$ENRICHMENT_API_PORT/docs"
echo "🏥 Health Check: http://localhost:$ENRICHMENT_API_PORT/health"
echo ""

# Start API
python api/enrichment_api.py
