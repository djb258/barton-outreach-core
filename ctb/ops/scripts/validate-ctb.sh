#!/bin/bash
# CTB Compliance Validation Script
# Validates repository structure against CTB Doctrine v1.3.3

set -e

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🔍 CTB COMPLIANCE VALIDATION"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Track validation status
VALIDATION_PASSED=0
WARNINGS=0

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check all 7 CTB branches exist
echo "📁 Checking CTB Branch Structure..."
echo "─────────────────────────────────────────────────────────"

BRANCHES=("sys" "ai" "data" "docs" "ui" "meta" "ops")
MISSING_BRANCHES=0

for branch in "${BRANCHES[@]}"; do
  if [ ! -d "ctb/$branch" ]; then
    echo -e "${RED}❌ Missing: ctb/$branch/${NC}"
    MISSING_BRANCHES=$((MISSING_BRANCHES + 1))
    VALIDATION_PASSED=1
  else
    echo -e "${GREEN}✅ Found: ctb/$branch/${NC}"
  fi
done

if [ $MISSING_BRANCHES -eq 0 ]; then
  echo -e "${GREEN}✅ All 7 CTB branches present!${NC}"
else
  echo -e "${RED}❌ Missing $MISSING_BRANCHES CTB branches${NC}"
fi

echo ""

# Check root directory item count
echo "📊 Checking Root Directory Organization..."
echo "─────────────────────────────────────────────────────────"

# Count only non-hidden items (excluding .git, .gitignore, etc.)
ROOT_ITEMS=$(ls | wc -l)
echo "Root items (visible): $ROOT_ITEMS"

if [ $ROOT_ITEMS -gt 25 ]; then
  echo -e "${YELLOW}⚠️  Warning: Root has $ROOT_ITEMS visible items (expected ~15-20)${NC}"
  WARNINGS=$((WARNINGS + 1))
elif [ $ROOT_ITEMS -le 20 ]; then
  echo -e "${GREEN}✅ Root directory is clean (≤20 items)${NC}"
else
  echo -e "${GREEN}✅ Root directory is acceptable ($ROOT_ITEMS items)${NC}"
fi

echo ""

# Check .gitignore completeness
echo "🔒 Checking .gitignore Completeness..."
echo "─────────────────────────────────────────────────────────"

GITIGNORE_CHECKS=(
  "apps/:Build artifacts ignored"
  ".claude/:IDE settings ignored"
  ".env:Environment files ignored"
  "node_modules/:Dependencies ignored"
  "dist/:Build output ignored"
  "*.pyc:Python cache ignored"
  ".pytest_cache/:Test cache ignored"
)

for check in "${GITIGNORE_CHECKS[@]}"; do
  PATTERN="${check%%:*}"
  DESCRIPTION="${check##*:}"

  if grep -q "$PATTERN" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ $DESCRIPTION ($PATTERN)${NC}"
  else
    echo -e "${YELLOW}⚠️  Missing: $DESCRIPTION ($PATTERN)${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
done

echo ""

# Check essential root files exist
echo "📄 Checking Essential Root Files..."
echo "─────────────────────────────────────────────────────────"

ESSENTIAL_FILES=(
  "CLAUDE.md:Bootstrap guide"
  "README.md:Repository documentation"
  "LICENSE:Legal license"
  ".gitignore:Git ignore rules"
  "requirements.txt:Python dependencies"
)

for file_check in "${ESSENTIAL_FILES[@]}"; do
  FILE="${file_check%%:*}"
  DESCRIPTION="${file_check##*:}"

  if [ -f "$FILE" ]; then
    echo -e "${GREEN}✅ $DESCRIPTION ($FILE)${NC}"
  else
    echo -e "${RED}❌ Missing: $DESCRIPTION ($FILE)${NC}"
    VALIDATION_PASSED=1
  fi
done

echo ""

# Check for common anti-patterns
echo "🚫 Checking for Anti-Patterns..."
echo "─────────────────────────────────────────────────────────"

# Check if there are Python files at root (should be in ctb/)
ROOT_PY_FILES=$(find . -maxdepth 1 -name "*.py" ! -name "start_server.py" 2>/dev/null | wc -l)
if [ $ROOT_PY_FILES -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Warning: Found $ROOT_PY_FILES Python files at root (should be in ctb/)${NC}"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}✅ No stray Python files at root${NC}"
fi

# Check if there are loose documentation files at root
ROOT_MD_FILES=$(find . -maxdepth 1 -name "*.md" ! -name "README.md" ! -name "CLAUDE.md" ! -name "LICENSE.md" ! -name "CTB*.md" ! -name "RECOMMENDED*.md" 2>/dev/null | wc -l)
if [ $ROOT_MD_FILES -gt 3 ]; then
  echo -e "${YELLOW}⚠️  Warning: Found $ROOT_MD_FILES extra Markdown files at root (should be in ctb/docs/)${NC}"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}✅ Documentation is organized${NC}"
fi

echo ""

# Check CTB documentation exists
echo "📚 Checking CTB Documentation..."
echo "─────────────────────────────────────────────────────────"

CTB_DOCS=(
  "ctb/README.md:CTB navigation guide"
  "CTB_FINAL_ACHIEVEMENT_REPORT.md:Achievement report"
)

for doc_check in "${CTB_DOCS[@]}"; do
  DOC="${doc_check%%:*}"
  DESCRIPTION="${doc_check##*:}"

  if [ -f "$DOC" ]; then
    echo -e "${GREEN}✅ $DESCRIPTION present${NC}"
  else
    echo -e "${YELLOW}⚠️  Missing: $DESCRIPTION ($DOC)${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
done

echo ""

# Final summary
echo "═══════════════════════════════════════════════════════════"
echo "  📊 VALIDATION SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $VALIDATION_PASSED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}🎉 Perfect CTB Compliance!${NC}"
  echo -e "${GREEN}✅ All checks passed${NC}"
  echo -e "${GREEN}✅ Zero warnings${NC}"
  echo ""
  echo "Status: 100% CTB Compliant ✅"
  exit 0
elif [ $VALIDATION_PASSED -eq 0 ]; then
  echo -e "${YELLOW}⚠️  CTB Compliance with Warnings${NC}"
  echo -e "${GREEN}✅ All critical checks passed${NC}"
  echo -e "${YELLOW}⚠️  $WARNINGS warnings found${NC}"
  echo ""
  echo "Status: Compliant with minor issues ⚠️"
  exit 0
else
  echo -e "${RED}❌ CTB Compliance Issues Detected${NC}"
  echo -e "${RED}❌ Critical issues found${NC}"
  if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings found${NC}"
  fi
  echo ""
  echo "Status: Non-compliant ❌"
  exit 1
fi
