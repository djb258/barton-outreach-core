#!/bin/bash
# Apify Actor Discovery Script
# Discovers all Apify actors and generates comprehensive inventory report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

echo "🚀 Starting Apify Actor Discovery"
echo "═══════════════════════════════════════════════════════════════════════"

# Load environment variables
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found, using defaults"
fi

# Check if APIFY_API_KEY is set
if [ -z "$APIFY_API_KEY" ]; then
    echo "❌ ERROR: APIFY_API_KEY not set in environment"
    echo "   Please set it in .env file or export it"
    exit 1
fi

echo "🔑 API Key found (${APIFY_API_KEY:0:10}...)"
echo ""

# Array of known/common Apify actors to check
KNOWN_ACTORS=(
    "apify/email-phone-scraper"
    "apify/linkedin-profile-scraper"
    "apify/website-content-crawler"
    "apify/linkedin-company-scraper"
    "apify/google-search-scraper"
    "apify/contact-finder"
    "apify/people-data-scraper"
    "apify/web-scraper"
    "compass/apollo-scraper"
    "compass/linkedin-people-scraper"
)

# Create output file
DISCOVERY_OUTPUT="$OUTPUT_DIR/apify_actors_discovered.json"
echo "{" > "$DISCOVERY_OUTPUT"
echo '  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$DISCOVERY_OUTPUT"
echo '  "process_id": "Apify Actor Discovery",' >> "$DISCOVERY_OUTPUT"
echo '  "unique_id": "04.01.99.11.05000.001",' >> "$DISCOVERY_OUTPUT"
echo '  "actors": [' >> "$DISCOVERY_OUTPUT"

ACTOR_COUNT=0
FIRST_ACTOR=true

echo "📋 Discovering Apify actors..."
echo ""

for ACTOR_ID in "${KNOWN_ACTORS[@]}"; do
    echo "  📥 Fetching: $ACTOR_ID"

    # Fetch actor details from Apify API
    RESPONSE=$(curl -s "https://api.apify.com/v2/acts/${ACTOR_ID}?token=${APIFY_API_KEY}")

    # Check if request was successful
    if echo "$RESPONSE" | grep -q '"data"'; then
        echo "     ✅ Found"

        # Add comma if not first actor
        if [ "$FIRST_ACTOR" = false ]; then
            echo "    ," >> "$DISCOVERY_OUTPUT"
        fi
        FIRST_ACTOR=false

        # Extract key information
        TITLE=$(echo "$RESPONSE" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
        DESCRIPTION=$(echo "$RESPONSE" | grep -o '"description":"[^"]*"' | head -1 | cut -d'"' -f4)
        IS_PUBLIC=$(echo "$RESPONSE" | grep -o '"isPublic":[^,}]*' | head -1 | cut -d':' -f2)

        echo "     📝 Title: $TITLE"

        # Write to JSON file
        echo "    {" >> "$DISCOVERY_OUTPUT"
        echo "      \"actorId\": \"$ACTOR_ID\"," >> "$DISCOVERY_OUTPUT"
        echo "      \"title\": \"$TITLE\"," >> "$DISCOVERY_OUTPUT"
        echo "      \"description\": \"$DESCRIPTION\"," >> "$DISCOVERY_OUTPUT"
        echo "      \"isPublic\": $IS_PUBLIC," >> "$DISCOVERY_OUTPUT"
        echo "      \"fullData\": $RESPONSE" >> "$DISCOVERY_OUTPUT"
        echo -n "    }" >> "$DISCOVERY_OUTPUT"

        ((ACTOR_COUNT++))
    else
        echo "     ⚠️  Not found or not accessible"
    fi
    echo ""
done

# Close JSON
echo "" >> "$DISCOVERY_OUTPUT"
echo "  ]," >> "$DISCOVERY_OUTPUT"
echo '  "totalDiscovered": '$ACTOR_COUNT',' >> "$DISCOVERY_OUTPUT"
echo '  "currentlyUsedActors": [' >> "$DISCOVERY_OUTPUT"
echo '    {' >> "$DISCOVERY_OUTPUT"
echo '      "actorId": "apify/email-phone-scraper",' >> "$DISCOVERY_OUTPUT"
echo '      "usage": "Primary contact scraper in apifyRunner.js",' >> "$DISCOVERY_OUTPUT"
echo '      "location": "agents/specialists/apifyRunner.js:18"' >> "$DISCOVERY_OUTPUT"
echo '    },' >> "$DISCOVERY_OUTPUT"
echo '    {' >> "$DISCOVERY_OUTPUT"
echo '      "actorId": "apify~linkedin-profile-scraper",' >> "$DISCOVERY_OUTPUT"
echo '      "usage": "LinkedIn profile scraping",' >> "$DISCOVERY_OUTPUT"
echo '      "location": "packages/mcp-clients/src/clients/apify-mcp-client.ts:57"' >> "$DISCOVERY_OUTPUT"
echo '    },' >> "$DISCOVERY_OUTPUT"
echo '    {' >> "$DISCOVERY_OUTPUT"
echo '      "actorId": "apify~website-content-crawler",' >> "$DISCOVERY_OUTPUT"
echo '      "usage": "Website contact extraction",' >> "$DISCOVERY_OUTPUT"
echo '      "location": "packages/mcp-clients/src/clients/apify-mcp-client.ts:118"' >> "$DISCOVERY_OUTPUT"
echo '    }' >> "$DISCOVERY_OUTPUT"
echo '  ]' >> "$DISCOVERY_OUTPUT"
echo "}" >> "$DISCOVERY_OUTPUT"

echo "═══════════════════════════════════════════════════════════════════════"
echo "📊 DISCOVERY SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════"
echo "✅ Actors Discovered: $ACTOR_COUNT"
echo "📁 Results saved to: $DISCOVERY_OUTPUT"
echo ""
echo "Next step: Run the analysis script to generate the full inventory report"
echo "═══════════════════════════════════════════════════════════════════════"
