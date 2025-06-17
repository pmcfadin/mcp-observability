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
  # Does this epic still have any OPEN tasks?
  if gh issue view "$EPIC" --json taskLists -q '.taskLists[].items[] | select(.state=="OPEN")' | grep -q .; then
    echo "⏭️  Epic #$EPIC still has open tasks – skipping."
  else
    echo "✅  Closing epic #$EPIC – no open child tasks remain."
    gh issue close "$EPIC" --comment "✅ All child tasks closed – housekeeping auto-close." | cat
  fi
  echo "---"
done

echo "🏁  Finished housekeeping." 