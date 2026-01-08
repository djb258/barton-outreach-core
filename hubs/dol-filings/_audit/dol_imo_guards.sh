#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# DOL IMO Guards — CI Regression Script (v1.2 - EIN Enforcement Gate)
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose: Enforce IMO Doctrine v1.2 boundaries at CI time
# Process: 01.04.02.04.22000 (DOL Sub-Hub)
# Agent: DOL_EIN_SUBHUB
#
# DOCTRINE:
#   The DOL Sub-Hub emits facts only.
#   All failures are DATA DEFICIENCIES, not system failures.
#   Therefore, the DOL Sub-Hub NEVER writes to AIR.
#
#   EIN ENFORCEMENT GATE:
#   For every outreach_context_id:
#     - 0 EINs → FAIL (DOL_EIN_MISSING)
#     - >1 EINs → FAIL (DOL_EIN_AMBIGUOUS)
#     - 1 EIN → PASS
#
# Exit Codes:
#   0 = All guards pass
#   1 = Guard violation detected
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════════════════"
echo "DOL IMO GUARDS — CI Regression Check (v1.2 - EIN Enforcement Gate)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOL_ROOT="$(dirname "$SCRIPT_DIR")"
VIOLATIONS=0

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 1: No CL writes (company_master)
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 1] Checking for CL writes (company.company_master)..."

CL_WRITE_PATTERNS=(
    "UPDATE.*company_master"
    "INSERT.*company_master"
    "DELETE.*company_master"
    "UPDATE.*company\.company_master"
    "INSERT.*company\.company_master"
    "DELETE.*company\.company_master"
)

CL_VIOLATIONS=0
for pattern in "${CL_WRITE_PATTERNS[@]}"; do
    MATCHES=$(grep -rniE "$pattern" "$DOL_ROOT/imo/" --include="*.py" 2>/dev/null || true)
    if [ -n "$MATCHES" ]; then
        echo "  ❌ FAIL: CL write detected!"
        echo "$MATCHES" | while read -r line; do
            echo "     $line"
        done
        CL_VIOLATIONS=$((CL_VIOLATIONS + 1))
    fi
done

if [ $CL_VIOLATIONS -eq 0 ]; then
    echo "  ✅ PASS: No CL writes detected"
else
    VIOLATIONS=$((VIOLATIONS + CL_VIOLATIONS))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 2: No BIT imports or signal emissions
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 2] Checking for BIT integration..."

BIT_PATTERNS=(
    "from.*bit_engine.*import"
    "import.*BITEngine"
    "import.*SignalType"
    "bit_engine\.create_signal"
    "_send_signal"
)

BIT_VIOLATIONS=0
for pattern in "${BIT_PATTERNS[@]}"; do
    MATCHES=$(grep -rniE "$pattern" "$DOL_ROOT/imo/" --include="*.py" 2>/dev/null | grep -v "_audit" || true)
    if [ -n "$MATCHES" ]; then
        echo "  ❌ FAIL: BIT integration detected!"
        echo "$MATCHES" | while read -r line; do
            echo "     $line"
        done
        BIT_VIOLATIONS=$((BIT_VIOLATIONS + 1))
    fi
done

if [ $BIT_VIOLATIONS -eq 0 ]; then
    echo "  ✅ PASS: No BIT integration detected"
else
    VIOLATIONS=$((VIOLATIONS + BIT_VIOLATIONS))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 3: NO AIR LOGGING (HARD KILL)
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 3] Checking for AIR logging (FORBIDDEN)..."

AIR_PATTERNS=(
    "INSERT.*air_log"
    "INSERT.*dol\.air_log"
    "write_air\("
    "write_air_log\("
    "AIR_EVENT"
    "dol\.air_log"
)

AIR_VIOLATIONS=0
for pattern in "${AIR_PATTERNS[@]}"; do
    # Exclude guard files, doctrine_guards.py (which defines the trap), and error_writer.py (which has traps)
    MATCHES=$(grep -rniE "$pattern" "$DOL_ROOT/imo/" --include="*.py" 2>/dev/null | \
              grep -v "doctrine_guards.py" | \
              grep -v "error_writer.py" | \
              grep -v "_audit" | \
              grep -v "# NOTE:" | \
              grep -v "# NO AIR" | \
              grep -v "FORBIDDEN" | \
              grep -v "trap" || true)
    if [ -n "$MATCHES" ]; then
        echo "  ❌ FAIL: AIR logging detected (FORBIDDEN)!"
        echo "$MATCHES" | while read -r line; do
            echo "     $line"
        done
        AIR_VIOLATIONS=$((AIR_VIOLATIONS + 1))
    fi
done

if [ $AIR_VIOLATIONS -eq 0 ]; then
    echo "  ✅ PASS: No AIR logging detected"
else
    VIOLATIONS=$((VIOLATIONS + AIR_VIOLATIONS))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 4: Doctrine guards present
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 4] Checking for doctrine_guards.py..."

if [ -f "$DOL_ROOT/imo/middle/doctrine_guards.py" ]; then
    # Also verify it contains AIR prohibition
    if grep -q "assert_no_air_logging" "$DOL_ROOT/imo/middle/doctrine_guards.py"; then
        echo "  ✅ PASS: doctrine_guards.py exists with AIR prohibition"
    else
        echo "  ⚠️  WARN: doctrine_guards.py exists but missing AIR prohibition"
    fi
else
    echo "  ❌ FAIL: doctrine_guards.py missing!"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 5: Error writer present (error-only)
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 5] Checking for error_writer.py (error-only)..."

if [ -f "$DOL_ROOT/imo/output/error_writer.py" ]; then
    # Verify it contains write_error_master
    if grep -q "write_error_master" "$DOL_ROOT/imo/output/error_writer.py"; then
        # Verify AIR functions are traps
        if grep -q "def write_air.*:.*raise" "$DOL_ROOT/imo/output/error_writer.py" || \
           grep -q "AIR logging is FORBIDDEN" "$DOL_ROOT/imo/output/error_writer.py"; then
            echo "  ✅ PASS: error_writer.py exists with AIR trap"
        else
            echo "  ⚠️  WARN: error_writer.py may not have AIR trap"
        fi
    else
        echo "  ❌ FAIL: error_writer.py missing write_error_master!"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
else
    echo "  ❌ FAIL: error_writer.py missing!"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 6: No marketing schema writes
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 6] Checking for marketing schema writes..."

MARKETING_PATTERNS=(
    "UPDATE.*marketing\."
    "INSERT.*marketing\."
    "DELETE.*marketing\."
)

MARKETING_VIOLATIONS=0
for pattern in "${MARKETING_PATTERNS[@]}"; do
    MATCHES=$(grep -rniE "$pattern" "$DOL_ROOT/imo/" --include="*.py" 2>/dev/null || true)
    if [ -n "$MATCHES" ]; then
        # Check if it's a staging table (allowed) or master table (forbidden)
        if echo "$MATCHES" | grep -qvE "staging"; then
            echo "  ❌ FAIL: Non-staging marketing write detected!"
            echo "$MATCHES" | while read -r line; do
                echo "     $line"
            done
            MARKETING_VIOLATIONS=$((MARKETING_VIOLATIONS + 1))
        fi
    fi
done

if [ $MARKETING_VIOLATIONS -eq 0 ]; then
    echo "  ✅ PASS: No forbidden marketing writes"
else
    VIOLATIONS=$((VIOLATIONS + MARKETING_VIOLATIONS))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 7: Error writes have suppression_key
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 7] Checking for suppression_key in error handling..."

if grep -q "suppression_key" "$DOL_ROOT/imo/output/error_writer.py" 2>/dev/null; then
    echo "  ✅ PASS: suppression_key found in error_writer.py"
else
    echo "  ❌ FAIL: suppression_key missing from error handling!"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 8: EIN Enforcement Gate present
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 8] Checking for EIN Enforcement Gate..."

if [ -f "$DOL_ROOT/imo/middle/dol_enforcement_gate.py" ]; then
    # Verify it contains the enforcement logic
    if grep -q "DOL_EIN_MISSING" "$DOL_ROOT/imo/middle/dol_enforcement_gate.py" && \
       grep -q "DOL_EIN_AMBIGUOUS" "$DOL_ROOT/imo/middle/dol_enforcement_gate.py"; then
        echo "  ✅ PASS: dol_enforcement_gate.py exists with EIN enforcement"
    else
        echo "  ⚠️  WARN: dol_enforcement_gate.py exists but missing error codes"
    fi
else
    echo "  ❌ FAIL: dol_enforcement_gate.py missing!"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GUARD 9: Enforcement Gate has no prohibited patterns
# ═══════════════════════════════════════════════════════════════════════════
echo "[GUARD 9] Checking enforcement gate for prohibited patterns..."

ENFORCEMENT_PATTERNS=(
    "fuzzy_match"
    "enrichment"
    "BITEngine"
    "emit_bit_signal"
)

ENFORCEMENT_VIOLATIONS=0
for pattern in "${ENFORCEMENT_PATTERNS[@]}"; do
    MATCHES=$(grep -rniE "$pattern" "$DOL_ROOT/imo/middle/dol_enforcement_gate.py" 2>/dev/null | \
              grep -v "prohibited_imports" | \
              grep -v "#" || true)
    if [ -n "$MATCHES" ]; then
        echo "  ❌ FAIL: Prohibited pattern '$pattern' in enforcement gate!"
        echo "$MATCHES" | while read -r line; do
            echo "     $line"
        done
        ENFORCEMENT_VIOLATIONS=$((ENFORCEMENT_VIOLATIONS + 1))
    fi
done

if [ $ENFORCEMENT_VIOLATIONS -eq 0 ]; then
    echo "  ✅ PASS: Enforcement gate clean (no fuzzy, no enrichment, no BIT)"
else
    VIOLATIONS=$((VIOLATIONS + ENFORCEMENT_VIOLATIONS))
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════════════════"
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ ALL GUARDS PASS — DOL IMO Doctrine v1.2 Compliant (EIN Enforcement Gate)"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "DOCTRINE STATEMENT:"
    echo "  The DOL Sub-Hub emits facts only."
    echo "  All failures are data deficiencies, not system failures."
    echo "  Therefore, the DOL Sub-Hub NEVER writes to AIR."
    echo ""
    echo "  EIN ENFORCEMENT RULE:"
    echo "    0 EINs  → FAIL (DOL_EIN_MISSING)"
    echo "    >1 EINs → FAIL (DOL_EIN_AMBIGUOUS)"
    echo "    1 EIN   → PASS"
    echo ""
    exit 0
else
    echo "❌ GUARD VIOLATIONS DETECTED: $VIOLATIONS"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "IMO Doctrine v1.2 Boundaries (DOL Sub-Hub - EIN Enforcement):"
    echo "  ✓ MAY read from company.company_master"
    echo "  ✓ MAY write to dol.* tables (append-only facts)"
    echo "  ✓ MAY write to shq.error_master (errors ONLY)"
    echo "  ✗ MAY NOT write to company.company_master"
    echo "  ✗ MAY NOT emit BIT signals"
    echo "  ✗ MAY NOT mint new company identity"
    echo "  ✗ MAY NOT write to AIR (dol.air_log is FORBIDDEN)"
    echo "  ✗ MAY NOT run fuzzy matching in enforcement gate"
    echo "  ✗ MAY NOT trigger enrichment in enforcement gate"
    echo ""
    exit 1
fi
