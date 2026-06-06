#!/usr/bin/env bash
# check-boundaries.sh — enforce the Control/Data-Plane seam contracts.
#
# Run from the monorepo root:
#   bash Vikshep/scripts/check-boundaries.sh
#
# Exit 1 on any violation; prints "boundaries OK" on clean pass.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

FAIL=0

# ---------------------------------------------------------------------------
# 1. No raw tensor arrays in any *Input MCP schema.
#    z.array(z.number().int()) is allowed (shape metadata — integer counts).
#    z.array(z.number())       is forbidden (float32 tensor payload).
# ---------------------------------------------------------------------------
echo "[check] 1. No tensor arrays in *Input MCP schemas…"
TENSOR_HITS=$(
  grep -RnE 'z\.array\(z\.number\(\)\)' \
       Vikshep/agent/src Vikshep/contract 2>/dev/null \
    | grep -iE 'Input' \
    | grep -v '\.int()' \
  || true
)
if [ -n "$TENSOR_HITS" ]; then
  echo "FAIL: tensor array found in MCP input schema:"
  echo "$TENSOR_HITS"
  FAIL=1
else
  echo "  PASS"
fi

# ---------------------------------------------------------------------------
# 2a. No 40-hex OID relics anywhere in the created trees.
# ---------------------------------------------------------------------------
echo "[check] 2a. No 40-hex OID relics…"
HEX40_HITS=$(
  grep -RnE '\[0-9a-f\]\{40\}' Vikshep dataplane-contrib 2>/dev/null || true
)
if [ -n "$HEX40_HITS" ]; then
  echo "FAIL: 40-hex ID found:"
  echo "$HEX40_HITS"
  FAIL=1
else
  echo "  PASS"
fi

# ---------------------------------------------------------------------------
# 2b. 28-hex regex present in the canonical OID contract file.
# ---------------------------------------------------------------------------
echo "[check] 2b. 28-hex regex in Vikshep/contract/objectId.ts…"
if grep -qE '\[0-9a-f\]\{28\}' Vikshep/contract/objectId.ts 2>/dev/null; then
  echo "  PASS"
else
  echo "FAIL: 28-hex regex missing from Vikshep/contract/objectId.ts"
  FAIL=1
fi

# ---------------------------------------------------------------------------
# 3. Audit 'as u64' in FOLDER 2 — only the shm host pointer may cross FFI.
#    This is a WARN, not a FAIL; each hit should be the pattern 'as_ptr() as u64'.
# ---------------------------------------------------------------------------
echo "[check] 3. Auditing 'as u64' in dataplane-contrib/omnipulse-rs…"
U64_HITS=$(
  grep -RnE 'as u64' dataplane-contrib/omnipulse-rs 2>/dev/null \
    | grep -v 'as_ptr() as u64' \
    | grep -v 'as_millis() as u64' \
    | grep -v 'coeff_count as u64' \
  || true
)
if [ -n "$U64_HITS" ]; then
  echo "  WARN: audit each 'as u64' — only the shm pointer may cross FFI:"
  echo "$U64_HITS"
else
  echo "  PASS (no unexpected 'as u64' casts)"
fi

# ---------------------------------------------------------------------------
# 4. No AI attribution in any file created by this plan.
#    Regex requires a model/tool name adjacent to attribution language.
#    Excludes: *.lock, LICENSE, *.md (the plan itself is not in these trees).
# ---------------------------------------------------------------------------
echo "[check] 4. No AI attribution in Vikshep/ or dataplane-contrib/…"
ATTR_HITS=$(
  grep -RniE \
       'co-?authored.*(claude|anthropic|gpt|openai|llm)|generated (with|by).*(claude|anthropic|gpt|openai|llm)|written (with|by).*(claude|ai\b|anthropic)' \
       --exclude="*.lock" \
       --exclude="*.map" \
       --exclude="LICENSE" \
       --exclude="*.bak" \
       --exclude-dir=node_modules \
       --exclude-dir=dist \
       --exclude-dir=.venv \
       --exclude-dir=__pycache__ \
       --exclude-dir=target \
       Vikshep dataplane-contrib 2>/dev/null \
  || true
)
if [ -n "$ATTR_HITS" ]; then
  echo "FAIL: AI-attribution text present:"
  echo "$ATTR_HITS"
  FAIL=1
else
  echo "  PASS"
fi

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "boundaries OK"
else
  echo "boundaries FAILED — see above"
  exit 1
fi
