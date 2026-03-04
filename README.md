# streamer-activity-notify

MVP backend scaffold for streamer activity notification app.

## Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
```

## Initial tables
- users
- streamers
- source_accounts
- watch_targets
- events
- notifications
