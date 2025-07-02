#!/usr/bin/env bash
# close_epics.sh – housekeeping helper for GitHub Issues
#
# Closes any open "epic" issues (label: epic) that have no unchecked task-list items.
# Requires: GitHub CLI (`gh`) authenticated with repo scope and jq.

set -euo pipefail

printf "\n🔍  Scanning for epics ready to close …\n\n"

# List all open issues tagged "epic" and iterate over their numbers.
EPICS=$(gh issue list --label epic --state open --json number -q '.[].number')

if [[ -z "$EPICS" ]]; then
  echo "🎉  No open epics found. Nothing to do."
  exit 0
fi

for EPIC in $EPICS; do
  # Does this epic still have any OPEN child issues referencing it ("Tracks #<EPIC>")?
  OPEN_CHILD_COUNT=$(gh issue list --state open --search "\"Tracks #$EPIC\"" --json number -q "map(select(.number != $EPIC)) | length")

  if [[ "$OPEN_CHILD_COUNT" -gt 0 ]]; then
    echo "⏭️  Epic #$EPIC still has $OPEN_CHILD_COUNT open child issues – skipping."
  else
    echo "✅  Closing epic #$EPIC – no open child issues remain."
    gh issue close "$EPIC" --comment "✅ All child issues closed – housekeeping auto-close." | cat
  fi
  echo "---"
done

echo "🏁  Finished housekeeping."
