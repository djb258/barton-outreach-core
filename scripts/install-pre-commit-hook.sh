#!/bin/bash
# Auto-generated git hook installer for pre-commit
# Run this script to install the Composio-integrated git hook

HOOK_FILE=".git/hooks/pre-commit"

echo "Installing pre-commit hook with Composio integration..."

cat > "$HOOK_FILE" << 'EOF'
#!/usr/bin/env bash
# HEIR/ORBT atomic fix enforcement + Composio integration

echo "🔍 Running pre-commit validation (HEIR/ORBT + Composio)..."

# HEIR/ORBT atomic fix enforcement
if [[ "${BMAD_ALLOW_MULTI:-0}" == "1" ]]; then
  echo "✅ BMAD_ALLOW_MULTI=1, bypassing atomic fix limit"
else
  CHANGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
  if [[ "$CHANGED" -gt 3 ]]; then
    echo "[HEIR/ORBT] Too many files in one fix ($CHANGED). Atomic fixes only."
    echo "Set BMAD_ALLOW_MULTI=1 to override."
    exit 1
  fi
  echo "✅ Atomic fix limit satisfied ($CHANGED files)"
fi

# Composio integration checks
if [ -f .claude/mcp.json ]; then
  echo "🤖 Composio integration detected"

  # Check if Node.js is available for config parsing
  if command -v node >/dev/null 2>&1; then
    COMPOSIO_ENABLED=$(node -pe "
      try {
        const config = JSON.parse(require('fs').readFileSync('.claude/mcp.json', 'utf8'));
        config.globalSettings?.gitDefaults?.useComposioForCommits || false;
      } catch(e) {
        false;
      }
    " 2>/dev/null)

    if [ "$COMPOSIO_ENABLED" = "true" ]; then
      echo "✅ Composio git integration enabled"

      # Generate Composio trace ID (in addition to BMAD trace ID)
      COMPOSIO_TRACE_ID="COMP-$(date +%s)-$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 6 2>/dev/null || echo "RAND")"
      export COMPOSIO_TRACE_ID
      echo "🆔 Generated Composio trace ID: $COMPOSIO_TRACE_ID"

      # Store for commit message enhancement
      echo "$COMPOSIO_TRACE_ID" > .git/COMPOSIO_TRACE_ID
    fi
  fi
fi

# Check for sensitive information
echo "🔒 Scanning for sensitive information..."
if git diff --cached --name-only | xargs grep -l "api.*key\|secret\|password\|token" 2>/dev/null | head -1; then
  echo "⚠️  Warning: Potential sensitive information detected in staged files"
  echo "Please review your changes before committing"
fi

echo "✅ Pre-commit validation completed"
exit 0
EOF

chmod +x "$HOOK_FILE"

echo "✅ pre-commit hook installed successfully"
echo "This hook includes both HEIR/ORBT validation and Composio integration"
