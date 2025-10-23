#!/bin/bash
# Setup CTB Enforcement Git Hooks
# Run this once after cloning the repository to enable automatic CTB validation

set -e

echo "🔧 Setting up CTB enforcement git hooks..."

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Path to hooks directory
HOOKS_DIR="$REPO_ROOT/.githooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Check if .githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ ERROR: .githooks directory not found"
    exit 1
fi

# Make hook scripts executable
echo "Making hook scripts executable..."
chmod +x "$HOOKS_DIR/pre-commit" 2>/dev/null || true

# Configure git to use .githooks directory
echo "Configuring git to use .githooks directory..."
git config core.hooksPath "$HOOKS_DIR"

echo ""
echo "✅ CTB enforcement hooks installed successfully!"
echo ""
echo "What happens now:"
echo "  • Every commit will auto-tag new files"
echo "  • CTB compliance will be checked automatically"
echo "  • Commits will be blocked if compliance < 70/100"
echo ""
echo "To bypass hook (NOT RECOMMENDED):"
echo "  git commit --no-verify"
echo ""
echo "To uninstall hooks:"
echo "  git config --unset core.hooksPath"
echo ""
