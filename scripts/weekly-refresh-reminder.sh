#!/usr/bin/env bash
# Weekly, human-in-the-loop reminder to refresh fablegen's model profiles.
#
# The SAFE default scheduler. It does NOT run an agent and does NOT touch git — it only
# reminds you (macOS notification + a due-marker + log line) to run the refresh yourself:
#
#     cd ~/Projects/fablegen && claude   # then: run the refresh-model-profiles skill
#
# Running it interactively keeps a human gate on every web-research and git-push tool call.
# (A fully unattended version would need `claude -p --dangerously-skip-permissions`, i.e. an
# agent with approvals disabled — an opt-in you enable yourself; see scripts/README.md.)
set -euo pipefail

FABLEGEN_DIR="${FABLEGEN_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="$FABLEGEN_DIR/scripts/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y-%m-%d)"

echo "$STAMP profile-refresh due" >>"$LOG_DIR/reminders.log"
: >"$LOG_DIR/REFRESH-DUE"   # marker file: presence means "a refresh is pending"

MSG="fablegen model profiles: weekly refresh due. Run the refresh-model-profiles skill."
if command -v osascript >/dev/null 2>&1; then
  osascript -e "display notification \"$MSG\" with title \"fablegen\" sound name \"Ping\"" || true
fi
echo "$MSG"
