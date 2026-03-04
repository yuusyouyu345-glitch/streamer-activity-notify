#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/backend"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install -r requirements.txt >/dev/null

: "${DATABASE_URL:=postgresql+psycopg2://postgres:postgres@localhost:5432/streamer_notify}"
export DATABASE_URL

alembic -c alembic.ini upgrade head
python -m app.seed_demo

echo "----------------------------------------"
echo "E2E ready"
echo "1) API start: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "2) Open UI files:"
echo "   - frontend/index.html"
echo "   - frontend/notification-settings.html"
echo "   - frontend/timeline.html"
echo "   - frontend/ops.html"
echo "----------------------------------------"
