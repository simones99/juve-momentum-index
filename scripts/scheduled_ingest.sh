#!/bin/bash
# Runs the football-data.org ingestion once a day (see
# ~/Library/LaunchAgents/com.juventum.scheduled-ingest.plist), late enough
# that all of that day's matches are finished. Starts Docker/the db
# container only if they weren't already running, and stops only what it
# started, so it doesn't disturb an active `docker compose up` dev session.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/scheduled-ingest.log"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
exec >> "$LOG_FILE" 2>&1

echo "=== Scheduled ingest run: $(date) ==="

DOCKER_WAS_RUNNING=true
if ! docker info >/dev/null 2>&1; then
  DOCKER_WAS_RUNNING=false
  echo "Docker daemon not running, starting Docker Desktop..."
  open -a Docker
  for _ in $(seq 1 60); do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
  if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon did not come up within 120s, aborting."
    exit 1
  fi
fi

DB_WAS_RUNNING=false
db_id="$(docker compose ps -q db 2>/dev/null)"
if [ -n "$db_id" ] && [ "$(docker inspect -f '{{.State.Running}}' "$db_id" 2>/dev/null)" = "true" ]; then
  DB_WAS_RUNNING=true
fi

docker compose up -d db
for _ in $(seq 1 30); do
  db_id="$(docker compose ps -q db 2>/dev/null)"
  status="$(docker inspect -f '{{.State.Health.Status}}' "$db_id" 2>/dev/null || echo "")"
  [ "$status" = "healthy" ] && break
  sleep 2
done

docker compose run --rm ingest
ingest_status=$?

if [ "$DB_WAS_RUNNING" = false ]; then
  docker compose stop db >/dev/null 2>&1
fi

if [ "$DOCKER_WAS_RUNNING" = false ]; then
  osascript -e 'quit app "Docker"' >/dev/null 2>&1
fi

echo "=== Done (exit $ingest_status): $(date) ==="
exit $ingest_status
