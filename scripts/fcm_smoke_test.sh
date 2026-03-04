#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Requires API + DB up and migrated.
# Optional envs: USER_ID, STREAMER_ID
: "${USER_ID:=1}"
: "${STREAMER_ID:=1}"

if [ -f docker-compose.yml ]; then
  echo "Running FCM smoke test in backend container..."
  docker compose exec -e USER_ID="$USER_ID" -e STREAMER_ID="$STREAMER_ID" backend \
    python -c "from app.smoke_fcm import run; run(user_id=int('$USER_ID'), streamer_id=int('$STREAMER_ID'))"
else
  echo "docker-compose.yml not found"
  exit 1
fi
