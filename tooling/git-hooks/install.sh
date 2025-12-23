#!/bin/bash
# ============================================================================
# Install Git Hooks for Hub & Spoke Architecture Enforcement
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Installing Hub & Spoke enforcement hooks..."
echo ""

# Install pre-commit hook
if [[ -f "$HOOKS_DIR/pre-commit" ]]; then
    echo "⚠️  Existing pre-commit hook found. Backing up to pre-commit.backup"
    mv "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit.backup"
fi

cp "$SCRIPT_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ Installed: pre-commit (Repo Shape Guard)"

echo ""
echo "🎉 All hooks installed successfully!"
echo ""
echo "The following checks will run on every commit:"
echo "  • No Python files at repo root"
echo "  • Only allowed top-level directories"
echo "  • No large files (>5MB) outside approved locations"
echo ""
