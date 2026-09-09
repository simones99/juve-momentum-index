#!/bin/bash
# Pings the backend's /admin/poll-live endpoint every couple of minutes (see
# ~/Library/LaunchAgents/com.juventum.scheduled-live-poll.plist). Unlike
# scheduled_ingest.sh, this never touches Docker or the DB directly: the
# endpoint itself is cheap on days with no Juventus match (one indexed DB
# query, no football-data.org call), so it's safe to call unconditionally on
# a tight interval — whether BACKEND_URL points at a local backend or the
# deployed Render one.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/scheduled-live-poll.log"
ENV_FILE="$PROJECT_DIR/backend/.env"

mkdir -p "$PROJECT_DIR/logs"
exec >> "$LOG_FILE" 2>&1

echo "=== Scheduled live poll run: $(date) ==="

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

if [ -z "${ADMIN_TOKEN:-}" ]; then
  echo "ERROR: ADMIN_TOKEN not set (check $ENV_FILE), aborting."
  exit 1
fi

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

http_status=$(curl -s -o "$response_file" -w "%{http_code}" \
  -X POST "$BACKEND_URL/api/v1/admin/poll-live" \
  -H "X-Admin-Token: $ADMIN_TOKEN")

echo "HTTP $http_status: $(cat "$response_file")"
echo "=== Done: $(date) ==="

if [ "$http_status" -lt 200 ] || [ "$http_status" -ge 300 ]; then
  exit 1
fi
