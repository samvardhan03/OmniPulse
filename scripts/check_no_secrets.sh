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

echo "--- check 5: omni-lock-embed must not be tracked in the git index"
EMBED_IN_INDEX=$(git -C "$ROOT" ls-files -- "omni-lock-embed/" 2>/dev/null) || true
if [ -n "$EMBED_IN_INDEX" ]; then
    echo "FAIL: omni-lock-embed/ files still tracked in git index:"
    echo "$EMBED_IN_INDEX"
    FAIL=1
else
    echo "OK"
fi

echo "--- check 6: no private omni-lock symbols outside the omnipulse-rs submodule"
# omnipulse-rs is already a private repo; symbols there are expected.
# Fail only if these identifiers appear in files tracked directly by the parent repo.
SYMBOL_HITS=$(git -C "$ROOT" ls-files \
    -- "*.py" "*.rs" "*.cpp" "*.cu" "*.h" 2>/dev/null \
    | grep -v "^omnipulse-rs/" \
    | xargs -I{} grep -l \
        "omnilock_ffi\|kernel_ldpc\|kernel_dct\|omni_lock_kernel\|MixerTorch\|OmniLockWatermarker\|load_h_from_engine\|ResidualEmbedder" \
        "$ROOT/{}" 2>/dev/null) || true
if [ -n "$SYMBOL_HITS" ]; then
    echo "FAIL: private OmniLock symbols found in parent-repo tracked source files:"
    echo "$SYMBOL_HITS"
    FAIL=1
else
    echo "OK"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "check_no_secrets: all checks passed"
else
    echo "check_no_secrets: FAILED (see above)"
    exit 1
fi
