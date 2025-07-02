#!/usr/bin/env bash

# gh-progress.sh
# Usage: ./scripts/gh-progress.sh <ISSUE_NUMBER> <EMOJI> <MESSAGE>
# Example: ./scripts/gh-progress.sh 42 "🚧" "Working on Helm package logic"

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <ISSUE_NUMBER> <EMOJI> <MESSAGE>" >&2
  exit 1
fi

ISSUE_NUMBER=$1
EMOJI=$2
shift 2
MESSAGE=$*

# shellcheck disable=SC2086
GH_MESSAGE="${EMOJI} ${MESSAGE}"

gh issue comment "$ISSUE_NUMBER" --body "$GH_MESSAGE"

echo "Commented on issue #$ISSUE_NUMBER: $GH_MESSAGE"
