#!/bin/bash
# Auto-generated git hook installer for pre-push
# Run this script to install the Composio-integrated git hook

HOOK_FILE=".git/hooks/pre-push"

echo "Installing pre-push hook with Composio integration..."

cat > "$HOOK_FILE" << 'EOF'
#!/usr/bin/env bash
# HEIR/ORBT trace validation + Composio integration before push

echo "🚀 Running pre-push validation (HEIR/ORBT + Composio)..."

# HEIR/ORBT trace validation
TRACE=$(git log -1 --pretty=%B | sed -n 's/.*BMAD_TRACE_ID=\([^ ]*\).*/\1/p')

# Check if Composio integration is enabled to possibly bypass BMAD requirement
COMPOSIO_BYPASS=false
if [ -f .claude/mcp.json ] && command -v node >/dev/null 2>&1; then
  COMPOSIO_ENABLED=$(node -pe "
    try {
      const config = JSON.parse(require('fs').readFileSync('.claude/mcp.json', 'utf8'));
      config.globalSettings?.gitDefaults?.useComposioForPush || false;
    } catch(e) {
      false;
    }
  " 2>/dev/null)

  if [ "$COMPOSIO_ENABLED" = "true" ]; then
    echo "🤖 Composio push integration enabled"

    # Check for Composio trace ID
    COMPOSIO_TRACE=$(git log -1 --pretty=%B | sed -n 's/.*COMPOSIO_TRACE_ID=\([^ ]*\).*/\1/p')
    if [ -n "$COMPOSIO_TRACE" ]; then
      echo "✅ Composio trace ID found: $COMPOSIO_TRACE"

      # Notify Composio MCP servers about the push
      if [ -f .claude/mcp.json ]; then
        echo "📡 Notifying Composio MCP servers..."

        # Create push notification file
        cat > .git/composio-push-notification.json << EOF
{
  "event": "pre-push",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "composioTraceId": "$COMPOSIO_TRACE",
  "bmadTraceId": "$TRACE",
  "repository": "$(basename $(git config --get remote.origin.url) .git)",
  "lastCommit": {
    "hash": "$(git log -1 --pretty=%H)",
    "message": "$(git log -1 --pretty=%s)",
    "author": "$(git log -1 --pretty='%an <%ae>')"
  },
  "remote": "$(git config --get remote.origin.url)"
}
EOF
        echo "✅ MCP notification prepared"
      fi

      # If Composio trace exists, we can be more lenient with BMAD
      if [ -z "$TRACE" ]; then
        echo "⚠️  No BMAD trace ID found, but Composio integration is active"
        COMPOSIO_BYPASS=true
      fi
    fi
  fi
fi

# BMAD validation with Composio considerations
if [ -z "$TRACE" ] && [ "$COMPOSIO_BYPASS" = "false" ]; then
  echo "[HEIR/ORBT] Missing BMAD_TRACE_ID in last commit body."
  echo "Either add BMAD_TRACE_ID or enable Composio integration"
  exit 1
elif [ -n "$TRACE" ]; then
  echo "✅ BMAD trace ID found: $TRACE"

  # Check for BMAD log file (allow bypass if Composio is enabled)
  if [ ! -f "logs/bmad/${TRACE}.json" ]; then
    if [ "$COMPOSIO_BYPASS" = "true" ]; then
      echo "⚠️  No BMAD log for TRACE $TRACE, but Composio integration allows bypass"
    else
      echo "[HEIR/ORBT] No BMAD log for TRACE $TRACE (run make bmad-bench)."
      exit 1
    fi
  else
    echo "✅ BMAD log file verified"
  fi
fi

echo "✅ Pre-push validation completed - ready to push!"
exit 0
EOF

chmod +x "$HOOK_FILE"

echo "✅ pre-push hook installed successfully"
echo "This hook includes both HEIR/ORBT validation and Composio integration"
