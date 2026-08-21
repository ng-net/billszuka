#!/usr/bin/env bash
# check-actions-minutes.sh — Report GitHub Actions minutes used / total for an account.
#
# Usage:
#   tools/check-actions-minutes.sh [owner]      # default: ng-net
#   tools/check-actions-minutes.sh --refresh    # show the gh auth refresh command
#
# Tries the GitHub REST billing endpoint, which needs the `user` OAuth scope
# (or `admin:org` for organization accounts). If the scope is missing, prints
# the exact one-liner to add it and exits non-zero.
#
# Endpoints:
#   GET /users/{user}/settings/billing/actions      (scope: user)
#   GET /orgs/{org}/settings/billing/actions        (scope: admin:org)
#
# Response shape (excerpt):
#   {
#     "total_minutes_used": 1234,
#     "total_paid_minutes_used": 0,
#     "included_minutes": 2000,
#     "minutes_used_breakdown": { "UBUNTU": 1234, "MACOS": 0, "WINDOWS": 0 },
#     "max_minutes_used": 0,
#     "max_minutes_used_time": "1970-01-01T00:00:00Z"
#   }

set -u
OWNER="${1:-ng-net}"
HOST="github.com"

case "$OWNER" in
  --refresh|-h|--help)
    cat <<EOF
tools/check-actions-minutes.sh — check GitHub Actions minutes via gh CLI.

To grant the required OAuth scope, run ONCE in a browser-enabled shell:

    gh auth refresh -h $HOST -s user

(For org accounts, use '-s admin:org' instead.)

Then re-run this script. Token scopes survive across sessions.

Without 'user' (or 'admin:org' for orgs) the billing endpoints return 404
even though the API path is valid.
EOF
    exit 0
    ;;
esac

# Probe active gh auth account + scopes
ACCT="$(gh auth status --hostname "$HOST" 2>&1 | awk -F'account ' '/Logged in to github.com account/ {print $2; exit}')"
[ -z "$ACCT" ] && { echo "ERROR: no active gh auth on $HOST. Run: gh auth login -h $HOST"; exit 2; }

echo "== GitHub Actions minutes for: $OWNER (gh auth account: $ACCT) =="

# Try user-scope endpoint first
RESP="$(gh api "/users/$OWNER/settings/billing/actions" 2>&1)"
RC=$?

if echo "$RESP" | grep -q '"total_minutes_used"'; then
  # Parse and pretty-print
  echo "$RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
used = d.get('total_minutes_used', 0)
included = d.get('included_minutes', 0)
paid = d.get('total_paid_minutes_used', 0)
breakdown = d.get('minutes_used_breakdown', {})
print(f'Total minutes used:      {used}')
print(f'Included quota:          {included}')
print(f'Paid (over-quota) used:  {paid}')
if included:
    pct = used / included * 100
    print(f'Usage:                   {pct:.1f}% of included quota')
if breakdown:
    print('By runner:')
    for k, v in sorted(breakdown.items()):
        print(f'  {k:8s} {v}')
"

elif echo "$RESP" | grep -q 'needs the "user" scope'; then
  echo "✗ Missing 'user' scope on $ACCT token."
  echo
  echo "Run ONCE in a browser-enabled shell:"
  echo "    gh auth refresh -h $HOST -s user"
  echo
  echo "Then re-run: $0 $OWNER"
  echo "(Token scopes are persisted in the macOS keychain — survives sessions.)"
  exit 1

elif echo "$RESP" | grep -q 'Not Found'; then
  # Could be: (a) $OWNER is actually an Org, or (b) typo.
  echo "✗ /users/$OWNER/... returned 404. $OWNER might be an Organization."
  echo "Trying /orgs/$OWNER/settings/billing/actions (needs 'admin:org' scope)..."
  echo
  RESP2="$(gh api "/orgs/$OWNER/settings/billing/actions" 2>&1)"
  if echo "$RESP2" | grep -q '"total_minutes_used"'; then
    echo "$RESP2" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Total minutes used: {d.get(\"total_minutes_used\", 0)} / {d.get(\"included_minutes\", 0)}')
print('Breakdown:', d.get('minutes_used_breakdown', {}))
"
  elif echo "$RESP2" | grep -q 'needs the "admin:org" scope'; then
    echo "✗ $OWNER is an Org. Need 'admin:org' scope:"
    echo "    gh auth refresh -h $HOST -s admin:org"
    exit 1
  else
    echo "✗ Both user and org endpoints failed:"
    echo "$RESP2" | head -3
    exit 1
  fi

else
  echo "✗ Unexpected response:"
  echo "$RESP" | head -3
  exit 1
fi
