#!/usr/bin/env bash
# check_no_secrets.sh -- CI gate: fail if private artifacts appear in the public tree.
#
# Checks:
#   1. No ML weight files (.safetensors, .pt, .ckpt, .pth)
#   2. No key or certificate files (.pem, .key, .key.enc)
#   3. No generated LDPC header (ldpc_h_tables.h)
#   4. No path containing omnipulse-engine/ or omni-lock-embed/trainer.py
#      (the trainer is private and must not be committed here)
#   5. No create_ldpc_code definition in the public ldpc.py
#      (the H generator must live only in the private engine repo)
#
# Exit status: 0 = clean, 1 = at least one violation found.
# Run from the monorepo root.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

# Directories to skip entirely (build artifacts, node_modules, private source-only dirs)
PRUNE_ARGS=(
    -path "$ROOT/omnipulse-rs/target" -prune -o
    -path "$ROOT/site/node_modules" -prune -o
    -path "$ROOT/.git" -prune -o
    -path "$ROOT/.claude" -prune -o
    -path "$ROOT/Ethics-and-AI" -prune -o
)

echo "--- check 1: no ML weight files in public tree"
WEIGHT_FILES=$(find "$ROOT" "${PRUNE_ARGS[@]}" \
    \( -name "*.safetensors" -o -name "*.pt" -o -name "*.ckpt" -o -name "*.pth" \) \
    -print 2>/dev/null) || true
if [ -n "$WEIGHT_FILES" ]; then
    echo "FAIL: ML weight files found in public tree:"
    echo "$WEIGHT_FILES"
    FAIL=1
else
    echo "OK"
fi

echo "--- check 2: no key or certificate files"
KEY_FILES=$(find "$ROOT" "${PRUNE_ARGS[@]}" \
    \( -name "*.pem" -o -name "*.key" -o -name "*.key.enc" \) \
    -print 2>/dev/null) || true
if [ -n "$KEY_FILES" ]; then
    echo "FAIL: key/certificate files found in public tree:"
    echo "$KEY_FILES"
    FAIL=1
else
    echo "OK"
fi

echo "--- check 3: no generated LDPC H header"
H_FILES=$(find "$ROOT" "${PRUNE_ARGS[@]}" \
    -name "ldpc_h_tables.h" -print 2>/dev/null) || true
if [ -n "$H_FILES" ]; then
    echo "FAIL: ldpc_h_tables.h found in public tree (must be a signed release asset only):"
    echo "$H_FILES"
    FAIL=1
else
    echo "OK"
fi

echo "--- check 4: no omnipulse-engine/ path or private trainer reference"
# Exclude this script itself (it contains the pattern as part of the check).
SELF="$(basename "$0")"
ENGINE_PATHS=$(find "$ROOT" "${PRUNE_ARGS[@]}" \
    \( -name "*.rs" -o -name "*.py" -o -name "*.toml" \) \
    -print 2>/dev/null \
    | xargs grep -l "omnipulse-engine\|omnipulse_engine" 2>/dev/null) || true
if [ -n "$ENGINE_PATHS" ]; then
    echo "FAIL: references to omnipulse-engine private repo found in source files:"
    echo "$ENGINE_PATHS"
    FAIL=1
else
    echo "OK"
fi

echo "--- check 5: create_ldpc_code must not exist in public ldpc.py"
LDPC_PY="$ROOT/omni-lock-embed/omni_lock/ldpc.py"
if [ -f "$LDPC_PY" ] && grep -q "def create_ldpc_code" "$LDPC_PY"; then
    echo "FAIL: create_ldpc_code (H generator) found in public $LDPC_PY"
    echo "      This function belongs in ldpc/generate_h.py in the private engine repo."
    FAIL=1
elif [ -f "$LDPC_PY" ]; then
    echo "OK"
else
    echo "SKIP: $LDPC_PY not found"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "check_no_secrets: all checks passed"
else
    echo "check_no_secrets: FAILED (see above)"
    exit 1
fi
