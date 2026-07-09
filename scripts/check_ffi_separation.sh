#!/usr/bin/env bash
# check_ffi_separation.sh — CI lint for FFI family separation.
#
# Enforces three invariants from merger_spec.md Phase 1 and CLAUDE.md rule 1:
#   1. omni-lock-core must not depend on cxx, bindgen, or cc at runtime.
#   2. omni-ffi must not reference any OmniLock symbols.
#   3. omni-wst-core and omni-lock-core must not cross-import each other.
#
# Exit status: 0 = all clean, 1 = at least one violation found.
# Run from the monorepo root (~/Desktop/omnipulse/).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

# ── 1. omni-lock-core/Cargo.toml must not mention cxx, bindgen, or cc
#       in [dependencies] (runtime).  Build-deps are a separate table and
#       are not checked here; the cmake-based build.rs needs no cc crate anyway.
echo "--- check 1: omni-lock-core runtime deps must not include cxx|bindgen|cc"
CARGO_TOML="$ROOT/omnipulse-rs/crates/omni-lock-core/Cargo.toml"
if ! [ -f "$CARGO_TOML" ]; then
    echo "FAIL: $CARGO_TOML not found"
    FAIL=1
else
    # Extract only the [dependencies] block (stop at next [section])
    DEPS_BLOCK=$(awk '/^\[dependencies\]/{found=1; next} found && /^\[/{exit} found{print}' "$CARGO_TOML")
    if echo "$DEPS_BLOCK" | grep -qE '^\s*(cxx|bindgen|cc)\s*='; then
        echo "FAIL: forbidden runtime dep (cxx|bindgen|cc) found in [dependencies]"
        grep -nE '^\s*(cxx|bindgen|cc)\s*=' "$CARGO_TOML" || true
        FAIL=1
    else
        echo "OK"
    fi
fi

# ── 2. omni-ffi must not reference OmniLock symbols
echo "--- check 2: omni-ffi must not reference omnilock symbols"
OMNI_FFI_DIR="$ROOT/omni-ffi"
if ! [ -d "$OMNI_FFI_DIR" ]; then
    echo "SKIP: $OMNI_FFI_DIR not found (submodule not initialised)"
else
    if grep -r --include="*.rs" --include="*.cpp" --include="*.cu" --include="*.h" \
              -l "omnilock\|OmniLock\|omni_lock" "$OMNI_FFI_DIR" 2>/dev/null | grep -q .; then
        echo "FAIL: omni-ffi references omnilock symbols"
        grep -r --include="*.rs" --include="*.cpp" --include="*.cu" --include="*.h" \
                -l "omnilock\|OmniLock\|omni_lock" "$OMNI_FFI_DIR" || true
        FAIL=1
    else
        echo "OK"
    fi
fi

# ── 3. omni-wst-core and omni-lock-core must not cross-import each other
echo "--- check 3: omni-wst-core and omni-lock-core must not cross-import"
WST_DIR="$ROOT/omni-wst-core"
LOCK_DIR="$ROOT/omnipulse-rs/crates/omni-lock-core"

WST_REFS_LOCK=0
LOCK_REFS_WST=0

if [ -d "$WST_DIR" ]; then
    if grep -r --include="*.rs" --include="*.toml" -l "omni.lock.core\|omni_lock_core\|omnilock" \
              "$WST_DIR" 2>/dev/null | grep -q .; then
        WST_REFS_LOCK=1
    fi
fi

if [ -d "$LOCK_DIR" ]; then
    if grep -r --include="*.rs" --include="*.toml" -l "omni.wst.core\|omni_wst_core\|omni_ffi\b" \
              "$LOCK_DIR" 2>/dev/null | grep -q .; then
        LOCK_REFS_WST=1
    fi
fi

if [ "$WST_REFS_LOCK" -eq 1 ] || [ "$LOCK_REFS_WST" -eq 1 ]; then
    echo "FAIL: cross-import detected"
    [ "$WST_REFS_LOCK" -eq 1 ] && \
        grep -r --include="*.rs" --include="*.toml" -l "omni.lock.core\|omni_lock_core\|omnilock" \
                "$WST_DIR" || true
    [ "$LOCK_REFS_WST" -eq 1 ] && \
        grep -r --include="*.rs" --include="*.toml" -l "omni.wst.core\|omni_wst_core\|omni_ffi\b" \
                "$LOCK_DIR" || true
    FAIL=1
else
    echo "OK"
fi

# ── Result
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "check_ffi_separation: all checks passed"
else
    echo "check_ffi_separation: FAILED (see above)"
    exit 1
fi
