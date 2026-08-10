#!/usr/bin/env bash
# clean_macos_metadata.sh — Remove macOS AppleDouble metadata pollution.
#
# When /Volumes/MC-BRAIN is mounted (SMB/NFS) and you run `npm install`,
# `git`, `cp`, etc. the kernel writes `._*` shadow files alongside every
# real file. These pollute directory listings, confuse `find`, and can
# break CSV parser wildcards. Run this script periodically.
#
# Usage:
#   tools/clean_macos_metadata.sh           # clean the whole repo
#   tools/clean_macos_metadata.sh path/...  # clean a specific subtree
#
# Idempotent. Safe to run after any `npm install` or `git pull` on a
# non-APFS volume.
#
# Requires: dot_clean (ships with macOS, /usr/sbin/dot_clean)

set -euo pipefail

if ! command -v dot_clean >/dev/null 2>&1; then
    echo "ERROR: dot_clean not found in PATH. This script is macOS-only." >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$ROOT}"

echo "Cleaning macOS AppleDouble metadata under: $TARGET"
dot_clean "$TARGET" 2>/dev/null || true

# dot_clean sometimes misses files in directories it didn't traverse
# (e.g. just-created ones). Belt-and-suspenders: also remove any
# remaining `._*` shadow files that have a real sibling.
strays=$(find "$TARGET" -name "._*" -not -path "*/.git/*" 2>/dev/null || true)
if [ -n "$strays" ]; then
    echo "Removing $(echo "$strays" | wc -l | tr -d ' ') stray AppleDouble files..."
    # Only delete if a non-shadow sibling exists at the same path
    echo "$strays" | while IFS= read -r f; do
        sibling="${f#./}"
        real="${sibling#./}"
        real="${real#./}"
        # Strip the leading ._ from the basename
        dir=$(dirname "$real")
        base=$(basename "$real")
        unshadowed="${dir}/${base#._}"
        if [ -f "$unshadowed" ] || [ -d "$unshadowed" ]; then
            rm -f "$real"
        fi
    done
fi

remaining=$(find "$TARGET" -name "._*" -not -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
echo "Done. Remaining ._* files: $remaining"
